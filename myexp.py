from graphviz import Digraph
from lark import Lark, Tree, Token
from lark.visitors import Interpreter

grammar = """
?start: stmt+

?stmt: PRINT                         -> print_stmt
     | NAME EQUAL expr               -> assign_stmt

?expr: term
     | expr "+" term                 -> add
     | expr "-" term                 -> sub

?term: factor
     | term "*" factor               -> mul
     | term "/" factor               -> div

?factor: NUMBER                      -> number
       | NAME                        -> var
       | "(" expr ")"                -> grouped_expr

%import common.CNAME -> NAME
%import common.NUMBER
%import common.WS
%ignore WS

PRINT: "print" "(" expr ")"
EQUAL: "="
"""

class SimpleLangInterpreter(Interpreter):
    def __init__(self):
        super().__init__()
        self.variables = {}

    def assign_stmt(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[2])
        self.variables[name] = value

    def print_stmt(self, tree):
        value = self.visit(tree.children[1])
        print(value)

    def number(self, tree):
        return int(tree.children[0])

    def var(self, tree):
        name = str(tree.children[0])
        if name in self.variables:
            return self.variables[name]
        else:
            raise ValueError(f"Undefined variable '{name}'")

    def add(self, tree):
        left = self.visit(tree.children[0])
        right = self.visit(tree.children[1])
        return left + right

    def sub(self, tree):
        left = self.visit(tree.children[0])
        right = self.visit(tree.children[1])
        return left - right

    def mul(self, tree):
        left = self.visit(tree.children[0])
        right = self.visit(tree.children[1])
        return left * right

    def div(self, tree):
        left = self.visit(tree.children[0])
        right = self.visit(tree.children[1])
        return left / right

# 示例代码
code = """
x = 10
y = 20
print (x + y)
"""

# 使用解析器
parser = Lark(grammar, parser='lalr', lexer='contextual')
parsed_tree = parser.parse(code)




def draw_tree(tree, graph, parent=None, count=0):
    node_id = str(count)
    label = tree.data if isinstance(tree, Tree) else str(tree)
    graph.node(node_id, label)

    if parent is not None:
        graph.edge(parent, node_id)

    count += 1
    for child in tree.children:
        if isinstance(child, Tree):
            count = draw_tree(child, graph, node_id, count)
        else:
            leaf_id = str(count)
            graph.node(leaf_id, str(child))
            graph.edge(node_id, leaf_id)
            count += 1
    return count


def visualize_tree(tree):
    graph = Digraph(format="png")
    draw_tree(tree, graph)
    return graph



# tree_graph = visualize_tree(parsed_tree)
# tree_graph.render('simple_lang_tree_demo')
# tree_graph.view()


interpreter = SimpleLangInterpreter()
interpreter.visit(parsed_tree)