import re


def _tokenize(expression):
    token_specification = [
        ('NUMBER', r'\d+(\.\d+)?[eE]-\d+|\d+(\.\d+)?[eE]\d+|\d+\.\d+|\d+\.|\.\d+|\d+'),  # Integer or decimal number
        ('PLUS', r'\+'),              # Addition (+)
        ('MINUS', r'-'),              # Subtraction (-)
        ('POW', r'\*\*'),             # Exponent (**)
        ('TIMES', r'\*'),             # Multiplication (*)
        ('DIVIDE', r'/'),             # Division (/)
        ('LPAREN', r'\('),            # Left Parenthesis
        ('RPAREN', r'\)'),            # Right Parenthesis
        ('ID', r'[A-Za-z_][A-Za-z_0-9]*'),  # Variable name (w/ underscores) (for substitutions)
        ('WHITESPACE', r'\s+'),             # Whitespace
        ('MISMATCH', r'.'),           # Anything else (will raise an error)
    ]

    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
    r = []
    nest = 0
    not_expecting_number_or_variable = False
    prevkind, prevvalue = None, None
    for match_object in re.finditer(tok_regex, expression):
        kind = match_object.lastgroup
        value = match_object.group()
        if kind == 'MISMATCH':
            raise SyntaxError(f"Invalid token '{value}'")
        elif kind == 'NUMBER':
            if prevkind == 'RPAREN':
                raise SyntaxError(f"Invalid Expression, number after right parethesis")
            value = float(value)
            r.append((kind, value))
        elif kind == 'LPAREN':
            nest += 1
            if prevkind == 'NUMBER':
                raise SyntaxError("Invalid Expression, left parenthesis after number")
            r.append((kind,value))
        elif kind == 'RPAREN':
            if not nest:
                raise SyntaxError("Unbalanced Parenthesis")
            r.append((kind,value))
            nest -= 1
        elif kind != 'WHITESPACE':
            r.append((kind, value))

        if kind != "WHITESPACE":

            
            if (prevkind == "ID" or prevkind == "NUMBER") and (kind == "NUMBER" and kind == "ID"):
                raise SyntaxError(f"Invalid Expression, number and variable have no operation in between")

            prevkind, prevvalue = kind, value
    
    if nest:
        raise SyntaxError("Unbalanced Parenthesis")

    
    # print(r)
    return r


def _apply_operator(operands: list, operator: str):
    if operator == 'UNARY_MINUS':
        if not operands:
            raise SyntaxError(f"Invalid expression")
        a = operands.pop()
        operands.append(-a)
        return operands
    
    if len(operands) <= 1:
        raise SyntaxError("Invalid Expression")
    b = operands.pop()
    a = operands.pop()
    if operator == '+':
        operands.append(a + b)
    elif operator == '-':
        operands.append(a - b)
    elif operator == '*':
        operands.append(a * b)
    elif operator == '/':
        operands.append(a / b)
    elif operator == '**':
        operands.append(a ** b)
    return operands

def _evaluate(tokens, variables):
    # print(tokens)
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '**': 3, 'UNARY_MINUS': 4}
    operands = []
    operators = []
    prevkind = None
    prevvalue = None
    for kind, value in tokens:
        if kind == 'NUMBER':
            operands.append(value)
        elif kind == 'ID':
            if value in variables:
                operands.append(variables[value])
            else:
                raise ValueError(f"Unknown variable: {value}")
            
        elif kind == 'MINUS':
            if (prevkind is None) or (prevkind in ['PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POW', 'LPAREN']):
                # unary minus occurs at start or after another operator or after a left parenthesis;
                while operators and operators[-1] in precedence and precedence[operators[-1]] >= precedence['UNARY_MINUS']:
                    operands = _apply_operator(operands, operators.pop())
                operators.append('UNARY_MINUS')
            else:
                # Binary minus
                while operators and operators[-1] in precedence and precedence[operators[-1]] >= precedence['-']:
                    operands = _apply_operator(operands, operators.pop())
                operators.append('-')
        elif kind == 'PLUS' or kind == 'TIMES' or kind == 'DIVIDE' or kind == 'POW':
            while (operators and operators[-1] in precedence and precedence[operators[-1]] >= precedence[value]):
                operands = _apply_operator(operands, operators.pop())
            operators.append(value)
        elif kind == 'LPAREN':
            operators.append('(')
        elif kind == 'RPAREN':
            while operators[-1] != '(':
                operands = _apply_operator(operands, operators.pop())
            # print(operands)
            # print(operators)
            operators.pop()
        prevkind = kind
        prevvalue = value

    while operators:
        operands = _apply_operator(operands, operators.pop())

    return operands[0]

def evaluate(expression, variables: dict=None):
    if not expression:
        return 0
    
    if isinstance(expression, (float, int)):
        return expression
    elif not isinstance(expression, str):
        raise ValueError(f"Invalid expression of type {type(expression)}: {expression}")


    if variables is None:
        variables = {}

    # print(expression)
    tokens = _tokenize(expression)
    try:
        result=  _evaluate(tokens, variables)
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result
    except Exception as e:
        raise SyntaxError(f"{e} in expression '{expression}'")

# if __name__ == "__main__":
    # print(evaluate("0.1+0.2", {"p":3}))

    # print(evaluate("2**(3-1)/(2+6)") == 0.5)
    # print(evaluate("-3*(1+2)") == -9)
    # print(evaluate("-1+2**(4-8*p4x)", {'p4x':1/2}) == 0)
    # print(evaluate("2*(3-1)")==4)
    # # print(evaluate('-3*-2+((2)')) # syntax error: unbalanced parenthesis
    # print(evaluate("2") == 2)
    # print(evaluate("2.2") == 2.2)
    # print(evaluate("2.") == 2)
    # print(evaluate(".2") == 0.2)
    # print(evaluate("(1-5)*0.1") == -0.4)
    # print(evaluate("0.1*(1-5)") == -0.4)
    # print(evaluate("(0.1)*(2-3)") == -0.1)
