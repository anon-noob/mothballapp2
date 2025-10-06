"""
Main markdown text cell containing a `CodeEdit` text input and a `RenderViewer` output viewer.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel,QSizePolicy, QStackedLayout
)
from BaseCell import Cell, CodeEdit, RenderViewer
from Linters import MDLinter
from typing import Literal
from Enums import *

class TextSection(Cell):
    """
    Markdown Cell with a `CodeEdit` input and a `RenderViewer` output. This cell alternates between showing `CodeEdit` in edit mode, and `RenderViewer` in render mode.
    """

    def __init__(self, parent, generalOptions: dict, colorOptions: dict, textOptions: dict, remove_callback, add_callback, move_callback, change_callback, initialMode: TextCellState):
        super().__init__(parent, generalOptions, colorOptions, textOptions, remove_callback, add_callback, move_callback, change_callback, CellType.TEXT)
        self.mode = initialMode
        self.linter = MDLinter(generalOptions, colorOptions, textOptions)
        self.raw_text = ""

        content_layout = QVBoxLayout()
        self.input_label = QLabel("Text:")
        self.input_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        content_layout.addWidget(self.input_label)

        # Create both widgets
        self.input_field = CodeEdit(generalOptions, colorOptions, textOptions, self)
        self.input_field.textChanged.connect(self.highlight)
        self.input_field.textChanged.connect(change_callback)

        self.render_field = RenderViewer(generalOptions, colorOptions, textOptions, self)
        # self.render_field.setOpenExternalLinks(True)
        self.render_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Use QStackedLayout to stack input and render fields
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.input_field)
        self.stacked_layout.addWidget(self.render_field)
        self.stacked_layout.setCurrentWidget(self.input_field)
        content_layout.addLayout(self.stacked_layout)

        content_layout.addStretch(1)
        self.main_layout.addLayout(content_layout)
        self.setLayout(self.main_layout)

        self.run_button.clicked.connect(self.renderText)
    
    def adjust_output_height(self):
        """
        Set rendered text's height based on height needed to display all content without scrolling.
        """
        doc = self.render_field.document()
        margins = self.render_field.contentsMargins()
        height = int(doc.size().height()) + margins.top() + margins.bottom()
        self.render_field.setFixedHeight(height)
    
    def highlight(self):
        """
        Get tokens to lint from `self.linter`, an object of `Linters.MDLinter`, and colorize.
        """
        text = self.input_field.text()
        tokens = self.linter.parseTextToHighlight(text)
        self.input_field.SendScintilla(self.input_field.SCI_STARTSTYLING, 0, len(text))
        for token, style in tokens:
            self.input_field.SendScintilla(self.input_field.SCI_SETSTYLING, len(token), style)
    
    def renderText(self):
        """
        Render the markdown into html text. Mode set from "edit" to "render" mode.
        """
        self.raw_text = self.input_field.text()
        self.render_field.renderTextfromMarkdown(self.linter, self.raw_text)
        self.stacked_layout.setCurrentWidget(self.render_field)
        self.run_button.clicked.disconnect(self.renderText)
        self.run_button.clicked.connect(self.editText)
        self.adjust_output_height()
        self.mode = "render"

    def editText(self):
        """
        Switch back from rendered mode to edit mode.
        """
        self.input_field.setText(self.raw_text)
        self.stacked_layout.setCurrentWidget(self.input_field)
        self.run_button.clicked.disconnect(self.editText)
        self.run_button.clicked.connect(self.renderText)
        self.highlight()
        self.mode = "edit"
    
    def getCellData(self):
        data = {
            "raw_text": self.input_field.text(),
            "cell_type": self.cellType,
            "mode": self.mode,
            "has_changed": False
        }
        return data

    def resizeEvent(self, event):
        if not self.render_field.isHidden():
            self.adjust_output_height()
            super().resizeEvent(event)