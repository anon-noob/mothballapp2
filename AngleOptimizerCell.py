from PyQt5.QtCore import Qt, QModelIndex, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QComboBox, QSizePolicy, QTextEdit, QItemDelegate, QTableView
from BaseCell import Cell
from Enums import *
import math
import optimizer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import MultipleLocator
from matplotlib.figure import Figure

class PlotWidget(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 3.5), facecolor="#393939") # in inches, change this to change initial setup
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
        self.x = x
        self.y = y
        self.plot()

class Worker(QObject):
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

class AddandDelModel(QStandardItemModel):
    ROW = 0
    COLUMN = 1
    DISABLED_ROLE = Qt.UserRole + 1
    def __init__(self, row, col, addingRowOrColumn, parent: QTableView):
        super().__init__(row, col, parent)
        self.setParent(parent)
        self.constantIndexes = [] # Cannot delete or rename element, and cannot remove its column
        self.constantRows = []
        self.indexRows = {}
        self.addingRowOrColumn = addingRowOrColumn
        self.defaultValues = []
        parent.clicked.connect(self.onClick)

    def flags(self, index):
        item = self.itemFromIndex(index)
        if item is not None and item.data(AddandDelModel.DISABLED_ROLE):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.row() in self.constantRows or (index.row(), index.column()) in self.constantIndexes:
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

    def onClick(self, index):
        if self.addingRowOrColumn == self.COLUMN: # If clicked on the last column, add a new column
            if index.column() == self.columnCount() - 1:
                x = self.newListOfItems(self.rowCount())
                self.appendColumn(x)
        elif self.addingRowOrColumn == self.ROW: # If clicked on the last column, add a new column
            if index.row() == self.rowCount() - 1:
                x = self.newListOfItems(self.columnCount())
                self.appendRow(x)

    def deleteIndexes(self, indexes: list):
        if self.addingRowOrColumn == self.COLUMN:
            if not all(self.data(index) in ('',None) for index in indexes if index.row() not in self.constantRows):
                for index in indexes:
                    if (index.row(), index.column()) not in self.constantIndexes:
                        self.setData(index, '')
            else: # Now every selected cell is empty. Check if any column was selected (must be the entire column).
                columns = [index.column() for index in indexes]
                rows = [index.row() for index in indexes]
                unique_columns = set(columns)
                row_count = self.rowCount()
                cols_to_delete = []
                for col in unique_columns:
                    if all(any(i.row() == row and i.column() == col for i in indexes) for row in range(row_count)):
                        cols_to_delete.append(col)
                for col in sorted(cols_to_delete, reverse=True):
                    self.removeColumn(col)
                if not self.columnCount():
                    self.appendColumn(self.newListOfItems(self.rowCount()))
                
                if self.indexRows:
                    for row, text in self.indexRows.items():
                        for i in range(self.columnCount()):
                            self.setData(self.index(row, i), f"{text}{i}",overrideConstants=True)
        elif self.addingRowOrColumn == self.ROW:
            if not all(self.data(index) in ('',None) for index in indexes):
                for index in indexes:
                    if (index.row(), index.column()) not in self.constantIndexes:
                        self.setData(index, '')
            else: # Now every selected cell is empty. Check if any row was selected (must be the entire row).
                columns = [index.column() for index in indexes]
                rows = [index.row() for index in indexes]
                unique_rows = set(rows)
                col_count = self.columnCount()
                rows_to_delete = []
                for row in unique_rows:
                    if all(any(i.row() == row and i.column() == col for i in indexes) for col in range(col_count)):
                        rows_to_delete.append(row)
                for row in sorted(rows_to_delete, reverse=True):
                    self.removeRow(row)
                if not self.rowCount():
                    self.appendRow(self.newListOfItems(self.columnCount()))
                        
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole, overrideConstants: bool = False):
        a = (index.row(), index.column())
        if not overrideConstants and (a in self.constantIndexes or index.row() in self.constantRows):
            return False
        return super().setData(index, value, role)

    def basicSetup(self, data: list[list]):
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

    
    def setConstantIndexes(self, row, col):
        self.constantIndexes.append((row, col))
    
    def setConstantRows(self, row: int):
        self.constantRows.append(row)
    
    def setIndexedRows(self, row: int, label: str):
        self.indexRows[row] = label

    def getData(self):
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
    "Mothball Code Cell, `CodeEdit` as the input field, `RenderViewer` as the output viewer. The actual highlighting is done here, and the highlighting logic is computed in its linter `self.linter`."
    MAX = 'max'
    MIN = 'min'
    def __init__(self, parent, generalOptions: dict, colorOptions: dict, textOptions: dict, remove_callback, add_callback, move_callback, change_callback):
        super().__init__(parent, generalOptions, colorOptions, textOptions, remove_callback, add_callback, move_callback, change_callback, CellType.OPTIMIZE)
        self.mode = CellType.OPTIMIZE
        self.p = parent # The main Mothball instance 
        self.worker = None
        self.t = None
        self.points = [[],[]]

        self.left_content_layout = QVBoxLayout()
        self.right_content_layout = QVBoxLayout()
        self.top_panel = QHBoxLayout()
        self.top_panel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.top_panel.setSizeConstraint(self.top_panel.SizeConstraint.SetFixedSize)
        self.bottom_panel = QHBoxLayout()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle {background-color: "+"#595959"+"; border-radius: 3px}")
        left_widget = QWidget()
        left_widget.setLayout(self.left_content_layout)
        right_widget = QWidget()
        right_widget.setLayout(self.right_content_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(splitter)
        
        # Choose axis X or Z Button
        self.help_button = QPushButton("Help")
        self.help_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.help_button.setStyleSheet("background-color: #363636")
        self.help_button.setToolTip("It's ok to ask for help! :D")
        self.help_button.clicked.connect(self.displayHelp)
        self.top_panel.addWidget(self.help_button, stretch=0)

        self.reference_values = QPushButton("Reference Values")
        self.reference_values.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.reference_values.setStyleSheet("background-color: #363636")
        self.reference_values.setToolTip("Useful reference values and tips")
        self.reference_values.clicked.connect(self.displayReferenceValues)
        self.top_panel.addWidget(self.reference_values, stretch=0)

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

        self.var_box = QTableView()
        self.var_box.setHorizontalHeader(None)
        style = "QHeaderView::section {background-color: "+"#363636" + ";color: white;font-weight: bold;} QTableCornerButton::section {background-color: #2e2e2e;}"
        self.var_box.setStyleSheet(style)

        # Set the model first to get row count
        self.te_model = AddandDelModel(2,1,AddandDelModel.COLUMN, self.var_box)
        self.te_model.setVerticalHeaderLabels(["Variable", "Value"])
        self.te_model.basicSetup([['init', 'num_ticks', 'wad_spd', 'wdwa_spd', 'wdwa_angle'], [0.3, 12, 0.3274, 0.3060548, 17.4786858]])
        self.te_model.setConstantIndexes(0,0)
        self.te_model.setConstantIndexes(0,1)
        self.var_box.setModel(self.te_model)
        self.var_box.horizontalHeader().hide()
        self.te_model.dataChanged.connect(change_callback)

        # Calculate height: header + (row count * row height)
        row_count = self.te_model.rowCount()
        row_height = 40
        total_heighty = (row_height * row_count) + 2
        self.var_box.setMaximumHeight(total_heighty)
        self.var_box.setMinimumHeight(total_heighty)
        self.var_box.horizontalHeader().hide()
        self.var_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.var_box.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.var_box.verticalHeader().setDefaultSectionSize(row_height)
        self.var_box.resizeRowsToContents()
        self.var_box.resizeColumnsToContents()
        self.var_box.horizontalHeader().setDefaultSectionSize(100)
        self.left_content_layout.addWidget(self.var_box)

        # View Initials and variables
        self.a = QTableView()
        self.a.setStyleSheet(style)
        self.setup = AddandDelModel(4, 1, AddandDelModel.COLUMN, self.a)
        self.setup.setVerticalHeaderLabels(["Angles", "Drag X", "Drag Z", "Accel"])
        self.setup.basicSetup([[f'F{i}' for i in range(12)], [0.546, 0.546] + [0.91]*10, [0.546, 0.546]+[0.91]*10, ['init', 0.3274]+[0.026]*10])
        self.a.setModel(self.setup)
        self.setup.setIndexedRows(0,'F')
        self.setup.setConstantRows(0)
        self.setup.setDefaultValues(['','0.91','0.91','0.026'])
        total_height = self.a.horizontalHeader().height() + (40 * self.setup.rowCount()) + 2
        self.a.setMaximumHeight(total_height)
        self.a.setMinimumHeight(total_height)
        self.a.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.a.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.a.resizeRowsToContents()
        self.a.resizeColumnsToContents()
        self.a.horizontalHeader().setDefaultSectionSize(100)
        self.setup.dataChanged.connect(change_callback)
        

        self.left_content_layout.addWidget(self.a)

        self.constraintsView = QTableView()
        self.constraintsView.setStyleSheet(style)

        
        self.lst = AddandDelModel(0, 8, AddandDelModel.ROW, self.constraintsView)
        self.lst.setHorizontalHeaderLabels(["Use?", "Name","Type", "t1", "+-", "t2", "<=>", "Number"])
        self.lst.setDefaultValues(["YES", "", "X", "", "-", "", ">", ""])
        self.constraintsView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.constraintsView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.active = ComboBoxDelegate(['YES', 'no'])
        self.constraintType = ComboBoxDelegate(["X","Z","F"])
        self.operation = ComboBoxDelegate(['-','+'])
        self.comparison = ComboBoxDelegate(['>','<','=','>=','<='])
        self.constraintsView.setItemDelegateForColumn(0, self.active)
        self.constraintsView.setItemDelegateForColumn(2, self.constraintType)
        self.constraintsView.setItemDelegateForColumn(4, self.operation)
        self.constraintsView.setItemDelegateForColumn(6, self.comparison)
        self.lst.basicSetup([["YES", "", "X", "", "-", "", ">", ""]])
        self.constraintsView.setModel(self.lst)
        self.constraintsView.horizontalHeader().setDefaultSectionSize(50)
        self.constraintsView.setColumnWidth(1, 150)
        self.constraintsView.setColumnWidth(7, 150)
        self.constraintsView.setMinimumHeight(300)
        self.lst.dataChanged.connect(change_callback)

        self.left_content_layout.addWidget(self.constraintsView)

        # View results
        self.console = QTextEdit()
        self.console.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_content_layout.addWidget(self.console)

        # View graph
        self.graph = PlotWidget()
        self.right_content_layout.addWidget(self.graph)

        self.run_button.clicked.connect(self.runSolver)

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
    
    def displayReferenceValues(self): # Change this plz
        self.console.setText("""Acceleration:
- WAD Accel: 0.3274
- WDWA Accel: 0.3060548
- WDWA Angle: 17.4786858
- Air: 0.02548 (=0.026*0.98)
- Air w/ strafe: 0.026
- Ground: 0.1274 (=0.13*0.98)
- Ground w/ strafe: 0.13
Values represent no potions and normal block slip (slip = 0.6). These values change depending on potion effects and block slipperiness. Only air is unaffected by potions and slipperiness.

Drag Values:
- Ground: 0.546 (=0.91*0.6)
- Air: 0.91
- Inertia (ground or air): 0

""")
    
    def displayHelp(self): # change this plz
        self.console.setText("""This is the optimization cell, meant for finding optimal angle sequences.
Set the axis (X or Z) to optimize for, and set the mode (max or min).

There are 3 tables provided. Click on the last row/column to add a row/column. Delete a row/column by highlighting the row/column, then press backspace.
                                   
The first table is where you set the variables and their numeric values. These variables can then be used for the bottom 2 tables. The variables `init` and `num_ticks` cannot be deleted. You must use `num_ticks` to set the number of ticks you are optimizing for, which must be less than or equal to the number of columns on the 2nd table. `init` is optional, and stands for the initial speed, defaulting to 0.

The second table contains the drag and acceleration values. The values provided upon creating this cell are the most common values. Set a column in `Drag X` or `Drag Z` to 0 to simulate inertia on x or z respectively.

The third table is where you put constraints. 
Set `Use?` to `YES` to incorporate it for your calculation. 
`Name` is optional. 
`Type` is a constraint for `X`,`Z`, or `F`, which is your rotation (or facing). 
`t1` and `t2` indicate what ticks to compare. 
`+-` is the add/subtract operation. 
`<=>` is for selecting the comparison.
`Number` is, simply a number. 
A row should read like an inequality, for example, "Z(8) - Z(1) > 1.6". 
                             
If you are incorporating inertia, be sure to add the constraint which restricts the distance traveled on the inertia tick. For example, "X(4) - X(3) < 0.005/0.91". Here, `0.005/0.91` is the speed needed to hit inertia.""")

    def runSolver(self):

        names, values = self.te_model.getData()
        variables = {n:v for n,v in zip(names, values)}


        data = self.setup.getData()

        if not data or len(data[0]) < int(variables['num_ticks']):
            raise RuntimeError(f"Data has fewer columns than num_ticks = {int(variables['num_ticks'])}")
        
        constraints = self.lst.getData()

        self.t = QThread()
        self.worker = Worker(self.axis_to_optimize, self.max_or_min, variables, data, constraints)
        self.worker.moveToThread(self.t)

        self.t.started.connect(self.worker.run)
        self.worker.finished.connect(self.onCompletion)
        self.worker.finished.connect(self.t.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.t.finished.connect(self.t.deleteLater)

        self.run_button.setDisabled(True)

        self.t.start()

    def onCompletion(self, res, c, d):
        self.run_button.setEnabled(True)
        if isinstance(res, str):
            self.toConsole(f"{res} {c}")
            return

        pts = d['points']
        x_pts = [round(l[0],6) for l in pts]
        z_pts = [round(i[1],6) for i in pts]
        self.points = [x_pts, z_pts]
        self.graph.setData(x_pts, z_pts)

        

        name, value = c
        offset = res.fun
        success = res.success
        message = res.message
        x = [round(math.degrees(p),3) for p in res.x]
        consecutive_diffs = [round(x[l]-x[l-1],3) for l in range(1, len(x))]
        
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
        self.toConsole("\n".join(lines))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            focused = self.focusWidget()
            if focused == self.var_box or focused == self.a or focused == self.constraintsView:
                selected_indexes = focused.selectionModel().selectedIndexes()
                if selected_indexes:
                    focused.model().deleteIndexes(selected_indexes)

        return super().keyPressEvent(event)  # Call the base class implementation to keep default behavior


# if __name__ == "__main__":
#     from PyQt5.QtWidgets import QMainWindow, QApplication
#     import sys
#     app = QApplication(sys.argv)
#     window = QMainWindow()
#     window.setCentralWidget(OptimizationSection(window, {}, {}, {}, 0, 0, 0, lambda x: x))
#     window.resize(1200, 800)
#     window.show()
#     sys.exit(app.exec())
