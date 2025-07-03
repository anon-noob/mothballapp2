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


if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

class Cell(QWidget):
    """
    Base `Cell` class, contains the left side panel framework and an empty main layout
    """
    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, cellType: Literal["code","text"]):
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
        if cellType == "text":
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
    STYLE_DEFAULT = 0
    STYLE_FAST = 1
    STYLE_SLOW = 2
    STYLE_STOP = 3
    STYLE_RETURN = 4
    STYLE_CALCS = 5
    STYLE_SETTER = 6
    STYLE_INPUTS = 7
    STYLE_MODIFIER = 8
    STYLE_NUMBERS = 9
    STYLE_COMMENT = 10
    STYLE_KW_ARG = 11
    STYLE_NEST0 = 12
    STYLE_NEST1 = 13
    STYLE_NEST2 = 14
    STYLE_ERROR = 15
    STYLE_VARS = 16
    STYLE_STRING = 17

    STYLE_LINKS = 18
    STYLE_HEADER1 = 19
    STYLE_HEADER2 = 20
    STYLE_HEADER3 = 21
    STYLE_RENDER_HEADER1 = 22
    STYLE_RENDER_HEADER2 = 23
    STYLE_RENDER_HEADER3 = 24

    STYLE_OUTPUT_LABEL = 25
    STYLE_OUTPUT_ZLABEL = 26
    STYLE_OUTPUT_XLABEL = 27
    STYLE_OUTPUT_WARNING = 28
    STYLE_OUTPUT_POSITIVE = 29
    STYLE_OUTPUT_NEGATIVE = 30
    STYLE_OUTPUT_TEXT = 31

    STYLE_POSITIONAL_PARAMETER = 32
    STYLE_POSITIONAL_OR_KEYWORD_PARAMETER = 33
    STYLE_KEYWORD_PARAMETER = 34
    STYLE_VAR_POSITIONAL_PARAMETER = 35

    STYLE_DATATYPE = 36

    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, parent=None, cellType: Literal["code", "text"] = "code"):
        super().__init__(parent)
        self.codeColorOptions = colorOptions["Code"]
        self.textColorOptions = textOptions["Code"]
        self.fontStyle = generalOptions["Default Font"]
        self.fontSize = generalOptions["Default Font Size"]
        # print(self.textColorOptions, textOptions)
        self.TOKEN_TO_CODE_COLOR_STYLE = {
            'default': 0,
            'fast': 1,
            'slow': 2,
            'stop': 3,
            'returners': 4,
            'calculators': 5,
            'setters': 6,
            'inputs': 7,
            'modifiers': 8,
            'numbers': 9,
            'comment': 10,
            'keyword': 11,
            'bracket0': 12,
            'bracket1': 13,
            'bracket2': 14,
            'error': 15,
            'variable': 16,
            'string': 17,
        }

        self.TOKEN_TO_TEXT_COLOR_STYLE = {
            'default': 0,
            'heading1': 19,
            'heading2': 20,
            'heading3': 21,
        }

        self.TOKEN_TO_RENDER_TEXT_COLOR_STYLE = {
            'default': 0,
            'link': 18,
            'heading1': 22,
            'heading2': 23,
            'heading3': 24,
            # 'Output Background': 23,
            # 'Block Background': 23,
        }

        self.backgroundColor = None
        self.defaultTextColor = None
        if cellType == "code":
            self.backgroundColor = colorOptions["Code Background"]
            self.defaultTextColor = self.codeColorOptions["default"]
        elif cellType == "text":
            self.backgroundColor = textOptions["Code Background"]
            self.defaultTextColor = self.textColorOptions["default"]

        self.setDefaultFont(QFont(self.fontStyle, self.fontSize))
        self.setFont(QFont(self.fontStyle, self.fontSize), self.STYLE_DEFAULT)
        self.setColor(QColor(self.codeColorOptions["fast"]), self.STYLE_FAST)
        self.setColor(QColor(self.codeColorOptions["slow"]), self.STYLE_SLOW)
        self.setColor(QColor(self.codeColorOptions["stop"]), self.STYLE_STOP)
        self.setColor(QColor(self.codeColorOptions["returners"]), self.STYLE_RETURN)
        self.setColor(QColor(self.codeColorOptions["calculators"]), self.STYLE_CALCS)
        self.setColor(QColor(self.codeColorOptions["setters"]), self.STYLE_SETTER)
        self.setColor(QColor(self.codeColorOptions["inputs"]), self.STYLE_INPUTS)
        self.setColor(QColor(self.codeColorOptions["modifiers"]), self.STYLE_MODIFIER)
        self.setColor(QColor(self.codeColorOptions["numbers"]), self.STYLE_NUMBERS)
        self.setColor(QColor(self.codeColorOptions["comment"]), self.STYLE_COMMENT)
        self.setColor(QColor(self.codeColorOptions["keyword"]), self.STYLE_KW_ARG)
        self.setColor(QColor(self.codeColorOptions["bracket1"]), self.STYLE_NEST0)
        self.setColor(QColor(self.codeColorOptions["bracket2"]), self.STYLE_NEST1)
        self.setColor(QColor(self.codeColorOptions["bracket0"]), self.STYLE_NEST2)
        self.setColor(QColor(self.codeColorOptions["error"]), self.STYLE_ERROR)
        self.setColor(QColor(self.codeColorOptions["variable"]), self.STYLE_VARS)
        self.setColor(QColor(self.codeColorOptions["string"]), self.STYLE_STRING)
        self.setColor(QColor(self.codeColorOptions["bool"]), self.STYLE_DATATYPE)
        self.setColor(QColor(self.defaultTextColor), self.STYLE_DEFAULT)

        self.setColor(QColor(self.textColorOptions["heading1"]), self.STYLE_HEADER1)
        self.setColor(QColor(self.textColorOptions["heading2"]), self.STYLE_HEADER2)
        self.setColor(QColor(self.textColorOptions["heading3"]), self.STYLE_HEADER3)

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

    def changeColor(self, styleString: str, newColor: str):
        "Change the color of `styleString` to a new color `newColor`, typically represented in hex format. `styleString` are names of tokens such as 'returners', 'variables', etc."
        if styleString in self.TOKEN_TO_CODE_COLOR_STYLE:
            self.codeColorOptions[styleString] = newColor
            self.setColor(QColor(self.codeColorOptions[styleString]), self.TOKEN_TO_CODE_COLOR_STYLE[styleString])
        if styleString in self.TOKEN_TO_TEXT_COLOR_STYLE:
            self.textColorOptions[styleString] = newColor
            self.setColor(QColor(self.textColorOptions[styleString]), self.TOKEN_TO_TEXT_COLOR_STYLE[styleString])

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
        self.setEolMode(QsciScintilla.EolUnix)

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
        self.setStyleSheet(f'background: {textOptions["Render Background"]}; color: {textOptions["Render"]["default"]};')
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
        codeColors = self.colorOptions['Code']
        outputColors = self.colorOptions['Output']
        html_lines = ['<html>\n', 
                      f'<body style="background-color:{self.textOptions["Render Background"]}; color:{self.textOptions["Code"]["default"]}; font-family:{self.options["Default Font"]}; font-size:{self.options["Default Font Size"]}pt; white-space: pre-wrap;">\n', 
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
                html_lines.append(f'<div style="background-color:{self.textOptions["Render"]["Block Background"]};">\n')
                curr_in_code = 1
            elif in_code == 3 and curr_in_code == 1: # block -> output
                html_lines.append('</div>')
                html_lines.append(f'<div style="background-color:{self.textOptions["Render"]["Output Background"]};">\n')
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
                case 0: # Default
                    if token:
                        html_lines.append(f"<span>{token}</span>")
                case 1: # Code: Fast Movers
                    html_lines.append(f"<span style='color:{codeColors['fast']};'>{token}</span>")
                case 2: # Code: Slow movers
                    html_lines.append(f"<span style='color:{codeColors['slow']};'>{token}</span>")
                case 3: # Code: Stop movers
                    html_lines.append(f"<span style='color:{codeColors['stop']};'>{token}</span>")
                case 4: # Code: Returners
                    html_lines.append(f"<span style='color:{codeColors['returners']};'>{token}</span>")
                case 5: # Code: Calculators
                    html_lines.append(f"<span style='color:{codeColors['calculators']};'>{token}</span>")
                case 6: # Code: Setters
                    html_lines.append(f"<span style='color:{codeColors['setters']};'>{token}</span>")
                case 7: # Code: Inputs
                    html_lines.append(f"<span style='color:{codeColors['inputs']};'>{token}</span>")
                case 8: # Code: Modifiers
                    html_lines.append(f"<span style='color:{codeColors['modifiers']};'>{token}</span>")
                case 9: # Code: Numbers
                    html_lines.append(f"<span style='color:{codeColors['numbers']};'>{token}</span>")
                case 10: # Code: comments
                    html_lines.append(f"<span style='color:{codeColors['comment']};'>{token}</span>")
                case 11: # Code: Keyword Args
                    html_lines.append(f"<span style='color:{codeColors['keyword']};'>{token}</span>")
                case 12: # Code: Nest 0 
                    html_lines.append(f"<span style='color:{codeColors['bracket1']};'>{token}</span>")
                case 13: # Code: Nest 1
                    html_lines.append(f"<span style='color:{codeColors['bracket2']};'>{token}</span>")
                case 14: # Code: Nest 2
                    html_lines.append(f"<span style='color:{codeColors['bracket0']};'>{token}</span>")
                case 15: # Code: Error
                    html_lines.append(f"<span style='color:{codeColors['error']};'>{token}</span>")
                case 16: # Code: Variables
                    html_lines.append(f"<span style='color:{codeColors['variable']};'>{token}</span>")
                case 17: # Code: Variables
                    html_lines.append(f"<span style='color:{codeColors['string']};'>{token}</span>")
                case 18: # LINKS
                    name,link = token[1:len(token)-1].split("](")
                    if os.path.exists(os.path.join(base_path,"images", link)):
                        html_lines.append(f"""<img src='{os.path.join(base_path,"images", link)}' alt='oops'>\n""")
                    else:
                        if not link.startswith("https://") and not link.startswith("http://"):
                            link = "https://" + link
                        html_lines.append(f"<a href='{link}' style='color:{self.textOptions['Render']['links']};'>{name}</a>")
                case 22:
                    html_lines.append(f"<span id='{token.strip()}' style='color:{self.textOptions['Render']['heading1']}; font-size:24pt;'>{token}</span>")
                case 23:
                    html_lines.append(f"<span id='{token.strip()}' style='color:{self.textOptions['Render']['heading2']}; font-size:21pt;'>{token}</span>")
                case 24:
                    html_lines.append(f"<span id='{token.strip()}' style='color:{self.textOptions['Render']['heading3']}; font-size:18pt;'>{token}</span>")
                case 25: # Output label
                    html_lines.append(f"<span style='color:{outputColors['label']};'>{token}</span>")
                case 26:
                    html_lines.append(f"<span style='color:{outputColors['zLabel']};'>{token}</span>")
                case 27:
                    html_lines.append(f"<span style='color:{outputColors['xLabel']};'>{token}</span>")
                case 28: # Warning
                    html_lines.append(f"<span style='color:{outputColors['warning']};'>{token}</span>")
                case 29: # Positive
                    html_lines.append(f"<span style='color:{outputColors['positiveNumber']};'>{token}</span>")
                case 30: # Negative
                    html_lines.append(f"<span style='color:{outputColors['negativeNumber']};'>{token}</span>")
                case 31: # Output Text
                    html_lines.append(f"<span style='color:{outputColors['text']};'>{token}</span>")
                case 32: # Positional Parameter
                    html_lines.append(f"<span style='color:{self.textOptions['Render']['Positional Parameter']};'>{token}</span>")
                case 33: # Positional or Keyword Parameter
                    html_lines.append(f"<span style='color:{self.textOptions['Render']['Positional or Keyword Parameter']};'>{token}</span>")
                case 34: # Keyword Parameter
                    html_lines.append(f"<span style='color:{self.textOptions['Render']['Keyword Parameter']};'>{token}</span>")
                case 35: # Var Positional Parameter
                    html_lines.append(f"<span style='color:{self.textOptions['Render']['Var Positional Parameter']};'>{token}</span>")
                case 36: # Datatype
                    html_lines.append(f"<span style='color:{self.textOptions['Render']['datatype']};'>{token}</span>")
        
        html_lines.append("</div>\n")
        html_lines.append("</body>\n")
        html_lines.append("</html>")
        # print(''.join(html_lines))
        self.setHtml("".join(html_lines))