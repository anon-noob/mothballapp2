from PyQt5.QtWidgets import QMainWindow, QTableView, QVBoxLayout, QWidget, QMenu, QFileDialog, QMessageBox, QTabWidget, QHBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QFont
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
            indexes = [A.get('W', -1), A.get('A', -1), A.get('S', -1), A.get('D', -1), A.get('JUMP', -1), A.get('SPRINT', -1), A.get('SNEAK', -1), A.get('ANGLE_X',-1), A.get('ANGLE_Y', -1)]
            for i in range(1, len(lines)):
                m = []
                k = lines[i].split(",")
                for ii in indexes:
                    if ii == -1:
                        m.append(y['false'])
                    else:
                        m.append(y.get(k[ii], k[ii]))
                result.append(m)
            self.formatted_data = result

        elif self.src == MacroFileExtension.CYV_JSON:
            self.raw_data = [["W","A",'S',"D","Space", "Sprint", "Sneak","Yaw", "Pitch"]] + self.raw_data
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


    def toMothball(self, strict_sprint: bool, no_sprint_sneak: bool, jump_duration: int):
        # strict sprint: unsprinting in a macro will unsprint in mothball
        # no sneak sprint: any sneak is walk, not sprint
        # this needs serious refactoring hELP
        # strict sprint
        n = []
        prev_sprint = False
        for i in self.formatted_data[1:]:
            w,a,s,d, space, sprint, sneak, yaw, pitch = i
            sp = (True if (not strict_sprint and prev_sprint and w != "X") else sprint != "X")
            n.append([w != "X", a != "X", s != "X", d != "X", space != "X", sp, sneak != "X", yaw, pitch])
            prev_sprint = sp

        # no sprint sneak
        m = []
        for i in n:
            w,a,s,d, space, sprint, sneak, yaw, pitch = i
            m.append([w,a,s,d, space, (False if no_sprint_sneak and sneak else sprint), sneak, yaw, pitch])
        

        # WASD Space Sprint Sneak Yaw Pitch
        cmds = []
        turns = []
        current_airtime = 0
        in_air = False

        for i in m:
            # sneak?, walk/sprint/stop?, jump?, '.', forward?, strafe?
            
            p = ['','','','.','','']
            w,a,s,d, space, sprint, sneak, yaw, pitch = i
            turns.append(round(float(yaw),3))

            if sneak:
                p[0] = "sn"
            if sprint and w:
                p[1] = "s"
            elif not sneak and (w or a or s or d):
                p[1] = "w"
            elif not (w or a or s or d):
                p[1] = "st"
            if space:
                p[2] = "j"
                in_air = True
                current_airtime = 1
            else:
                if in_air and current_airtime + 1 <= jump_duration:
                    current_airtime += 1
                    p[2] = "a"
                elif in_air and current_airtime + 1 > jump_duration:
                    in_air = False
            
            if w and not s:
                p[4] = "w"
            elif s and not w:
                p[4] = "s"
            if a and not d:
                p[5] = "a"
            elif d and not a:
                p[5] = "d"
            
            if p[4] != 's' and not p[5]:
                p[4] = ''
                p[3] = ''
            
            cmds.append(''.join(p))

            


        # compression turns
        turns2 = {}
        last_nonzero = 0
        encountered_zero = False
        for i,turn in enumerate(turns):
            if last_nonzero != i and turn and not encountered_zero:
                turns2[last_nonzero].append(str(turn))
            else:
                if turn:
                    last_nonzero = i
                    turns2[last_nonzero] = [str(turn)]
                    encountered_zero = False
                else:
                    encountered_zero = True
        
        # Insert
        newcmds = []
        for i,x in enumerate(cmds):
            if i in turns2:
                if len(turns2[i]) == 1:
                    newcmds.append(f"turn({turns2[i][0]})")
                else:
                    newcmds.append(f"tq({','.join(turns2[i])})")
            newcmds.append(x)

        # compress movement cmds
        cmds2 = []
        prev = newcmds[0]
        count = 1
        for i in newcmds[1:]:
            if i == prev:
                count += 1
            elif i != prev:
                if count > 1:
                    cmds2.append(prev + f"({count})")
                else:
                    cmds2.append(prev)
                count = 1
                prev = i
        else:
            if count > 1:
                cmds2.append(prev + f"({count})")
            else:
                cmds2.append(prev)

        return cmds2
    
class MacroViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Viewer")
        self.opened_files = []

        self.setStyleSheet("""QToolTip { 
                           background-color: #2e2e2e; 
                           color: white; 
                           border: black solid 1px
                           }""")

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

        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)


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

        l.addWidget(table)

        rightside = QVBoxLayout()

        nss_btn = QPushButton("No Sprint Sneak")
        nss_btn.setCheckable(True)
        nss_btn.setToolTip("When toggled, any sneak tick is unsprinted.")
        nss_btn.setStyleSheet("QPushButton::checked {background-color: #2980b9} QToolTip {background-color: #2e2e2e; color:white}")
        rightside.addWidget(nss_btn)

        ss_btn = QPushButton("Strict Sprint")
        ss_btn.setCheckable(True)
        ss_btn.setToolTip("When toggled, it will match sprint and unsprint ticks directly, even if it is not possible in game.")
        ss_btn.setStyleSheet("QPushButton::checked {background-color: #2980b9} QToolTip {background-color: #2e2e2e; color:white}")
        rightside.addWidget(ss_btn)

        jump_duration_layout = QHBoxLayout()
        label = QLabel("Jump Duration")
        label.setToolTip("The default duration of a jump. For example, a jump normally lasts 12 ticks.")
        jump_duration_layout.addWidget(label)
        jump_duration_input = QLineEdit()
        jump_duration_input.setText("12")
        jump_duration_layout.addWidget(jump_duration_input)
        rightside.addLayout(jump_duration_layout)

        convert = QPushButton("Convert to Mothball")
        rightside.addWidget(convert)

        output_field = QTextEdit()
        output_field.setFont(QFont("Consolas", 14))
        rightside.addWidget(output_field)
        l.addLayout(rightside)

        convert.clicked.connect(lambda _,m=model,o=output_field,strict_sprint=ss_btn, no_sprint_sneak=nss_btn, j=jump_duration_input: self.getMothballString(m,o, strict_sprint, no_sprint_sneak,j))
        l.setStretchFactor(table, 2)
        l.setStretchFactor(rightside,1)

        self.tabWidget.addTab(w, basename)
        self.opened_files.append(basename)

    def getMothballString(self, model, output_field, strict_sprint, no_sprint_sneak, jump_duration):
        duration = jump_duration.text()
        try:
            duration = max(0,int(duration))
        except:
            duration = 12
        a = model.toMothball(strict_sprint.isChecked(), no_sprint_sneak.isChecked(), duration)
        output_field.setText(" ".join(a))
        

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