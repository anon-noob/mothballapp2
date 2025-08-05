"""
Contains classes `CodeLinter` and `TextLinter`, which are for highlighting the user input. \\
See `RenderViewer` in the `BaseCell` module for highlighting the outputs of code or markdown text.
"""

import re
import mothball_simulation_xz as mxz
import mothball_simulation_y as my
from utils import *
import string
from typing import Literal
from Enums import *

class CodeLinter:
    """
    Manages linting mothball syntax and mothball simulation outputs.
    """

    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict, mode: CellType):
        self.mode = mode # xz or y
        self.options = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
        self.words = []
        self.word_to_index = {}
        self.text = ""
        self.bracket_colors = {0:Style.NEST1, 1:Style.NEST2, 2:Style.NEST0}
        if mode == CellType.XZ:
            for i in mxz.Player.FUNCTIONS_BY_TYPE.values():
                self.words += i

            self.modifiers = ["water","wt", "lava","lv", "ladder", "ld", "block", "bl", "vine", "web"]
            self.inputs = ["w","s","a","d","wa","wd","sa","sd"]

            for e, func_list in enumerate(mxz.Player.FUNCTIONS_BY_TYPE.values(),1):
                for word in func_list:
                    self.word_to_index[word] = e
        elif mode == CellType.Y:
            for i in my.Player.FUNCTIONS_BY_TYPE.values():
                self.words += i
            self.modifiers = ["water","wt", "lava","lv", "ladder", "ld", "bl", "vine", "web"]
            self.inputs = []

            for e, func_list in enumerate(my.Player.FUNCTIONS_BY_TYPE.values(),1):
                for word in func_list:
                    self.word_to_index[word] = e
        
    def lintTexttoTokens(self, text: str) -> list[tuple[str, int]]:
        """
        Parses `text` and tokenizes. Returns a list of tuples for linting. See `self.toColorTokens()`
        """
        self.text = text.replace("\r","") # Only have newlines \n (might solve issue of position and buffer size not matching)
        tokens = self.parseText()
        return self.toColorTokens(tokens)
        
    def matchParenthesis(self, stack: list, char: str):
        """
        checks if the closing `char` bracket matches the next `stack`'s opening braket
        """
        try:
            a = stack[-1]
        except:
            return False
        parenthesis_mapping = {
            ")": "(",
            "}": "{",
            "]": "["
        }
        if parenthesis_mapping[char] == a:
            return True
        return False

    def toColorTokens(self, listOfTokens: list[str]) -> list[tuple[str, int]]:
        """
        Main function for linting. Returns a list of 2-tuples, each tuple contains the token and the style to lint.
        """
        tokens_and_style: list[tuple[str, int]] = []

        curr_line = 0
        follows_dot = False
        in_square_brackets = False
        local_parenthesis_stack = []
        local_parenthesis_stack_index = []
        in_comment = False
        last_function = ""
        depth = 0
        func_stack = FunctionStack()
        curr_func = func_stack.peek()
        in_string = False
        last_nonspace_token = ""
        last_nonspace_token_index = -1
        index = -1
        local_vars = [] + list(mxz.Player().local_vars)
        in_curly_brackets = False
        
        for token in listOfTokens:
            if token == "\n":
                curr_line += 1
            
            elif token.startswith("\\"):
                tokens_and_style.append((token, Style.BACKSLASH))
                index += 1
                if not token.isspace():
                    last_nonspace_token = token
                    last_nonspace_token_index = index
                continue

            elif in_comment:
                tokens_and_style.append((token, Style.COMMENT))
                index += 1
                if token == "#":
                    in_comment = False
                if not token.isspace():
                    last_nonspace_token = token
                    last_nonspace_token_index = index
                continue

            elif follows_dot:
                follows_dot = False
                if token in self.inputs:
                    tokens_and_style.append((token, Style.INPUTS))
                    index += 1
                    if not token.isspace():
                        last_nonspace_token = token
                        last_nonspace_token_index = index
                    continue
            
            elif in_string and token not in ",#=}" and not in_curly_brackets:
                if last_function == "var" and token not in string.punctuation.replace("_","") and curr_func.current_parameter().name == "variable_name":
                    tokens_and_style.append((token, Style.VARS))
                    local_vars.append(token)
                    index += 1
                elif token == ")":
                    index += 1
                    if self.matchParenthesis(local_parenthesis_stack, token):
                        depth -= 1
                        tokens_and_style.append((token, self.bracket_colors[depth % 3]))
                        local_parenthesis_stack.pop()
                        ind = local_parenthesis_stack_index.pop()
                        tokens_and_style[ind] = (tokens_and_style[ind][0], self.bracket_colors[depth % 3])
                        in_string = False
                        if not func_stack.is_empty():
                            func_stack.pop()
                            curr_func = None
                            last_function = ""
                            if not func_stack.is_empty():
                                curr_func = func_stack.peek()
                                last_function = curr_func.func
                    else:
                        tokens_and_style.append((token, Style.ERROR))
                elif token == "{":
                    tokens_and_style.append((token, Style.ERROR))
                    index += 1
                    depth += 1
                    local_parenthesis_stack.append(token)
                    local_parenthesis_stack_index.append(index)
                    in_curly_brackets = not in_curly_brackets
                else:
                    tokens_and_style.append((token, Style.STRING))
                    index += 1
                if not token.isspace():
                    last_nonspace_token = token
                    last_nonspace_token_index = index
                continue

            if token == "#":
                in_comment = True
                tokens_and_style.append((token, Style.COMMENT))
                index += 1

            elif in_square_brackets:
                if token in self.modifiers:
                    tokens_and_style.append((token, Style.MODIFIER))
                    index += 1
                elif token == "]":
                    in_square_brackets = False
                    depth -= 1
                    tokens_and_style.append((token, self.bracket_colors[depth % 3]))
                    index += 1
                    ind = local_parenthesis_stack_index.pop()
                    tokens_and_style[ind] = (tokens_and_style[ind][0], self.bracket_colors[depth % 3])
                    local_parenthesis_stack.pop()
                else:
                    tokens_and_style.append((token, Style.DEFAULT))
                    index += 1

            elif token == ".":
                follows_dot = True
                tokens_and_style.append((token, Style.DEFAULT))
                index += 1
            
            elif token.lower() in ('true', 'false'):
                tokens_and_style.append((token, Style.BOOL))
                index += 1

            elif token in self.words and not follows_dot: # Identify main functions (sprint, zmm, bwmm, etc.)
                tokens_and_style.append((token, self.word_to_index[token]))
                index += 1
                last_function = token
            
            elif token in local_vars:
                tokens_and_style.append((token, Style.VARS))
                index += 1

            elif token in "({[":
                tokens_and_style.append((token, Style.ERROR))
                # tokens_and_style.append((token, self.bracket_colors[depth % 3]))
                depth += 1
                index += 1
                local_parenthesis_stack.append(token)
                local_parenthesis_stack_index.append(index)
                # print(local_parenthesis_stack)
                if token == "[":
                    in_square_brackets = True
                elif token == "(":
                    if last_function:
                        func_stack.push(self.getFunction(last_function))
                        curr_func = func_stack.peek()
                        if curr_func.current_parameter() and curr_func.current_parameter_datatype() == str:
                            if curr_func.func not in ['repeat', 'bwmm', 'xbwmm', 'wall', "xwall", 'blocks',"xblocks", "taps", "possibilities", "xpossibilities", "xzpossibilities"]:
                                in_string = True
                elif token == "{":
                    in_curly_brackets = not in_curly_brackets

            elif token == ",": # NEXT PARAMETER
                in_string = False
                tokens_and_style.append((token, Style.DEFAULT))
                index += 1

                if curr_func and not curr_func.after_keyword:
                    if curr_func.current_parameter().kind == inspect.Parameter.VAR_POSITIONAL:
                        if curr_func.current_parameter().annotation == str and curr_func.func not in ["taps"]:
                            in_string = True
                    else:
                        curr_func.discard_parameter()

                        if curr_func.current_parameter() and curr_func.current_parameter_datatype() == str:
                            if curr_func.func not in ['repeat', 'bwmm', 'xbwmm', 'wall', "xwall", 'blocks',"xblocks", "taps", "possibilities", "xpossibilities", "xzpossibilities"]:
                                in_string = True
            
                elif curr_func and curr_func.after_keyword:
                    curr_func.discard_parameter(curr_func.curr_param_name)

            elif token == "=": # KEYWORD ARGUMENT
                in_string = False
                tokens_and_style.append((token, Style.DEFAULT))
                index += 1
                if curr_func:
                    curr_func.set_after_keyword()
                if curr_func and last_nonspace_token in curr_func.keyword_parameters_remaining:
                    text, style = tokens_and_style[last_nonspace_token_index]
                    tokens_and_style[last_nonspace_token_index] = (text, Style.KW_ARG)


                    curr_func.curr_param_name = last_nonspace_token
                    if curr_func.keyword_parameters_remaining[last_nonspace_token].annotation == str:
                        if curr_func.func not in ['repeat', 'bwmm', 'xbwmm', 'wall', "xwall", 'blocks',"xblocks", "taps", "possibilities", "xpossibilities", "xzpossibilities"]:
                            in_string = True
            
            elif token in ")}]":
                if self.matchParenthesis(local_parenthesis_stack, token):
                    local_parenthesis_stack.pop()
                    ind = local_parenthesis_stack_index.pop()
                    depth -= 1
                    tokens_and_style.append((token, self.bracket_colors[depth % 3]))
                    tokens_and_style[ind] = (tokens_and_style[ind][0], self.bracket_colors[depth % 3])
                    index += 1
                    if token == ")":
                        if not func_stack.is_empty():
                            func_stack.pop()
                            curr_func = None
                            last_function = ""
                            if not func_stack.is_empty():
                                curr_func = func_stack.peek()
                                last_function = curr_func.func
                    elif token == "}":
                        in_curly_brackets = not in_curly_brackets
                else:
                    tokens_and_style.append((token, Style.ERROR))
                    index += 1
            
            elif token.isnumeric():
                tokens_and_style.append((token, Style.NUMBERS))
                index += 1
            
            else:
                tokens_and_style.append((token, Style.DEFAULT))
                index += 1
            if not token.isspace():
                last_nonspace_token = token
                last_nonspace_token_index = index

        return tokens_and_style

    def getFunction(self, name: str):
        """
        Returns the Mothball function object given the function's `name` or alias.
        """
        if self.mode == CellType.XZ:
            return mxz.Player.FUNCTIONS[name]
        elif self.mode == CellType.Y:
            return my.Player.FUNCTIONS[name]

    def parseText(self):
        """
        Parse `self.text`, returns a list of parsed tokens `result`. Running `''.join(result)` returns the original string.
        """
        results = []
        item = ""
        follows_backslash = False
        for char in self.text:
            if follows_backslash:
                follows_backslash = False
                item += char
                results.append(item)
                item = ""
            elif not follows_backslash:
                if char in "(){}[]\\ .,/|-=+*#\n":
                    if item:
                        results.append(item)
                    item = ""
                    if char != "\\":
                        results.append(char)
                    elif char == "\\":
                        follows_backslash = True
                        item = char
                    continue
                item += char
        if item:
            results.append(item)
        return results

    def parseOutput(self, outputLines: list[tuple[str]], displayOutputBackground: bool = True):
        """
        Parse the output
        """
        result = []

        for i, line in enumerate(outputLines):
            string, expr_type = line
            if i + 1 < len(outputLines):
                string += "\n"
            if expr_type == "normal":
                result.append((string, Style.OUTPUT_TEXT, 0))
            else:
                result += self.separate(string, expr_type)
        
        if result and result[-1][0] == "\n":
            result.pop()
        if displayOutputBackground: # Set flag to 3
            result = [(x[0], x[1], 3) for x in result]
        return result

    def separate(self, string: str, expr_type: str):
        """
        Internal function.
        
        Separates strings in the form `label: a` or `label: a + b` into a list `[label, :, a, +, b]` 
        """
        result: list[tuple[str, str]] = []

        expr_type_to_tag_name = {
            "expr": Style.OUTPUT_LABEL,
            "x-expr": Style.OUTPUT_XLABEL,
            "z-expr": Style.OUTPUT_ZLABEL,
            "warning": Style.OUTPUT_WARNING
        }

        a, b = string.split(": ")
        tag_name = expr_type_to_tag_name.get(expr_type)
        if tag_name is None:
            return [(string, Style.OUTPUT_TEXT, 0)]
        result.append((a, tag_name, 0))
        result.append((": ", Style.DEFAULT, 0))

        if expr_type == "warning":
            result.append((b, Style.OUTPUT_TEXT, 0))
            return result
        
        b = b.split(" ")
         
        # Either 1 or 3 items
        b_float = float(b[0])
        if b_float >= 0: # positive number
            result.append((b[0], Style.OUTPUT_POSITIVE, 0))
        else: # Negative number
            result.append(('-', Style.DEFAULT, 0))
            result.append((b[0][1:], Style.OUTPUT_NEGATIVE, 0))

        if len(b) == 3:
            sign = b[1]
            number = b[2]
            result.append((f" {sign} ", Style.DEFAULT, 0))
            result.append((number, Style.OUTPUT_POSITIVE if sign == '+' else Style.OUTPUT_NEGATIVE, 0))
        
        # result.append(("\n", self.STYLE_DEFAULT, 0))
        # print(result)
        return result

    def getFunctionSignature(self, nameOrAlias):
        func = mxz.Player.FUNCTIONS.get(nameOrAlias)
        if not func:
            return []
        func_name = func.__name__
        aliases = mxz.Player.ALIASES.get(func_name)

        params = inspect.signature(func).parameters.values()
        positional: list[inspect.Parameter] = []
        positional_or_keyword: list[inspect.Parameter] = []
        keyword: list[inspect.Parameter] = []
        var_position: list[inspect.Parameter] = []

        for i in params:
            if i.name == "self":
                continue
            if i.kind == inspect.Parameter.POSITIONAL_ONLY:
                positional.append(i)
            if i.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                positional_or_keyword.append(i)
            if i.kind == inspect.Parameter.KEYWORD_ONLY:
                keyword.append(i)
            if i.kind == inspect.Parameter.VAR_POSITIONAL:
                var_position.append(i)
        
        result = []
        if aliases:
            result.append(("Aliases: ", Style.DEFAULT))
            for alias in aliases:
                result.append((alias, self.word_to_index[func_name]))
                result.append((", ", Style.DEFAULT))
            if result and result[-1][0] == ", ": result.pop()
            result.append(("\n", Style.DEFAULT))

        if func_name in self.words: # Identify main functions (sprint, zmm, bwmm, etc.)
            result.append((func_name, self.word_to_index[func_name]))
        result.append(("(", self.bracket_colors[0]))

        def appendTokens(lst_of_params, style):
            result = []
            for i in lst_of_params:
                if style == Style.VAR_POSITIONAL_PARAMETER:
                    result.append(("*", Style.DEFAULT))
                result.append((i.name, style))
                c = i.annotation.__name__
                if "float" in c:
                    c = "float"
                result.append((": ", Style.DEFAULT))
                result.append((c, Style.DATATYPE))
                if isinstance(i.default, (int,float)):
                    result.append((" = ", Style.DEFAULT))
                    result.append((str(i.default), Style.NUMBERS))
                elif isinstance(i.default, str):
                    result.append((" = ", Style.DEFAULT))
                    result.append((i.default, Style.STRING))
                elif i.default is None:
                    result.append((" = ", Style.DEFAULT))
                    result.append(("None", Style.DATATYPE))
                result.append((", ", Style.DEFAULT))
            return result

        result.extend(appendTokens(positional, Style.POSITIONAL_PARAMETER))
        if positional:
            result.append(("/, ", Style.DEFAULT))
        result.extend(appendTokens(positional_or_keyword, Style.POSITIONAL_OR_KEYWORD_PARAMETER))
        result.extend(appendTokens(var_position, Style.VAR_POSITIONAL_PARAMETER))
        if keyword and not var_position:
            result.append(("*, ", Style.DEFAULT))
        result.extend(appendTokens(keyword, Style.KEYWORD_PARAMETER))
        

        if result:
            if result[-1][0] == ", ": 
                result.pop()
            elif result[-1][0] == "/, ": 
                result.pop()
                result.append(("/", Style.DEFAULT))
        result.append((")", self.bracket_colors[0]))

        return result
    

class MDLinter:
    """
    Manages linting markdown (not including inline code and block quotes)
    """

    def __init__(self, generalOptions: dict, colorOptions: dict, textOptions: dict):
        self.raw_text = ""
        self.options = generalOptions
        self.colorOptions = colorOptions
        self.textOptions = textOptions
    
    def detectAttachments(self, text: str):
        """
        Detect if `text` has a link or not
        """
        # Define the regex pattern to match [text](link)
        pattern = r'(\[.*?\]\(.*?\))'
        result = []

        # Split the text based on the pattern
        parts = re.split(pattern, text)
        for part in parts:
            if part:
                if part.startswith("[") and part.endswith(")"):
                    result.append((part, Style.LINKS, 0))
                else:
                    result.append((part, Style.DEFAULT, 0))

        # Remove empty strings and return the result
        return result
    
    def lineParse(self, text: str):
        """
        Parse a single line `text`, handles inline code.
        """
        tokens = []

        # Parse: The idea is "words, `code`, and `mistaeks" -> ["words, ", 'code', ", and ", 'mistaeks']
        a = text.split("`")
        # print(a)
        maximum = len(a)
        for i, word in enumerate(a):
            if i % 2:
                if i + 1 < maximum:
                    tokens += [(x[0], x[1], 2) for x in CodeLinter(self.options, self.colorOptions, self.textOptions, CellType.XZ).lintTexttoTokens(word)]
                else:
                    tokens.append(("`", Style.DEFAULT, 0))
                    tokens += self.detectAttachments(word)
                    # tokens.append((word, self.STYLE_DEFAULT, 0))
            else:
                tokens += self.detectAttachments(word)
                # tokens.append((word, self.STYLE_DEFAULT, 0))
        return tokens
    
    def parseTextToRender(self, text: str):
        """
        Parses `text`. Returns a list of 3-tuples, each tuple contains the text, style, and an integer `0,1,2`.

        - `0` means normal text
        - `1` means code block 
        - `2` means inline code 
        """
        self.raw_text = text
        tokens = []
        code_block = False
        show_code_output = False
        show_func_sig = False
        code = ""
        for line in self.raw_text.split("\n"):
            if not code_block:
                if line.startswith("# "): # Heading 1
                    tokens.append((line[2:] + "\n", Style.RENDER_HEADER1, 0))
                elif line.startswith("## "):
                    tokens.append((line[3:] + "\n", Style.RENDER_HEADER2, 0))
                elif line.startswith("### "):
                    tokens.append((line[4:] + "\n", Style.RENDER_HEADER3, 0))
                elif line.startswith("```"):
                    code_block = True
                    args = line[3:].strip().split("/")
                    if args and args[0]=="mothball":
                        if len(args) == 2 and args[1]=="output":
                            show_code_output = True
                        elif len(args) == 2 and args[1]=="signature":
                            show_func_sig = True
                            # TODO (not implemented yet)
                else:
                    tokens += self.lineParse(line + "\n")
            elif code_block:
                if line.startswith("```"):
                    if show_func_sig:
                        a = CodeLinter(self.options, self.colorOptions, self.textOptions, CellType.XZ)
                        bb = [(x[0], x[1], 1) for x in a.getFunctionSignature(code[0:len(code)-1])]
                        tokens += bb

                    else: # Normal code
                        a = CodeLinter(self.options, self.colorOptions, self.textOptions, CellType.XZ)
                        bb = [(x[0], x[1], 1) for x in a.lintTexttoTokens(code[0:len(code)-1])]
                        tokens += bb
                        # print(tokens)
                        
                        if show_code_output:
                            p=mxz.Player()
                            try:
                                p.simulate(code)
                            except Exception as e:
                                p.output = [(f"Error: {e}", "normal")]
                            # print(code)
                            # print("ADDING", p.output)
                            tokens += a.parseOutput(p.output, True)

                    code = ""
                    code_block = False
                    show_code_output = False
                    show_func_sig = False
                else:
                    code += line + "\n"
        # print(tokens)
        return tokens
    
    def parseTextToHighlight(self, text: str):
        """
        Parses `text`. Returns a list of 2-tuples, each tuple contains the text and the linting style.
        """
        self.raw_text = text
        tokens = []
        for line in self.raw_text.split("\n"):
            if line.startswith("# "): # Heading 1
                tokens.append((line + "\n", Style.HEADER1))
            elif line.startswith("## "):
                tokens.append((line + "\n", Style.HEADER2))
            elif line.startswith("### "):
                tokens.append((line + "\n", Style.HEADER3))
            else:
                tokens.append((line + "\n", Style.DEFAULT))
        return tokens