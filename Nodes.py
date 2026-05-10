# Every class here is one kind of node in Lumen's Abstract Syntax Tree.
# The interpreter will pattern-match on these to decide what to do.

class NumberNode:
    def __init__(self, tok):
        self.tok       = tok
        self.pos_start = tok.pos_start
        self.pos_end   = tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


class StringNode:
    def __init__(self, tok):
        self.tok       = tok
        self.pos_start = tok.pos_start
        self.pos_end   = tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


class BoolNode:
    def __init__(self, tok):
        self.tok       = tok
        self.pos_start = tok.pos_start
        self.pos_end   = tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


class VarAccessNode:
    """Reading the value of a variable: x"""
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start    = var_name_tok.pos_start
        self.pos_end      = var_name_tok.pos_end

    def __repr__(self):
        return f'(access {self.var_name_tok.value})'


class VarAssignNode:
    """Assigning a variable: let x = 10  /  final let x = 10"""
    def __init__(self, var_name_tok, value_node, is_final=False):
        self.var_name_tok = var_name_tok
        self.value_node   = value_node
        self.is_final     = is_final
        self.pos_start    = var_name_tok.pos_start
        self.pos_end      = value_node.pos_end

    def __repr__(self):
        prefix = 'final ' if self.is_final else ''
        return f'({prefix}let {self.var_name_tok.value} = {self.value_node})'


class BinOpNode:
    """Binary operation: left OP right"""
    def __init__(self, left_node, op_tok, right_node):
        self.left_node  = left_node
        self.op_tok     = op_tok
        self.right_node = right_node
        self.pos_start  = left_node.pos_start
        self.pos_end    = right_node.pos_end

    def __repr__(self):
        return f'({self.left_node} {self.op_tok} {self.right_node})'


class UnaryOpNode:
    """Unary operation: -x  /  not x"""
    def __init__(self, op_tok, node):
        self.op_tok    = op_tok
        self.node      = node
        self.pos_start = op_tok.pos_start
        self.pos_end   = node.pos_end

    def __repr__(self):
        return f'({self.op_tok} {self.node})'


class IfNode:
    """
    cases: list of (condition_node, body_nodes) for if / elseif branches
    else_case: list of body_nodes or None
    """
    def __init__(self, cases, else_case, pos_start, pos_end):
        self.cases      = cases
        self.else_case  = else_case
        self.pos_start  = pos_start
        self.pos_end    = pos_end


class ForRangeNode:
    """for i in start to end then ... end"""
    def __init__(self, var_name_tok, start_node, end_node, body_nodes, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.start_node   = start_node
        self.end_node     = end_node
        self.body_nodes   = body_nodes
        self.pos_start    = pos_start
        self.pos_end      = pos_end


class ForCStyleNode:
    """for (init; condition; step) then ... end"""
    def __init__(self, init_node, condition_node, step_node, body_nodes, pos_start, pos_end):
        self.init_node      = init_node
        self.condition_node = condition_node
        self.step_node      = step_node
        self.body_nodes     = body_nodes
        self.pos_start      = pos_start
        self.pos_end        = pos_end


class WhileNode:
    """while condition then ... end"""
    def __init__(self, condition_node, body_nodes, pos_start, pos_end):
        self.condition_node = condition_node
        self.body_nodes     = body_nodes
        self.pos_start      = pos_start
        self.pos_end        = pos_end


class DoWhileNode:
    """do then ... end  while condition"""
    def __init__(self, body_nodes, condition_node, pos_start, pos_end):
        self.body_nodes     = body_nodes
        self.condition_node = condition_node
        self.pos_start      = pos_start
        self.pos_end        = pos_end


class FuncDefNode:
    """func name(params) then ... end"""
    def __init__(self, func_name_tok, param_toks, body_nodes, pos_start, pos_end):
        self.func_name_tok = func_name_tok
        self.param_toks    = param_toks
        self.body_nodes    = body_nodes
        self.pos_start     = pos_start
        self.pos_end       = pos_end


class CallNode:
    """name(arg1, arg2, ...)"""
    def __init__(self, node_to_call, arg_nodes, pos_start, pos_end):
        self.node_to_call = node_to_call
        self.arg_nodes    = arg_nodes
        self.pos_start    = pos_start
        self.pos_end      = pos_end


class ReturnNode:
    """return expr"""
    def __init__(self, return_node, pos_start, pos_end):
        self.return_node = return_node   # may be None
        self.pos_start   = pos_start
        self.pos_end     = pos_end


class ArrayLiteralNode:
    """let scores of int[6] = {1, 2, 3}  or  let scores of int[] = {1, 2}"""
    def __init__(self, var_name_tok, element_type, size_node, element_nodes, is_final, pos_start, pos_end):
        self.var_name_tok  = var_name_tok
        self.element_type  = element_type   # 'int' | 'float' | 'bool' | 'string'
        self.size_node     = size_node       # NumberNode or None (dynamic)
        self.element_nodes = element_nodes   # list of expression nodes
        self.is_final      = is_final
        self.pos_start     = pos_start
        self.pos_end       = pos_end


class ArrayAccessNode:
    """scores at 0"""
    def __init__(self, array_node, index_node, pos_start, pos_end):
        self.array_node = array_node
        self.index_node = index_node
        self.pos_start  = pos_start
        self.pos_end    = pos_end


class ArrayAssignNode:
    """scores at 0 = 99"""
    def __init__(self, array_name_tok, index_node, value_node, pos_start, pos_end):
        self.array_name_tok = array_name_tok
        self.index_node     = index_node
        self.value_node     = value_node
        self.pos_start      = pos_start
        self.pos_end        = pos_end


class VarReassignNode:
    """Bare reassignment: x = expr  (no let, no final)"""
    def __init__(self, var_name_tok, value_node, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.value_node   = value_node
        self.pos_start    = pos_start
        self.pos_end      = pos_end

    def __repr__(self):
        return f'(reassign {self.var_name_tok.value} = {self.value_node})'


class ForEachNode:
    """for item in array then ... end"""
    def __init__(self, var_name_tok, array_node, body_nodes, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.array_node   = array_node
        self.body_nodes   = body_nodes
        self.pos_start    = pos_start
        self.pos_end      = pos_end


class CharNode:
    """A char literal: 'a'"""
    def __init__(self, tok):
        self.tok       = tok
        self.pos_start = tok.pos_start
        self.pos_end   = tok.pos_end

    def __repr__(self):
        return f"'{self.tok.value}'"


class ThrowNode:
    """throw expr"""
    def __init__(self, expr_node, pos_start, pos_end):
        self.expr_node = expr_node
        self.pos_start = pos_start
        self.pos_end   = pos_end


class TryCatchNode:
    """try then ... on error err then ... [always then ...] end"""
    def __init__(self, try_body, err_name_tok, catch_body, always_body, pos_start, pos_end):
        self.try_body     = try_body
        self.err_name_tok = err_name_tok   # the 'err' identifier token
        self.catch_body   = catch_body
        self.always_body  = always_body    # may be None
        self.pos_start    = pos_start
        self.pos_end      = pos_end


class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end   = pos_end

class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end   = pos_end


class VarTypedAssignNode:
    """let x of int = 10 — typed mutable variable"""
    def __init__(self, var_name_tok, declared_type, value_node, is_final, pos_start, pos_end):
        self.var_name_tok  = var_name_tok
        self.declared_type = declared_type   # 'int' | 'float' | 'bool' | 'string' | 'char'
        self.value_node    = value_node
        self.is_final      = is_final
        self.pos_start     = pos_start
        self.pos_end       = pos_end


class StructDefNode:
    """struct Name then fields/methods end"""
    def __init__(self, name_tok, fields, methods, pos_start, pos_end):
        self.name_tok  = name_tok
        self.fields    = fields    # list of (name_tok, declared_type, default_node)
        self.methods   = methods   # list of FuncDefNode
        self.pos_start = pos_start
        self.pos_end   = pos_end


class StructInstantiateNode:
    """StructName(arg1, arg2, ...)"""
    def __init__(self, name_tok, arg_nodes, pos_start, pos_end):
        self.name_tok  = name_tok
        self.arg_nodes = arg_nodes
        self.pos_start = pos_start
        self.pos_end   = pos_end


class FieldAccessNode:
    """obj.field"""
    def __init__(self, obj_node, field_tok, pos_start, pos_end):
        self.obj_node  = obj_node
        self.field_tok = field_tok
        self.pos_start = pos_start
        self.pos_end   = pos_end


class FieldAssignNode:
    """obj.field = value"""
    def __init__(self, obj_node, field_tok, value_node, pos_start, pos_end):
        self.obj_node   = obj_node
        self.field_tok  = field_tok
        self.value_node = value_node
        self.pos_start  = pos_start
        self.pos_end    = pos_end