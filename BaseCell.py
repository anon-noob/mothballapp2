"""
Base Cell Class containing the common framework for each cell, which is the side panel with its buttons.
Also contains `QsciScintilla` editor, subclassed by `CodedEditor`, and a `QsciLexerCustom` lexer subclassed by `CellLexer`. Linting logic is on `Linters`.
Also contains `RenderViewer`, used to render Mothball code outputs and markdown text.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,QHBoxLayout,QTextBrowser
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from PyQt5.Qsci import QsciLexerCustom, QsciScintilla
from utils import *
from Linters import CodeLinter, MDLinter
from typing import Literal
import os, sys
from Enums import *


if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

class Cell(QWidget):
    """
    Base `Cell` class, contains the left side panel framework and an empty main layout
    """
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, cellType: CellType):
        super().__init__()
        self.cellType = cellType
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.options = generalOptions

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(10)

        # Side button panel (vertical)
        self.side_panel = QWidget(self)
        self.side_panel.setStyleSheet("QPushButton{background-color: " + "#1d1d1d}")
        self.side_panel_layout = QVBoxLayout(self.side_panel)
        self.side_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.side_panel_layout.setSpacing(5)
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        self.run_button = QPushButton("▶")
        self.add_xz_button = QPushButton("+X")
        self.add_y_button = QPushButton("+Y")
        self.add_text_button = QPushButton("T")
        self.delete_button = QPushButton("🗑")
        self.setStyleSheet("""QToolTip { 
                           background-color: #2e2e2e; 
                           color: white; 
                           border: black solid 1px
                           }""")
        self.up_button.setToolTip("Move Up")
        self.down_button.setToolTip("Move Down")
        if cellType == CellType.TEXT:
            self.run_button.setToolTip("Render/Edit")
        else:
            self.run_button.setToolTip("Run")
        self.add_xz_button.setToolTip("Add XZ Section Below")
        self.add_y_button.setToolTip("Add Y Section Below")
        self.add_text_button.setToolTip("Add Text Section Below")
        self.delete_button.setToolTip("Delete Section")

        self.side_panel_layout.addWidget(self.run_button)
        self.side_panel_layout.addWidget(self.add_xz_button)
        self.side_panel_layout.addWidget(self.add_y_button)
        self.side_panel_layout.addWidget(self.add_text_button)
        self.side_panel_layout.addWidget(self.delete_button)
        self.side_panel_layout.addWidget(self.up_button)
        self.side_panel_layout.addWidget(self.down_button)
        self.side_panel_layout.addStretch(1)
        self.side_panel.setFixedWidth(40)
        self.main_layout.addWidget(self.side_panel)

class CellLexer(QsciLexerCustom):
    "Lexer for notebook cells, both code and text cells. The actual lexing is manually done at `CodeCell` and `TextCell`."
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, parent=None, cellType: Literal["code", "text"] = "code"):
        super().__init__(parent)
        self.codeColorOptions = colorOptions[StringLiterals.CODE]
        self.textColorOptions = textOptions[StringLiterals.CODE]
        self.fontStyle = generalOptions["Default Font"]
        self.fontSize = generalOptions["Default Font Size"]

        self.backgroundColor = None
        self.defaultTextColor = None
        if cellType == CellType.TEXT:
            self.backgroundColor = textOptions[StringLiterals.CODE_BACKGROUND]
            self.defaultTextColor = self.textColorOptions[Style.DEFAULT]
        else:
            self.backgroundColor = colorOptions[StringLiterals.CODE_BACKGROUND]
            self.defaultTextColor = self.codeColorOptions[Style.DEFAULT]

        self.setDefaultFont(QFont(self.fontStyle, self.fontSize))
        self.setFont(QFont(self.fontStyle, self.fontSize), Style.DEFAULT)

        for style in Style.getCodeEditStyles():
            self.setColor(QColor(self.codeColorOptions[style]), style)

        self.setColor(QColor(self.defaultTextColor), Style.DEFAULT)

        self.setColor(QColor(self.textColorOptions[Style.HEADER1]), Style.HEADER1)
        self.setColor(QColor(self.textColorOptions[Style.HEADER2]), Style.HEADER2)
        self.setColor(QColor(self.textColorOptions[Style.HEADER3]), Style.HEADER3)

    def styleText(self, start: int, end: int):
        pass

    def description(self, style: int):
        return " "
    
    def font(self, style: int):
        return QFont(self.fontStyle, self.fontSize)

    def defaultPaper(self, style: int):
        return QColor(self.backgroundColor)

    def defaultColor(self, style: int):
        return QColor(self.defaultTextColor)

    # def changeColor(self, styleString: str, newColor: str):
    #     "Change the color of `styleString` to a new color `newColor`, typically represented in hex format. `styleString` are names of tokens such as 'returners', 'variables', etc."
    #     if styleString in self.TOKEN_TO_CODE_COLOR_STYLE:
    #         self.codeColorOptions[styleString] = newColor
    #         self.setColor(QColor(self.codeColorOptions[styleString]), self.TOKEN_TO_CODE_COLOR_STYLE[styleString])
    #     if styleString in self.TOKEN_TO_TEXT_COLOR_STYLE:
    #         self.textColorOptions[styleString] = newColor
    #         self.setColor(QColor(self.textColorOptions[styleString]), self.TOKEN_TO_TEXT_COLOR_STYLE[styleString])

class CodeEdit(QsciScintilla):
    "Main code editor for code cells and markdown text edit cells."
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, parent):
        super().__init__(parent)
        self.mainLexer = CellLexer(generalOptions, colorOptions, textOptions)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBraceMatching(QsciScintilla.StrictBraceMatch)
        self.setWrapMode(QsciScintilla.WrapWord)
        self.setLexer(self.mainLexer)
        self.textChanged.connect(self.adjustHeight)
        self.setEolMode(QsciScintilla.EolMode.EolUnix)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, e):
        self.adjustHeight()
        return super().resizeEvent(e)
    
    def adjustHeight(self):
        "Adjust height based on visible lines, including word wrapped lines"
        logical_lines = max(1,self.lines())
        new_height = 0
        for i in range(logical_lines):
            wrap = self.SendScintilla(self.SCI_WRAPCOUNT, i)
            line_height = self.SendScintilla(self.SCI_TEXTHEIGHT, i)
            new_height += (wrap if wrap > 0 else 1) * line_height

        self.setFixedHeight(new_height + 2)

class RenderViewer(QTextBrowser):
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, parent):
        super().__init__(parent)
        self.options = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.setStyleSheet(f'background: {textOptions[StringLiterals.RENDER_BACKGROUND]}; color: {textOptions[StringLiterals.RENDER][Style.DEFAULT]};')
        self.setOpenExternalLinks(True)
        self.verticalScrollBar().setVisible(False)
    
    def renderTextfromOutput(self, linter: CodeLinter, output: list[tuple[str,str]], displayOutputBackground: bool = False):
        "Render raw output into html text."
        tokens = linter.parseOutput(output, displayOutputBackground)
        self.render(tokens)
    
    def renderTextfromMarkdown(self, linter: MDLinter, text: str):
        "Render the markdown into html text."
        tokens = linter.parseTextToRender(text)
        self.render(tokens)
    
    def render(self, tokens: list[tuple[str,int,int]]):
        "Inner render function, use `renderTextfromOutput` and `renderTextfromMarkdown`. Render the HTML given the tokens, which is a list of 3-tuples, each containing the text, style, and a flag variable for whether text is inline/block code or not."
        codeColors = self.colorOptions[StringLiterals.CODE]
        outputColors = self.colorOptions[StringLiterals.OUTPUT]
        html_lines = ['<html>\n', 
                      f'<body style="background-color:{self.textOptions[StringLiterals.RENDER_BACKGROUND]}; color:{self.textOptions[StringLiterals.CODE][Style.DEFAULT]}; font-family:{self.options["Default Font"]}; font-size:{self.options["Default Font Size"]}pt; white-space: pre-wrap;">\n', 
                      '<div>']
        curr_in_code = 0
        last_element = None

        # print(tokens)
        for i, element in enumerate(tokens):
            token, style, in_code = element
            if token and (token.endswith("\n") or token.endswith("\r\n")) and (i+1 < len(tokens) and tokens[i+1][2] == 1 and in_code == 0):
                token = token.strip()

            if in_code == 1 and curr_in_code == 0: # default -> block
                html_lines.append('</div>')
                html_lines.append(f'<div style="background-color:{self.textOptions[StringLiterals.RENDER_BLOCK_BACKGROUND]};">\n')
                curr_in_code = 1
            elif in_code == 3 and curr_in_code == 1: # block -> output
                html_lines.append('</div>')
                html_lines.append(f'<div style="background-color:{self.textOptions[StringLiterals.RENDER_CODE_BACKGROUND]};">\n')
                curr_in_code = 3
            elif in_code == 2 and curr_in_code == 0: # default -> inline
                html_lines.append(f'<code style="font-family:{self.options["Default Font"]};">')
                curr_in_code = 2

            elif in_code == 0:
                if curr_in_code == 1: # block -> default
                    html_lines.append('</div>')
                    html_lines.append('<div>')
                    curr_in_code = 0
                elif curr_in_code == 3: # output -> default
                    html_lines.append('</div>')
                    html_lines.append('<div>')
                    curr_in_code = 0
                elif curr_in_code == 2: # inline -> default
                    html_lines.append('</code>')
                    curr_in_code = 0


            token = token.replace("\r", "")
            if not token and not curr_in_code:
                continue
            match style:
                case Style.DEFAULT: # Default
                    if token:
                        html_lines.append(f"<span>{token}</span>")
                case _ if style in Style.getCodeEditStyles():
                    html_lines.append(f"<span style='color:{codeColors[style]};'>{token}</span>")
                case Style.LINKS:
                    name,link = token[1:len(token)-1].split("](")
                    if os.path.exists(os.path.join(base_path,"images", link)):
                        html_lines.append(f"""<img src='{os.path.join(base_path,"images", link)}' alt='oops'>\n""")
                    else:
                        if not link.startswith("https://") and not link.startswith("http://"):
                            link = "https://" + link
                        html_lines.append(f"<a href='{link}' style='color:{self.textOptions[StringLiterals.RENDER][Style.LINKS]};'>{name}</a>")
                case _ if style in Style.getCodeOutputStyles():
                    html_lines.append(f"<span style='color:{outputColors[style]};'>{token}</span>")
                case _ if style in Style.getTextOutputStyles():
                    if style == Style.RENDER_HEADER1:
                        html_lines.append(f"<span id='{token.strip()}' style='color:{self.textOptions[StringLiterals.RENDER][style]}; font-size:24pt;'>{token}</span>")
                    elif style == Style.RENDER_HEADER2:
                        html_lines.append(f"<span id='{token.strip()}' style='color:{self.textOptions[StringLiterals.RENDER][style]}; font-size:21pt;'>{token}</span>")
                    elif style == Style.RENDER_HEADER3:
                        html_lines.append(f"<span id='{token.strip()}' style='color:{self.textOptions[StringLiterals.RENDER][style]}; font-size:18pt;'>{token}</span>")
                    else:
                        html_lines.append(f"<span style='color:{self.textOptions[StringLiterals.RENDER][style]};'>{token}</span>")

        html_lines.append("</div>\n")
        html_lines.append("</body>\n")
        html_lines.append("</html>")
        # print(''.join(html_lines))
        self.setHtml("".join(html_lines))