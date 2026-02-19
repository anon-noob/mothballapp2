import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QSplitter, QFrame, QLineEdit, QPushButton, QGridLayout, QComboBox, QTextEdit, QLabel, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
from ExprEval import evaluate

class Container(QWidget):

    finished = pyqtSignal(int, str, list, list) # id, color, x, y
    deleted = pyqtSignal(int) # id
    hidden = pyqtSignal(int) # id

    HIDDEN = 0
    SUCCESS = 1
    ERROR = 2

    def __init__(self, id: int, main_trajectory_xpts: list, main_trajectory_ypts: list):
        """
        main_trajectory_xpts and main_trajectory_ypts are references to a list containing the x and y points which are ALREADY SHIFTED
        meaning that if the points were shifted, then since they reference the same lists, the lines will be redrawn accordingly
        """
        super().__init__()
        layout = QHBoxLayout()
        layout.setSpacing(5)
        self.setLayout(layout)
        self.xpts = []
        self.zpts = []

        self.status = 0

        self.main_x = main_trajectory_xpts
        self.main_y = main_trajectory_ypts

        
        
        self.id = id

        self.isShown = True

        self.status_button = QPushButton(""); self.status_button.setFixedSize(32,32)
        self.status_button.clicked.connect(self.toggle_isshown)
        layout.addWidget(self.status_button,alignment=Qt.AlignmentFlag.AlignTop)
        self.deletebtn = QPushButton("🗑"); self.deletebtn.setFixedSize(32,32)
        self.deletebtn.clicked.connect(self.delete)
        self.combo_box = QComboBox()
        self.combo_box.addItem("Red")
        self.combo_box.setItemData(0, QColor('#ff0000'), Qt.ItemDataRole.TextColorRole)
        
        self.combo_box.addItem("Orange")
        self.combo_box.setItemData(1, QColor("#ff6600"), Qt.ItemDataRole.TextColorRole)
        
        self.combo_box.addItem("Yellow")
        self.combo_box.setItemData(2, QColor("#ffff00"), Qt.ItemDataRole.TextColorRole)

        self.combo_box.addItem("Green")
        self.combo_box.setItemData(3, QColor('#00ff00'), Qt.ItemDataRole.TextColorRole)

        self.combo_box.addItem("Blue")
        self.combo_box.setItemData(4, QColor('#0000ff'), Qt.ItemDataRole.TextColorRole)
        
        self.combo_box.addItem("Purple")
        self.combo_box.setItemData(5, QColor("#9900ff"), Qt.ItemDataRole.TextColorRole)
        
        self.combo_box.addItem("Pink")
        self.combo_box.setItemData(6, QColor("#ff00a2"), Qt.ItemDataRole.TextColorRole)

        self.change_combobox_color()
        self.combo_box.currentIndexChanged.connect(self.change_combobox_color)
        self.combo_box.currentIndexChanged.connect(lambda: self.finished.emit(self.id, self.combo_box.currentData(Qt.ItemDataRole.TextColorRole).name(), self.xpts,self.zpts))

        layout.addWidget(self.deletebtn, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.combo_box, alignment=Qt.AlignmentFlag.AlignTop)
        self.textedit = QTextEdit()
        self.textedit.setFixedHeight(int(self.textedit.document().documentLayout().documentSize().height()) + 2)
        self.textedit.textChanged.connect(self.adjust_height)
        self.textedit.textChanged.connect(self.attempt_to_graph)
        
        layout.addWidget(self.textedit, alignment=Qt.AlignmentFlag.AlignTop)
    
    def setStatus(self, status: int, error_message: str):
        self.status = status
        match status:
            case self.HIDDEN:
                self.status_button.setText("O")
                self.status_button.setToolTip(error_message)
                self.status_button.setStyleSheet("QPushButton {color: yellow} QToolTip {color:white}")
            case self.ERROR:
                try:
                    self.status_button.setText("❌")
                except:
                    self.status_button.setText("X")
                self.status_button.setToolTip(error_message)
                self.status_button.setStyleSheet("QPushButton {color: red} QToolTip {color:white}")
            case self.SUCCESS:
                try:
                    self.status_button.setText("✔")
                except:
                    self.status_button.setText("O")
                self.status_button.setToolTip(error_message)
                self.status_button.setStyleSheet("QPushButton {color: green} QToolTip {color:white}")

    def toggle_isshown(self):
        self.isShown = not self.isShown
        if self.isShown:
            # self.finished.emit(self.id, self.combo_box.currentData(Qt.ItemDataRole.TextColorRole).name(), self.xpts,self.ypts)
            self.attempt_to_graph()
        else:
            self.setStatus(self.HIDDEN, "This line is hidden")
            self.hidden.emit(self.id)

    def generate_variable_dict_for_evaluation(self):
        d = {'px': 0.0625}
        for i, x in enumerate(self.main_x):
            d[f"x{i}"] = x
        for i, z in enumerate(self.main_y):
            d[f"z{i}"] = z
        return d


    def adjust_height(self):
        newh = int(self.textedit.document().documentLayout().documentSize().height() + 2)
        self.textedit.setFixedHeight(max(newh, 38))

    def delete(self):
        self.deleted.emit(self.id)
        self.deleteLater()
    
    def change_combobox_color(self):
        self.setStyleSheet(f"QComboBox {{color: {self.combo_box.currentData(Qt.ItemDataRole.TextColorRole).name()}}}")

    def attempt_to_graph(self):
        if not self.isShown:
            return
        newtext = self.textedit.toPlainText().strip()
        "Attempts to parse into comma separated (x,y) coordinates"
        depth = 0
        x = []
        y = []
        current_item = ""
        expecting_comma = False
        
        for char in newtext:
            if expecting_comma and char != ",":
                self.setStatus(self.ERROR, "Expected comma after closing parenthesis to separate coordinate points")
                return
            elif expecting_comma and char == ",":
                expecting_comma = False
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    self.setStatus(self.ERROR, "Unmatching parenthesis: a closing parenthesis is unpaired with an open parenthesis.")
                    return
                if depth == 0:
                    # PARSE
                    pair_of_nums = current_item[1:len(current_item)].split(",")
                    if len(pair_of_nums) != 2:
                        self.setStatus(self.ERROR, f"Expected 2 values inside parenthesis, got {len(pair_of_nums)} instead")
                        return
                    try:
                        xpt, ypt = pair_of_nums
                        d = self.generate_variable_dict_for_evaluation()
                        xpt = evaluate(xpt, d)
                        ypt = evaluate(ypt, d)

                        if abs(xpt) > 10:
                            self.setStatus(self.ERROR, f"x coordinate {xpt} is outside the allowed range [-10, 10]")
                            return
                        if abs(ypt) > 10:
                            self.setStatus(self.ERROR, f"y coordinate {ypt} is outside the allowed range [-10, 10]")
                            return

                        x.append(xpt)
                        y.append(ypt)
                    except Exception as e:
                        self.setStatus(self.ERROR, f"Failed to parse: {e}")
                        return

                    current_item = ""
                    expecting_comma = True
                    continue

            if not char.isspace():
                current_item += char
        # else:
        if depth != 0:
            self.setStatus(self.ERROR, "Unmatching parenthesis: an open parenthesis is unpaired with a closed parenthesis.")
            return

        self.xpts = x
        self.zpts = y
        self.finished.emit(self.id, self.combo_box.currentData(Qt.ItemDataRole.TextColorRole).name(), x,y)
        self.setStatus(self.SUCCESS, "Successfully parsed coordinates")

    def getData(self):
        return {"id": self.id, # id might be irrelevant/not needed (?)
                "color": self.combo_box.currentData(Qt.ItemDataRole.TextColorRole).name(),
                "x": self.xpts,
                "z": self.zpts,
                "input": self.textedit.toPlainText(),
                "display": self.isShown,
                "status": self.status,
                "message": self.status_button.toolTip(),
                }

class EditPlotWidget(QMainWindow):
    # See the Container class for the representations
    redrawNeeded = pyqtSignal(int, str, list, list) # simply redraw the graph
    eraseNeeded = pyqtSignal(int) # id; erases the graph completely
    hidingNeeded = pyqtSignal(int) # id; hides the graph but can be toggled back on with redrawNeeded

    def __init__(self):
        super().__init__()
        self.list_of_containers: list[Container] = []
        self.xpts = [] # xpts and zpts are the main trajectory which are points that are already shifted (if at all). These lists are to
        self.zpts = [] # be passed BY REFERENCE so as to update all this and all containers at once.
        self.count = 0


        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        hlayout = QHBoxLayout()

        self.add_entry = QPushButton("Add")
        hlayout.addWidget(self.add_entry)
        self.add_entry.clicked.connect(self.new_entry)

        self.help_label = QLabel("Hover for Help")
        self.help_label.setToolTip("Input points in the form (x,y), comma separated.\nLines are drawn from point to point in the order you put them in.\nYou can use x and z coordinates directly from the optimal trajectory\nusing the variable names \"x#\" and \"z#\", for example, (x1, z2 + 0.01)\nAn Example: (0.125,0.3275), (0.45, z4), (13*px,z4+0.9)\n\nNotes:\n - Max allowed coordinates from -10 to 10\n - The variable px is defined to be 0.0625\n - The left button can be used to toggle a line's visibility.\n - Hover over the left button to see error messages.")
        hlayout.addWidget(self.help_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(hlayout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.draw_lines_widget = QWidget()
        self.scroll_area.setWidget(self.draw_lines_widget)

        self.draw_lines_layout = QVBoxLayout(self.draw_lines_widget)
        self.draw_lines_layout.setSpacing(0)
        self.draw_lines_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
    def redraw_all(self):
        for i in self.list_of_containers:
            i.attempt_to_graph()
    
    def new_entry(self):
        container = Container(self.count, self.xpts, self.zpts)
        self.list_of_containers.append(container)

        self.draw_lines_layout.addWidget(container)
        self.count += 1

        container.deleted.connect(self.reindex)
        container.finished.connect(lambda a,b,c,d: self.redrawNeeded.emit(a,b,c,d))
        container.hidden.connect(lambda i: self.hidingNeeded.emit(i))
        return container

    def update_main_trajectory(self, x, z): # reminder that this should be in place
        self.xpts.clear()
        self.zpts.clear()
        for a in x:
            self.xpts.append(a)
        for b in z:
            self.zpts.append(b)


    def reindex(self, id: int):
        self.count -= 1
        self.eraseNeeded.emit(id)
        x = self.findChildren(Container)
        for w in x:
            if w.id > id:
                w.id -= 1
    
    def get_all_line_data(self):
        d = []
        for c in self.list_of_containers:
            d.append(c.getData())
        return d
    
    def setup_lines(self, data: list[dict]):
        for c in data:
            container = self.new_entry()
            index = container.combo_box.findData(c["color"], Qt.ItemDataRole.TextColorRole)
            container.combo_box.setCurrentIndex(index)
            container.xpts = c['x']
            container.zpts = c['z']
            container.isShown = c['display']
            container.setStatus(c['status'],c['message'])
            container.textedit.setText(c['input']) # TODO: this triggers the attempt to graph. This may be annoying as saving with an invalid state will simply not display the previous displayable graph since last exiting.
            

    
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        x = self.findChildren(Container)
        for w in x:
            w.adjust_height()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = EditPlotWidget()
#     window.show()
#     sys.exit(app.exec_())

