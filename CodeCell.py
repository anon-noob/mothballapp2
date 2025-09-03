"""
Main code cell containing a `CodeEdit` text input and a `RenderViewer` output viewer.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QSizePolicy
)
import MothballSimulationXZ as mxz
import MothballSimulationY as my

from PyQt5.QtCore import Qt

from PyQt5.QtGui import QColor
from BaseCell import Cell, CodeEdit, RenderViewer
from Linters import CodeLinter
from Enums import *
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QFileDialog, QWidget, QComboBox
import os, json
# import glob
# from pathlib import Path


## Delete newline when ctrl v
## Extend codelinter to handle outputs

if 0:
    import Mothball

class SimulationSection(Cell):
    "Mothball Code Cell, `CodeEdit` as the input field, `RenderViewer` as the output viewer. The actual highlighting is done here, and the highlighting logic is computed in its linter `self.linter`."
    def __init__(self, parent, generalOptions: dict, colorOptions: dict, textOptions: dict, remove_callback, add_callback, move_callback, change_callback, mode: CellType):
        super().__init__(parent, generalOptions, colorOptions, textOptions, mode)
        self.mode = mode
        self.words = []
        self.raw_output = []
        self.linter = CodeLinter(generalOptions, colorOptions, textOptions, mode)
        self.mc_macros_folder = generalOptions["Path to Minecraft Macro Folder"]
        self.macros = {}
        self.p: Mothball.MainWindow = parent # The main Mothball instance 

        content_layout = QVBoxLayout()
        if mode == CellType.XZ:
            self.input_label = QLabel("Input (XZ):")
        else:
            self.input_label = QLabel("Input (Y):")
        self.input_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Keep label height fixed
        content_layout.addWidget(self.input_label)

        self.input_field = CodeEdit(generalOptions, colorOptions, textOptions, self)
        self.input_field.textChanged.connect(self.highlight)
        self.input_field.textChanged.connect(change_callback)
        self.input_field.setMatchedBraceForegroundColor(QColor("lime"))
        self.input_field.setUnmatchedBraceForegroundColor(QColor('red'))
        self.input_field.setUnmatchedBraceBackgroundColor(QColor("#4F4F4F"))
        self.input_field.setMatchedBraceBackgroundColor(QColor("#4F4F4F"))

        self.bracket_colors = {0:Style.NEST0, 1:Style.NEST1, 2:Style.NEST2}

        content_layout.addWidget(self.input_field)

        self.output_and_artifacts = QWidget()
        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.output_and_artifacts.setLayout(hlayout)

        self.output_label = QLabel("Output:")
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.output_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Keep label height fixed
        hlayout.addWidget(self.output_label)
        

        self.artifacts_produced_label = QLabel("Macros:")
        self.artifacts_produced_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Keep label height fixed
        hlayout.addWidget(self.artifacts_produced_label)
        self.artifacts_produced_label.hide()
        self.artifacts_list = QComboBox()
        hlayout.addWidget(self.artifacts_list)
        self.artifacts_list.hide()
        content_layout.addWidget(self.output_and_artifacts)
        
        self.view_macro = QPushButton("View")
        self.view_macro.hide()
        hlayout.addWidget(self.view_macro)
        self.view_macro.clicked.connect(self.viewMacro)

        self.save_to_folder_button = QPushButton("Save")
        self.save_to_folder_button.hide()
        hlayout.addWidget(self.save_to_folder_button)
        self.save_to_folder_button.clicked.connect(self.saveToFolder)

        # Popup for save success
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWindowFlags(Qt.WindowType.ToolTip)
        self.message_label.hide()
        hlayout.addWidget(self.message_label)

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
        self.add_xz_button.clicked.connect(lambda: add_callback(self, CellType.XZ))
        self.add_y_button.clicked.connect(lambda: add_callback(self, CellType.Y))
        self.add_text_button.clicked.connect(lambda: add_callback(self, CellType.TEXT))

        self.adjust_output_height()

    def viewMacro(self):
        file = self.artifacts_list.currentText()
        _ , ext = os.path.splitext(file)
        if ext == '.json':
            exttype = MacroFileExtension.CYV_JSON
        elif ext == '.csv':
            exttype = MacroFileExtension.MPK_CSV
        
        self.p.openMacroViewer(file,self.macros[file],exttype)

    def saveToFolder(self):
        if not self.mc_macros_folder:
            # self.message_label.setText(f"No folder destination was set")
            # self.message_label.setStyleSheet("background-color: " + "#dff0d8" "; color: "+"#763c3c"+"; border: 1px solid "+"#763c3c"+"; padding: 4px;")
            # self.message_label.show()
            # return
            self.mc_macros_folder = r"C:\Users\bryan\AppData\Roaming\.minecraft\MPKMod\macros"
        if os.path.exists(self.mc_macros_folder):
            file = self.artifacts_list.currentText()
            _ , ext = os.path.splitext(file)
            with open(os.path.join(self.mc_macros_folder, file), "w") as f:
                if ext == '.json':
                    json.dump(self.macros[file], f)
                    self.message_label.setText(f"Saved to {self.mc_macros_folder}")
                    self.message_label.setStyleSheet("background-color: #dff0d8; color: #3c763d; border: 1px solid #3c763d; padding: 4px;")
                    self.message_label.show()
                elif ext == '.csv':
                    f.write(self.macros[file])
                    self.message_label.setText(f"Saved to {self.mc_macros_folder}")
                    self.message_label.setStyleSheet("background-color: #dff0d8; color: #3c763d; border: 1px solid #3c763d; padding: 4px;")
                    self.message_label.show()
        else:
            self.message_label.setText(f"Folder {self.mc_macros_folder} doesn't exist")
            self.message_label.setStyleSheet("background-color: " + "#dff0d8" "; color: "+"#763c3c"+"; border: 1px solid "+"#763c3c"+"; padding: 4px;")
            self.message_label.show()

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
            if self.mode == CellType.XZ:
                p = mxz.PlayerSimulationXZ()
            elif self.mode == CellType.Y:
                p = my.PlayerSimulationY()
            p.simulate(text)
            self.output_field.renderTextfromOutput(self.linter, p.output)
            self.raw_output = p.output
            
            if self.mode == CellType.XZ:
                if p.macros:
                    self.artifacts_list.clear()
                    self.artifacts_produced_label.show()
                    self.artifacts_list.show()
                    self.view_macro.show()
                    self.save_to_folder_button.show()
                    for name, artifact in p.macros.items():
                        self.artifacts_list.addItem(name)
                    self.macros = p.macros

        except Exception as e:
            output = [(ExpressionType.TEXT, f"Error: {e}")]
            self.output_field.renderTextfromOutput(self.linter, output)
            self.raw_output = output
    
    def resizeEvent(self, event):
        self.adjust_output_height()
        super().resizeEvent(event)
    
    def closeEvent(self, a0):

        return super().closeEvent(a0)