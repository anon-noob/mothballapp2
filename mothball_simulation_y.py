from numpy import float32 as f32
from typing import Literal
import re
import inspect
from collections import Counter

class MothballSequence(str):
    "Subclass of str, flag for a mothball sequence instead of a generic string."
    pass

class Player:

    JUMP = 0
    GROUND = 1
    AIR = 2
    SLIME = 3

    WATER =  0b1
    LAVA =   0b10
    WEB =    0b100
    LADDER = 0b1000

    ALIAS_TO_MODIFIER = {"water": WATER,"wt": WATER,"lv": LAVA,"lava": LAVA,"web": WEB,"ladder": LADDER,"ld": LADDER,"vine": LADDER}
    
    _can_have_modifiers = ["up", "down", "jump", "air"]

    MODIFIERS = [WATER, LAVA, WEB, LADDER]

    FUNCTIONS_BY_TYPE = {
        "fast-movers": ["jump", "j", "air", "a", "slime"],
        "slow-movers": ["up", "down"],
        "setters": ["sety", "y", "setvy", "vy", "inertia","setceiling", "ceil"],
        "calculators": ["repeat", "r", "poss", "print", "inertialistener", "il"],
        "returners": ["ty", "sty", "outy", "outvy", "help"]
    }

    def __init__(self) -> None:
        self.y = 0.0
        self.vy = 0.0

        self.precision = 7

        self.inertia_threshold = 0.005

        self.previously_in_web = False

        self.state = self.GROUND

        self.modifiers = 0

        self.record = {}
        
        self.local_vars = {"px": 0.0625}
        self.local_funcs = {}

        self.output: list[tuple[str | Literal['normal', 'z-expr', 'x-expr', 'expr']]] = []

        self.closed_vars = {} # For declaring functions only

        self.ceiling = None
        self.hit_ceiling = False

    @staticmethod
    def clean_backslashes(string: str):
        "Replaces backslashes if possible. Anything with `\` followed by a char will be replaced."
        return string.replace("\,", ",").replace("\(", "(").replace("\)", ")").replace("\#", "#").replace("\{", "{").replace("\}", "}").replace("\=", "=") # i hate myself

    def safe_eval(self, expr: str, datatype: type, locals_dict: dict):
        "Evaluate and convert `expr` to `datatype`. If `datatype = str`, it returns the `expr` as normal."
        if datatype in [float, int, f32]:
            if "__" in expr:
                    raise RuntimeError(f"Rejected unsafe expression {expr}")
            
            result = eval(expr, {"__builtins__": {}}, locals_dict)
            converted_value = datatype(result) if result is not None else None
            return converted_value
        else:
            return expr

    def add_output(self, string: str):
        """
        Appends to the `Player` object's `output` attribute, used for displaying results as normal
        """
        string = Player.clean_backslashes(self.formatted(str(string)))
        self.output.append((string, "normal"))


    def add_output_with_label(self, label: str, string: str = '', expr_type: str = 'z-expr'):
        """
        Appends to the `Player` object's `output` attribute, used for displaying results in the form `label: string`

        All strings can be formatted by putting variable names inside curly brackets `{}`

        `expr_type` is either `z-expr`, `x-expr`, or just `expr`
        """
        label = Player.clean_backslashes(self.formatted(label))
        string = Player.clean_backslashes(self.formatted(str(string)))
        self.output.append((f"{label}: {string}", expr_type))
    
    def format_number(self, value: float, centered_about: float = 0, return_as_string = False):
        """
        Returns `value` as a number or an expression as a string. Automatically rounds the decimals according to the `Player` object's `precision` attribute.
        
        If `centered_about = 0`, return `value` as a string. \\
        Otherwise, return a mathematical expression as a string such that the expression evaluates to `value` by adding or subtracting from `centered_about`. Note that `centered_about` will not be rounded.

        ```py
        >> p = Player()
        >> p.format_number(3.1415926)
        "3.1415926"
        >> p.precision = 3 # now all numbers will round to 3 decimal places
        >> p.format_number(3.1415926)
        "3.142"
        >> p.format_number(3.1415926, 2.71828)
        "2.71828 + 0.423"
        >> p.format_number(1.616, 2.71828)
        "2.71828 - 1.102"
        ```
        """
        if centered_about:
            return f"{centered_about} {'-' if centered_about - value > 0 else '+'} {f'{abs(value - centered_about):.{self.precision}f}'}"

        else:
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
                    # print(f"{item_to_eval = }")
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
    
    def move(self, duration, jump_boost = 0, up = False, down = False, state = "GROUND"):
        
        for _ in range(duration):
            
            self.y += self.vy # (Pre order)
            if self.hit_ceiling:
                self.vy = 0
                self.y = self.ceiling - 1.8
                self.hit_ceiling = False

            # idk
            if self.previously_in_web:
                self.vy = 0

            if state == self.JUMP:
                self.vy = 0.42 + 0.1 * jump_boost
                # self.y = 0.0

            elif self.modifiers & self.WATER:
                a = self.vy * 0.8 - 0.02
                if abs(a) < self.inertia_threshold:
                    a = 0
                if up:
                    self.vy = a + 0.04 # Going up
                if down:
                    self.vy = a # Going down
            
            elif self.modifiers & self.LAVA:
                a = self.vy * 0.5 - 0.02
                if abs(a) < self.inertia_threshold:
                    a = 0
                if up:
                    self.vy = a + 0.04 # Going up
                if down:
                    self.vy = a # Going down
            
            else:
                if state == self.SLIME:
                    self.vy = -self.vy
                self.vy = (self.vy - 0.08) * 0.98
                if self.modifiers & self.LADDER:
                    if up:
                        self.vy = 0.12 * 0.98
                    elif down:
                        self.vy = max(-0.15, self.vy)
            
            # idk

            if abs(self.vy) < self.inertia_threshold and not self.modifiers & self.WATER:
                self.vy = 0

            if self.modifiers & self.WEB:
                self.vy = self.vy / 20

            self.previously_in_web = self.modifiers & self.WEB
            self.previously_in_water = self.modifiers & self.WATER
            self.previously_in_lava = self.modifiers & self.LAVA

            if self.ceiling and self.y + self.vy + 1.8 >= self.ceiling:
                self.vy = self.ceiling - self.y - 1.8
                self.hit_ceiling = True
            
            self.possibilities_helper()
            self.inertialistener_helper()
            
        
    
    def possibilities_helper(self):
        if not self.record:
            return
        
        if self.vy < 0:
            
            top_diff = self.y % 0.0625
            top = self.y - top_diff
            botdiff = (self.y + self.vy) % 0.0625
            bot = self.y + self.vy - botdiff + 0.0625

            self.add_output_with_label(f"Tick {self.record['tick']}", f"{self.format_number(self.y)} ({top} to {bot})")
        self.record['tick'] += 1
    
    def get_inertia_speed(self):
        return self.inertia_threshold / f32(0.91)
    
    def jump(self, duration: int = 1, jump_boost: int = 0):
        self.move(1, state = self.JUMP, jump_boost = jump_boost)
        self.move(duration - 1, state = self.AIR)

    def air(self, duration: int = 1):
        self.move(duration, state=self.AIR)

    def outy(self, centered_at: float = 0.0, label: str = "outy"):
        self.add_output_with_label(label, self.format_number(self.y, centered_about=centered_at), "expr")

    def outvy(self, centered_at: float = 0.0, label: str = "vy"):
        self.add_output_with_label(label, self.format_number(self.vy, centered_about=centered_at), "expr")
    
    def sety(self, e: float):
        self.y = e
    
    def inertia(self, value: float):
        self.inertia_threshold = value

    def outty(self, centered_at: float = 0, label: str = "top y"):
        self.add_output_with_label(label, self.format_number(self.y + 1.8, centered_about=centered_at), "expr")
    
    def outsty(self, centered_at: float = 0, label: str = "top y (sneak)"):
        self.add_output_with_label(label, self.format_number(self.y + 1.5, centered_about=centered_at), "expr")
    
    def slime(self, height: float = 0.0):
        self.move(1, state=self.SLIME)
        self.y = height
    
    def repeat(self, sequence: MothballSequence, count: int = 1):
        for _ in range(count):
            self.simulate(sequence, return_defaults=False, locals=self.local_vars)
    
    def printdisplay(self, string:str = ""):
        self.add_output(string)

    def setceiling(self, height: float = 0.0):
        if height == 0.0:
            self.ceiling = None
        if height < 1.5:
            raise ValueError("Ceiling height is too low") # This will change with the scale attribute later on
        self.ceiling = height

    def setvy(self, value: float, /):
        self.vy = value
    
    def up(self, duration: int = 1):
        self.move(duration, up=True)
    
    def down(self, duration: int = 1):
        self.move(duration, down=True)
    
    def possibilities(self, sequence: MothballSequence):
        if not self.record: # JUST FOR NOW
            self.record = {"tick":1}
        else:
            raise TypeError(f"Nested posibilities functions are not allowed.")
        self.simulate(sequence, return_defaults=False)
        self.record = {}

    def ballhelp(self, func: str):
        "Gets help about function `func`"
        f = Player.FUNCTIONS.get(func)
        if f is None:
            f = self.local_funcs.get(func)
            # print(self.local_funcs)
            # print(f)
            if f is None:
                raise NameError(f"Function {func} not found")
            

        f_sig = inspect.signature(f).parameters
        # print(f"Help with {func}\n-------------------")
        # print('Arguments:')
        self.add_output(f"Help with {func}:")
        self.add_output(f"  Arguments:")
        

        # print(f_sig.values())
        for y in f_sig.values(): # PLEASE ADD * and /
            # print(f"\t{y}")
            if y.name != "self":
                self.add_output(f"    {y}")
        
        self.add_output('')
        # print(f.__doc__)
        self.add_output(f.__doc__)

    FUNCTIONS = {
        "jump": jump, "j": jump,
        "outy": outy,
        "outvy": outvy,
        "sety": sety, "y": sety,
        "inertia": inertia,
        "air": air, "a": air,
        "repeat": repeat, "r": repeat,
        "print": printdisplay,
        "outty": outty, "outtopy": outty,
        "outsty": outsty, "outsneaktopy": outsty,
        "slime": slime,
        "setceiling": setceiling, "setceil": setceiling, "ceil": setceiling,
        "vy": setvy, "setvy": setvy,
        "possibilities": possibilities, "poss": possibilities,
        "ballhelp": ballhelp, "help": ballhelp,
        "up": up,
        "down": down
    }


    def get_suggestions(self, string: str):
        """
        Given `string`, return a list of suggestions from all possible mothball commands that best matches `string`.

        For example, if `wtrsprint` was inputted, a possible suggestion is `sprintwater`.
        """
        
        matches_start = []
        matches_part = [] # If string in word
        matches_char_count = {}

        for command in Player.FUNCTIONS.keys():
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

    def parse(self, string: str, splitters: tuple = ("\n", " ", "\r", "\t")) -> list: 
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
        
        matches_next_element = lambda e: ((e == ")" and stack[-1] == "(") or (e == "]" and stack[-1] == "["))

        follows_slash = False

        # Delete comments
        string = self.remove_comments(string)

        # Regex to change '|' into 'x(0) z(0)'
        replace_bar_regex = r"(\|)"
        string = re.sub(replace_bar_regex, "x(0) z(0)", string)
        
        for char in string + splitters[0]:

            if char == "\\":
                follows_slash = True
                token += char
                continue

            elif (char == "(" or char == "[") and not follows_slash:
                stack.append(char)
            elif (char == ")" or char == "]") and not follows_slash:
                if not stack:
                    raise SyntaxError("Unmatched brackets")
                if not matches_next_element(char):
                    raise SyntaxError("Unmatched brackets")
                stack.pop()

            
            if char in splitters and not stack and not follows_slash:
                token = token.strip()
                result.append(token) if token else None
                token = ""

            else:
                token += char

            follows_slash = False
        
        if stack:
            raise SyntaxError("Unmatched open parethesis")

        # print(f"{string=} gave {result=}")
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
        # print(tokenize_regex)

        error1, func_name, inputs, modifiers, args, error2 = re.findall(tokenize_regex, string, flags=re.DOTALL)[0]
#         print(f"""Result for {string}: 
# Error1: {error1}
# Func: {func_name}
# Inputs: {inputs}
# Modifiers: {modifiers}
# Args: {args}
# Error2: {error2}""")

        if error1 and error1 != "-":
            
            raise SyntaxError(f"Unknown item {error1} in {string}")
        elif error2:
            raise SyntaxError(f"Unknown item {error2} in {string}")
        
        if string[0] == "-":
            self.reverse = True
        else:
            self.reverse = False


        func = Player.FUNCTIONS.get(func_name)
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
        args = self.parse(args, splitters=",")
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

        if func.__name__ not in Player._can_have_modifiers and modifiers:
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
        # print(positional_only)
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
        # print(can_be_positional)

        if len(required_positionals) > len(args):
            number_of_missing = len(required_positionals) - len(args)
            raise TypeError(f"{func.__name__} missing {number_of_missing} positional-only argument{'s' if number_of_missing > 1 else ''}: {', '.join(list(required_positionals)[len(args):])}")

        for i in range(min(len(args), len(can_be_positional))):

            # RISKY RISKY RISKY RISKY RISKY
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
        
        # print(args, can_be_positional)
        if len(args) < len(can_be_positional):
            a = len(args) - len(can_be_positional)
            can_be_positional = {x:can_be_positional[x] for x in list(can_be_positional)[a:]}
        
        elif var_positional and len(args) > len(can_be_positional):
            for j in args[len(can_be_positional):]:
                c = self.safe_eval(j, list(var_positional.values())[0], locals)
                converted_args.append(c)
                # print(converted_args)
        
        elif not var_positional and len(args) > len(can_be_positional):
            raise TypeError(f"{func.__name__} accepts at most {len(can_be_positional)} positional arguments, got {len(args)} instead")
        
        can_be_keyword = can_be_positional | keyword_only

        ### Check the keyword args ###
        for kw, value in kwargs.items():
            datatype = can_be_keyword.get(kw)

            # print(kw, datatype)

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
        # print(self.modifiers)
        args = token["args"]
        kwargs = token["kwargs"]

        func(self, *args, **kwargs)
    
    def simulate(self, sequence: str, return_defaults = True, locals: dict = None):

        parsed_tokens = self.parse(sequence)

        # print(parsed_tokens)

        for token in parsed_tokens:
            runnable = self.tokenize(token, locals=locals)
            # pp(runnable)
            self.run(runnable)

        
        if return_defaults and not self.output:
            self.add_output_with_label("Y", self.y, "z-expr")
            self.add_output_with_label("VY", self.vy, "z-expr")
    def show_output(self):
        for tup in self.output:
            print(tup[0])

if __name__ == "__main__":
    p = Player()
    # s = "jump(15) outy slime outy a(7) outy"
    # s = "jump(12) outy y(0.125) jump(12) outy"
    s = "inertia(0.003) il(j outvy r(a outvy outy, 14))"
    # s = "il(j outvy r(a outvy, 14))"
    p.simulate(s)
    p.show_output()

    