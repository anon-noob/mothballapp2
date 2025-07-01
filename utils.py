import inspect
from copy import deepcopy
class BlockData:
    def __init__(self):
        self.line_number = 0
        self.depth = 0
        self.parenthesis_stack = []
        self.in_string = False
        self.in_comment = False
        self.in_brackets = False
        self.function_stack = FunctionStack()
        self.current_function = ''
        self.last_nonspace_token = ''
    
    def __repr__(self):
        return f"<Line {self.line_number}>(depth={self.depth}, stack={self.parenthesis_stack})"

class FunctionSignatures:
    def __init__(self, func):
        a = inspect.signature(func).parameters
        self.func = func.__name__
        # print("A", self.func)
        self.positional_parameters_remaining = [x for x in a.values() if (x.kind != inspect.Parameter.VAR_KEYWORD and x.kind != inspect.Parameter.KEYWORD_ONLY) and x.name != 'self']
        self.keyword_parameters_remaining = {n:x for n,x in a.items() if (x.kind != inspect.Parameter.POSITIONAL_ONLY and x.kind != inspect.Parameter.VAR_POSITIONAL) and x.name != 'self'}
        self.after_keyword = False
        self.curr_param_name = ""
    
    def current_parameter(self):
        if self.positional_parameters_remaining:
            return self.positional_parameters_remaining[0]
        elif self.keyword_parameters_remaining:
            # return self.keyword_parameters_remaining[0]
            return
    
    def set_after_keyword(self):
        self.after_keyword = True
        self.positional_parameters_remaining = []

    def discard_parameter(self, name = ''):
        if self.positional_parameters_remaining and not name:
            self.positional_parameters_remaining.pop(0)
            if not self.positional_parameters_remaining:
                self.after_keyword = True

        elif self.keyword_parameters_remaining:
            if name in self.keyword_parameters_remaining:
                self.after_keyword = False
                self.positional_parameters_remaining = []
                del self.keyword_parameters_remaining[name]
    
    def current_parameter_datatype(self):
        a = self.current_parameter()
        if a:
            return a.annotation

class FunctionStack:
    def __init__(self):
        self.stack: list[FunctionSignatures] = []
    
    def push(self, item):
        if callable(item):
            self.stack.append(FunctionSignatures(item))
        else:
            raise TypeError("Not a function")

    def pop(self):
        if self.stack:
            return self.stack.pop()
        raise IndexError("pop from empty stack")

    def peek(self):
        if self.stack:
            return self.stack[-1]
        return None

    def is_empty(self):
        return len(self.stack) == 0

    def size(self):
        return len(self.stack)

    def get_function_signature(self, index=-1):
        if not self.stack:
            raise IndexError("stack is empty")
        func = self.stack[index]
        if callable(func):
            return inspect.signature(func)
        else:
            raise TypeError("Object at index is not callable")
    
    def copy(self):
        return deepcopy(self)

# if __name__ == "__main__":
    # import mothball_simulation_xz as xz
    # f = xz.Player.zmm
    # b = FunctionStack()
    # b.push(f)
    # print(b.peek().current_parameter(), b.peek().current_parameter_datatype())
    # b.peek().set_after_keyword()
    # print(b.peek().keyword_parameters_remaining)