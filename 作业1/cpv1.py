"""
return code table:
0 - 不可以执行
1 - 可以继续执行
2 - continue信号
3 - break信号
"""


from lark import Lark, Tree
from graphviz import Digraph
from lark.visitors import Interpreter

calc_grammar = r"""
    ?start: (stmt | NEWLINE)*

    ?stmt: simple_stmt | compound_stmt | comment_stmt

    ?comment_stmt: COMMENT                    -> comment_stmt
    
    ?simple_stmt: (expr | print | assign | self_calc | reassign | bit_op | break_stmt | continue_stmt)
      
    print: "print" "(" (print_factor)*  [sep_factor] [end_factor]")" -> print_stmt
    
    print_factor: [","] + expr -> print_factor_stmt
    
    sep_factor: [","] + "sep" "=" expr -> print_sep_stmt

    end_factor: [","] + "end" "=" expr -> print_end_stmt

    assign: type one_var ("," one_var)*  -> assign_stmt
          | type NAME                    -> stmt_stmt
    one_var: NAME "=" expr -> assign_stmt2
    
    self_calc: NAME "++"        -> self_add
          | NAME "--"        -> self_sub
          | "++" NAME        -> self_add
          | "--" NAME        -> self_sub
        
    reassign: NAME "=" expr       -> reassign_stmt
    
    bit_op: NAME "+=" expr -> aug_add
          | NAME "-=" expr -> aug_sub
          | NAME "*=" expr -> aug_mul
          | NAME "/=" expr -> aug_div
          | NAME "//=" expr -> aug_div_int
          | NAME "**=" expr -> aug_pow
          | NAME "%=" expr  -> aug_mod

    break_stmt: "break" -> break_stmt

    continue_stmt: "continue" -> continue_stmt

    ?compound_stmt: (if_stmt | for_stmt | while_stmt | do_while_stmt)
    
    if_stmt : ifstmt (elifstmt)* (elsestmt)? -> if_else_stmt
    while_stmt : "while" "(" condition ")" block -> while_stmt
    do_while_stmt : "do" block "while" "(" condition ")" -> do_while_stmt
    for_stmt: "for" "(" [simple_stmt] ";" [condition] ";" [simple_stmt] ")" block -> for_stmt
               
    ifstmt: "if" "(" condition ")" block     -> if_stmt
    elifstmt: "elif" "(" condition ")" block -> if_stmt
    elsestmt: "else" block              -> else_stmt
    condition: expr                           -> condition_func
            | expr + (("&&" | "and") + expr)+ -> condition_and_func
            | expr + (("||" | "or") + expr)+ -> condition_or_func
    block: "{" [stmt+] "}"                      -> block_stmt

    COMMENT: "!!" /[^\n]*/ NEWLINE
    
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
    
    ?sum: compute_op
         | sum "&" compute_op  -> and_op
         | expr "|" compute_op  -> or_op
         | expr "^" compute_op  -> xor_op
         | "~" compute_op -> neg_op
         | "!" compute_op -> not_op
         | expr "<<" compute_op  -> left_shift_op
         | expr ">>" compute_op  -> right_shift_op
    ?compute_op: product
        | compute_op "+" product    -> add
        | compute_op "-" product    -> sub

    ?product: atom
        | product "**" atom   -> pow
        | product "*" atom    -> mul
        | product "/" atom    -> div
        | product "//" atom   -> div_int
        | product "%" atom    -> mod

    ?atom: NUMBER              -> number
         | STRING              -> string
         | NAME                -> var
         | "True"              -> true_bool
         | "False"             -> false_bool
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

    def print_factor_stmt(self, tree):
        print(self.visit(tree.children[0]), end='')
        return 0

    def print_sep_stmt(self, tree):
        print(self.visit(tree.children[0]), end='')

    def print_end_stmt(self, tree):
        print(self.visit(tree.children[0]), end='')
        return 1

    def print_stmt(self, tree):
        for stmt in tree.children[:-2]:
            if stmt == None:
                continue
            self.visit(stmt)
            if tree.children[-2] == None:
                print(end=' ')
            else:
                self.visit(tree.children[-2])
        if(tree.children[-1] == None):
            print(end='\n')
        else:
            self.visit(tree.children[-1])
        return 1

    def stmt_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        name = str(tree.children[0])
        if name in self.vars:
            raise ValueError(f"Variable '{name}' already exists")
        if var_type == '<class \'str\'>':
            self.vars[name] = ''
        else:
            self.vars[name] = 0
            

    def assign_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        for stmt in tree.children[1:]:
            lst = self.visit(stmt)
            if var_type != lst[0]:
                raise TypeError(f"Cannot assign {type(lst[2]).__name__} value to int variable '{lst[1]}'.")
        return 1

    def assign_stmt2(self, tree):
        name = str(tree.children[0])
        if name in self.vars:
            raise ValueError(f"Variable '{name}' already exists")
        value = self.visit(tree.children[1])
        self.vars[name] = value
        return [str(type(value)), name, value]

    def reassign_stmt(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[1])
        print("value", value)
        if name not in self.vars:
            raise ValueError(f"Undefined variable '{name}'")
        if type(self.vars[name]) != type(value):
            raise TypeError(f"Cannot assign {type(value).__name__} value to variable '{name}' of type {type(self.vars[name]).__name__}")
        self.vars[name] = value
        return 1

    def and_op(self, tree): 
        return self.visit(tree.children[0]) & self.visit(tree.children[1])

    def or_op(self, tree):
        return self.visit(tree.children[0]) | self.visit(tree.children[1])
    
    def xor_op(self, tree):
        return self.visit(tree.children[0]) ^ self.visit(tree.children[1])
    
    def neg_op(self, tree):
        return ~self.visit(tree.children[0])
    
    def not_op(self, tree):
        return not self.visit(tree.children[0])
    
    def left_shift_op(self, tree):
        return self.visit(tree.children[0]) << self.visit(tree.children[1])
    
    def right_shift_op(self, tree):
        return self.visit(tree.children[0]) >> self.visit(tree.children[1])

    def add(self, tree):
        return self.visit(tree.children[0]) + self.visit(tree.children[1])

    def sub(self, tree):
        return self.visit(tree.children[0]) - self.visit(tree.children[1])

    def mul(self, tree):
        return self.visit(tree.children[0]) * self.visit(tree.children[1])

    def pow(self, tree):
        return self.visit(tree.children[0]) ** self.visit(tree.children[1])

    def div(self, tree):
        return self.visit(tree.children[0]) / self.visit(tree.children[1])

    def div_int(self, tree):
        return self.visit(tree.children[0]) // self.visit(tree.children[1])

    def mod(self, tree):
        return self.visit(tree.children[0]) % self.visit(tree.children[1])

    def self_add(self, tree):
        name = str(tree.children[0])
        value = self.vars[name]
        if type(value) != int:
            raise TypeError(f"Cannot use ++ or -- operator on non-integer variable '{name}'")
        self.vars[name] = value + 1
        return 1
    
    def self_sub(self, tree):
        name = str(tree.children[0])
        value = self.vars[name]
        if type(value) != int:
            raise TypeError(f"Cannot use ++ or -- operator on non-integer variable '{name}'")
        self.vars[name] = value - 1
        return 1
    
    def aug_add(self, tree):
        name = str(tree.children[0])
        self.vars[name] += self.visit(tree.children[1])
        return 1
    
    def aug_sub(self, tree):
        name = str(tree.children[0])
        self.vars[name] -= self.visit(tree.children[1])
        return 1
    
    def aug_mul(self, tree):
        name = str(tree.children[0])
        self.vars[name] *= self.visit(tree.children[1])
        return 1

    def aug_div(self, tree):
        name = str(tree.children[0])
        self.vars[name] /= self.visit(tree.children[1])
        return 1
    
    def aug_mod(self, tree):
        name = str(tree.children[0])
        self.vars[name] %= self.visit(tree.children[1])
        return 1
    
    def aug_div_int(self, tree):
        name = str(tree.children[0])
        self.vars[name] //= self.visit(tree.children[1])
        return 1

    def aug_pow(self, tree):
        name = str(tree.children[0])
        self.vars[name] **= self.visit(tree.children[1])
        return 1

    def number(self, tree):
        num_str = str(tree.children[0])
        return int(num_str) if '.' not in num_str else float(num_str)

    def string(self, tree):
        str =  tree.children[0][1:-1]
        return bytes(str, "utf-8").decode("unicode_escape")

    def int_type(self, tree):
        return '<class \'int\'>'

    def float_type(self, tree):
        return '<class \'float\'>'

    def string_type(self, tree):
        return '<class \'str\'>'

    def bool_type(self, tree):
        return '<class \'bool\'>'

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

    def condition_func(self, tree):
        if self.visit(tree.children[0]):
            return 1
        return 0

    def condition_and_func(self, tree):
        for stmt in tree.children:
          if not self.visit(stmt):
              return 0
        return 1
    
    def condition_or_func(self, tree):
        for stmt in tree.children:
          if self.visit(stmt):
              return 1
        return 0

    def block_stmt(self, tree):
        for stmt in tree.children:
            condition = self.visit(stmt)
            if condition > 1:
                return condition
        return condition

    def if_stmt(self, tree):
        condition = self.visit(tree.children[0])
        if condition == 1:
            return self.visit(tree.children[1])
        return 0

    def else_stmt(self, tree):
        return self.visit(tree.children[0])
    
    def if_else_stmt(self, tree):
        for stmt in tree.children:
            condition = self.visit(stmt)
            if condition > 0:
                return condition
        return 0

    def while_stmt(self, tree):
        while True:
            condition = self.visit(tree.children[0])
            if not condition:
                break
            condition = self.visit(tree.children[1])
            if condition == 2:
                continue
            elif condition == 3:
                break
            
    def do_while_stmt(self, tree):
        while True:
            condition = self.visit(tree.children[0])
            if condition == 2:
                continue
            elif condition == 3:
                break
            condition = self.visit(tree.children[1])
            if not condition:
                break
        
    def for_stmt(self, tree):
        if tree.children[0] != None:
           self.visit(tree.children[0])
        while True:
            if tree.children[1] != None:
                condition = self.visit(tree.children[1])
                if not condition:
                    break
            if tree.children[3] != None:  
                condition = self.visit(tree.children[3])
                if condition == 3:
                    break
            if tree.children[2] != None:  
                self.visit(tree.children[2])
            
    def break_stmt(self, tree):
      return 3

    def continue_stmt(self, tree):
        return 2

calc_parser = Lark(calc_grammar, parser='lalr', lexer='contextual')

code = r"""
print(1+2, 3, 4, sep=",", end="|||||")
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
