from parser import Ast


class Env:
    def __init__(self, parent):
        self.parent = parent
        self.table = {}

    def get(self, key):
        env = self
        while env is not None:
            if key in env.table:
                return env[key]
            env = env.parent
        return None

    def set_value(self, key, value):
        self.table[key] = value

    def assign_value(self, key, value):
        env = self
        while env is not None:
            if key in env.table:
                env[key] = value
                return
            env = env.parent
        raise Exception(f"Runtime Error: {key} not found")


class Fun:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.arity = len(params)
        self.body = body


class Interpreter:
    def __init__(self, ast):
        self.ast = ast
        self.env = Env(None)

    def run(self):
        for stmt_or_dclr in self.ast["body"]:
            self.evaluate(stmt_or_dclr)

    def evaluate(self, stmt_or_dclr):
        match stmt_or_dclr["type"]:
            case Ast.EXPR_STMT:
                self.expression(stmt_or_dclr["expression"])
            case Ast.PRINT_STMT:
                value = self.expression(stmt_or_dclr["value"])
                print(value)
            case Ast.LET_DCLR:
                key = self.expression(stmt_or_dclr["name"])
                value = self.expression(stmt_or_dclr["value"])
                self.env.set_value(key, value)
            case Ast.BLOCK_STMT:
                self.env = Env(self.env)
                self.evaluate(stmt_or_dclr["body"])
                self.env = self.env.parent
            case Ast.IF_STMT:
                self.if_stmt(stmt_or_dclr)
            case Ast.WHILE_STMT:
                self.while_stmt(stmt_or_dclr)
            case Ast.FUNCTION_DCLR:
                self.function(stmt_or_dclr)
            case _:
                raise Exception(f"Internal Error {stmt_or_dclr}")

    def function(self, expr):
        name = self.expression(expr["name"])
        params = [self.expression(param) for param in expr["params"]]
        function = Fun(name, params, expr["body"])
        self.env.set_value(name, function)

    def if_stmt(self, expr):
        if self.expression(expr["test"]):
            self.evaluate(expr["consequent"])
        else:
            self.evaluate(expr["alternative"])

    def while_stmt(self, expr):
        while self.expression(expr["test"]):
            self.evaluate(expr["body"])

    def expression(self, expr):
        match expr["type"]:
            case Ast.BINARY:
                return self.binary(expr)
            case Ast.UNARY:
                return self.unary(expr)
            case Ast.NUMBER | Ast.BOOLEAN | Ast.NULL | Ast.STRING:
                return expr["value"]
            case Ast.DICTIONARY:
                return dict(expr["items"])
            case Ast.IDENTIFIER:
                name = expr["value"]
                value = self.env.get(name)
                if value is None:
                    raise Exception(f"Runtime Error: identifier {name} "
                                    f"not found on line: {expr['line']}")
                return value
            case Ast.CALL:
                return self.call(expr)
            case Ast.ASSIGNMENT:
                key = self.expression(expr["name"])
                value = self.expression(expr["value"])
                self.env.assign_value(key, value)
                return value
            case _:
                raise Exception("Internal Error")

    def call(self, expr):
        function = self.expression(expr["callee"])

        if not isinstance(function, Fun):
            raise Exception(f"Runtime Error: {function} is not callable")

        if len(expr["arguments"]) != function.arity:
            raise Exception(f"Runtime Error: incorrect number "
                            f"of arguments provided to function {function.name}")

        self.env = Env(self.env)

        args = [self.expression(arg) for arg in expr["arguments"]]

        for param, arg in zip(function.params, args):
            self.env.set_value(param, arg)

        for stmt_or_dclr in function.body:
            self.evaluate(stmt_or_dclr)

        self.env = self.env.parent

    def unary(self, expr):
        value = self.expression(expr["argument"])

        match expr["operator"]:
            case "-":
                return -value
            case "!":
                return not value
            case _:
                raise Exception("Internal Error")

    def binary(self, expr):
        lhs = self.expression(expr["left"])
        rhs = self.expression(expr["right"])

        match expr["operator"]:
            case "+":
                return lhs + rhs
            case "-":
                return lhs - rhs
            case "*":
                return lhs * rhs
            case "/":
                return lhs / rhs
            case ">":
                return lhs > rhs
            case ">=":
                return lhs >= rhs
            case "<":
                return lhs < rhs
            case "<=":
                return lhs <= rhs
            case "!=":
                return lhs != rhs
            case "==":
                return lhs == rhs
            case "and":
                return lhs and rhs
            case "or":
                return lhs or rhs
            case _:
                raise Exception("Internal Error")