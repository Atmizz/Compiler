from lark import Lark, Tree
from graphviz import Digraph
from lark.visitors import Interpreter

calc_grammar = r"""
    ?start: stmt+

    ?stmt: "print" "(" expr ")" -> print_stmt
          | COMMENT                    -> comment_stmt

          
          | type NAME "=" expr  -> assign_stmt
          | NAME "++"        -> self_add
          | NAME "--"        -> self_sub
          | "++" NAME        -> self_add
          | "--" NAME        -> self_sub
          | NAME "=" expr       -> reassign_stmt
          

          | ifstmt (elifstmt)* (elsestmt)? -> if_else_stmt
          
          
          | "while" "(" expr ")" block -> while_stmt
          | "do" block "while" "(" expr ")" -> do_while_stmt
          | "for" "(" (type NAME "=" expr)? ";" (expr)? ";" (expr)? ")" block -> for_stmt
          

    ifstmt: "if" "(" expr ")" block     -> if_stmt
    elifstmt: "elif" "(" expr ")" block -> if_stmt
    elsestmt: "else" block              -> else_stmt
    block: "{" stmt+ "}"

    COMMENT: "//" /[^\n]*/ NEWLINE
    
    NEWLINE: "\n"

    ?type: "int"              -> int_type
         | "float"            -> float_type
         | "string"           -> string_type
         | "bool"             -> bool_type

    ?expr: sum
         | comparison

    ?comparison: expr "<" expr  -> less_than
         | expr ">" expr  -> greater_than
         | expr "==" expr -> equal
         | expr "!=" expr -> not_equal
         | expr "<=" expr -> less_than_equal
         | expr ">=" expr -> greater_than_equal
    
    ?sum: product
        | expr "+" product    -> add
        | expr "-" product    -> sub

    ?product: atom
        | product "*" atom    -> mul
        | product "/" atom    -> div

    ?atom: NUMBER              -> number
         | STRING              -> string
         | NAME                -> var
         | "true"              -> true_bool
         | "false"             -> false_bool
         | "(" expr ")"        -> grouped_expr

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS
    %import common.ESCAPED_STRING -> STRING

    %ignore WS
    %ignore COMMENT
    %ignore NEWLINE
"""


class CalculateTree(Interpreter):
    def __init__(self):
        self.vars = {}

    def print_stmt(self, tree):
        print(self.visit(tree.children[0]))

    def assign_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        name = str(tree.children[1])
        value = self.visit(tree.children[2])
        if var_type == 'int':
            if not isinstance(value, int):
                raise TypeError(f"Cannot assign {type(value).__name__} value to int variable '{name}'.")
            self.vars[name] = int(value)
        elif var_type == 'float':
            if not isinstance(value, (int, float)):
                raise TypeError(f"Cannot assign {type(value).__name__} value to float variable '{name}'.")
            self.vars[name] = float(value)
        elif var_type == 'string':
            if not isinstance(value, str):
                raise TypeError(f"Cannot assign {type(value).__name__} value to string variable '{name}'.")
            self.vars[name] = value
        elif var_type == 'bool':
            if not isinstance(value, bool):
                raise TypeError(f"Cannot assign {type(value).__name__} value to bool variable '{name}'.")
            self.vars[name] = value

    def reassign_stmt(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[1])
        if name not in self.vars:
            raise ValueError(f"Undefined variable '{name}'")
        if type(self.vars[name]) != type(value):
            raise TypeError(f"Cannot assign {type(value).__name__} value to variable '{name}' of type {type(self.vars[name]).__name__}")
        self.vars[name] = value
    
    def add(self, tree):
        return self.visit(tree.children[0]) + self.visit(tree.children[1])

    def sub(self, tree):
        return self.visit(tree.children[0]) - self.visit(tree.children[1])

    def mul(self, tree):
        return self.visit(tree.children[0]) * self.visit(tree.children[1])

    def div(self, tree):
        return self.visit(tree.children[0]) / self.visit(tree.children[1])

    def self_add(self, tree):
        print("children", tree.children)
        name = str(tree.children[0])
        value = self.vars[name]
        if type(value) != int:
            raise TypeError(f"Cannot use ++ or -- operator on non-integer variable '{name}'")
        self.vars[name] = value + 1
        return value
    
    def self_sub(self, tree):
        name = str(tree.children[0])
        value = self.vars[name]
        if type(value) != int:
            raise TypeError(f"Cannot use ++ or -- operator on non-integer variable '{name}'")
        self.vars[name] = value - 1
        return value
    
    def number(self, tree):
        num_str = str(tree.children[0])
        return int(num_str) if '.' not in num_str else float(num_str)

    def string(self, tree):
        str =  tree.children[0][1:-1]
        return bytes(str, "utf-8").decode("unicode_escape")

    def int_type(self, tree):
        return 'int'

    def float_type(self, tree):
        return 'float'

    def string_type(self, tree):
        return 'string'

    def bool_type(self, tree):
        return 'bool'

    def var(self, tree):
        name = str(tree.children[0])
        if name in self.vars:
            return self.vars[name]
        else:
            raise ValueError(f"Undefined variable '{name}'")

    def true_bool(self, tree):
        return True

    def false_bool(self, tree):
        return False

    def comment_stmt(self, tree):
            pass  # 忽略注释

    def less_than(self, tree):
        return self.visit(tree.children[0]) < self.visit(tree.children[1])

    def less_equal(self, tree):
        return self.visit(tree.children[0]) <= self.visit(tree.children[1])

    def greater_than(self, tree):
        return self.visit(tree.children[0]) > self.visit(tree.children[1])

    def greater_equal(self, tree):
        return self.visit(tree.children[0]) >= self.visit(tree.children[1])

    def equal(self, tree):
        return self.visit(tree.children[0]) == self.visit(tree.children[1])

    def not_equal(self, tree):
        return self.visit(tree.children[0]) != self.visit(tree.children[1])
    
    def less_than_equal(self, tree):
        return self.visit(tree.children[0]) <= self.visit(tree.children[1])
    
    def greater_than_equal(self, tree):
        return self.visit(tree.children[0]) >= self.visit(tree.children[1])

    def if_stmt(self, tree):
        condition = self.visit(tree.children[0])
        if condition != 0:
            self.visit(tree.children[1])
            return True
        return False

    def else_stmt(self, tree):
        self.visit(tree.children[0])
    
    def if_else_stmt(self, tree):
        for stmt in tree.children:
            if self.visit(stmt):
                break

    def while_stmt(self, tree):
        while True:
            condition = self.visit(tree.children[0])
            if not condition:
                break
            self.visit(tree.children[1])
            
    def do_while_stmt(self, tree):
        while True:
            self.visit(tree.children[0])
            condition = self.visit(tree.children[1])
            if not condition:
                break
        
    def for_stmt(self, tree):
        print("tree", tree.children)
        return 


# Create the parser
calc_parser = Lark(calc_grammar, parser='lalr', lexer='contextual')

# Example code to parse and interpret
code = r"""
for(int i = 0; i < 10; i = i + 1) {
    print(i)
}
"""

parsed_tree = calc_parser.parse(code)
interpreter = CalculateTree()
interpreter.visit(parsed_tree)

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



tree_graph = visualize_tree(parsed_tree)
tree_graph.render('simple_lang_tree_demo')
tree_graph.view()
