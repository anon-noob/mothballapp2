"""
Main code cell containing a `CodeEdit` text input and a `RenderViewer` output viewer.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QSizePolicy
)
import mothball_simulation_xz as mxz
import mothball_simulation_y as my

from PyQt5.QtCore import Qt

from PyQt5.QtGui import QColor
from BaseCell import Cell, CodeEdit, RenderViewer
from Linters import CodeLinter
from typing import Literal


## Delete newline when ctrl v
## Extend codelinter to handle outputs

class SimulationSection(Cell):
    "Mothball Code Cell, `CodeEdit` as the input field, `RenderViewer` as the output viewer. The actual highlighting is done here, and the highlighting logic is computed in its linter `self.linter`."
    STYLE_DEFAULT = 0
    STYLE_FAST = 1
    STYLE_SLOW = 2
    STYLE_STOP = 3
    STYLE_RETURN = 4
    STYLE_CALCS = 5
    STYLE_SETTER = 6
    STYLE_INPUTS = 7
    STYLE_MODIFIER = 8
    STYLE_NUMBERS = 9
    STYLE_COMMENT = 10
    STYLE_KW_ARG = 11
    STYLE_NEST0 = 12
    STYLE_NEST1 = 13
    STYLE_NEST2 = 14
    STYLE_ERROR = 15

    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, remove_callback, add_callback, move_callback, change_callback, mode: Literal["xz","y"]):
        super().__init__(generalOptions, colorOptions, textOptions, "code")
        self.mode = mode
        self.words = []
        self.raw_output = []
        self.linter = CodeLinter(generalOptions, colorOptions, textOptions, mode)

        content_layout = QVBoxLayout()
        self.input_label = QLabel("Input:")
        self.input_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Keep label height fixed
        content_layout.addWidget(self.input_label)

        self.input_field = CodeEdit(generalOptions, colorOptions, textOptions, self)
        self.input_field.textChanged.connect(self.highlight)
        self.input_field.textChanged.connect(change_callback)
        self.input_field.setMatchedBraceForegroundColor(QColor("lime"))
        self.input_field.setUnmatchedBraceForegroundColor(QColor('red'))
        self.input_field.setUnmatchedBraceBackgroundColor(QColor("#4F4F4F"))
        self.input_field.setMatchedBraceBackgroundColor(QColor("#4F4F4F"))

        self.bracket_colors = {0:self.STYLE_NEST0, 1:self.STYLE_NEST1, 2:self.STYLE_NEST2}

        content_layout.addWidget(self.input_field)

        self.output_label = QLabel("Output:")
        self.output_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Keep label height fixed
        content_layout.addWidget(self.output_label)

        self.output_field = RenderViewer(generalOptions, colorOptions, textOptions, self)
        self.output_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.output_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output_field.verticalScrollBar().setVisible(False)
        self.output_field.textChanged.connect(self.adjust_output_height)

        content_layout.addWidget(self.output_field)

        content_layout.addStretch(1)  # Add stretch at the end to push widgets up

        self.main_layout.addLayout(content_layout)
        self.setLayout(self.main_layout)

        self.up_button.clicked.connect(lambda: move_callback(self, -1))
        self.down_button.clicked.connect(lambda: move_callback(self, 1))
        self.run_button.clicked.connect(self.run_simulation)
        self.delete_button.clicked.connect(lambda: remove_callback(self))
        self.add_xz_button.clicked.connect(lambda: add_callback(self, "xz"))
        self.add_y_button.clicked.connect(lambda: add_callback(self, "y"))
        self.add_text_button.clicked.connect(lambda: add_callback(self, "text"))

        self.adjust_output_height()

    def highlight(self):
        "Get tokens to lint from `self.linter`, an object of `Linters.CodeLinter`, and colorize."
        text = self.input_field.text()
        self.input_field.SendScintilla(self.input_field.SCI_STARTSTYLING, 0, len(text))
        tokens = self.linter.lintTexttoTokens(text)
        for token, style in tokens:
            self.input_field.SendScintilla(self.input_field.SCI_SETSTYLING, len(token), style)

    def adjust_output_height(self):
        "Set height based on height needed to display all content without scrolling."
        doc = self.output_field.document()
        margins = self.output_field.contentsMargins()
        height = int(doc.size().height()) + margins.top() + margins.bottom()
        self.output_field.setFixedHeight(height)

    def run_simulation(self):
        "Execute the Mothball code and show its output."
        text = self.input_field.text()
        try:
            if self.mode == "xz":
                p = mxz.Player()
            elif self.mode == "y":
                p = my.Player()
            p.simulate(text)
            self.output_field.renderTextfromOutput(self.linter, p.output)
            self.raw_output = p.output
        except Exception as e:
            output = [(f"Error: {e}", 'normal')]
            self.output_field.renderTextfromOutput(self.linter, output)
            self.raw_output = output

    
    def resizeEvent(self, event):
        self.adjust_output_height()
        super().resizeEvent(event)