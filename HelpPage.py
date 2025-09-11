"""
The main documentation window, using `RenderViewer` to display text.
"""

import sys, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QSplitter, QVBoxLayout, QWidget
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QTimer
from TextCell import MDLinter, RenderViewer

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

directory = os.path.join(base_path, "Mothball_Pages")

def loadPage(filename):
    try:
        with open(os.path.join(base_path, "Mothball_Pages", filename)) as f:
            return f.read()
    except Exception as e:
        return f"Could not load page {filename}: {e}"
    
introduction = loadPage("Introduction.txt")
documentationIntro = loadPage("DocumentationIntro.txt")
learnTheBasics = loadPage("LearnTheBasics.txt")
movementDocumentation = loadPage("MovementDocumentation.txt")
movementHelp = loadPage("MovementHelp.txt")
optimizationHelp = loadPage("OptimizationHelp.txt")
outputHelp = loadPage("OutputHelp.txt")
setterHelp = loadPage("SetterHelp.txt")
welcomePage = loadPage("WelcomePage.txt")
usingTheIDE = loadPage("UsingTheIDE.txt")
setterdocumentation = loadPage("SetterDocumentation.txt")

def getHeadings(text: str):
    """
    Gets the headings in markdown formatted `text`, which are all lines that start with `#,##,###`.

    Returns a list of tuples which contain the heading and the heading level. `#` heading level is 0, `##` is 1, `###` is 2.
    """
    headers: list[tuple[str, int]] = []
    in_code_block = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_code_block = not in_code_block

        if not in_code_block:
            if line.startswith("# "):
                headers.append((line[2:], 0))
            elif line.startswith("## "):
                headers.append((line[3:], 1))
            elif line.startswith("### "):
                headers.append((line[4:], 2))
    return headers

class MainWindow(QMainWindow):
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict):
        super().__init__()
        self.generalOptions = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.setWindowTitle("Documentation Viewer")
        self.setGeometry(100, 100, 900, 600)

        self.pages = {
            "Introduction": introduction, 
            "Documentation Intro": documentationIntro, 
            "Basics": learnTheBasics, 
            "Movement Documentation": movementDocumentation, 
            "Movement Help": movementHelp, 
            "Optimization Help": optimizationHelp, 
            "Output Help": outputHelp, 
            "Setter Help": setterHelp,
            "IDE": usingTheIDE, 
            "Setter Documentation": setterdocumentation
        }

        self.current_doc = None  # Track which document is currently loaded

        # Layout using QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # TreeView for the table of contents
        self.tree = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Contents"])
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        splitter.addWidget(self.tree)

        # QTextBrowser for the document viewer
        self.text_browser = RenderViewer(generalOptions,colorOptions,textOptions,self)
        splitter.addWidget(self.text_browser)
        splitter.setStretchFactor(1, 1)

        # Set main layout
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        # Load sample pages
        self.populateTree()

        # Connect selection event
        self.tree.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        QApplication.processEvents()
        self.loadDocument("page9")

    def populateTree(self):
        """
        Populate `QTreeView` with the elements and nesting based on headings of the text.\\
        Additionally, clicking on an element will direct you to the relevant page and scroll to the appropiate section.\\
        Uses hmtl anchors.
        """
        for page_name, page in self.pages.items():
            page_root = QStandardItem(page_name)
            page_root.setEditable(False)
            page_root.setData({"doc": page_name, "anchor": None}, Qt.UserRole)

            last_heading1 = None
            last_heading2 = None
            for heading, lvl in getHeadings(page):
                item = QStandardItem(heading)
                item.setEditable(False)
                item.setData({"doc": page_name, "anchor": heading}, Qt.UserRole)
                if lvl==0:
                    page_root.appendRow(item)
                    last_heading1 = item
                    last_heading2 = None
                elif lvl == 1:
                    last_heading1.appendRow(item)
                    last_heading2 = item
                elif lvl == 2: # DANGEROUS! Temp fix: use heading 1
                    if last_heading2 is not None:
                        last_heading2.appendRow(item)
                    else:
                        last_heading1.appendRow(item)
                    
            
            self.model.appendRow(page_root)
            
    def onSelectionChanged(self, selected, deselected):
        if not selected.indexes():
            return

        index = selected.indexes()[0]
        data = index.data(Qt.UserRole)
        if not data:
            return
        # print(data)

        doc = data.get("doc")
        anchor = data.get("anchor")

        if doc != self.current_doc:
            self.loadDocument(doc)
            self.current_doc = doc

        if anchor:
            QTimer.singleShot(100, lambda: self.text_browser.scrollToAnchor(anchor))

    def loadDocument(self, doc_name: str):
        md = self.pages.get(doc_name, welcomePage)
        self.text_browser.renderTextfromMarkdown(MDLinter(self.generalOptions,self.colorOptions,self.textOptions), md)

if __name__ == "__main__":
    import FileHandler
    a=FileHandler.getCodeColorSettings()
    b=FileHandler.getGeneralSettings()
    c=FileHandler.getTextColorSettings()
    app = QApplication(sys.argv)
    window = MainWindow(b,a,c)
    window.show()
    sys.exit(app.exec_())
