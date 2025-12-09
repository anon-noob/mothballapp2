from PyQt5.QtCore import Qt, QModelIndex, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QComboBox, QSizePolicy, QTextEdit, QItemDelegate, QTableView, QHeaderView
from BaseCell import Cell
from Enums import *
import math
import optimizer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import MultipleLocator
from matplotlib.figure import Figure

class PlotWidget(FigureCanvas):
    "Widget for displaying a plot"
    def __init__(self, parent=None):
        fig = Figure(figsize=(3.6, 1.6), facecolor="#393939") # in inches, change this to change initial setup
        # fig = Figure(facecolor="#393939") # in inches, change this to change initial setup
        self.ax = fig.add_subplot(111)

        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(self.sizePolicy().Expanding,self.sizePolicy().Expanding)
        self.updateGeometry()

        # initial data ( prob add more random initial data)
        X = [math.sin(k*math.pi/20) ** 3 for k in range(-20, 21)]
        Y = [(1/16) * (13 * math.cos(i*math.pi/20) - 5 * math.cos(2*i*math.pi/20) - 2 * math.cos(3*i*math.pi/20) - math.cos(4*i*math.pi/20)) + 0.375 for i in range(-20, 21)]
        
        self.x = X
        self.y = Y
        self.plot()

    def plot(self):
        "Plot the graph with data given from `self.x`, `self.y`"
        self.ax.clear()
        self.ax.set_facecolor("#5B5B5B")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")

        self.ax.plot(self.x, self.y, marker="o", linestyle="-", color='lime')

        self.ax.xaxis.set_major_locator(MultipleLocator(0.5))
        self.ax.xaxis.set_minor_locator(MultipleLocator(0.125))
        self.ax.yaxis.set_major_locator(MultipleLocator(0.5))
        self.ax.yaxis.set_minor_locator(MultipleLocator(0.125))

        self.ax.grid(which="both", linestyle="--", linewidth=0.5, color='white')
        self.draw()

    def setData(self, x,y):
        "Set the x and y coordinates"
        self.x = x
        self.y = y
        self.plot()

class Worker(QObject):
    "Worker for executing angle optimizations using threading"
    finished = pyqtSignal(object, object, object)

    def __init__(self, axis_to_optimize, max_or_min, variables: dict, data: list[list], constraints: list[list]):
        super().__init__()
        self.axis_to_optimize = axis_to_optimize
        self.max_or_min = max_or_min
        self.variables = variables
        self.data = data
        self.constraints = constraints
        self.isrunning = False

    def run(self):
        self.isrunning = True
        try:
            a = optimizer.Optimizer()
            a.setupVars(self.variables)
            a.setupConstants(self.data[1], self.data[2], self.data[3])
            a.setupConstraints(self.constraints)
            
            res, c = a.optimize(self.axis_to_optimize, self.max_or_min)
            d = a.postprocess()
            self.finished.emit(res, c, d)
        except Exception as e:
            self.finished.emit(f"Error occurred!", str(e), "")
        self.isrunning = False

class ComboBoxDelegate(QItemDelegate):
    "Set a combobox item delegate containing `items`"
    def __init__(self, items: list[str]):
        super().__init__()
        self.items = items
        
    def createEditor(self, parent, option, index: QModelIndex):
        combo = QComboBox(parent)
        combo.addItems(self.items)
        return combo

    def setEditorData(self, editor, index: QModelIndex):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index: QModelIndex):
        model.setData(index, editor.currentText(), Qt.EditRole)


class CustomItemModel(QStandardItemModel):
    """
    Model for a tableview, supports adding/deleting rows or columns, depending on the direction of expansion.

    Supports setting indexes constant (cannot be changed or deleted), constant rows, index rows for autoindexing, and default value when adding cells.
    """
    ROW = 0
    COLUMN = 1
    def __init__(self, row, col, addingRowOrColumn, parent: QTableView):
        super().__init__(row, col, parent)
        self.setParent(parent)
        self.indexRows = {}
        self.constantRows: set[int] = set()
        self.constantColumns: set[int] = set()
        self.constantIndexes: set[tuple[int, int]] = set()
        self.addingRowOrColumn = addingRowOrColumn
        self.defaultValues = []
        # parent.clicked.connect(self.onClick)

    def flags(self, index):
        row = index.row()
        col = index.column()
        if row in self.constantRows or col in self.constantRows or (row, col) in self.constantIndexes or row in self.indexRows:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return super().flags(index)

    def setDefaultValues(self, values: list[str]):
        if self.addingRowOrColumn == self.COLUMN and self.rowCount() != len(values):
            raise ValueError(f"Size of values doesn't match rows {len(values)} != {self.rowCount()}")
        if self.addingRowOrColumn == self.ROW and self.columnCount() != len(values):
            raise ValueError(f"Size of values doesn't match rows {len(values)} != {self.columnCount()}")
        self.defaultValues = values

    def newListOfItems(self, n: int):
        x = []
        for _ in range(n):
            if _ not in self.indexRows:
                if self.defaultValues:
                    x.append(QStandardItem(self.defaultValues[_]))
                else:
                    x.append(QStandardItem(''))
            else:
                x.append(QStandardItem(f'{self.indexRows[_]}{self.columnCount()}'))
        return x

    def add(self):
        if self.addingRowOrColumn == self.ROW:
            x = self.newListOfItems(self.columnCount())
            self.appendRow(x)
        elif self.addingRowOrColumn == self.COLUMN:
            x = self.newListOfItems(self.rowCount())
            self.appendColumn(x)
    
    def delete(self, x):
        x = list(x)
        x.sort(reverse=True)
        if self.addingRowOrColumn == self.ROW:
            remover = self.removeRow
        elif self.addingRowOrColumn == self.COLUMN:
            remover = self.removeColumn
        
        for a in x:
            remover(a)
        
        if self.addingRowOrColumn == self.ROW and self.rowCount() == 0:
            self.add()
        elif self.addingRowOrColumn == self.COLUMN and self.columnCount() == 0:
            self.add()
    
    def deleteIndexes(self, indexes):
        x = [i for i in indexes if i.row() not in self.constantRows and i.row() not in self.indexRows and i.column() not in self.constantColumns and (i.row(), i.column()) not in self.constantIndexes]

        for index in x:
            self.setData(index, "")

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        return super().setData(index, value, role)

    def basicSetup(self, data: list[list]):
        "Set some data to the entire model"
        if self.addingRowOrColumn == self.COLUMN:
            self.removeRows(1, self.rowCount())
            self.removeColumns(0, self.columnCount())
            for col in range(len(data[0])):
                self.appendColumn([QStandardItem(str(text)) for text in [x[col] for x in data]])
        else:
            self.removeRows(0, self.rowCount())
            self.removeColumns(1, self.columnCount())
            for row in range(len(data)):
                self.appendRow([QStandardItem(str(text)) for text in data[row]])

    
    def setConstantIndexes(self, row: int, col: int):
        self.constantIndexes.add((row, col))
    
    def setConstantRows(self, row: int):
        self.constantRows.add(row)
    
    def setConstantColumns(self, col: int):
        self.constantColumns.add(col)

    def setIndexedRows(self, row: int, label: str):
        self.indexRows[row] = label

    def getData(self):
        "Get all data returned as a 2-d array"
        all_data = []
        for row in range(self.rowCount()):
            row_data = []
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item:
                    row_data.append(item.data(Qt.ItemDataRole.DisplayRole))
                else:
                    row_data.append('')
            all_data.append(row_data)

        return all_data
        
class OptimizationSection(Cell):
    "Mothball Angle Optimizer, for optimizing specific sequences of angles."
    MAX = 'max'
    MIN = 'min'
    def __init__(self, parent, generalOptions: dict, colorOptions: dict, textOptions: dict, remove_callback, add_callback, move_callback, change_callback, copy_callback):
        super().__init__(parent, generalOptions, colorOptions, textOptions, remove_callback, add_callback, move_callback, change_callback, copy_callback, CellType.OPTIMIZE)
        self.mode = CellType.OPTIMIZE
        self.p = parent # The main Mothball instance 
        self.worker = None
        self.the_thread = None
        self.points = [[],[]]

        self.left_content_layout = QVBoxLayout()
        self.right_content_layout = QVBoxLayout()
        self.top_panel = QHBoxLayout()
        self.top_panel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.top_panel.setSizeConstraint(self.top_panel.SizeConstraint.SetFixedSize)
        self.bottom_panel = QHBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        vsplitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle {background-color: "+"#595959"+"; border-radius: 3px}")
        left_widget = QWidget()
        left_widget.setLayout(self.left_content_layout)
        right_widget = QWidget()
        right_widget.setLayout(self.right_content_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        vsplitter.setStretchFactor(0, 2)
        vsplitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(splitter)
        self.setStyleSheet("QPushButton{background-color: " + "#1d1d1d}")
        
        # Help Button (TO CHANGE)
        self.help_button = QPushButton("Help")
        self.help_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.help_button.setStyleSheet("background-color: #363636")
        self.help_button.setToolTip("It's ok to ask for help! :D")
        self.help_button.clicked.connect(self.displayHelp)
        self.top_panel.addWidget(self.help_button, stretch=0)

        # Choose axis X or Z Button
        self.axis_to_optimize = OptimizeCellAxis.X # dont worry, this is toggleable
        self.choose_axis_button = QPushButton(f"Axis: {self.axis_to_optimize}")
        self.choose_axis_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.choose_axis_button.clicked.connect(self.toggleAxis)
        self.choose_axis_button.setToolTip("The target axis to optimize, either X or Z.")
        self.choose_axis_button.setStyleSheet("background-color: #363636")
        self.top_panel.addWidget(self.choose_axis_button, stretch=0)

        # Maximize or Minimize
        self.max_or_min = OptimizationSection.MIN
        self.choose_max_or_min_button = QPushButton(f"Mode: {self.max_or_min}")
        self.choose_max_or_min_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.choose_max_or_min_button.clicked.connect(self.toggleMode)
        self.choose_max_or_min_button.setToolTip("Try to find the max or min.")
        self.choose_max_or_min_button.setStyleSheet("background-color: #363636")
        self.top_panel.addWidget(self.choose_max_or_min_button, stretch=0)


        self.left_content_layout.addLayout(self.top_panel)


        # self.variables_layout = QHBoxLayout()
        # self.variable_buttons_layout = QVBoxLayout()
        # self.var_add_button = QPushButton("+")
        # self.var_add_button.setToolTip("Add a column for a new variable. (Ctrl Shift +)")
        # self.var_delete_button = QPushButton("-")
        # self.var_delete_button.setToolTip("Delete the columns associated with the currently selected cells. (Ctrl -)")
        # self.var_add_button.setFixedSize(30,30)
        # self.var_delete_button.setFixedSize(30,30)
        # self.variable_buttons_layout.addWidget(self.var_add_button)
        # self.variable_buttons_layout.addWidget(self.var_delete_button)
        # self.variables_layout.addLayout(self.variable_buttons_layout)
        
        # Box for setting variables
        self.var_box = QTableView()
        self.var_box.setHorizontalHeader(None)
        style = "QHeaderView::section {background-color: "+"#363636" + ";color: white;font-weight: bold;} QTableCornerButton::section {background-color: #2e2e2e;}"
        self.var_box.setStyleSheet(style)

        # Set the model first to get row count
        self.var_box_model = CustomItemModel(2,1,CustomItemModel.COLUMN, self.var_box)
        self.var_box_model.setVerticalHeaderLabels(["Variable", "Value"])
        self.var_box_model.basicSetup([['init', 'num_ticks', 'init_guess', 'wad_spd', 'wdwa_spd', 'wdwa_angle'], [0.3, 12, 0, 0.3274, 0.3060548, 17.4786858]])
        self.var_box_model.setConstantIndexes(0,0) # cannot remove "init" (initial speed)
        self.var_box_model.setConstantIndexes(0,1) # cannot remove "num_ticks"
        self.var_box_model.setConstantIndexes(0,2) # cannot remove "init_guess"
        self.var_box.setModel(self.var_box_model)
        self.var_box.horizontalHeader().hide()
        self.var_box_model.dataChanged.connect(change_callback)

        self.var_box.resizeRowsToContents()
        self.var_box.resizeColumnsToContents()

        # self.var_add_button.clicked.connect(self.add_variable)
        # self.var_delete_button.clicked.connect(self.delete_variable)

        row_count = self.var_box_model.rowCount()
        row_height = self.var_box.rowHeight(0)
        h = (row_height * row_count)+2 # content margins are top, bottom = 1,1, so it is +2

        self.var_box.setFixedHeight(h)
        self.var_box.horizontalHeader().hide()
        self.var_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.var_box.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.var_box.verticalHeader().setDefaultSectionSize(row_height)
        self.var_box.horizontalHeader().setDefaultSectionSize(100)
        self.var_box.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.var_box.horizontalHeader().setMinimumWidth(100)

        # self.variables_layout.addWidget(self.var_box)

        # self.left_content_layout.addLayout(self.variables_layout)
        self.left_content_layout.addWidget(self.var_box)
        

        # View Constants
        # self.drag_and_accel_layout = QHBoxLayout()
        # self.drag_and_accel_button_layout = QVBoxLayout()
        # self.drag_and_accel_add_button = QPushButton("+")
        # self.drag_and_accel_add_button.setToolTip("Add a column for a new variable. (Ctrl Shift +)")
        # self.drag_and_accel_delete_button = QPushButton("-")
        # self.drag_and_accel_delete_button.setToolTip("Delete the columns associated with the currently selected cells. (Ctrl -)")
        # self.drag_and_accel_add_button.setFixedSize(30,30)
        # self.drag_and_accel_delete_button.setFixedSize(30,30)
        # self.drag_and_accel_button_layout.addWidget(self.drag_and_accel_add_button)
        # self.drag_and_accel_button_layout.addWidget(self.drag_and_accel_delete_button)
        # self.drag_and_accel_layout.addLayout(self.drag_and_accel_button_layout)

        self.drag_and_accel_table = QTableView()
        self.drag_and_accel_table.setStyleSheet(style)
        self.drag_and_accel_model = CustomItemModel(4, 1, CustomItemModel.COLUMN, self.drag_and_accel_table)
        self.drag_and_accel_model.setVerticalHeaderLabels(["Angles", "Drag X", "Drag Z", "Accel"])
        self.drag_and_accel_model.basicSetup([[f'F{i}' for i in range(12)], [0.546, 0.546] + [0.91]*10, [0.546, 0.546]+[0.91]*10, ['init', 0.3274]+[0.026]*10])
        self.drag_and_accel_table.setModel(self.drag_and_accel_model)
        self.drag_and_accel_model.setIndexedRows(0,'F')
        # self.drag_and_accel_model.setConstantRows(0)
        self.drag_and_accel_model.setDefaultValues(['','0.91','0.91','0.026'])
        total_height = (self.drag_and_accel_table.rowHeight(0) * self.drag_and_accel_model.rowCount()) + 2
        self.drag_and_accel_table.setFixedHeight(total_height)
        self.drag_and_accel_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.drag_and_accel_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.drag_and_accel_table.resizeRowsToContents()
        self.drag_and_accel_table.resizeColumnsToContents()
        self.drag_and_accel_table.horizontalHeader().setDefaultSectionSize(100)
        self.drag_and_accel_model.dataChanged.connect(change_callback)
        
        # self.drag_and_accel_add_button.clicked.connect(self.add_drag)
        # self.drag_and_accel_delete_button.clicked.connect(self.delete_drag)

        # self.drag_and_accel_layout.addWidget(self.drag_and_accel_table)
        # self.left_content_layout.addLayout(self.drag_and_accel_layout)

        self.left_content_layout.addWidget(self.drag_and_accel_table)

        # Constraints
        # self.constraints_layout = QHBoxLayout()
        # self.constraints_button_layout = QVBoxLayout()
        # self.constraints_add_button = QPushButton("+")
        # self.constraints_delete_button = QPushButton("-")
        # self.constraints_moveup_button = QPushButton("↑")
        # self.constraints_movedown_button = QPushButton("↓")
        # self.constraints_add_button.setFixedSize(30,30)
        # self.constraints_delete_button.setFixedSize(30,30)
        # self.constraints_moveup_button.setFixedSize(30,30)
        # self.constraints_movedown_button.setFixedSize(30,30)
        # self.constraints_button_layout.addWidget(self.constraints_add_button)
        # self.constraints_button_layout.addWidget(self.constraints_delete_button)
        # self.constraints_button_layout.addWidget(self.constraints_moveup_button)
        # self.constraints_button_layout.addWidget(self.constraints_movedown_button)
        # self.constraints_layout.addLayout(self.constraints_button_layout)


        self.constraints_table = QTableView()
        self.constraints_table.horizontalHeader().setStretchLastSection(True)
        self.constraints_table.setStyleSheet(style)

        
        self.constraints_model = CustomItemModel(0, 8, CustomItemModel.ROW, self.constraints_table)
        self.constraints_model.setHorizontalHeaderLabels(["Use?", "Name","Type", "t1", "+-", "t2", "<=>", "Number"])
        self.constraints_model.setDefaultValues(["YES", "", "X", "", "-", "", ">", ""])
        self.constraints_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.constraints_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.active = ComboBoxDelegate(['YES', 'no'])
        self.constraintType = ComboBoxDelegate(["X","Z","F"])
        self.operation = ComboBoxDelegate(['-','+'])
        self.comparison = ComboBoxDelegate(['>','<','='])
        self.constraints_table.setItemDelegateForColumn(0, self.active)
        self.constraints_table.setItemDelegateForColumn(2, self.constraintType)
        self.constraints_table.setItemDelegateForColumn(4, self.operation)
        self.constraints_table.setItemDelegateForColumn(6, self.comparison)
        self.constraints_model.basicSetup([["YES", "", "X", "", "-", "", ">", ""]])
        self.constraints_table.setModel(self.constraints_model)
        self.constraints_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.constraints_table.setMinimumHeight(300)
        self.constraints_model.dataChanged.connect(change_callback)

        # self.constraints_layout.addWidget(self.constraints_table)

        # self.constraints_add_button.clicked.connect(self.add_constraint)
        # self.constraints_delete_button.clicked.connect(self.delete_constraint)

        # self.left_content_layout.addLayout(self.constraints_layout)

        self.left_content_layout.addWidget(self.constraints_table)


        # View results
        self.console = QTextEdit()
        self.console.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        vsplitter.addWidget(self.console)

        # View graph
        self.plot = PlotWidget()
        vsplitter.addWidget(self.plot)
        # self.right_content_layout.addWidget(self.plot)

        self.right_content_layout.addWidget(vsplitter)

        self.run_button.clicked.connect(self.runSolver)
    
    def add_variable(self):
        self.var_box_model.add()
    
    def delete_variable(self):
        x = set(i.column() for i in self.var_box.selectedIndexes() if i.column() not in (0,1,2))
        self.var_box_model.delete(x)

    def add_drag(self):
        self.drag_and_accel_model.add()
    
    def delete_drag(self):
        x = set(i.column() for i in self.drag_and_accel_table.selectedIndexes())
        self.drag_and_accel_model.delete(x)
        for row, text in self.drag_and_accel_model.indexRows.items():
            for i in range(self.drag_and_accel_model.columnCount()):
                self.drag_and_accel_model.setData(self.drag_and_accel_model.index(row, i), f"{text}{i}")
        
    def add_constraint(self):
        self.constraints_model.add()

    def delete_constraint(self):
        x = set(i.row() for i in self.constraints_table.selectedIndexes())
        self.constraints_model.delete(x)

    def toggleAxis(self):
        if self.axis_to_optimize == OptimizeCellAxis.Z:
            self.axis_to_optimize = OptimizeCellAxis.X
        elif self.axis_to_optimize == OptimizeCellAxis.X:
            self.axis_to_optimize = OptimizeCellAxis.Z
        self.choose_axis_button.setText(f"Axis: {self.axis_to_optimize}")
    
    def toggleMode(self):
        if self.max_or_min == OptimizationSection.MAX:
            self.max_or_min = OptimizationSection.MIN
        elif self.max_or_min == OptimizationSection.MIN:
            self.max_or_min = OptimizationSection.MAX
        self.choose_max_or_min_button.setText(f"Mode: {self.max_or_min}")
    
    def toConsole(self, text):
        self.console.setText(text)
    
    def displayHelp(self): # change this plz
        self.console.setText("""This is the optimization cell, meant for finding optimal angle sequences.
Set the axis (X or Z) to optimize for, and set the mode (max or min).

There are 3 tables provided. Press Ctrl Plus (or Ctrl Shift =) to add a row/column. Delete a row/column by highlighting part of the row(s)/column(s) you want to delete, then press Ctrl minus (Ctrl -).
                                   
The first table is where you set the variables and their numeric values. These variables can then be used for the bottom 2 tables. The variables `init` and `num_ticks` cannot be deleted. You must use `num_ticks` to set the number of ticks you are optimizing for, which must be less than or equal to the number of columns on the 2nd table. `init` is optional, and stands for the initial speed, defaulting to 0.

The second table contains the drag and acceleration values. The values provided upon creating this cell are the most common values. Set a column in `Drag X` or `Drag Z` to 0 to simulate inertia on x or z respectively.

The third table is where you put constraints. 
Set `Use?` to `YES` to incorporate it for your calculation. 
`Name` is optional. 
`Type` is a constraint for `X`,`Z`, or `F`, which is your rotation (or facing). 
`t1` and `t2` indicate what ticks to compare. `t2` can be left empty.
`+-` is the add/subtract operation. 
`<=>` is for selecting the comparison.
`Number` is, simply a number, or an expression.
A row should read like an inequality, for example, "Z(8) - Z(1) > 1.6". 
                             
If you are incorporating inertia, be sure to add the constraint which restricts the distance traveled on the inertia tick. For example, "X(4) - X(3) < 0.005/0.91". Here, `0.005/0.91` is the speed needed to hit inertia.""")

    def runSolver(self):
        names, values = self.var_box_model.getData()
        variables = {n:v for n,v in zip(names, values)}
        data = self.drag_and_accel_model.getData()

        try:
            m = variables['num_ticks']
        except KeyError:
            self.toConsole(f"Error: Something went wrong, couldn't find 'num_ticks'")
            self.setStatus(self.ERROR)
            return
        
        try:
            m = int(m)
        except ValueError:
            self.toConsole(f"Error: I don't understand what num_ticks={m} means. It should be a positive integer.")
            self.setStatus(self.ERROR)
            return
        
        if not data or len(data[0]) < m:
            self.toConsole(f"Error: Drag and Accel data has fewer columns than num_ticks = {m}")
            self.setStatus(self.ERROR)
            return
        
        constraints = self.constraints_model.getData()

        self.the_thread = QThread()
        self.worker = Worker(self.axis_to_optimize, self.max_or_min, variables, data, constraints)
        self.worker.moveToThread(self.the_thread)

        self.the_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.onCompletion)
        self.worker.finished.connect(self.the_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.the_thread.finished.connect(self.the_thread.deleteLater)

        self.run_button.setDisabled(True)

        self.setStatus(self.RUNNING)
        self.the_thread.start()

    def onCompletion(self, res, constraint_values, postprocess_dict):
        # Constraint_values are the constraint functions evaluated with the optimiized output.
        # When the values are close to 0, then it is binding. 
        self.run_button.setEnabled(True)
        if isinstance(res, str):
            self.toConsole(f"{res} {constraint_values}")
            self.setStatus(self.ERROR)
            return

        pts = postprocess_dict['points']
        x_pts = [round(l[0],6) for l in pts]
        z_pts = [round(i[1],6) for i in pts]
        self.points = [x_pts, z_pts]
        self.plot.setData(x_pts, z_pts)

        

        name, value = constraint_values
        offset = res.fun
        success = res.success
        message = res.message
        x = [round(math.degrees(p),3) for p in res.x]
        for i, angle in enumerate(x):
            # Range of angle is [-360, 360]
            if angle > 180:
                x[i] = round(angle - 360,3)
            elif angle < -180:
                x[i] = round(angle + 360,3)
        consecutive_diffs = [round(x[l]-x[l-1],3) for l in range(1, len(x))]
        x_velocities = [round(x_pts[j]-x_pts[j-1],7) for j in range(1, len(x_pts))]
        z_velocities = [round(z_pts[j]-z_pts[j-1],7) for j in range(1, len(z_pts))]

        lines = []
        lines.append(message)
        lines.append(f"Success: {success}")
        lines.append("")
        lines.append(f"Position: {offset * -1 if self.max_or_min == 'max' else offset}")
        lines.append("")
        lines.append(f"Angles: {x}")
        lines.append(f"Turns: {consecutive_diffs}")
        lines.append("")
        if name and value:
            lines.append(f"Constraint Values")
            for n, v in zip(name, value):
                lines.append(f"{n}: {v}")
        else:
            lines.append("No Constraints")
        
        lines.append("")
        lines.append("(X,Z) position")
        for i,j in zip(x_pts, z_pts):
            lines.append(f"  {i}, {j}")
        lines.append("")
        lines.append("(X,Z) velocities")
        for i,j in zip(x_velocities, z_velocities):
            lines.append(f"  {i}, {j}")
        self.toConsole("\n".join(lines))

        if success:
            self.setStatus(self.SUCCESS)
        else:
            self.setStatus(self.ERROR)

    def getCellData(self):
        data = {
            "cell_type": self.cellType,
            "axis": self.axis_to_optimize,
            "mode": self.max_or_min,
            "variables": self.var_box_model.getData(),
            "drags": self.drag_and_accel_model.getData(),
            "constraints": self.constraints_model.getData(),
            "output": self.console.toPlainText(),
            "points": self.points
            }
        return data

    def setupCell(self, data):
        if not all([x in ("cell_type", "axis","mode","variables","drags","constraints", "output", "points") for x in data]):
            return
        if self.axis_to_optimize != data['axis']:
            self.choose_axis_button.click()
        if self.max_or_min != data['mode']:
            self.choose_max_or_min_button.click()
        self.var_box_model.basicSetup(data['variables'])
        self.drag_and_accel_model.basicSetup(data['drags'])
        self.constraints_model.basicSetup(data['constraints'])
        self.toConsole(data['output'])
        self.plot.setData(data['points'][0], data['points'][1])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            focused = self.focusWidget()
            if focused == self.var_box or focused == self.drag_and_accel_table or focused == self.constraints_table:
                selected_indexes = focused.selectionModel().selectedIndexes()
                if selected_indexes:
                    focused.model().deleteIndexes(selected_indexes)
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() ==  Qt.Key.Key_Plus:
                focused = self.focusWidget()
                if focused == self.var_box:
                    self.var_box_model.add()
                elif focused == self.drag_and_accel_table:
                    self.drag_and_accel_model.add()
                elif focused == self.constraints_table:
                    self.constraints_model.add()
            elif event.key() == Qt.Key.Key_Minus:
                focused = self.focusWidget()
                if focused == self.var_box:
                    self.delete_variable()
                elif focused == self.drag_and_accel_table:
                    self.delete_drag()
                elif focused == self.constraints_table:
                    self.delete_constraint()
                    

        return super().keyPressEvent(event)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QMainWindow, QApplication
    import sys
    app = QApplication(sys.argv)
    window = QMainWindow()
    ll = OptimizationSection(window, {}, {}, {}, 0, 0, 0, lambda x: x, 0)
    ll.status_button.clicked.connect(lambda: print(ll.var_box.height()))
    window.setCentralWidget(ll)
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
