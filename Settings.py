"""
Settings Window using `QTabWidget`.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QTabWidget, QWidget,QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton, QTabBar, QLabel, QCheckBox, QLineEdit, QTextBrowser, QSizePolicy, QListWidget, QListWidgetItem, QColorDialog
)
from PyQt5.QtGui import QColor
from BaseCell import RenderViewer
from Linters import CodeLinter, MDLinter
import mothball_simulation_xz as mxz
from typing import Literal

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
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict):
        super().__init__()
        self.generalOptions = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions

        self.setWindowTitle('QTabWidget Example')
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
        self.tab_widget.addTab(self.tab3, "Preferences")
        # self.tab_widget.addTab(self.tab4, "General")

        # Tab 1 content #######################################
        self.tab1_layout = QHBoxLayout()
        self.cell = RenderViewer(generalOptions, colorOptions, textOptions,self)
        self.mdlinter = MDLinter(generalOptions, colorOptions, textOptions)
        self.linter = CodeLinter(generalOptions, colorOptions, textOptions,"xz")
        self.colorCodeDisplay()

        self.tab1_layout.addWidget(self.cell)
        self.tab1.setLayout(self.tab1_layout)
        self.colorsWidget = colorOptions["Code"]
        self.outputWidget = colorOptions["Output"]

        self.listwidget = QListWidget()
        for token, color in self.colorsWidget.items():
            x = QListWidgetItem(token)
            self.listwidget.addItem(x)
            x.setBackground(QColor(color))
            x.setForeground(QColor("#000000"))
        
        self.tab1_layout.addWidget(self.listwidget)
        self.listwidget.itemDoubleClicked.connect(lambda i: self.colorDialog(i, 0))

        # Tab 2 content ############################################
        self.tab2_layout = QHBoxLayout()
        self.cell2 = RenderViewer(generalOptions,colorOptions,textOptions,self)
        self.colorCodeOutputDisplay()

        self.tab2_layout.addWidget(self.cell2)
        self.tab2.setLayout(self.tab2_layout)
        self.colorsWidget = colorOptions["Code"]
        self.outputWidget = colorOptions["Output"]

        self.listwidget2 = QListWidget()
        for token, color in self.outputWidget.items():
            x = QListWidgetItem(token)
            self.listwidget2.addItem(x)
            x.setBackground(QColor(color))
            x.setForeground(QColor("#000000"))
        
        self.tab2_layout.addWidget(self.listwidget2)
        self.listwidget2.itemDoubleClicked.connect(lambda i: self.colorDialog(i, 1))

        # Tab 3 content ######################################
        self.tab3_layout = QGridLayout()
        checkbox = QCheckBox("Ask before deleting a cell")
        checkbox.setToolTip("When toggled on, always confirm twice before deleting a cell.")
        checkbox.setStyleSheet("""QToolTip {background-color:" + "#D4C00C" + ";color:" + "#ffffff" + "}""")
        self.tab3_layout.addWidget(checkbox, 1, 1,1,2)
        self.tab3_layout.addWidget(QLineEdit(),2,1,1,1)
        maxlines = QLabel("Max Lines")
        maxlines.setToolTip("Cells display using at most x lines. Minimum 10 lines.\nSet to any number less than 10 to indicate infinite lines allowed.")
        maxlines.setStyleSheet("""QToolTip {background-color:" + "#D4C00C" + ";color:" + "#ffffff" + "}""")
        self.tab3_layout.addWidget(maxlines,2,2,1,1)
        self.tab3_layout.addWidget(QPushButton("Save"),3,1,1,2)
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
        p=mxz.Player()
        try:
            p.simulate(SettingsWindow.SAMPLE_CODE)
        except Exception as e:
            p.output = [(f"Error: {e}", "normal")]
        self.cell2.renderTextfromOutput(self.linter, p.output)

if __name__ == '__main__':
    import FileHandler
    a=FileHandler.getCodeColorSettings()
    b=FileHandler.getGeneralSettings()
    c=FileHandler.getTextColorSettings()
    app = QApplication(sys.argv)
    window = SettingsWindow(b,a,c)
    window.show()
    sys.exit(app.exec_())
