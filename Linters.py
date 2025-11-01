"""
Contains classes `CodeLinter` and `TextLinter`, which are for highlighting the user input. \\
See `RenderViewer` in the `BaseCell` module for highlighting the outputs of code or markdown text.
"""

import re
import MothballSimulationXZ as mxz
import MothballSimulationY as my
from utils import *
import string
from Enums import *

# PLEASE FIX OUTPUT RENDERING CRASH

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
            for i in mxz.PlayerSimulationXZ.FUNCTIONS_BY_TYPE.values():
                self.words += i

            self.modifiers = ["water","wt", "lava","lv", "ladder", "ld", "block", "bl", "vine", "web",'soulsand','ss']
            self.inputs = ["w","s","a","d","wa","wd","sa","sd"]

            for e, func_list in enumerate(mxz.PlayerSimulationXZ.FUNCTIONS_BY_TYPE.values(),1):
                for word in func_list:
                    self.word_to_index[word] = e
        elif mode == CellType.Y:
            for i in my.PlayerSimulationY.FUNCTIONS_BY_TYPE.values():
                self.words += i
            self.modifiers = ["water","wt", "lava","lv", "ladder", "ld", "vine", "web"]
            self.inputs = []

            for e, func_list in enumerate(my.PlayerSimulationY.FUNCTIONS_BY_TYPE.values(),1):
                for word in func_list:
                    self.word_to_index[word] = e
        else:
            self.inputs = []
            self.modifiers = []
        
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
        local_vars = [] + list(mxz.PlayerSimulationXZ().local_vars)
        custom_funcs = []
        custom_funcs_vars = []

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
            
            elif in_string and token not in "(,#=}" and not in_curly_brackets:
                if last_function == "var" and token not in string.punctuation.replace("_","") and curr_func.current_parameter().name == "variable_name":
                    tokens_and_style.append((token, Style.VARS))
                    local_vars.append(token)
                    index += 1
                elif (last_function == "function" or last_function == "func") and token not in string.punctuation.replace("_",""):
                    if curr_func.current_parameter().name == "name":
                        tokens_and_style.append((token, Style.CUSTOM_FUNC))
                        custom_funcs.append(token)
                    elif curr_func.current_parameter().name == "args":
                        tokens_and_style.append((token, Style.CUSTOM_FUNC_PARAMETER))
                        custom_funcs_vars[-1].append(token)
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
                            if last_function == "func" or last_function == "function":
                                custom_funcs_vars.pop()
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
            
            elif token in custom_funcs:
                tokens_and_style.append((token, Style.CUSTOM_FUNC))
                index += 1

            elif custom_funcs_vars and token in custom_funcs_vars[-1]:
                tokens_and_style.append((token, Style.CUSTOM_FUNC_PARAMETER))
                index += 1

            elif token in local_vars:
                tokens_and_style.append((token, Style.VARS))
                index += 1

            elif token in "({[":
                tokens_and_style.append((token, Style.ERROR))
                depth += 1
                index += 1
                local_parenthesis_stack.append(token)
                local_parenthesis_stack_index.append(index)
                if token == "[":
                    in_square_brackets = True
                elif token == "(":
                    if last_function:
                        func_stack.push(self.getFunction(last_function))
                        curr_func = func_stack.peek()
                        if curr_func.current_parameter() and curr_func.current_parameter_datatype() == str: 
                            in_string = True
                        if last_function == "func" or last_function == "function":
                            custom_funcs_vars.append([])
                elif token == "{":
                    in_curly_brackets = not in_curly_brackets

            elif token == ",": # NEXT PARAMETER
                in_string = False
                tokens_and_style.append((token, Style.DEFAULT))
                index += 1

                if curr_func and not curr_func.after_keyword:
                    if curr_func.current_parameter() and curr_func.current_parameter().kind == inspect.Parameter.VAR_POSITIONAL:
                        if curr_func.current_parameter().annotation == str and curr_func.func not in ["taps"]:
                            in_string = True
                    else:
                        curr_func.discard_parameter()

                        if curr_func.current_parameter() and curr_func.current_parameter_datatype() == str:
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
                            
                            if last_function == "func" or last_function == "function":
                                custom_funcs_vars.pop()
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

        # print(tokens_and_style)
        return tokens_and_style

    def getFunction(self, name: str):
        """
        Returns the Mothball function object given the function's `name` or alias.
        """
        if self.mode == CellType.XZ:
            return mxz.PlayerSimulationXZ.FUNCTIONS[name]
        elif self.mode == CellType.Y:
            return my.PlayerSimulationY.FUNCTIONS[name]

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
                if char in "(){}[]\\ .,/|-=+*#\n\t":
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
        MAP = {ExpressionType.X_LABEL: Style.OUTPUT_XLABEL,
         ExpressionType.X_LABEL_WITH_EXPRESSION: Style.OUTPUT_XLABEL,
         ExpressionType.Z_LABEL: Style.OUTPUT_ZLABEL,
         ExpressionType.Z_LABEL_WITH_EXPRESSION: Style.OUTPUT_ZLABEL,
         ExpressionType.X_INERTIA_HIT: Style.OUTPUT_XLABEL,
         ExpressionType.X_INERTIA_MISS: Style.OUTPUT_XLABEL,
         ExpressionType.Z_INERTIA_HIT: Style.OUTPUT_ZLABEL,
         ExpressionType.Z_INERTIA_MISS: Style.OUTPUT_ZLABEL,
         ExpressionType.TEXT: Style.OUTPUT_TEXT,
         ExpressionType.GENERAL_LABEL_WITH_NUMBER: Style.OUTPUT_LABEL,
         ExpressionType.GENERAL_LABEL_WITH_EXPRESSION: Style.OUTPUT_LABEL,
         ExpressionType.GENERAL_LABEL: Style.OUTPUT_LABEL,
         ExpressionType.WARNING: Style.OUTPUT_WARNING}

        result = []

        # print(outputLines)

        for i, line in enumerate(outputLines):
            expr_type, tokens = line
            
            match expr_type:
                case ExpressionType.X_LABEL | ExpressionType.Z_LABEL | ExpressionType.GENERAL_LABEL_WITH_NUMBER: # outx: 1.23 --> [outx, : , 1.23]
                    result.append((tokens[0], MAP[expr_type], 0))
                    result.append((tokens[1], Style.DEFAULT, 0))
                    if tokens[2][0] == "-":
                        result.append((tokens[2][0], Style.DEFAULT, 0))
                        result.append((tokens[2][1:], Style.OUTPUT_NEGATIVE, 0))
                    else:
                        result.append((tokens[2], Style.OUTPUT_POSITIVE, 0))

                case ExpressionType.X_LABEL_WITH_EXPRESSION | ExpressionType.Z_LABEL_WITH_EXPRESSION | ExpressionType.GENERAL_LABEL_WITH_EXPRESSION: # outx: 1.27 - 0.04 --> [outx, : , 1.27,  - , 0.04]
                    result.append((tokens[0], MAP[expr_type], 0))
                    result.append((tokens[1], Style.DEFAULT, 0))
                    if tokens[2][0] == "-":
                        result.append((tokens[2][0], Style.DEFAULT, 0))
                        result.append((tokens[2][1:], Style.OUTPUT_NEGATIVE, 0))
                    else:
                        result.append((tokens[2], Style.OUTPUT_POSITIVE, 0))
                    negative = "-" in tokens[3]
                    result.append((tokens[3], Style.DEFAULT, 0))
                    if negative:
                        result.append((tokens[4], Style.OUTPUT_NEGATIVE, 0))
                    else:
                        result.append((tokens[4], Style.OUTPUT_POSITIVE, 0))
                
                case ExpressionType.TEXT | ExpressionType.GENERAL_LABEL: # DANGER, add as tuple!!!
                    result.append((tokens[0], MAP[expr_type], 0))
                
                case ExpressionType.WARNING:
                    result.append((tokens[0], MAP[expr_type], 0))
                    result.append((tokens[1], Style.DEFAULT, 0))
                    result.append((tokens[2], Style.OUTPUT_TEXT, 0))
                
                case ExpressionType.X_INERTIA_HIT | ExpressionType.Z_INERTIA_HIT:
                    result.append((tokens[0], MAP[expr_type], 0))
                    result.append((tokens[1], Style.DEFAULT, 0))
                    if tokens[2][0] == "-":
                        result.append((tokens[2][0], Style.DEFAULT, 0))
                        result.append((tokens[2][1:], Style.OUTPUT_NEGATIVE, 0))
                    else:
                        result.append((tokens[2], Style.OUTPUT_POSITIVE, 0))
                    result.append((tokens[3], Style.DEFAULT, 0))
                    result.append((tokens[4], Style.OUTPUT_POSITIVE, 0))
                    result.append((tokens[5], Style.DEFAULT, 0))
                case ExpressionType.X_INERTIA_MISS | ExpressionType.Z_INERTIA_MISS:
                    result.append((tokens[0], MAP[expr_type], 0))
                    result.append((tokens[1], Style.DEFAULT, 0))
                    if tokens[2][0] == "-":
                        result.append((tokens[2][0], Style.DEFAULT, 0))
                        result.append((tokens[2][1:], Style.OUTPUT_NEGATIVE, 0))
                    else:
                        result.append((tokens[2], Style.OUTPUT_POSITIVE, 0))
                    result.append((tokens[3], Style.DEFAULT, 0))
                    result.append((tokens[4], Style.OUTPUT_NEGATIVE, 0))
                    result.append((tokens[5], Style.DEFAULT, 0))

            result.append(("\n",Style.DEFAULT,0))


        if result and result[-1][0] == "\n":
            result.pop()

        return result

    def getFunctionSignature(self, nameOrAlias):
        func = mxz.PlayerSimulationXZ.FUNCTIONS.get(nameOrAlias)
        if not func:
            return []
        func_name = func.__name__
        aliases = mxz.PlayerSimulationXZ.ALIASES.get(func_name)

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
                    code = code.strip()
                    if show_func_sig:
                        a = CodeLinter(self.options, self.colorOptions, self.textOptions, CellType.XZ)
                        bb = [(x[0], x[1], 1) for x in a.getFunctionSignature(code)]
                        # print("1", bb)
                        tokens += bb

                    elif show_code_output:
                        bb = [(x[0], x[1], 3) for x in self.parseTextToOutput(code)]
                        # print("2", bb)
                        tokens += bb
                        pass

                    else: # normal code
                        a = CodeLinter(self.options, self.colorOptions, self.textOptions, CellType.XZ)
                        bb = [(x[0], x[1], 1) for x in a.lintTexttoTokens(code)]
                        # print("3", bb)
                        tokens += bb

                    code = ""
                    code_block = False
                    show_code_output = False
                    show_func_sig = False
                else:
                    code += line + "\n"
        # print(tokens)
        return tokens
    
    def parseTextToOutput(self, text: str):
        MAP = {"x": ExpressionType.X_LABEL,
         "xe": ExpressionType.X_LABEL_WITH_EXPRESSION,
         "z": ExpressionType.Z_LABEL,
         "ze": ExpressionType.Z_LABEL_WITH_EXPRESSION,
         "xih": ExpressionType.X_INERTIA_HIT,
         "xim": ExpressionType.X_INERTIA_MISS,
         "zih": ExpressionType.Z_INERTIA_HIT,
         "zim": ExpressionType.Z_INERTIA_MISS,
         "t": ExpressionType.TEXT,
         "gn": ExpressionType.GENERAL_LABEL_WITH_NUMBER,
         "ge": ExpressionType.GENERAL_LABEL_WITH_EXPRESSION,
         "g": ExpressionType.GENERAL_LABEL,
         "w": ExpressionType.WARNING}
        
        item = ""
        components = []
        style = []
        outputLines = text.split("//\n")
        # print(outputLines)
        for i in outputLines:
            l = i.split("|")
            # print(l)
            if l and not l[0]:
                continue

            try:
                expr_type, expr_text = l
                expr_type = MAP[expr_type.strip()]
            except ValueError as e:
                raise ValueError(f"Error at {i}: {e}")
            
            components.append((expr_type, expr_text.split("/")))

        # print(components)
        return CodeLinter(self.options, self.colorOptions, self.textOptions, CellType.XZ).parseOutput(components)
    
    def parseTextToHighlight(self, text: str):
        """
        Parses `text`. Returns a list of 2-tuples, each tuple contains the text and the linting style.
        """
        # THIS MIGHT BE THE ISSUE TO THE LINUX PROBLEM
        self.raw_text = text
        # tokens = []
        
        # # (NEW CODE ATTEMPT) First parse
        # results = []

        # item = ""
        # for char in text:
        #     if char == "\n":
        #         if item:
        #             results.append(item)
        #             results.append(char)
        #         item = ""
        #         continue
        #     item += char
        # if item:
        #     results.append(item)
        
        # tokens = []
        # for i in results:
        #     if i.startswith("# "):
        #         tokens.append((i, Style.HEADER1))
        #     else:
        #         tokens.append((i, Style.DEFAULT))
        return [(text, Style.DEFAULT)]
        # return tokens
        
        
        
        
        
        
        
        # m = self.raw_text.split("\n")
        # print(m, "\n".join(m) == self.raw_text)
        # for line in m:
            # if line.startswith("# "): # Heading 1
            #     tokens.append((line + "\n", Style.HEADER1))
            # elif line.startswith("## "):
            #     tokens.append((line + "\n", Style.HEADER2))
            # elif line.startswith("### "):
            #     tokens.append((line + "\n", Style.HEADER3))
            # else:
            # tokens.append((line + "\n", Style.DEFAULT))
        # return tokens

# a = MDLinter({},{},{})
# print(a.parseTextToHighlight("""Hello and welcome!
# to my greatest
# achievement"""))