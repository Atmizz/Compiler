from lark import Lark, Transformer

# 文法定义
grammar = """
    start: expr*

    ?expr: assign
         | print
         | ifstmt
         | sum

    assign: type NAME "=" sum -> assign_var
    print: "print" "(" sum ")" -> print_expr

    ifstmt: "if" "(" sum ")" "{" expr* "}" elifstmt* -> if_stmt
          | "if" "(" sum ")" "{" expr* "}" elifstmt* "else" "{" expr* "}" -> if_else_stmt

    elifstmt: "elif" "(" sum ")" "{" expr* "}" -> elif_stmt

    ?type: "int"   -> int_type
         | "float" -> float_type
         | "string" -> string_type
         | "bool" -> bool_type

    ?sum: product
         | sum "+" product     -> add
         | sum "-" product     -> sub
         | atom COMP atom      -> compare

    ?product: atom
            | product "*" atom -> mul
            | product "/" atom -> div

    ?atom: NUMBER              -> number
         | STRING              -> string
         | "true"              -> true_bool
         | "false"             -> false_bool
         | NAME                -> var
         | "(" sum ")"

    COMP: "<" | "<=" | ">" | ">=" | "==" | "!="

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS
    %import common.ESCAPED_STRING -> STRING
    %ignore WS
"""

# 创建解析器
parser = Lark(grammar, parser='lalr')

# 语法树转换器
class CalculateTree(Transformer):
    def __init__(self):
        self.variables = {}

    def assign_var(self, items):
        var_type, name, value = items

        # 类型检查
        if var_type == 'int' and not isinstance(value, int):
            raise ValueError(f"Variable '{name}' must be of type int.")
        elif var_type == 'float' and not isinstance(value, float):
            raise ValueError(f"Variable '{name}' must be of type float.")
        elif var_type == 'string' and not isinstance(value, str):
            raise ValueError(f"Variable '{name}' must be of type string.")
        elif var_type == 'bool' and not isinstance(value, bool):
            raise ValueError(f"Variable '{name}' must be of type bool.")

        self.variables[name] = value
        return value

    def print_expr(self, items):
        value = items[0]
        print(value)
        return value

    def add(self, items):
        return items[0] + items[1]

    def sub(self, items):
        return items[0] - items[1]

    def mul(self, items):
        return items[0] * items[1]

    def div(self, items):
        return items[0] / items[1]

    def number(self, items):
        num_str, = items  # 解包元组
        return int(num_str) if '.' not in num_str else float(num_str)

    def string(self, items):
        str_val, = items  # 解包元组
        return str_val[1:-1]  # 去掉引号

    def var(self, items):
        var_name, = items  # 解包元组
        if var_name in self.variables:
            return self.variables[var_name]
        raise ValueError(f"Undefined variable: {var_name}")

    def int_type(self, items):
        return 'int'

    def float_type(self, items):
        return 'float'

    def string_type(self, items):
        return 'string'

    def bool_type(self, items):
        return 'bool'

    def true_bool(self, items):
        return True

    def false_bool(self, items):
        return False

    def if_stmt(self, items):
        condition, exprs, elif_stmts = items
        if condition:
            for expr in exprs:
                self.transform(expr)
        else:
            for elif_stmt in elif_stmts:
                self.transform(elif_stmt)

    def elif_stmt(self, items):
        condition, exprs = items
        if condition:
            for expr in exprs:
                self.transform(expr)
            return True  # 找到了符合条件的elif，停止执行后续的elif或else
        return False

    def if_else_stmt(self, items):
        condition, exprs_if_true, elif_stmts, exprs_if_false = items
        if condition:
            for expr in exprs_if_true:
                self.transform(expr)
        elif any(self.transform(elif_stmt) for elif_stmt in elif_stmts):
            pass  # 如果elif块被处理，则跳过else块
        else:
            for expr in exprs_if_false:
                self.transform(expr)

# 创建转换器实例
transformer = CalculateTree()

# 表达式求值函数
def eval_expression(expression):
    tree = parser.parse(expression)
    transformer.transform(tree)
    return transformer.variables  # 返回变量字典

# 测试代码
code = """
int x = 2 + 3 * 4
float y = x * 2.5
string name = "Alice"
bool is_active = true
print(x + y)
print(name)
print(is_active)
if (x > 10) {
    print("x is greater than 10")
} elif (x != 14) {
    print("bye")
}
else {
    print("x is not greater than 10")
}
"""

if __name__ == "__main__":
    variables = eval_expression(code)