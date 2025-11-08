"""
The main Mothball Window, a coding notebook-like experience, with 3 types of cells: horizontal movement, vertical movement, and markdown.

Contains:
- File save system
- Basic (but incomplete) documentation
- Customizable colors and other settings (NOT FINISHED/FULLY IMPLEMENTED)
"""

import CrashHandler
import sys,os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, QMenu, QMainWindow, QFileDialog, QMessageBox, QShortcut
)
from PyQt5.QtGui import QKeySequence
from typing import Literal, Union, Optional
import HelpPage
import Settings
import AboutMothball
from PyQt5.QtCore import Qt, QTimer
from utils import * 
import CodeCell, TextCell, AngleOptimizerCell
import FileHandler
import json
import ParkourWordle
import ReferencePage
from Enums import CellType, TextCellState
from version import __version__
import MacroViewer
from UndoRedoCell import ActionStack

# Reorganize the help page
# Fix settings
# Something is wrong with action stack when undoing towards the end

# Default settings for each simulation (version, pre, etc)

# Debian Linux fix: run in console `sudo apt-get install libxcb-xinerama0`

"""ERRORS:
(Linux) Type in Text Cells does this error
Assertion [lengthStyle == 0 || (lengthStyle > 0 && lengthStyle + position <= style.Length())] failed at ../../tmpym18yovx/QScintilla2/QScintilla_src-2.14.1/scintilla/src/CellBuffer.cpp 635

Aborted
"""
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
        self.CELLS: list[Union[TextCell.TextSection, CodeCell.SimulationSection, AngleOptimizerCell.OptimizationSection]] = []

        self.setWindowTitle(f"Mothball Notebook v{__version__} - Unnamed")
        self.name = ""
        self.path = ""
        self.unsaved_changes = False
        self.user = FileHandler.user_path
        FileHandler.createDirectories()
        self.version = __version__

        self.codecell_colors = FileHandler.getCodeColorSettings()
        self.textcell_colors = FileHandler.getTextColorSettings()
        self.settings = FileHandler.getGeneralSettings()

        while FileHandler.versionIsOutdated(self.settings['Version']):
            self.settings, self.codecell_colors, self.textcell_colors = FileHandler.settings_version_map.get(self.settings['Version'], FileHandler.getDefaultSettings)()

        self.help_page = None
        self.about_page = None
        self.settings_page = None
        self.wordle_page = None
        self.macro_viewer = None
        self.reference_page = None

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
        self.empty_add_optimize_button = QPushButton("Op")
        self.empty_add_xz_button.setToolTip("Add XZ Section")
        self.empty_add_y_button.setToolTip("Add Y Section")
        self.empty_add_text_button.setToolTip("Add Text Section")
        self.empty_add_optimize_button.setToolTip("Add Optimization Section")
        empty_layout.addWidget(self.empty_add_xz_button)
        empty_layout.addWidget(self.empty_add_y_button)
        empty_layout.addWidget(self.empty_add_text_button)
        empty_layout.addWidget(self.empty_add_optimize_button)
        self.empty_add_widget.hide()  # Hide initially

        self.section_container.addWidget(self.empty_add_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.section_widget)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.main_layout.addWidget(self.scroll_area)
        
        self.setCentralWidget(central_widget)  # Set central widget
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        

        self.empty_add_xz_button.clicked.connect(lambda: self.addCell(cellType=CellType.XZ))
        self.empty_add_y_button.clicked.connect(lambda: self.addCell(cellType=CellType.Y))
        self.empty_add_text_button.clicked.connect(lambda: self.addCell(cellType=CellType.TEXT))
        self.empty_add_optimize_button.clicked.connect(lambda: self.addCell(cellType=CellType.OPTIMIZE))

        self.createMenus()
        self.unsaved_changes = False

        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo)
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut.activated.connect(self.redo)

        self.addCell()  # Add the first section by default
    
        QTimer.singleShot(0, self.restoreWorkFromCrash)

        self.resize_big_shortcut = QShortcut(QKeySequence.StandardKey.ZoomIn, self, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.resize_small_shortcut = QShortcut(QKeySequence.StandardKey.ZoomOut, self, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.resize_big_shortcut.activated.connect(self.resizeBig)
        self.resize_small_shortcut.activated.connect(lambda: print("BYE"))

    def resizeBig(self):
        pass

    def restoreWorkFromCrash(self):
        with open(FileHandler.getPathToLastState(), "r") as f:
            d = json.load(f)
            if not d.get('crashed'):
                return
        
        if d.get('tempfile'):
            a = QMessageBox.question(self, "Restore Work", f"Mothball previously crashed. Restore previous notebook?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if a == QMessageBox.StandardButton.Yes:
                self.openFile(FileHandler.getPathToTempFile())

    def copyCell(self, cell_or_index_to_copy: Union[CodeCell.SimulationSection, TextCell.TextSection, AngleOptimizerCell.OptimizationSection, int]):
        """
        Copy the cell given, or the cell at the index given.
        """
        if isinstance(cell_or_index_to_copy, int):
            index = cell_or_index_to_copy
            cell = self.CELLS[cell_or_index_to_copy + 1]
        else:
            index = self.section_container.indexOf(cell_or_index_to_copy)
            cell = cell_or_index_to_copy

        d = cell.getCellData()
        
        newcell = self.addCell(cell, cell.cellType)
        newcell.setupCell(d)
        if cell.cellType != CellType.OPTIMIZE:
            QTimer.singleShot(50,newcell.input_field.adjustHeight)
            QTimer.singleShot(50,newcell.adjust_output_height)

    def addCell(self, after_cell_or_at_index: Optional[Union[CodeCell.SimulationSection, TextCell.TextSection, AngleOptimizerCell.OptimizationSection, int]] = None, cellType: CellType = CellType.XZ, addActionStack:bool = True, *, initialMode: TextCellState = TextCellState.EDIT):
        """
        Add a new xz (horizontal), y (vertical), or text (markdown) cell below. Returns the new cell.
        """
        self.empty_add_widget.hide()
        QApplication.processEvents()

        if cellType == CellType.XZ or cellType == CellType.Y:
            section = CodeCell.SimulationSection(self, self.settings, self.codecell_colors, self.textcell_colors, self.removeCell, self.addCell, self.moveCell, self.onChangeDetected, self.copyCell, mode=cellType)
        elif cellType == CellType.TEXT:
            section = TextCell.TextSection(self, self.settings, self.codecell_colors, self.textcell_colors, self.removeCell, self.addCell, self.moveCell, self.onChangeDetected, self.copyCell, initialMode=initialMode)
        elif cellType == CellType.OPTIMIZE:
            section = AngleOptimizerCell.OptimizationSection(self, self.settings, self.codecell_colors, self.textcell_colors, self.removeCell, self.addCell, self.moveCell, self.onChangeDetected, self.copyCell)

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
        
    def removeCell(self, cell_or_index: Union[CodeCell.SimulationSection, TextCell.TextSection, AngleOptimizerCell.OptimizationSection, int], addActionStack: bool = True):
        """
        Remove the cell `section`. If there are no more cells, show the empty cell widget.
        """
        if isinstance(cell_or_index, int):
            index = cell_or_index
            cell = self.CELLS[index]
        else:
            cell = cell_or_index
            index = self.CELLS.index(cell)
        
        if isinstance(cell, CodeCell.SimulationSection):
            if cell.worker is not None:
                cell.cancel()
        elif isinstance(cell, AngleOptimizerCell.OptimizationSection):
            if cell.worker is not None and cell.worker.isrunning:
                return

        data = self.getCellData(index)
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

    def moveCell(self, cell_or_index: Union[CodeCell.SimulationSection, TextCell.TextSection, AngleOptimizerCell.OptimizationSection, int], direction: Literal[-1,1], addActionStack: bool = True):
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
        macroView = menuBar.addMenu("&Macros")
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

        openMacroView = macroView.addAction("Open Macro Viewer")
        fileMenu.addSeparator()

        about_action = helpMenu.addAction("About Mothball")
        documetation_action = helpMenu.addAction("Mothball Documentation")
        reference_values = helpMenu.addAction("Reference Values")
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

        openMacroView.triggered.connect(self.openMacroViewer)

        about_action.triggered.connect(self.openAbout)
        documetation_action.triggered.connect(self.openDocumentation)
        reference_values.triggered.connect(self.openReferenceWindow)

        open_wordle_action.triggered.connect(self.openPkWordle)
    
    def undo(self):
        self.actionStack.undo()
        QApplication.processEvents()
        
    def redo(self):
        self.actionStack.redo()
        QApplication.processEvents()

    def openSettings(self):
        """
        Opens the settings window.
        """
        self.settings_page = Settings.SettingsWindow(self, self.settings, self.codecell_colors, self.textcell_colors)
        self.settings_page.show()

    def getCellData(self, index: int) -> dict:
        return self.CELLS[index].getCellData()

    def getAllCellData(self) -> dict:
        data = {"fileName": self.name, "version": self.version}
        for i in range(0, len(self.CELLS)):
            data[i] = self.getCellData(i)
        return data

    def saveFile(self):
        """
        Saves the current notebook. If the notebook is unnamed, run `saveAsFile`.
        """
        if not self.name:
            self.saveAsFile()
        else:
            data = self.getAllCellData()
            self.unsaved_changes = False
            with open(self.path, "w") as f:
                json.dump(data, f, indent=4)
            
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
            
            data = self.getAllCellData()

            with open(self.path, "w") as f:
                json.dump(data, f, indent=4)

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
    
    def openFile(self, filepath: str = None):
        """
        Handles opening and loading files. See `FileHandler` for the data being loaded, which is a dictionary.
        """
        from_dialog = False
        if not filepath:
            from_dialog = True
            
        if from_dialog:
            if self.unsaved_changes:
                reply = QMessageBox.question(self, "Open Notebook", "Open a notebook without saving?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            filepath = QFileDialog(self).getOpenFileName(self, "Open File", FileHandler.getNotebooks())[0]

        if not filepath:
            return

        fileName = os.path.splitext(os.path.basename(filepath))[0]
        logs = None
        self.clearAllCells()
        try:
            f = FileHandler.loadFile(filepath)
        except Exception as logs:
            QMessageBox.warning(self, "Failed to load", f"file {self.name} has encountered a fatal error. Please check and update the file!\nLogs: {logs}", QMessageBox.StandardButton.Ok)
            return
        i = 0
        same_version = self.version == f.version

        while f.version != self.version:
            d = FileHandler.notebooks_version_map.get(f.version)
            if d is None:
                break
            else:
                d(filepath)
                f = FileHandler.loadFile(filepath)
                same_version = self.version == f.version

        while True:
            cell = f.cells.get(i)
            if cell is None:
                break

            try:
                c = self.addCell(cellType=cell.cell_type)
                c.setupCell(cell.__dict__)
                if c.cellType != CellType.OPTIMIZE:
                    QTimer.singleShot(0,c.adjust_output_height)
                
            except Exception as e:
                print(e)

            i += 1

        if from_dialog:
            self.path = filepath
            self.name = fileName
            self.setWindowTitle(f"Mothball Notebook v{self.version} - " + fileName)
            self.unsaved_changes = False

        self.actionStack.reset()
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
            
            with open(FileHandler.getPathToLastState(), 'w') as file:
                json.dump({"crashed":False, "tempfile":False, "log": ""}, file)
            return super().closeEvent(event)
        else:
            for page in (self.about_page, self.wordle_page, self.help_page, self.settings_page):
                if page is not None and page.isVisible():
                    page.close()
            with open(FileHandler.getPathToLastState(), 'w') as file:
                json.dump({"crashed":False, "tempfile":False, "log": ""}, file)
            return super().closeEvent(event)
    
    def openPkWordle(self):
        if self.wordle_page is not None and self.wordle_page.isVisible():
            self.wordle_page.activateWindow()
            return
        self.wordle_page = ParkourWordle.GUI()
        self.wordle_page.show()
    
    def openReferenceWindow(self):
        if self.reference_page is not None and self.reference_page.isVisible():
            self.reference_page.activateWindow()
            return
        self.reference_page = ReferencePage.MainWindow(self.settings, self.codecell_colors, self.textcell_colors)
        self.reference_page.show()
    
    def openMacroViewer(self, filename: str = None, macrodata = None, macroType = None):
        if self.macro_viewer is not None and self.macro_viewer.isVisible():
            self.macro_viewer.activateWindow()
        else:
            self.macro_viewer = MacroViewer.MacroViewer()
            self.macro_viewer.resize(650, 650)
            self.macro_viewer.show()

        if filename is not None and macrodata is not None and macroType is not None:
            self.macro_viewer.addTab(filename, macrodata)
    
    def updateGeneralSettings(self, newsettings: dict):
        for cell in self.CELLS:
            if isinstance(cell, CodeCell.SimulationSection):
                cell.mc_macros_folders = newsettings["Macro Folders"]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    
    crash_handler = CrashHandler.CrashHandler(window)
    sys.excepthook = crash_handler.f

    window.resize(1200, 800)
    window.setMinimumSize(600,400)
    window.show()
    sys.exit(app.exec())

