"""
Settings Window using `QTabWidget`.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QTabWidget, QWidget,QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton, QTabBar, QLabel, QCheckBox, QLineEdit, QTextBrowser, QSizePolicy, QListWidget, QListWidgetItem, QColorDialog, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from BaseCell import RenderViewer
from Linters import CodeLinter, MDLinter
import MothballSimulationXZ as mxz
from typing import Literal
from Enums import *
import FileHandler

class SettingsWindow(QWidget):
    """
    The main settings window.
    """
    SAMPLE_CODE = """version(1.21) 
sprint(8, slow=3) sprintair.wd walk.s walk[water](3) stop stopair
outx(0.03125, label=hey I'm an x axis output) vec
wall(1.8125, repeat(sprintjump.wa(4), 2)) zb(2.2, z output)
var(new_var, 37) print(new_var: {new_var})
print(help\, its been 4 years) # comments are \# cool #
func(hello, param, code=print(hello {param} {new_var} times))
hello(mothballer)"""
    APPEND_ERROR = """
# parenthesis # (( { ( {{}} ) } ))
( 4..5 #ERRORS#"""
    def __init__(self, parent, generalOptions: dict, colorOptions: dict, textOptions: dict):
        super().__init__()
        self.generalOptions = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.p = parent

        self.setWindowTitle('Settings')
        self.setGeometry(100, 100, 900, 600)
        
        # Create QTabWidget
        self.tab_widget = QTabWidget(self)
        self.setStyleSheet("""background-color: #2e2e2e; color: #ffffff; font-size: 12pt""")
        
        # Add tabs to the QTabWidget
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        # self.tab4 = QWidget()

        # Set tab contents
        self.tab_widget.addTab(self.tab1, "Code Editing")
        self.tab_widget.addTab(self.tab2, "Code Output")
        self.tab_widget.addTab(self.tab3, "Macro Paths")

        #######################################################
        # Tab 1 content #######################################
        #######################################################
        self.tab1_vertical_layout = QVBoxLayout()
        self.tab1_layout = QHBoxLayout()
        self.cell = RenderViewer(generalOptions, colorOptions, textOptions,self)
        self.mdlinter = MDLinter(generalOptions, colorOptions, textOptions)
        self.linter = CodeLinter(generalOptions, colorOptions, textOptions,CellType.XZ)
        self.colorCodeDisplay()

        self.tab1_layout.addWidget(self.cell)
        self.tab1.setLayout(self.tab1_vertical_layout)
        self.colorsWidget = colorOptions[StringLiterals.CODE]
        

        self.listwidget = QListWidget()
        for style in self.colorsWidget:
            x = QListWidgetItem(Style.STYLE_TO_NAME[style])
            color = self.colorsWidget.get(style)
            if color is None:
                self.listwidget.addItem(f"CANT FIND STYLE {style}")
            else:
                self.listwidget.addItem(x)
                x.setBackground(QColor(self.colorsWidget[style]))
            x.setForeground(QColor("#000000"))
        
        self.tab1_layout.addWidget(self.listwidget)
        self.listwidget.itemDoubleClicked.connect(lambda i: self.colorDialog(i, 0))

        self.tab1_vertical_layout.addLayout(self.tab1_layout)
        self.tab1_bottom_buttons_layout = QHBoxLayout()
        self.b = QPushButton("Apply")
        self.tab1_bottom_buttons_layout.addWidget(self.b)
        self.c = QPushButton("New Theme")
        self.tab1_bottom_buttons_layout.addWidget(self.c)
        self.e = QPushButton("Rename Theme")
        self.tab1_bottom_buttons_layout.addWidget(self.e)
        self.f = QPushButton("Delete Theme")
        self.tab1_bottom_buttons_layout.addWidget(self.f)
        self.d = QComboBox()
        self.tab1_bottom_buttons_layout.addWidget(self.d)
        self.tab1_vertical_layout.addLayout(self.tab1_bottom_buttons_layout)

        #######################################################
        # Tab 2 content #######################################
        #######################################################
        self.tab2_layout = QHBoxLayout()
        self.cell2 = RenderViewer(generalOptions,colorOptions,textOptions,self)
        self.colorCodeOutputDisplay()

        self.tab2_layout.addWidget(self.cell2)
        self.tab2.setLayout(self.tab2_layout)
        
        self.outputWidget = colorOptions[StringLiterals.OUTPUT]

        self.listwidget2 = QListWidget()
        for token, color in self.outputWidget.items():
            x = QListWidgetItem(Style.STYLE_TO_NAME[token])
            self.listwidget2.addItem(x)
            x.setBackground(QColor(color))
            x.setForeground(QColor("#000000"))
        
        self.tab2_layout.addWidget(self.listwidget2)
        self.listwidget2.itemDoubleClicked.connect(lambda i: self.colorDialog(i, 1))

        #######################################################
        # Tab 3 content #######################################
        #######################################################
        self.tab3_layout = QGridLayout()

        self.table = QTableWidget()
        self.table.setRowCount(len(self.generalOptions["Macro Folders"]))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Alias', 'Path'])
        self.table.setStyleSheet("QTableWidget { padding: 10px}"
                                 "QTableWidgetItem { padding-left: 10px; padding-right: 10px}"
                                 "QHeaderView::section {padding-left: 30px; padding-right: 30px; background-color: "+"#565656" + ";color: white;font-weight: bold;} QTableCornerButton::section {background-color: #2e2e2e;}")

        # Populate table with JSON data
        for i, (key, value) in enumerate(self.generalOptions["Macro Folders"].items()):
            self.table.setItem(i, 0, QTableWidgetItem(key))
            self.table.setItem(i, 1, QTableWidgetItem(value))
            y = self.table.item(i, 1)
            y.setFlags(y.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.tab3_layout.addWidget(self.table, 0, 0, 1, 4)

        self.add_btn = QPushButton("Add")
        self.delete_btn = QPushButton("Delete")
        self.edit_pathname_btn = QPushButton("Edit Path")
        self.save_btn = QPushButton("Save")

        self.add_btn.clicked.connect(self.addRow)
        self.delete_btn.clicked.connect(self.deleteRow)
        self.edit_pathname_btn.clicked.connect(self.editPath)
        self.save_btn.clicked.connect(self.savePaths)

        self.add_btn.setToolTip("Add a new path")
        self.delete_btn.setToolTip("Highlight a row and delete path")
        # self.edit_alias_btn.setToolTip("Highlight a cell and edit")
        self.edit_pathname_btn.setToolTip("Highlight a cell and edit")
        self.save_btn.setToolTip("Save these paths")

        self.tab3_layout.addWidget(self.add_btn, 1, 0)
        self.tab3_layout.addWidget(self.delete_btn, 1, 1)
        # self.tab3_layout.addWidget(self.edit_alias_btn, 1, 2)
        self.tab3_layout.addWidget(self.edit_pathname_btn, 1, 2)
        self.tab3_layout.addWidget(self.save_btn, 1, 3)

        self.tab3.setLayout(self.tab3_layout)

        

        # Set the layout for the main window
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: #3f3f3f;
                color: white;
                margin-right: 10px;
                padding: 10px;
            }

            QTabBar::tab:selected {
                background: #2980b9;
                color: white;
            }

            QTabBar::tab:hover {
                background: #5dade2;
            }
        """)

    def addRow(self):
        self.table.insertRow(self.table.rowCount())
        n = self.table.rowCount()
        x = QTableWidgetItem("")
        self.table.setItem(n-1, 0, x)
        y = QTableWidgetItem("")
        self.table.setItem(n-1, 1, y)
        y.setFlags(y.flags() & ~Qt.ItemFlag.ItemIsEditable)
    
    def deleteRow(self):
        self.table.removeRow(self.table.currentRow())
        if not self.table.rowCount():
            self.addRow()

    def editPath(self):
        x = self.table.item(self.table.currentRow(), 1)
        f = self.openfiledialog()
        if f:
            x.setData(0, f)


    def openfiledialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        return folder

    def savePaths(self):
        keys = []
        values = []
        for i in range(self.table.rowCount()):
            keys.append(self.table.item(i, 0).data(0))
            values.append(self.table.item(i, 1).data(0))

        d = {k:v for k,v in zip(keys, values)}
        self.generalOptions["Macro Folders"] = d
        FileHandler.saveGeneralSettings(self.generalOptions)

    def colorDialog(self, item: QListWidgetItem, mode: Literal[0,1]):
        """
        Opens the color dialog invoked by double clicking an item in the `QListWidget`.\\
        The `mode` indicates which `QListWidget` was invoked, `0` for code, `1` for outputs. 
        """
        self.C = QColorDialog()
        c = self.C.getColor(item.background().color())
        if c.isValid():
            item.setBackground(QColor(c.name()))
            if mode == 0:
                self.colorsWidget[item.text()] = c.name()
                self.cell.colorOptions[item.text()] = c.name()
                self.linter.colorOptions[item.text()] = c.name()
                self.colorCodeDisplay()
            elif mode == 1:
                self.outputWidget[item.text()] = c.name()
                self.cell2.colorOptions[item.text()] = c.name()
                self.linter.colorOptions[item.text()] = c.name()
                self.colorCodeOutputDisplay()
                
    def save(self):
        FileHandler.saveCodeColorSettings(self.colorOptions)
        FileHandler.saveTextColorSettings(self.textOptions)
        FileHandler.saveGeneralSettings(self.generalOptions)

    def colorCodeDisplay(self):
        """
        Colorize the code
        """
        bb = [(x[0], x[1], 0) for x in self.linter.lintTexttoTokens(SettingsWindow.SAMPLE_CODE + SettingsWindow.APPEND_ERROR)]
        self.cell.render(bb)

    def colorCodeOutputDisplay(self):
        '''
        Run mothball code and colorize the output
        '''
        p=mxz.PlayerSimulationXZ()
        try:
            p.simulate(SettingsWindow.SAMPLE_CODE)
        except Exception as e:
            p.output = [(f"Error: {e}", "normal")]
        self.cell2.renderTextfromOutput(self.linter, p.output)

if __name__ == '__main__':
    a=FileHandler.getCodeColorSettings()
    b=FileHandler.getGeneralSettings()
    c=FileHandler.getTextColorSettings()
    app = QApplication(sys.argv)
    window = SettingsWindow(None, b,a,c)
    window.show()
    sys.exit(app.exec_())
