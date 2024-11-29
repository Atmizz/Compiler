"""
return code table:
0 - 不可以执行
1 - 可以继续执行
2 - continue信号
3 - break信号
4 - return语句
"""


from lark import Lark, Tree
from graphviz import Digraph
from lark.visitors import Interpreter

calc_grammar = r"""
    ?start: (stmt | NEWLINE)*

    ?stmt: simple_stmt | compound_stmt | comment_stmt

    ?comment_stmt: COMMENT                    -> comment_stmt
    
    ?simple_stmt: (expr | print | assign | self_calc | reassign | bit_op | break_stmt | continue_stmt | return_stmt)
      
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

    return_stmt: "return" [expr] -> return_stmt

    ?compound_stmt: (if_stmt | for_stmt | while_stmt | do_while_stmt | func_def)
    
    if_stmt : ifstmt (elifstmt)* (elsestmt)? -> if_else_stmt
    while_stmt : "while" "(" condition ")" block -> while_stmt
    do_while_stmt : "do" block "while" "(" condition ")" -> do_while_stmt
    for_stmt: "for" "(" [simple_stmt] ";" [condition] ";" [simple_stmt] ")" block -> for_stmt
    func_def: "func" NAME "(" [arg_list] ")" block -> func_def_stmt
    func_call: NAME "(" [arg_values] ")" -> func_call_stmt
    
    ifstmt: "if" "(" condition ")" block     -> if_stmt
    elifstmt: "elif" "(" condition ")" block -> if_stmt
    elsestmt: "else" block              -> else_stmt
    condition: expr                           -> condition_func
            | expr + (("&&" | "and") + expr)+ -> condition_and_func
            | expr + (("||" | "or") + expr)+ -> condition_or_func
    block: "{" [stmt+] "}"                      -> block_stmt
    arg_list: arg ("," arg)* -> arg_list
    arg: type NAME        
    arg_values: expr ("," expr)* -> arg_values

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
         | func_call
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
        self.global_vars = {}
        self.local_vars_stack = []
        self.functions = {}

    def print_factor_stmt(self, tree):
        print(self.visit(tree.children[0]), end='')
        return [1, None]

    def print_sep_stmt(self, tree):
        print(self.visit(tree.children[0]), end='')
        return [1, None]

    def print_end_stmt(self, tree):
        print(self.visit(tree.children[0]), end='')
        return [1, None]

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
        return [1, None]

    def stmt_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        name = str(tree.children[0])
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                raise ValueError(f"Variable '{name}' already exists")
        if name in self.global_vars:
            raise ValueError(f"Variable '{name}' already exists")
        if var_type == '<class \'str\'>':
            self.global_vars[name] = ''
        else:
            self.global_vars[name] = 0
        return [1, None]
            
    def assign_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        for stmt in tree.children[1:]:
            lst = self.visit(stmt)
            if var_type != lst[0]:
                raise TypeError(f"Cannot assign {type(lst[2]).__name__} value to int variable '{lst[1]}'.")
        return [1, None]

    def assign_stmt2(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[1])
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                raise ValueError(f"Variable '{name}' already exists")
            self.local_vars_stack[-1][name] = value
        else:
            if name in self.global_vars:
                raise ValueError(f"Variable '{name}' already exists")
            self.global_vars[name] = value
        return [str(type(value)), name, value]

    def reassign_stmt(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[1])
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                self.local_vars_stack[-1][name] = value
        if name not in self.global_vars:
            raise ValueError(f"Undefined variable '{name}'")
        if type(self.global_vars[name]) != type(value):
            raise TypeError(f"Cannot assign {type(value).__name__} value to variable '{name}' of type {type(self.global_vars[name]).__name__}")
        self.global_vars[name] = value
        return [1, None]

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

    def get_val(self, tree, name):
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                return self.local_vars_stack[-1][name]
        else :
            if name in self.global_vars:
                return self.global_vars[name]
        raise ValueError(f"Undefined variable '{name}'")
            
    def modify_val(self, tree, name, value):
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                self.local_vars_stack[-1][name] = value
        else:
            if name in self.global_vars:
                self.global_vars[name] = value

    def self_add(self, tree):
        name = str(tree.children[0])
        value = self.get_val(tree, name)
        if type(value) != int:
            raise TypeError(f"Cannot use ++ operator on non-integer variable '{name}'")
        self.modify_val(tree, name, value + 1)
        return [1, None]
    
    def self_sub(self, tree):
        name = str(tree.children[0])
        value = self.get_val(tree, name)
        if type(value) != int:
            raise TypeError(f"Cannot use -- operator on non-integer variable '{name}'")
        self.modify_val(tree, name, value - 1)
        return [1, None]
    
    def aug_add(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) + self.visit(tree.children[1]))
        return [1, None]
    
    def aug_sub(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) - self.visit(tree.children[1]))
        return [1, None]
    
    def aug_mul(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) * self.visit(tree.children[1]))
        return [1, None]

    def aug_div(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) / self.visit(tree.children[1]))
        return [1, None]
    
    def aug_mod(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) % self.visit(tree.children[1]))
        return [1, None]
    
    def aug_div_int(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) // self.visit(tree.children[1]))
        return [1, None]

    def aug_pow(self, tree):
        name = str(tree.children[0])
        self.modify_val(tree, name, self.get_val(tree, name) ** self.visit(tree.children[1]))
        return [1, None]

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

        if self.local_vars_stack:
            for local_vars in reversed(self.local_vars_stack):
                if name in local_vars:
                    return local_vars[name]

        if name in self.global_vars:
            return self.global_vars[name]
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
            return [1, None]
        return [0, None]

    def condition_and_func(self, tree):
        for stmt in tree.children:
          condition = self.visit(stmt)
          if not condition[0]:
              return [0, None]
        return [1, None]
    
    def condition_or_func(self, tree):
        for stmt in tree.children:
          condition = self.visit(stmt)
          if condition[0]:
              return [1, None]
        return [0, None]

    def alter_local(self, tree):
        for name in self.local_vars_stack[-2]:
            self.local_vars_stack[-2][name] = self.local_vars_stack[-1][name]
        self.local_vars_stack.pop()
        
    def block_stmt(self, tree):
        self.local_vars_stack.append(self.local_vars_stack[-1])
        for stmt in tree.children:
            condition = self.visit(stmt)
            if condition[0] > 1:
                self.alter_local(self)
                return condition
        self.alter_local(self)
        return [1, None]

    def if_stmt(self, tree):
        self.local_vars_stack.append({})
        condition = self.visit(tree.children[0])
        flag = [0, None]
        if condition[0] == 1:
            flag = self.visit(tree.children[1])
        self.local_vars_stack.pop()
        return flag

    def else_stmt(self, tree):
        self.local_vars_stack.append({})
        condition = self.visit(tree.children[0])
        self.local_vars_stack.pop()
        return condition
    
    def if_else_stmt(self, tree):
        for stmt in tree.children:
            condition = self.visit(stmt)
            if condition[0] > 0:
                return condition
        return [0, None]

    def while_stmt(self, tree):
        self.local_vars_stack.append({})
        while True:
            condition = self.visit(tree.children[0])
            if not condition[0]:
                break
            condition = self.visit(tree.children[1])
            if condition[0] == 2:
                continue
            elif condition[0] == 3:
                break
            elif condition[0] == 4:
                return condition
        self.local_vars_stack.pop()
        return [1, None]
            
    def do_while_stmt(self, tree):
        self.local_vars_stack.append({})
        while True:
            condition = self.visit(tree.children[0])
            if condition[0] == 2:
                continue
            elif condition[0] == 3:
                break
            elif condition[0] == 4:
                return condition
            condition = self.visit(tree.children[1])
            if not condition:
                break
        self.local_vars_stack.pop()
        return [1, None]
        
    def for_stmt(self, tree):
        self.local_vars_stack.append({})
        if tree.children[0] != None:
           self.visit(tree.children[0])
        while True:
            if tree.children[1] != None:
                condition = self.visit(tree.children[1])
                if not condition[0]:
                    break
            if tree.children[3] != None:  
                condition = self.visit(tree.children[3])
                if condition[0] == 3:
                    break
                elif condition[0] == 4:
                    return condition
            if tree.children[2] != None:  
                self.visit(tree.children[2])
        self.local_vars_stack.pop()
        return [1, None]
    
    def break_stmt(self, tree):
        return [3, None]

    def continue_stmt(self, tree):
        return [2, None]

    def func_def_stmt(self, tree):
        func_name = str(tree.children[0])
        args = self.visit(tree.children[1])
        body = tree.children[2]
        self.functions[func_name] = (args, body)
        return [1, None]
    
    def arg_list(self, tree):
        args = []
        for arg in tree.children:
            name = str(arg.children[1])
            self.global_vars[name] = 0
            if self.visit(arg.children[0]) == '<class \'str\'>':
                self.global_vars[name] = ''
            args.append(name)
        return args
        
    def func_call_stmt(self, tree):
        func_name = str(tree.children[0])
        if func_name not in self.functions:
            raise NameError(f"Function '{func_name}' not defined")
        args, body = self.functions[func_name]
        arg_values = self.visit(tree.children[1])
        local_vars = dict(zip(args, arg_values))
        if len(args) != len(arg_values):
            raise ValueError(f"Function '{func_name}' expects {len(args)} arguments, but got {len(arg_values)}")
        self.local_vars_stack.append(local_vars)
        result = self.visit(body)
        self.local_vars_stack.pop()
        if result[0] == 4:
            return result[1]
        return None
    
    def arg_values(self, tree):
        arg_values = []
        for arg in tree.children:
            arg_values.append(self.visit(arg))
        return arg_values
    
    def return_stmt(self, tree):
        if len(tree.children) > 0:
            return_value = self.visit(tree.children[0])
        else:
            return_value = None
        return [4, return_value]

calc_parser = Lark(calc_grammar, parser='lalr', lexer='contextual')

code = r"""
func fib(int x) {
    if(x <= 2) {
        return 1
    }
    return fib(x - 1) + fib(x - 2)
}
print(fib(10))
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
# tree_graph.view()
