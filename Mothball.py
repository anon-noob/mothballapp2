"""
The main Mothball Window, a coding notebook-like experience, with 3 types of cells: horizontal movement, vertical movement, and markdown.

Contains:
- File save system
- Basic (but incomplete) documentation
- Customizable colors and other settings (NOT FINISHED/FULLY IMPLEMENTED)
"""

import sys,os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, QMenu, QMainWindow, QFileDialog, QMessageBox
)
from typing import Literal, Union, Optional
import HelpPage
import Settings
import AboutMothball
from PyQt5.QtCore import Qt, QTimer
from utils import * 
import CodeCell
import TextCell
import FileHandler
import json
import ParkourWordle
from Enums import CellType, TextCellState

# Scintilla resizing issue with newlines (prob show scrollbar?)
# Comments and docstring
# Reorganize the help page
# Re-enumerate the enums
# Fix settings
# Add other remaining colors
# Var should not lint as strings

class ActionStack:
    """
    Keeps track of GUI changes, mainly adding, removing, and moving cells. `undo` executes the action, `redo` executes the opposite action. 
    """
    DELETE_ACTION = 0
    CREATE_ACTION = 1
    MOVE_ACTION = 2

    UNDO = 3
    REDO = 4

    class DeleteCellAction:
        def __init__(self, index: int):
            self.action = ActionStack.DELETE_ACTION
            self.index = index
        def __repr__(self):
            return f"Delete(index={self.index})"
    class CreateCellAction:
        def __init__(self, index: int, data: dict):
            self.action = ActionStack.CREATE_ACTION
            self.data = data
            self.index = index
        def __repr__(self):
            return f"Create(insert_at_index={self.index}, data={self.data})"
    class MoveCellAction:
        def __init__(self, source: int, direction: Literal[-1,1]):
            self.action = ActionStack.MOVE_ACTION
            self.source = source
            self.direction = direction
        def __repr__(self):
            return f"Move(src={self.source}, direction={self.direction})"

    def __init__(self, parent: "MainWindow"):
        self.parent = parent # GUI
        self.undoStack: list[Union[ActionStack.DeleteCellAction, ActionStack.CreateCellAction, ActionStack.MoveCellAction]] = []
        self.redoStack: list[Union[ActionStack.DeleteCellAction, ActionStack.CreateCellAction, ActionStack.MoveCellAction]] = []

    def addDeleteAction(self, index: int):
        "When the user adds a cell, push a `delete` action to the `undoStack`"
        self.undoStack.append(ActionStack.DeleteCellAction(index))
        self.redoStack = []

    def addCreateAction(self, index: int, data):
        "When the user deletes a cell, push a `create` action to the `undoStack`"
        self.undoStack.append(ActionStack.CreateCellAction(index, data))
        self.redoStack = []

    def addMoveAction(self, source: int, direction: int):
        "When the user moves a cell, push a `move` action to the `undoStack`"
        self.undoStack.append(ActionStack.MoveCellAction(source, direction))
        self.redoStack = []

    def executeAction(self, undo_or_redo: Literal[3,4]):
        if undo_or_redo == self.UNDO:
            popping = self.undoStack
            adding = self.redoStack
        elif undo_or_redo == self.REDO:
            popping = self.redoStack
            adding = self.undoStack
        
        if not popping:
            return
        action = popping.pop()
        match action.action:
            case self.DELETE_ACTION: # pop the delete action, add the create action
                data = self.parent.removeCell(action.index, addActionStack=False)
                adding.append(ActionStack.CreateCellAction(action.index, data))

            case self.CREATE_ACTION: # pop the create action, add the delete action
                t = action.data['type']
                if t == "text":
                    cell = self.parent.addCell(action.index, cellType=action.data['type'], addActionStack=False)
                    cell.input_field.setText(action.data["raw_text"])
                    cell.render_field.renderTextfromMarkdown(cell.linter, action.data["raw_text"])
                    QApplication.processEvents()
                    QTimer.singleShot(100, lambda: self.continueProcess(cell))
                    adding.append(ActionStack.DeleteCellAction(action.index))
                elif t == "code":
                    cell = self.parent.addCell(action.index, cellType=action.data["mode"], addActionStack=False)
                    cell.input_field.setText(action.data["code"])
                    cell.output_field.renderTextfromOutput(cell.linter, action.data["raw_output"])
                    cell.raw_output = action.data["raw_output"]
                    QApplication.processEvents()
                    QTimer.singleShot(100, lambda: self.continueProcess(cell))
                    adding.append(ActionStack.DeleteCellAction(action.index))

            case self.MOVE_ACTION: # pop the move action, add the same move action
                self.parent.moveCell(action.source, action.direction, addActionStack=False)
                adding.append(ActionStack.MoveCellAction(action.source, action.direction))

    def undo(self):
        self.executeAction(self.UNDO)

    def redo(self):
        self.executeAction(self.REDO)


    def reset(self):
        self.undoStack = []
        self.redoStack = []
    
    def __repr__(self):
        return f"""ActionStack-> UndoStack:{self.undoStack}\n              RedoStack:{self.redoStack}"""
    
    def continueProcess(self, cell):
        """
        Resize cells after processing all events.
        """
        cell.input_field.adjustHeight()
        cell.adjust_output_height()
        QApplication.processEvents()

#######################################
#            MAIN WINDOW              #
#######################################


class MainWindow(QMainWindow):
    """
    # Main Window
    
    This main window is a code notebook, with code cells and outputs and markdown rendering, alongside their respective syntax highlighting.
    
    Tools are located on the left side such as run, add, move, and delete. A topbar menu is also provided.
    """
    def __init__(self):
        super().__init__()
        self.actionStack: ActionStack = ActionStack(self)
        self.CELLS: list[Union[TextCell.TextSection, CodeCell.SimulationSection]] = []

        self.setWindowTitle("Mothball Notebook - Unnamed")
        self.name = ""
        self.path = ""
        self.unsaved_changes = False
        self.user = FileHandler.user_path
        FileHandler.createDirectories()
        self.version = FileHandler.VERSION

        FileHandler.reindexFiles() # For update purposes only!

        self.codecell_colors = FileHandler.getCodeColorSettings()
        self.textcell_colors = FileHandler.getTextColorSettings()
        self.settings = FileHandler.getGeneralSettings()

        self.help_page = None
        self.about_page = None
        self.settings_page = None
        self.wordle_page = None

        # Create a central widget and set layout
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #2e2e2e;color: white")
        self.main_layout = QVBoxLayout(central_widget)

        self.section_widget = QWidget()
        self.section_container = QVBoxLayout(self.section_widget)
        self.section_container.setSpacing(10)
        self.section_widget.setLayout(self.section_container)

        # Add X/Y buttons for empty state
        self.empty_add_widget = QWidget()
        self.empty_add_widget.setStyleSheet("QPushButton{background-color: " + "#1d1d1d}")
        empty_layout = QHBoxLayout(self.empty_add_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_add_xz_button = QPushButton("+X")
        self.empty_add_y_button = QPushButton("+Y")
        self.empty_add_text_button = QPushButton("T")
        self.empty_add_xz_button.setToolTip("Add XZ Section")
        self.empty_add_y_button.setToolTip("Add Y Section")
        self.empty_add_text_button.setToolTip("Add Text Section")
        empty_layout.addWidget(self.empty_add_xz_button)
        empty_layout.addWidget(self.empty_add_y_button)
        empty_layout.addWidget(self.empty_add_text_button)
        self.empty_add_widget.hide()  # Hide initially

        self.section_container.addWidget(self.empty_add_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.section_widget)
        self.main_layout.addWidget(self.scroll_area)

        self.setCentralWidget(central_widget)  # Set central widget

        self.addCell()  # Add the first section by default

        self.empty_add_xz_button.clicked.connect(lambda: self.addCell(cellType=CellType.XZ))
        self.empty_add_y_button.clicked.connect(lambda: self.addCell(cellType=CellType.Y))
        self.empty_add_text_button.clicked.connect(lambda: self.addCell(cellType=CellType.TEXT))

        self.createMenus()
        self.unsaved_changes = False
        
    
    def addCell(self, after_cell_or_at_index: Optional[Union[CodeCell.SimulationSection, TextCell.TextSection, int]] = None, cellType: CellType = CellType.XZ, addActionStack:bool = True, *, initialMode: TextCellState = TextCellState.EDIT):
        """
        Add a new xz (horizontal), y (vertical), or text (markdown) cell below. Returns the new cell.
        """
        self.empty_add_widget.hide()
        QApplication.processEvents()

        if cellType == CellType.XZ or cellType == CellType.Y:
            section = CodeCell.SimulationSection(self.settings, self.codecell_colors, self.textcell_colors, self.removeCell, self.addCell, self.moveCell, self.onChangeDetected, mode=cellType)
        elif cellType == CellType.TEXT:
            section = TextCell.TextSection(self.settings, self.codecell_colors, self.textcell_colors, self.removeCell, self.addCell, self.moveCell, self.onChangeDetected, initialMode=initialMode)
        
        if after_cell_or_at_index is None: # Add to the bottom end
            self.section_container.addWidget(section)
            self.CELLS.append(section)

        elif isinstance(after_cell_or_at_index, int):
            self.section_container.insertWidget(after_cell_or_at_index + 1, section)
            self.CELLS.insert(after_cell_or_at_index, section)
        else:
            index = self.section_container.indexOf(after_cell_or_at_index)
            self.CELLS.insert(index, section)
            self.section_container.insertWidget(index + 1, section)

        self.onChangeDetected()
        if addActionStack:
            self.actionStack.addDeleteAction(self.section_container.indexOf(section)-1)
        return section
        
    def removeCell(self, cell_or_index: Union[CodeCell.SimulationSection, TextCell.TextSection, int], addActionStack: bool = True):
        """
        Remove the cell `section`. If there are no more cells, show the empty cell widget.
        """
        if isinstance(cell_or_index, int):
            index = cell_or_index
            cell = self.CELLS[index]
        else:
            cell = cell_or_index
            index = self.CELLS.index(cell)

        data = self.collectCellData(index)
        self.section_container.removeWidget(cell)
        cell.setParent(None)
        cell.deleteLater()
        self.CELLS.remove(cell)
        if len(self.CELLS) == 0:
            self.empty_add_widget.show()
        self.onChangeDetected()
        if addActionStack:
            self.actionStack.addCreateAction(index, data)
        return data

    def moveCell(self, cell_or_index: Union[CodeCell.SimulationSection, TextCell.TextSection, int], direction: Literal[-1,1], addActionStack: bool = True):
        """
        Swap with the cell up (`direction = -1`) or down (`direction = 1`)
        """
        layout = self.section_container
        if isinstance(cell_or_index, int):
            index = cell_or_index
            cell = self.CELLS[index]
        else:
            index = self.CELLS.index(cell_or_index)
            cell = cell_or_index


        new_index = index + direction
        if 0 <= new_index < len(self.CELLS):
            layout.removeWidget(cell)
            layout.insertWidget(new_index + 1, cell)
            self.CELLS[index], self.CELLS[new_index] = self.CELLS[new_index], self.CELLS[index]
        
            self.onChangeDetected()
            if addActionStack:
                self.actionStack.addMoveAction(index, direction)
    
    def createMenus(self):
        """
        Create the top bar menu. Contains file, settings, and help.
        """
        menuBar = self.menuBar()
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        editMenu = menuBar.addMenu("&Edit")
        settingsMenu = menuBar.addMenu("&Settings")
        helpMenu = menuBar.addMenu("&Help")
        minigameMenu = menuBar.addMenu("&Minigames")
        
        new_action = fileMenu.addAction("New")
        open_action = fileMenu.addAction("Open")
        save_action = fileMenu.addAction("Save")
        save_as_action = fileMenu.addAction("Save As")
        fileMenu.addSeparator()

        undo_action = editMenu.addAction("Undo")
        redo_action = editMenu.addAction("Redo")
        fileMenu.addSeparator()

        open_settings = settingsMenu.addAction("Settings")
        fileMenu.addSeparator()

        about_action = helpMenu.addAction("About Mothball")
        documetation_action = helpMenu.addAction("Mothball Documentation")
        fileMenu.addSeparator()
        
        open_wordle_action = minigameMenu.addAction("Pk Wordle")
        fileMenu.addSeparator()

        new_action.triggered.connect(self.newFile)
        open_action.triggered.connect(self.openFile)
        save_action.triggered.connect(self.saveFile)
        save_as_action.triggered.connect(self.saveAsFile)

        undo_action.triggered.connect(self.undo)
        redo_action.triggered.connect(self.redo)

        open_settings.triggered.connect(self.openSettings)

        about_action.triggered.connect(self.openAbout)
        documetation_action.triggered.connect(self.openDocumentation)

        open_wordle_action.triggered.connect(self.openPkWordle)
    
    def undo(self):
        self.actionStack.undo()
    
    def redo(self):
        self.actionStack.redo()

    def openSettings(self):
        """
        Opens the settings window.
        """
        self.settings_page = Settings.SettingsWindow(self.settings, self.codecell_colors, self.textcell_colors)
        self.settings_page.show()

    def collectCellData(self, index: int) -> dict:
        data = {}
        if isinstance(self.CELLS[index], CodeCell.SimulationSection):
            data = {
                "name": self.name,
                "cell_type": self.CELLS[index].cellType,
                "code": self.CELLS[index].input_field.text(),
                "exec_time": "None",
                "has_changed": False,
                "raw_output": self.CELLS[index].raw_output
            }
        elif isinstance(self.CELLS[index], TextCell.TextSection):
            data = {
                "raw_text": self.CELLS[index].input_field.text(),
                "cell_type": self.CELLS[index].cellType,
                "mode": self.CELLS[index].mode,
                "has_changed": False
            }
        return data

    def collectAllCellData(self) -> dict:
        """
        Collects all data, recording each cell's input and output. Returns a dictionary in the form
        ```
        data: dict = {
            "fileName": name_of_file,
            "1": cell1_Data,
            "2": cell2_Data,
            "3": cell3_Data,
            ...: ...
        }
        ```

        Cell data differs depending on its `type`, which is either `code` or `text`. Type `code` cells have data
        ```
        code_cell_data: dict = {
            "name": name_of_cell,
            "mode": Literal[0,1,2], # 0 = xz, 1 = y
            "code": code_input, # The actual Mothball code
            "exec_time": "None",
            "has_changed": False,
            "raw_output": code_raw_output # The raw output from running the Mothball code 
        }
        ```

        Type `text` cells have data
        ```
        text_cell_data: dict = {
            "raw_text": cell_input_text, # The given markdown text
            "mode": Literal["edit","render"], # Determines if the cell is in edit or render mode
            "has_changed": False
        }
        ```
        """
        data = {"fileName": self.name, "version": self.version}
        for i in range(0, len(self.CELLS)):
            data[i] = self.collectCellData(i)
            
        return data

    def saveFile(self):
        """
        Saves the current notebook. If the notebook is unnamed, run `saveAsFile`.
        """
        if not self.name:
            self.saveAsFile()
        else:
            data = self.collectAllCellData()
            self.unsaved_changes = False
            with open(self.path, "w") as f:
                json.dump(data, f)
            
            self.setWindowTitle(self.windowTitle().rstrip("*"))

    def saveAsFile(self):
        """
        Save a notebook, always prompting for a name.
        """
        filepath = QFileDialog(self).getSaveFileName(self, "Save File", FileHandler.getNotebooks())[0]
        if filepath:
            self.unsaved_changes = False
            if not filepath.endswith(".json"):
                filepath += ".json"
            
            self.path = filepath
            
            basename = os.path.basename(filepath)
            self.name = os.path.splitext(basename)[0]
            
            data = self.collectAllCellData()

            with open(self.path, "w") as f:
                json.dump(data, f)

            self.setWindowTitle(f"Mothball Notebook - {self.name}")

    def newFile(self):
        """
        Clears all cells into a fresh notebook. 
        """
        reply = QMessageBox.question(self, "New Notebook", "Open a new notebook without saving?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.clearAllCells()
        self.empty_add_widget.show()
        self.name = ""
        self.path = ""
        self.unsaved_changes = False
        self.actionStack.reset()
        self.setWindowTitle("Mothball Notebook - Unnamed")
    
    def openFile(self):
        """
        Handles opening and loading files. See `FileHandler` for the data being loaded, which is a dictionary.
        """
        if self.unsaved_changes:
            reply = QMessageBox.question(self, "Open Notebook", "Open a notebook without saving?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        filepath = QFileDialog(self).getOpenFileName(self, "Open File", FileHandler.getNotebooks())[0]
        if filepath:
            self.unsaved_changes = False
            self.path = filepath
            self.clearAllCells()
            f = FileHandler.loadFile(filepath)
            i = 0
            self.name = f.fileName
            while True:
                cell = f.cells.get(i)
                if cell is None:
                    break

                if cell.cell_type == CellType.TEXT:
                    b = self.addCell(cellType=cell.cell_type)
                    b.input_field.setText(cell.raw_text)
                    if cell.mode == "render":
                        b.renderText()

                else:
                    b = self.addCell(cellType=cell.cell_type)
                    b.input_field.setText(cell.code.rstrip())
                    b.output_field.renderTextfromOutput(b.linter, cell.raw_output)
                    b.raw_output = cell.raw_output
                    
                i += 1
            self.setWindowTitle("Mothball Notebook - " + f.fileName)
            self.actionStack.reset()
            QApplication.processEvents()
            QTimer.singleShot(100, self.continueOpenFileProcess)
    
    def continueOpenFileProcess(self):
        """
        Resize cells after processing all events.
        """
        for cell in self.CELLS:
            cell.input_field.adjustHeight()
            cell.adjust_output_height()
        QApplication.processEvents()

    def clearAllCells(self):
        """
        Clears all cells.
        """
        for cell in self.CELLS:
            cell.setParent(None)
            cell.deleteLater()
        self.CELLS = []
    
    def openDocumentation(self):
        """
        Opens the documentation window.
        """
        if self.help_page is not None and self.help_page.isVisible():
            self.help_page.activateWindow()
            return
        self.help_page = HelpPage.MainWindow(self.settings, self.codecell_colors, self.textcell_colors)
        self.help_page.show()
    
    def openAbout(self):
        """
        Opens the about window.
        """
        if self.about_page is not None and self.about_page.isVisible():
            self.about_page.activateWindow()
            return
        self.about_page = AboutMothball.MainWindow(self.settings, self.codecell_colors, self.textcell_colors)
        self.about_page.show()
    
    def onChangeDetected(self):
        if not self.unsaved_changes:
            self.unsaved_changes = True
            self.setWindowTitle(self.windowTitle().rstrip("*") + "*")
    
    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(self, "Unsaved Changes", "Save changes?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Cancel:
                return event.ignore()
        
            if reply == QMessageBox.Yes:
                self.saveFile()
            for page in (self.about_page, self.wordle_page, self.help_page, self.settings_page):
                if page is not None and page.isVisible():
                    page.close()
            return super().closeEvent(event)
        else:
            for page in (self.about_page, self.wordle_page, self.help_page, self.settings_page):
                if page is not None and page.isVisible():
                    page.close()
            return super().closeEvent(event)
    
    def openPkWordle(self):
        if self.wordle_page is not None and self.wordle_page.isVisible():
            self.wordle_page.activateWindow()
            return
        self.wordle_page = ParkourWordle.GUI()
        self.wordle_page.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())

