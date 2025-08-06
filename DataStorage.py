from dataclasses import dataclass
from Enums import *

@dataclass
class CodeCell:
    """
    name: name of file \\
    mode: `xz` or `y` \\
    code: the code string \\
    raw_output: the raw output of the code, as a `list[tuple]`
    """
    name: str
    cell_type: CellType
    code: str
    exec_time: str | None
    has_changed: bool
    raw_output: list[list]

@dataclass
class TextCell:
    """
    name: name of file \\
    mode: `edit` or `render` \\
    raw_text: the raw output of the code, as a `list[tuple]`
    """
    cell_type: CellType
    mode: StringLiterals
    has_changed: bool
    raw_text: str

@dataclass
class File:
    """
    fileName: the file name \\
    version: the version string \\
    cells: dictionary of `int` as keys, indicating order, and `CodeCell` or `TextCell` dataclass
    """
    fileName: str
    version: str
    cells: dict[int,CodeCell | TextCell]