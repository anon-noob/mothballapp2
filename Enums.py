class Style(int):
    "Styles for colorizing text"
    a = iter(range(64))
    
    # Default
    DEFAULT = next(a)

    # Mothball Code
    FAST = next(a)
    SLOW = next(a)
    STOP = next(a)
    RETURN = next(a)
    CALCS = next(a)
    SETTER = next(a)
    INPUTS = next(a)
    MODIFIER = next(a)
    NUMBERS = next(a)
    COMMENT = next(a)
    KW_ARG = next(a)
    NEST0 = next(a)
    NEST1 = next(a)
    NEST2 = next(a)
    ERROR = next(a)
    VARS = next(a)
    STRING = next(a)
    BACKSLASH = next(a)
    COMMENT_BACKSLASH = next(a)
    CUSTOM_FUNC = next(a)
    CUSTOM_FUNC_PARAMETER = next(a)
    BOOL = next(a)

    # Code Outputs
    OUTPUT_LABEL = next(a)
    OUTPUT_ZLABEL = next(a)
    OUTPUT_XLABEL = next(a)
    OUTPUT_WARNING = next(a)
    OUTPUT_POSITIVE = next(a)
    OUTPUT_NEGATIVE = next(a)
    OUTPUT_TEXT = next(a)
    OUTPUT_PLACEHOLDER = next(a)

    # Rendered text for documentation
    RENDER_HEADER1 = next(a)
    RENDER_HEADER2 = next(a)
    RENDER_HEADER3 = next(a)
    DATATYPE = next(a)
    POSITIONAL_PARAMETER = next(a)
    POSITIONAL_OR_KEYWORD_PARAMETER = next(a)
    KEYWORD_PARAMETER = next(a)
    VAR_POSITIONAL_PARAMETER = next(a)

    # Text edits and rendered texts
    LINKS = next(a)
    HEADER1 = next(a)
    HEADER2 = next(a)
    HEADER3 = next(a)

    CODE_EDIT_STYLES = (FAST,SLOW,STOP,RETURN,CALCS,SETTER,INPUTS,MODIFIER,NUMBERS,COMMENT,KW_ARG,NEST0,NEST1,NEST2,ERROR,VARS,STRING,BACKSLASH,COMMENT_BACKSLASH,CUSTOM_FUNC,CUSTOM_FUNC_PARAMETER,BOOL) 
    CODE_OUTPUT_STYLES = (OUTPUT_LABEL,OUTPUT_ZLABEL,OUTPUT_XLABEL,OUTPUT_WARNING,OUTPUT_POSITIVE,OUTPUT_NEGATIVE,OUTPUT_TEXT,OUTPUT_PLACEHOLDER)
    TEXT_RENDER_STYLES = (LINKS,RENDER_HEADER1,RENDER_HEADER2,RENDER_HEADER3,DATATYPE,POSITIONAL_PARAMETER,POSITIONAL_OR_KEYWORD_PARAMETER,KEYWORD_PARAMETER,VAR_POSITIONAL_PARAMETER)

    @classmethod
    def getCodeEditStyles(cls):
        return cls.CODE_EDIT_STYLES
    
    @classmethod
    def getCodeOutputStyles(cls):
        return cls.CODE_OUTPUT_STYLES
    
    @classmethod
    def getTextOutputStyles(cls):
        return cls.TEXT_RENDER_STYLES


class CellType(int):
    "Cell mode, can be `xz` for horizontal movement simulations, `y` for vertical, and `text` for text cells"
    XZ = 0
    Y = 1
    TEXT = 2

class TextCellState(int):
    "State of a text cell, either in `render` or `edit` mode"
    RENDER = 0
    EDIT = 1

class StringLiterals(str):
    CODE = "code"
    TEXT = "text"
    OUTPUT = "output"
    RENDER = "render"
    CODE_BACKGROUND = "code background"
    OUTPUT_BACKGROUND = "output background"
    RENDER_BLOCK_BACKGROUND = "render block background"
    RENDER_CODE_BACKGROUND = "render code background"
    RENDER_BACKGROUND = "render background"