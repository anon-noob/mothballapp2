from dataclasses import dataclass
from Enums import *

@dataclass
class CodeCell:
    name: str
    cell_type: CellType
    code: str
    exec_time: str | None
    has_changed: bool
    raw_output: list[list]

@dataclass
class TextCell:
    cell_type: CellType
    mode: StringLiterals
    has_changed: bool
    raw_text: str

@dataclass
class AngleOptimizerCell:
    cell_type: CellType
    axis: OptimizeCellAxis
    mode: str
    variables: list[list]
    drags: list[list]
    constraints: list[list]
    output: str
    points: list[list[int],list[int]]

@dataclass
class File:
    """
    fileName: the file name \\
    version: the version string \\
    cells: dictionary of `int` as keys, indicating order, and `CodeCell` or `TextCell` dataclass
    """
    fileName: str
    version: str
    cells: dict[int,CodeCell | TextCell | AngleOptimizerCell]