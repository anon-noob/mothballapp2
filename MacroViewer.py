from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QMenu, QFileDialog, QMessageBox, QTabWidget
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor
import json
import FileHandler
from Enums import MacroFileExtension
import os

class MacroFileGrid(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.raw_data: list[list[str]] = []
        self.src = 0
        self.formatted_data = []
    
    def setupModel(self, data, src):
        self.raw_data = data
        self.src = src
        if self.src == MacroFileExtension.MPK_CSV:
            lines = self.raw_data.split("\n")
            result = []
            A = {x:i for i, x in enumerate(lines[0].split(","))}
            y = {'true': '✔', 'false':"X"}
            result.append(['W','A','S','D','Space', 'Sprint', 'Sneak','Yaw','Pitch'])
            indexes = [A['W'], A['A'], A['S'], A['D'], A['JUMP'], A['SPRINT'], A['SNEAK'], A['ANGLE_X'], A['ANGLE_Y']]
            for i in range(1, len(lines)):
                m = []
                k = lines[i].split(",")
                for ii in indexes:
                    m.append(y.get(k[ii], k[ii]))
                result.append(m)
            self.formatted_data = result

        elif self.src == MacroFileExtension.CYV_JSON:
            self.raw_data = [["W","A",'S',"D","Space",'Sprint',"Sneak","Yaw", "Pitch"]] + self.raw_data
            self.formatted_data = []
            y = {'true': '✔', 'false':"X"}
            for i in self.raw_data:
                x = []
                for l in i:
                    x.append(y.get(l, l))
                self.formatted_data.append(x)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.formatted_data[0][section]
            else: # Qt.Vertical
                return str(section + 1)

    def data(self, index, role=Qt.DisplayRole):
        value = self.formatted_data[index.row() + 1][index.column()]
        if role == Qt.DisplayRole:
            return value
        if role == Qt.ForegroundRole:
            if value == '✔':
                return QColor("green")
            elif value == 'X':
                return QColor("red")
            try:
                float_val = float(value)
                if float_val > 0:
                    return QColor("orange")
                else:
                    return QColor("yellow")
            except (ValueError, TypeError):
                pass

    
    def rowCount(self, parent=None):
        return len(self.formatted_data) - 1  # Exclude header from row count

    def columnCount(self, parent=None):
        if not self.formatted_data:
            return 0
        return len(self.formatted_data[0])
    
class MacroViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Viewer")
        self.opened_files = []

        self.tabWidget = QTabWidget()
        self.tabWidget.setStyleSheet("""
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

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        container.setStyleSheet("background-color: #2e2e2e; color: white;")
        self.setWindowTitle("Macro Viewer")
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.removeTab)

        self.createMenus()
    
    def removeTab(self, index: int):
        del self.opened_files[index]
        self.tabWidget.removeTab(index)
    
    def addTab(self, filename, data):
        table = QTableView()
        table.setStyleSheet("""
    QHeaderView::section {
        background-color: #2e2e2e;
        color: white;
        font-weight: bold;
    } QTableView {
        background-color: #2e2e2e
    } QTableCornerButton::section {
        background-color: #2e2e2e;
    }
""")
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == ".json":
            src = MacroFileExtension.CYV_JSON
        elif ext == ".csv":
            src = MacroFileExtension.MPK_CSV     

        basename = os.path.basename(filename)
        if basename in self.opened_files:
            index = self.opened_files.index(basename)
            self.tabWidget.setCurrentIndex(index)
            return
        
        model = MacroFileGrid()
        model.setupModel(data, src)
        table.setModel(model)
        table.horizontalHeader().setStretchLastSection(False)
        table.resizeColumnsToContents()

        self.tabWidget.addTab(table, basename)
        self.opened_files.append(basename)  
    
    def createMenus(self):
        menuBar = self.menuBar()
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

        open_from_mothball_action = fileMenu.addAction("Open from Mothball")
        open_from_mc_mods_action = fileMenu.addAction("Open from MC Mods")
        fileMenu.addSeparator()
        

        open_from_mothball_action.triggered.connect(lambda x=0: self.openFile(0))
        open_from_mc_mods_action.triggered.connect(lambda x=1: self.openFile(1))
    
    def openFile(self, src):
        if src == 0:
            src = FileHandler.getMacros()
        elif src == 1:
            src = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".minecraft", "MPKMod", "macros") # TEST
        
        options = QFileDialog.Options()
        file_filter = "CSV Files (*.csv);;JSON Files (*.json)"
        file_path, _ = QFileDialog.getOpenFileName(self,"Open Macro File",src,file_filter,options=options)
        if file_path:
            try:
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                if ext == ".json":
                    with open(file_path) as f:
                        data = json.load(f)
                elif ext == ".csv":
                    with open(file_path) as f:
                        data = f.read()
                else:
                    QMessageBox.warning(self, "Invalid File", "Please select a CSV or JSON file.")
                    return
                # Add header if needed, or handle as appropriate
                self.addTab(file_path, data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")