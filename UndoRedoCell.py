from typing import Literal, Union
from PyQt5.QtCore import Qt, QTimer
from Enums import CellType
from version import __version__
import MacroViewer

class ActionStack:
    """
    Keeps track of GUI changes, mainly adding, removing, and moving cells. `undo` executes the action, `redo` executes the opposite action. 
    """
    DELETE_ACTION = 0
    CREATE_ACTION = 1
    MOVE_ACTION = 2

    UNDO = 0
    REDO = 1

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

    def __init__(self, parent):
        self.parent = parent # GUI
        self.undoStack: list[Union[ActionStack.DeleteCellAction, ActionStack.CreateCellAction, ActionStack.MoveCellAction]] = []
        self.redoStack: list[Union[ActionStack.DeleteCellAction, ActionStack.CreateCellAction, ActionStack.MoveCellAction]] = []

    def addDeleteAction(self, index: int):
        "When the user adds a cell, push a `delete` action to the `undoStack`"
        self.undoStack.append(ActionStack.DeleteCellAction(index))
        self.redoStack.clear()

    def addCreateAction(self, index: int, data):
        "When the user deletes a cell, push a `create` action to the `undoStack`"
        self.undoStack.append(ActionStack.CreateCellAction(index, data))
        self.redoStack.clear()

    def addMoveAction(self, source: int, direction: int):
        "When the user moves a cell, push a `move` action to the `undoStack`"
        self.undoStack.append(ActionStack.MoveCellAction(source, direction))
        self.redoStack.clear()

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
                t = action.data["cell_type"]
                if t == CellType.TEXT:
                    cell = self.parent.addCell(action.index, cellType=action.data['cell_type'], addActionStack=False)
                    QTimer.singleShot(0,cell.adjust_output_height)
                    
                elif t == CellType.XZ or t == CellType.Y:
                    cell = self.parent.addCell(action.index, cellType=action.data["cell_type"], addActionStack=False)
                    QTimer.singleShot(0,cell.adjust_output_height)

                elif t == CellType.OPTIMIZE:
                    cell = self.parent.addCell(action.index, cellType=action.data["cell_type"], addActionStack=False)
                
                adding.append(ActionStack.DeleteCellAction(action.index))
                cell.setupCell(action.data)

            case self.MOVE_ACTION: # pop the move action, add the same move action
                self.parent.moveCell(action.source, action.direction, addActionStack=False)
                adding.append(ActionStack.MoveCellAction(action.source, action.direction))

    def undo(self):
        self.executeAction(self.UNDO)

    def redo(self):
        self.executeAction(self.REDO)

    def reset(self):
        self.undoStack.clear()
        self.redoStack.clear()
    
    def __repr__(self):
        return f"""ActionStack-> UndoStack:{self.undoStack}\n              RedoStack:{self.redoStack}"""