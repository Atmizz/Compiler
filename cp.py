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
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton,  QPlainTextEdit, QLabel
from PySide6.QtGui import QFont

calc_grammar = r"""
    ?start: (stmt | NEWLINE)*

    ?stmt: simple_stmt | compound_stmt | comment_stmt

    ?comment_stmt: COMMENT                    -> comment_stmt
    
    ?simple_stmt: (expr | print | input | assign | self_calc | reassign | bit_op | break_stmt | continue_stmt | return_stmt | array_def | array_assign)
    
    print: "print" "(" (print_factor)*  [sep_factor] [end_factor]")" -> print_stmt
    print_factor: [","] + expr -> print_factor_stmt
    sep_factor: [","] + "sep" "=" expr -> print_sep_stmt
    end_factor: [","] + "end" "=" expr -> print_end_stmt

    input: "cin" (input_factor)+ -> input_stmt
    input_factor: ">>" NAME -> input_factor_stmt

    assign: type var_factor ("," var_factor)*  -> assign_stmt
    var_factor: (unassign_var | assign_var)
    unassign_var: NAME -> unassign_stmt
    assign_var: NAME "=" expr -> assign_stmt2

    array_def: type NAME "[" expr "]" -> array_def
    array_access: NAME "[" expr "]" -> array_access
    array_assign: NAME "[" expr "]" "=" expr -> array_assign
    
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

    ?compound_stmt: (if_stmt | for_stmt | while_stmt | do_while_stmt | func_def | class_def | class_instance | class_extends | try_catch_stmt)
    
    if_stmt : ifstmt (elifstmt)* (elsestmt)? -> if_else_stmt
    ifstmt: "if" "(" condition ")" block     -> if_stmt
    elifstmt: "elif" "(" condition ")" block -> if_stmt
    elsestmt: "else" block              -> else_stmt
    condition: expr                           -> condition_func
            | expr + (("&&" | "and") + expr)+ -> condition_and_func
            | expr + (("||" | "or") + expr)+ -> condition_or_func
    
            
    while_stmt : "while" "(" condition ")" block -> while_stmt
    do_while_stmt : "do" block "while" "(" condition ")" -> do_while_stmt
    for_stmt: "for" "(" [simple_stmt] ";" [condition] ";" [simple_stmt] ")" block -> for_stmt
    
    func_def: "func" NAME "(" [arg_list] ")" block -> func_def_stmt
    func_call: NAME "(" [arg_values] ")" -> func_call_stmt


    class_def: "class" NAME "{" [class_arg_list] [class_func_list] "}" -> class_def
    class_extends: "class" NAME "extends" NAME "{" [class_arg_list] [class_func_list] "}" -> class_extends
    class_instance: NAME NAME -> class_instance
    class_var: NAME "." NAME -> class_var
    class_func: NAME "." NAME "(" [arg_values] ")" -> class_func
    class_arg_list: (arg ["=" expr])+ -> class_arg_list
    class_func_list : ("func" NAME "(" [arg_list] ")" block)+ -> class_func_list
    this_var: "this" "." NAME -> this_var
    this_func: "this" "." NAME "(" [arg_values] ")" -> this_func
    super_var: "super" "." NAME -> super_var
    super_func: "super" "." NAME "(" [arg_values] ")" -> super_func

    try_catch_stmt: "try" block "catch" "(" NAME ")" block -> try_catch_stmt

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
         | class_var
         | class_func
         | this_var
         | this_func
         | super_var
         | super_func
         | array_access
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
        self.local_classes_stack = []
        self.functions = {}
        self.classes = {}
        self.classes_super = {}
        self.arrays = {}
        self.printResult = str()

    def print_factor_stmt(self, tree):
        # print(self.visit(tree.children[0]), end='')
        self.printResult += str(self.visit(tree.children[0]))
        return [1, None]

    def print_sep_stmt(self, tree):
        # print(self.visit(tree.children[0]), end='')
        self.printResult += str(self.visit(tree.children[0]))
        return [1, None]

    def print_end_stmt(self, tree):
        # print(self.visit(tree.children[0]), end='')
        self.printResult += str(self.visit(tree.children[0]))
        return [1, None]

    def print_stmt(self, tree):
        for i in range(0, len(tree.children) - 2):
            stmt = tree.children[i]
            if stmt == None:
                continue
            self.visit(stmt)
            if tree.children[-2] == None:
                # print(end=' ')
                if i < len(tree.children) - 3:
                    self.printResult += ' '
            else:
                self.visit(tree.children[-2])
        if(tree.children[-1] == None):
            # print(end='\n')
            self.printResult += '\n'
        else:
            self.visit(tree.children[-1])
        return [1, None]

    def input_stmt(self, tree):
        for stmt in tree.children[0:]:
            self.visit(stmt)
        return [1, None]

    def input_assign_stmt(self, tree, set, name):
        x = input()
        if str(type(set[name])) == '<class \'str\'>':
            set[name] = x
        elif str(type(set[name])) == '<class \'float\'>':
            set[name] = float(x)
        else:
            set[name] = int(x)

    def input_factor_stmt(self, tree):
        name = str(tree.children[0])
        flag = False
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                self.input_assign_stmt(tree, self.local_vars_stack[-1], name)
                flag = True
        else:
            if name in self.global_vars:
                self.input_assign_stmt(tree, self.global_vars, name)
                flag = True
        if not flag:
            raise ValueError(f"Variable '{name}' not found")
        
    def stmt_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        name = str(tree.children[1])
        if self.local_vars_stack:
            if name in self.local_vars_stack[-1]:
                raise ValueError(f"Variable '{name}' already exists")
        if name in self.global_vars:
            raise ValueError(f"Variable '{name}' already exists")
        x = 0
        if var_type == '<class \'str\'>':
            x = ''
        if self.local_vars_stack:
            self.local_vars_stack[-1][name] = x
        else:
            self.global_vars[name] = x
        return [1, None]
            
    def assign_stmt(self, tree):
        var_type = self.visit(tree.children[0])
        self.local_vars_stack.append({var_type : 1})
        for stmt in tree.children[1:]:
            self.visit(stmt)
        self.local_vars_stack.pop()
        return [1, None]

    def assign_to_var(self, tree, name, value):
        if len(self.local_vars_stack) > 1:
            if name in self.local_vars_stack[-2]:
                raise ValueError(f"Variable '{name}' already exists")
            self.local_vars_stack[-2][name] = value
        else:
            if name in self.global_vars:
                raise ValueError(f"Variable '{name}' already exists")
            self.global_vars[name] = value

    def unassign_stmt(self, tree):
        name = str(tree.children[0])
        value = 0
        self.assign_to_var(tree, name, value)

    def assign_stmt2(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[1])
        if str(type(value)) not in self.local_vars_stack[-1]:
                raise TypeError(f"Cannot assign {str(type(value))} value to int variable '{name}'.")
        self.assign_to_var(tree, name, value)

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
        argsAndTypes = self.visit(tree.children[1])
        args = argsAndTypes[0]
        types = tuple(argsAndTypes[1])
        if (func_name, types) in self.functions:
            raise ValueError(f"Function '{func_name}' already defined")
        body = tree.children[2]
        self.functions[(func_name, types)] = (args, body)
        return [1, None]
    
    def arg_list(self, tree):
        args = []
        types = []
        for arg in tree.children:
            name = str(arg.children[1])
            arg_type = self.visit(arg.children[0])
            args.append(name)
            types.append(arg_type)
        return [args, types]
        
    def func_call_stmt(self, tree):
        func_name = str(tree.children[0])
        arg_values = self.visit(tree.children[1])
        types = []
        for arg_value in arg_values:
            types.append(str(type(arg_value)))
        types = tuple(types)
        if (func_name, types) not in self.functions:
            raise NameError(f"Function '{func_name}' not defined")
        args, body = self.functions[(func_name, types)]
        local_vars = dict(zip(args, arg_values))
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

    def class_def(self, tree):
        class_name = str(tree.children[0])
        if class_name in self.classes:
            raise NameError(f"Class '{class_name}' already defined")
        class_vars = {}
        class_funcs = {}
        if tree.children[1] != None:
            class_vars = self.visit(tree.children[1])
        if tree.children[2] != None:
            class_funcs = self.visit(tree.children[2])
        self.classes[class_name] = (class_vars, class_funcs, class_name)
        return [1, None]

    def class_arg_list(self, tree):
        class_vars = {}
        for i in range(0, len(tree.children), 2):
            arg = tree.children[i]
            value = tree.children[i+1]
            name = str(arg.children[1])
            if value == None:
                value = 0
                if self.visit(arg.children[0]) == '<class \'str\'>':
                    value = ''
            else:
                value = self.visit(value)
            class_vars[name] = value
        return class_vars

    def class_func_list(self, tree):
        class_funcs = {}
        for i in range(0, len(tree.children), 3):
            name = str(tree.children[i])
            args = []
            types = []
            if tree.children[i+1] != None:
                argsAndTypes = self.visit(tree.children[i+1])
                args = argsAndTypes[0]
                types = argsAndTypes[1]
            types = tuple(types)
            body = tree.children[i+2]
            if (name, types) in class_funcs:
                raise ValueError(f"Function '{name}' already defined")
            class_funcs[(name, types)] = (args, body)
        return class_funcs
    
    def class_instance(self, tree):
        class_type = str(tree.children[0])
        class_name = str(tree.children[1])
        if class_type not in self.classes:
            raise NameError(f"Class '{class_type}' not defined")
        if class_name in self.classes:
            raise NameError(f"Class instance '{class_name}' already defined")
        class_vars, class_funcs, class_type = self.classes[class_type]
        class_vars_copy = class_vars.copy()
        self.classes[class_name] = (class_vars_copy, class_funcs, class_type)
        return [1, None]

    def class_func_impl(self, tree, class_name, func_name):
        func_values = []
        types = []
        if tree.children[-1] != None:
            func_values = self.visit(tree.children[-1])
        for arg_value in func_values:
            types.append(str(type(arg_value)))
        types = tuple(types)
        if (func_name, types) not in self.classes[class_name][1]:
            raise NameError(f"Class '{class_name}' has no function '{func_name}'")
        self.local_classes_stack.append(class_name)
        args, body = self.classes[class_name][1][(func_name, types)]
        local_vars = dict(zip(args, func_values))
        self.local_vars_stack.append(local_vars)
        result = self.visit(body)
        self.local_vars_stack.pop()
        self.local_classes_stack.pop()
        if result[0] == 4:
            return result[1]
        return None

    def class_var(self, tree):
        name = str(tree.children[0])
        var = str(tree.children[1])
        if name not in self.classes:
            raise NameError(f"Class instance '{name}' not defined")
        if var not in self.classes[name][0]:
            raise NameError(f"Class instance '{name}' has no attribute '{var}'")
        return self.classes[name][0][var]

    def class_func(self, tree):
        class_name = str(tree.children[0])
        func_name = str(tree.children[1])
        if class_name not in self.classes:
            raise NameError(f"Class '{class_name}' not defined")
        return self.class_func_impl(tree, class_name, func_name)
    
    def this_var(self, tree):
        if len(self.local_classes_stack) == 0:
            raise NameError("No class instance defined")
        name = self.local_classes_stack[-1]
        var = str(tree.children[0])
        if var not in self.classes[name][0]:
            raise NameError(f"Class instance '{name}' has no attribute '{var}'")
        return self.classes[name][0][var]

    def this_func(self, tree):
        if len(self.local_classes_stack) == 0:
            raise NameError("No class instance defined")
        class_name = self.local_classes_stack[-1]
        func_name = str(tree.children[0])
        return self.class_func_impl(tree, class_name, func_name)
    
    def super_var(self, tree):
        if len(self.local_classes_stack) == 0:
            raise NameError("No class instance defined")
        name = self.local_classes_stack[-1]
        vars, funcs, class_type = self.classes[name]
        if class_type not in self.classes_super:
            raise NameError("No super class defined")
        name = self.classes_super[class_type]
        var = str(tree.children[0])
        if var not in self.classes[name][0]:
            raise NameError(f"Class instance '{name}' has no attribute '{var}'")
        return self.classes[name][0][var]

    def super_func(self, tree):
        if len(self.local_classes_stack) == 0:
            raise NameError("No class instance defined")
        name = self.local_classes_stack[-1]
        vars, funcs, class_type = self.classes[name]
        if class_type not in self.classes_super:
            raise NameError("No super class defined")
        name = self.classes_super[class_type]
        func_name = str(tree.children[0])
        return self.class_func_impl(tree, name, func_name)

    def class_extends(self, tree):
        class_name = str(tree.children[0])
        base_class = str(tree.children[1])
        if base_class not in self.classes:
            raise NameError(f"Class '{base_class}' not defined")
        if class_name in self.classes:
            raise NameError(f"Class '{class_name}' already defined")
        self.classes_super[class_name] = base_class
        base_vars, base_funcs, base_class_type = self.classes[base_class]
        class_vars = base_vars.copy()
        class_funcs = base_funcs.copy()
        if tree.children[2] != None:
            new_vars = self.visit(tree.children[2])
            class_vars.update(new_vars)
        if tree.children[3] != None:
            new_funcs = self.visit(tree.children[3])
            class_funcs.update(new_funcs)
        self.classes[class_name] = (class_vars, class_funcs, class_name)
        return [1, None]

    def try_catch_stmt(self, tree):
        name = str(tree.children[1])
        try:
            self.local_vars_stack.append({})
            self.visit(tree.children[0])
            return [1, None]
        except Exception as e:
            exception_var = str(e)
            self.local_vars_stack.append({name: exception_var})
            self.visit(tree.children[2])
            return [1, None]

    def array_def(self, tree):
        type = self.visit(tree.children[0])
        name = str(tree.children[1])
        size = int(self.visit(tree.children[2]))
        if size <= 0:
            raise ValueError("Array size must be positive")
        x = 0
        if type == "<class 'str'>":
            x = ''
        self.arrays[name] = [x] * size
        return [1, None]
    
    def array_access(self, tree):
        name = str(tree.children[0])
        index = int(self.visit(tree.children[1]))
        if name not in self.arrays:
            raise NameError(f"Array '{name}' not defined")
        if index >= len(self.arrays[name]):
            raise IndexError(f"Array '{name}' index out of range")
        return self.arrays[name][index]
    
    def array_assign(self, tree):
        name = str(tree.children[0])
        index = int(self.visit(tree.children[1]))
        value = self.visit(tree.children[2])
        tp = str(type(value))
        if name not in self.arrays:
            raise NameError(f"Array '{name}' not defined")
        if tp != str(type(self.arrays[name][0])):
            raise TypeError(f"Array '{name}' type mismatch")
        if index >= len(self.arrays[name]):
            raise IndexError(f"Array '{name}' index out of range")
        self.arrays[name][index] = value
        return [1, None]
        

calc_parser = Lark(calc_grammar, parser='lalr', lexer='contextual')


# 已经实现静态数组
# try catch

# code = r"""
# int a, b
# cin >> a >> b
# print(a + b)
# """

# parsed_tree = calc_parser.parse(code)

interpreter = CalculateTree()
# interpreter.visit(parsed_tree)

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


# GUI

class Main():
    def __init__(self):
        self.window = QMainWindow()
        self.window.resize(1080, 720)
        self.window.move(400, 200)
        self.window.setWindowTitle('CP Code Editor')
        self.textEdit = QPlainTextEdit(self.window)
        self.textEdit.setPlaceholderText("edit code here")
        self.textEdit.move(3, 3)
        self.textEdit.resize(800, 710)
        self.textEdit.setFont(QFont("Courier", 18))

        self.resultLabel = QLabel(self.window)
        self.resultLabel.setText("Result:")
        self.resultLabel.move(805, 85)
        self.resultLabel.setFont(QFont("Courier", 18))
        self.resultLabel.setStyleSheet("color: red;")

        self.result = QPlainTextEdit(self.window)
        self.result.setReadOnly(True)
        self.result.move(805, 120)
        self.result.setFont(QFont("Courier", 18))
        self.result.setStyleSheet("color: red;")
        self.result.setFixedSize(270, 593)

        self.button = QPushButton('Run', self.window)
        self.button.resize(250, 80)
        self.button.move(805, 3)
        self.button.setFont(QFont("Courier", 18))
        self.button.clicked.connect(self.run)

    def run(self):
        interpreter.__init__()
        code = self.textEdit.toPlainText()
        parsed_tree = calc_parser.parse(code)
        interpreter.visit(parsed_tree)
        self.result.setPlainText(interpreter.printResult)
        # tree_graph = visualize_tree(parsed_tree)
        # tree_graph.render('simple_lang_tree_demo')
        # tree_graph.view()

app = QApplication([])

mainWindow = Main()
mainWindow.window.show()

app.exec()