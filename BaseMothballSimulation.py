from math import sin, cos, atan2 as arctan, sqrt, copysign, degrees as deg
from numpy import float32 as f32
from typing import Literal
import re
import inspect
from collections import Counter
from pprint import pp
import functools
from Enums import ExpressionType

class OverwriteError(Exception):
    pass

class MothballSequence(str):
    "Subclass of str, flag for a mothball sequence instead of a generic string."
    pass

class BasePlayer:
    pi = 3.14159265358979323846
    MODIFIERS = tuple()
    ALIAS_TO_MODIFIER = {}
    FUNCTIONS = {}
    ALIASES = {}
    FUNCTIONS_BY_TYPE = {}
    _can_have_modifiers=()
    _can_have_input=()
    _fortyfive_methods=()

    def __init__(self) -> None:
        self.precision = 7
        self.inertia_threshold = 0.005
        self.modifiers = 0
        self.reverse = False

        self.previously_sprinting = False
        self.previously_sneaking = False
        self.previously_in_web = False

        self.local_vars = {"px": 0.0625}
        self.local_funcs = {}

        self.output: list[tuple[ExpressionType, tuple]] = []

        self.closed_vars = {} # For declaring functions only

        self.call_stack = [] # For debugging and error messaging

    @staticmethod
    def record_to_call_stack(func):
        "Decorator which appends and pops from call stack for functions which accept a `MothballSequence`"
        @functools.wraps(func)
        def inner(*args, **kwargs):
            # args[0] == self
            args[0].call_stack.append(func.__name__)
            func(*args, **kwargs)
            args[0].call_stack.pop()
        return inner

    @staticmethod
    def isfloat(string: str):
        try: 
            float(string)
            return True
        except ValueError: 
            return False
    
    @staticmethod
    def clean_backslashes(string: str):
        "Replaces backslashes if possible. Anything with `\` followed by a char will be replaced."
        return string.replace("\,", ",").replace("\(", "(").replace("\)", ")").replace("\#", "#").replace("\{", "{").replace("\}", "}").replace("\=", "=") # i hate myself

    def safe_eval(self, expr: str, datatype: type, locals_dict: dict):
        "Evaluate and convert `expr` to `datatype`. If `datatype = str`, it returns the `expr` as normal."
        if datatype in [float, int, f32, bool]:
            if datatype == bool:
                if expr.strip().lower() == "true":
                    return True
                elif expr.strip().lower() == "false":
                    return False
                else:
                    return bool(expr)

            if "__" in expr:
                    raise RuntimeError(f"Rejected unsafe expression {expr}")
            
            result = eval(expr, {"__builtins__": {}}, locals_dict)
            converted_value = datatype(result) if result is not None else None
            return converted_value
        else: # strings
            return expr

    def add_to_output(self, expression_type: ExpressionType, label: str = '', string_or_num: str | float = '', num2: float = 0, strip_label: bool = True):
        if strip_label:
            label = label.strip()
        match expression_type:
            case ExpressionType.Z_LABEL | ExpressionType.X_LABEL | ExpressionType.GENERAL_LABEL_WITH_NUMBER:
                if num2:
                    expression_type += 1 # changes ExpressionType Flag
                    nn = string_or_num - num2
                    self.output.append((expression_type, 
                                    (BasePlayer.clean_backslashes(self.formatted(label)), ": ", self.truncate_number(num2), " - " if nn <= 0 else " + ", self.truncate_number(abs(nn)))))
                else:
                    self.output.append((expression_type, 
                                    (BasePlayer.clean_backslashes(self.formatted(label)), ": ", self.truncate_number(string_or_num))))

            case ExpressionType.TEXT:
                self.output.append((expression_type, 
                                    (self.formatted(string_or_num.strip()),)))
            case ExpressionType.WARNING:
                self.output.append((expression_type, 
                                    ("Warning", ": ", BasePlayer.clean_backslashes(self.formatted(string_or_num.strip())))))
            case ExpressionType.Z_INERTIA_HIT | ExpressionType.X_INERTIA_HIT | ExpressionType.Z_INERTIA_MISS | ExpressionType.X_INERTIA_MISS:
                a = abs(abs(string_or_num) - abs(num2))
                self.output.append((expression_type, 
                                    (BasePlayer.clean_backslashes(self.formatted(label)), ": ", self.truncate_number(string_or_num), " (", self.truncate_number(a), ")")))
            case ExpressionType.GENERAL_LABEL:
                self.output.append((expression_type, (BasePlayer.clean_backslashes(self.formatted(label)),)))
    
    def truncate_number(self, value: float):
        return f"{value:.{self.precision}f}"
    
    def formatted(self, string: str):
        "Formats string just like an f-string"
        formatted_string = ""

        item_to_eval = ""
        in_expr = False
        depth = 0

        for char in string:
            if char == "{":
                in_expr = not in_expr
                if not in_expr:
                    item_to_eval = ""
                    formatted_string += char
                else:
                    item_to_eval += char
                depth += 1

            elif char == "}":
                if depth == 0:
                    raise SyntaxError("Unmatched Brackets")

                depth -= 1
                if in_expr:
                    item_to_eval += char

                    item_to_eval = item_to_eval[1:len(item_to_eval) - 1]
                    if item_to_eval:
                        x = eval(item_to_eval, {"__builtins__": {}}, self.local_vars)
                        x = str(x)

                        formatted_string += x
                    item_to_eval = ''
                else: 
                    formatted_string += item_to_eval + char
                    item_to_eval = ''

                in_expr = not in_expr
            elif in_expr:
                item_to_eval += char
            else:
                formatted_string += char
        
        if depth != 0:
            raise SyntaxError("Unmatched Brackets")

        return formatted_string

    def move(self):
        "Implement in the subclasses"
        ...

    def get_suggestions(self, string: str):
        """
        Given `string`, return a list of suggestions from all possible mothball commands that best matches `string`.

        For example, if `wtrsprint` was inputted, a possible suggestion is `sprintwater`.
        """
        
        matches_start = []
        matches_part = [] # If string in word
        matches_char_count = {}

        for command in BasePlayer.FUNCTIONS.keys():
            # 1. Matches start
            if command.startswith(string):
                matches_start.append(command)
            elif string in command:
                matches_part.append(command)
            else:
                cmd_count = Counter(command)
                str_count = Counter(string)

                off_by = 0
                for char, count in str_count.items():
                    try:
                        if count == cmd_count[char]:
                            off_by -= 1
                        else:
                            off_by += count - cmd_count[char]
                    except KeyError: # not a character
                        off_by += 1
                off_by += abs(len(command) - len(string))
                if off_by < len(command): matches_char_count[command] = off_by

                
                
        # pp(matches_char_count)
        matches_char_count = sorted(matches_char_count, key=lambda e: matches_char_count[e])

        return matches_start + matches_part + matches_char_count
    
    def remove_comments(self, string: str):
        "Removes comments delimited by `#`"
        result = ""
        in_comment = False
        follows_slash = False

        for char in string:
            if char == "#" and not follows_slash:
                in_comment = not in_comment
                continue

            if not in_comment:
                result += char

            if char == "\\" and not follows_slash:
                follows_slash = True
                
            
            else:
                follows_slash = False
        
        return result

    def parse(self, string: str, splitters: tuple = ("\n", " ", "\r", "\t"), strict_whitespace: bool = True) -> list: 
        """
        Splits the string at any of the splitters that are outside of parenthesis. By default, it splits at any whitespace. 
        
        Returns a list of strings (or tokens), raises `SyntaxError` if parenthesis are unmatched.

        ```py
        >> tokens = Player.parse(\"walk(1) sprintjump.wa(2, 5) sprintair(10)\")
        >> tokens
        [\"walk(1)\", \"sprintjump.wa(2, 5)\", \"sprintair(10)\"]
        ```

        Comments are delimited by the `#` symbol. Anything between comments will be ignored.

        ```py
        >> tokens = Player.parse(
        \"\"\"walkjump(1) 
        # this is a comment # 
        sprintair(11) sprint 
        # and this is another comment\"\"\"
        )
        >> tokens
        [\"walkjump(1)\", \"sprintair(11)\", \"sprint\"]
        ```
        """

        result = []
        token = ""
        stack = []
        current = 0
        high = len(string)
        expecting_whitespace = False
        
        matches_next_element = lambda e: ((e == ")" and stack[-1] == "(") or (e == "]" and stack[-1] == "["))

        follows_slash = False

        # Delete comments
        string = self.remove_comments(string)

        # Regex to change '|' into 'x(0) z(0)'
        replace_bar_regex = r"(\|)"
        string = re.sub(replace_bar_regex, "x(0) z(0)", string)
        
        for char in string + splitters[0]:
            if strict_whitespace:
                if expecting_whitespace and not char.isspace():
                    if char in ")]":
                        raise SyntaxError(f"Unmatched brackets at character {current}: {string[max(0, current-5):min(high, current + 5)]}")
                    else:
                        msg = f"Space needed at character {current}"
                        if self.call_stack:
                            msg += f" (inside {', '.join(self.call_stack)})"
                        msg += f": {string[max(0, current-7):min(high, current + 7)]}"
                        raise SyntaxError(msg)
                else:
                    expecting_whitespace = False

            if char == "\\":
                follows_slash = True
                token += char
                continue

            elif (char == "(" or char == "[") and not follows_slash:
                stack.append(char)
            elif (char == ")" or char == "]") and not follows_slash:
                if not stack:
                    raise SyntaxError(f"Unmatched brackets at character {current}: {string[max(0, current-5):min(high, current + 5)]}")
                if not matches_next_element(char):
                    raise SyntaxError(f"Unmatched brackets at character {current}: {string[max(0, current-5):min(high, current + 5)]}")
                stack.pop()
                if not stack:
                    token += char
                    follows_slash = False
                    expecting_whitespace = True
                    current += 1
                    continue

            
            if char in splitters and not stack and not follows_slash:
                token = token.strip()
                result.append(token) if token else None
                token = ""

            else:
                token += char
                current += 1

            follows_slash = False
            expecting_whitespace = False
        
        if stack:
            raise SyntaxError("Unmatched open parethesis")

        # print(result)
        return result
    
    def tokenize(self, string: str, locals: dict = None) -> dict:
        """
        Tokenizes the string to a dictionary containing the function, positional arguments, and keyword arguments of appropiate types. 
        
        Returns as a dictionary in the form
        ```py
        {"function": function, "inputs": str, "args": list, "kwargs": dict}
        ```

        where `inputs` is a string which will be used as a function modifier. 

        Raises `SyntaxError` if a positional argument follows a keyword argument. \\
        Raises `TypeError` if these functions: (`stop`, `stopair`, `stopjump`, and 45 movement) recieves an input.
        Raises any other error encountered while converting datatypes.
        """

        # tokenize_regex = r'(\W)?([^.\(\-)]+)(?:\.([^\(\.]+))?(?:\[(.*)\])?(?:\((.*)\))?(.+)?'
                         # r'(\W)?([^.\(\-)]+)(?:\.([^\(\.]+))?             (?:\((.*)\))?(.+)?'
        e1 = r"(\W)?"
        func = r"([^.\[\(\-\)\]]+)"
        inputs = r"(?:\.([wasdWASD]+))?"
        modifiers = r"(?:\[(.*)\])?"
        args = r"(?:\((.*)\))?"
        e2 = r"(.+)?"

        tokenize_regex = e1 + func + inputs + modifiers + args + e2 
        error1, func_name, inputs, modifiers, args, error2 = re.findall(tokenize_regex, string, flags=re.DOTALL)[0]

        if error1 and error1 != "-":
            
            raise SyntaxError(f"Unknown item {error1} in {string}")
        elif error2:
            raise SyntaxError(f"Unknown item {error2} in {string}")
        
        if string[0] == "-":
            self.reverse = True
        else:
            self.reverse = False


        func = self.FUNCTIONS.get(func_name)
        if func is None:
            func = self.local_funcs.get(func_name) # CHANGES
            if func is None:
                error_msg = f"{func_name} is not a valid function. "
                suggestions = self.get_suggestions(func_name)
                
                if suggestions:
                    suggestions = suggestions[0:min(4, len(suggestions))]
                    error_msg += f"Did you mean {', '.join(suggestions)}?"

                raise NameError(error_msg)

        
        positional_args = []
        keyword_args = {}

        # TEST TEST TEST!!!!!! -> removes "None" from the args
        args = self.parse(args, splitters=",", strict_whitespace=False)
        # args = [x for x in self.parse(args, splitters=",") if x not in [None, "None"]]
        
        
        keyword_regex = r"^\s*?(\w+)\s*=\s*(.+)\s*$"
        after_keyword = False

        for arg in args:
            result = re.findall(keyword_regex, arg, flags=re.DOTALL)

            if result: # keyword
                key,value = result[0]
                if key in keyword_args:
                    raise SyntaxError(f"Repeated keyword argument {key}")

                keyword_args[key.strip()] = value.strip()
                after_keyword = True
            else: # positional
                if after_keyword:
                    raise SyntaxError("Positional argument cannot follow keyword arguments")
                
                positional_args.append(arg)
        
        positional_args, keyword_args = self.check_types(func, positional_args, keyword_args, locals=locals)
        if modifiers:
            modifiers = self.validate_modifiers(modifiers.split(","))
        else:
            modifiers = 0

        if self._can_have_input and func.__name__ not in self._can_have_input:
            if inputs:
                raise TypeError(f"{func.__name__}() cannot be modified by an input")
            if self._fortyfive_methods and func.__name__ in self._fortyfive_methods:
                inputs = "w"

        elif not inputs:
            inputs = "w"
        elif inputs not in ["w","wa","wd", "s", "sa", "sd", "a", "d"]:
            raise ValueError(f"function {func_name} received bad input '{inputs}', it can only be w, s, a, d, wa, wd, sa, wd.")

        if func.__name__ not in self._can_have_modifiers and modifiers:
            raise TypeError(f"{func.__name__}() cannot be modified by a modifier")
        
        return {"function": func, "inputs": inputs, "modifiers": modifiers, "args": positional_args, "kwargs": keyword_args}
    
    def validate_modifiers(self, modifiers: list):
        m = 0
        for i, modify in enumerate(modifiers):
            a = self.ALIAS_TO_MODIFIER[modify.strip()]
            m = m | a
            if a not in self.MODIFIERS:
                raise TypeError(f"No such modifier '{a}'")
        return m


    def check_types(self, func, args: list, kwargs: dict, locals = None):
        """
        Type checks each argument in `args` and `kwargs` according to the  annotations in `func`. If successful, returns a list of positional args and a dict of keyword args.

        Raises any appropiate error encountered while converting strings to the necessary datatypes.
        """
        if locals is None:
            locals = self.local_vars

        converted_args = []
        converted_kwargs = {}

        signature = inspect.signature(func).parameters.values()

        positional_only = {x.name:x.annotation for x in signature if x.kind == inspect.Parameter.POSITIONAL_ONLY and x.name != "self"}
        positional_or_keyword = {x.name:x.annotation for x in signature if x.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and x.name != "self"}
        keyword_only = {x.name:x.annotation for x in signature if x.kind == inspect.Parameter.KEYWORD_ONLY}
        var_positional = {x.name:x.annotation for x in signature if x.kind == inspect.Parameter.VAR_POSITIONAL}

        # Watch out for potential errors
        required_positionals = {x.name:x.annotation for x in signature if x.kind == inspect.Parameter.POSITIONAL_ONLY and x.default == inspect.Parameter.empty and x.name != "self"}

        # Idea: First check the positional arguments using positional_only and positional_or_keyword. 
        # Once positional_only runs out, start using positional_or_keyword.
        # Once both runs out, use var_positional
        # Raise error if there's too many positional arguments (var_positional is empty)

        ### Check the positional arguments ###
        can_be_positional = positional_only | positional_or_keyword

        if len(required_positionals) > len(args):
            number_of_missing = len(required_positionals) - len(args)
            raise TypeError(f"{func.__name__} missing {number_of_missing} positional-only argument{'s' if number_of_missing > 1 else ''}: {', '.join(list(required_positionals)[len(args):])}")

        for i in range(min(len(args), len(can_be_positional))):

            datatype = list(can_be_positional.values())[i]
            if datatype == inspect.Parameter.empty:
                datatype = str

            converted_value = self.safe_eval(args[i], datatype, locals)

            if list(can_be_positional)[i] == "duration" and func.__name__ not in self.local_funcs:
                if converted_value is not None and converted_value < 0:
                    raise ValueError(f"Positional argument 'duration' should be a non-negative integer")
                elif converted_value is None:
                    converted_value = 1
            elif list(can_be_positional)[i] == "label":
                if converted_value is None:
                    converted_value = func.__name__


            converted_args.append(converted_value)
        
        if len(args) < len(can_be_positional):
            a = len(args) - len(can_be_positional)
            can_be_positional = {x:can_be_positional[x] for x in list(can_be_positional)[a:]}
        
        elif var_positional and len(args) > len(can_be_positional):
            for j in args[len(can_be_positional):]:
                c = self.safe_eval(j, list(var_positional.values())[0], locals)
                converted_args.append(c)
        
        elif not var_positional and len(args) > len(can_be_positional):
            raise TypeError(f"{func.__name__} accepts at most {len(can_be_positional)} positional arguments, got {len(args)} instead")
        
        can_be_keyword = can_be_positional | keyword_only

        ### Check the keyword args ###
        for kw, value in kwargs.items():
            datatype = can_be_keyword.get(kw)

            if datatype is None:
                raise TypeError(f"{func.__name__} has no keyword argument '{kw}'")
            
            elif datatype in [int, float, f32]:
                converted_kwargs[kw] = self.safe_eval(value, datatype, locals)
            else:

                converted_kwargs[kw] = datatype(value)
                
        
        return converted_args, converted_kwargs
        
    def run(self, token):
        """
        Runs the token.

        `token` is a dictionary in the form
        ```py
        {"function": function, "inputs": str, "args": list, "kwargs": dict}
        ```
        
        where `inputs` is a string which will be used as a function modifier.
        """

        func = token["function"]
        self.inputs = token["inputs"]
        self.modifiers = token["modifiers"]
        args = token["args"]
        kwargs = token["kwargs"]

        func(self, *args, **kwargs)
    
    def simulate(self, sequence: str, return_defaults = True, locals: dict = None):

        parsed_tokens = self.parse(sequence)


        for token in parsed_tokens:
            runnable = self.tokenize(token, locals=locals)
            self.run(runnable)

        
        if return_defaults and not self.output:
            self.show_default_output()
            
    def show_default_output(self): ...

    def show_output(self):
        s = ""
        for tup in self.output:
            ss = "".join(tup[1])
            print(ss)
            s += ss + "\n"
        return s