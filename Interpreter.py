from lexer import (
    TT_CHAR,
    TT_PLUS, TT_MINUS, TT_MUL, TT_DIV,
    TT_EQEQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE,
    TT_KEYWORD,
)
from nodes import (
    ArrayLiteralNode, ArrayAccessNode, ArrayAssignNode,
    VarReassignNode, ForEachNode, CharNode,
    ThrowNode, TryCatchNode,
    NumberNode, StringNode, BoolNode,
    VarAccessNode, VarAssignNode,
    BinOpNode, UnaryOpNode,
    IfNode, ForRangeNode, ForCStyleNode, WhileNode, DoWhileNode,
    FuncDefNode, CallNode, ReturnNode,
)
from errors import Error

# ── Runtime Error ─────────────────────────────────────────────────────────────

class LumenRuntimeError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        result  = self.generate_traceback()
        result += f'{self.error_name}: {self.details}\n'
        from string_with_arrows import string_with_arrows
        result += string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        result  = ''
        pos     = self.pos_start
        ctx     = self.context
        while ctx:
            result = f'  File {pos.fn}, line {pos.ln + 1}, in {ctx.display_name}\n' + result
            pos    = ctx.parent_entry_pos
            ctx    = ctx.parent
        return 'Traceback (most recent call last):\n' + result

# ── Runtime Result ────────────────────────────────────────────────────────────

class RuntimeResult:
    def __init__(self):
        self.value        = None
        self.error        = None
        self.return_value = None
        self.throw_value  = None   # string message from 'throw'

    def register(self, res):
        if res.error:
            self.error = res.error
        if res.return_value is not None:
            self.return_value = res.return_value
        if res.throw_value is not None:
            self.throw_value = res.throw_value
        return res.value

    def success(self, value):
        self.value = value
        return self

    def success_return(self, value):
        self.return_value = value
        return self

    def success_throw(self, message):
        self.throw_value = message
        return self

    def failure(self, error):
        self.error = error
        return self

    def should_return(self):
        return self.error or self.return_value is not None or self.throw_value is not None

# ── Context (scope) ───────────────────────────────────────────────────────────

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name     = display_name
        self.parent           = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table     = SymbolTable(parent.symbol_table if parent else None)


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}   # name -> (value, is_final)
        self.parent  = parent

    def get(self, name):
        val = self.symbols.get(name)
        if val is None and self.parent:
            return self.parent.get(name)
        return val  # (value, is_final) or None

    def set(self, name, value, is_final=False):
        self.symbols[name] = (value, is_final)

    def assign(self, name, value):
        """Reassign existing variable — respects final, walks scopes."""
        if name in self.symbols:
            _, is_final = self.symbols[name]
            if is_final:
                return False, True   # exists, is final
            self.symbols[name] = (value, False)
            return True, False       # assigned, not final
        if self.parent:
            return self.parent.assign(name, value)
        return False, False          # not found

# ── Lumen Value types ─────────────────────────────────────────────────────────

class LumenValue:
    def __init__(self, pos_start=None, pos_end=None, context=None):
        self.pos_start = pos_start
        self.pos_end   = pos_end
        self.context   = context

    def set_pos(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end   = pos_end
        return self

    def set_context(self, context):
        self.context = context
        return self

    def illegal_op(self, other=None):
        return RuntimeError(
            self.pos_start, (other or self).pos_end,
            f"Illegal operation on {type(self).__name__}",
            self.context
        )


class LumenNumber(LumenValue):
    def __init__(self, value):
        super().__init__()
        self.value = value

    # arithmetic
    def added_to(self, other):
        if isinstance(other, LumenNumber):
            return LumenNumber(self.value + other.value).set_context(self.context), None
        return None, self.illegal_op(other)

    def subbed_by(self, other):
        if isinstance(other, LumenNumber):
            return LumenNumber(self.value - other.value).set_context(self.context), None
        return None, self.illegal_op(other)

    def multed_by(self, other):
        if isinstance(other, LumenNumber):
            return LumenNumber(self.value * other.value).set_context(self.context), None
        return None, self.illegal_op(other)

    def dived_by(self, other):
        if isinstance(other, LumenNumber):
            if other.value == 0:
                return None, LumenRuntimeError(
                    other.pos_start, other.pos_end,
                    "Division by zero", self.context
                )
            result = self.value / other.value
            # keep int if both were ints and result is whole
            if isinstance(self.value, int) and isinstance(other.value, int) and result == int(result):
                result = int(result)
            return LumenNumber(result).set_context(self.context), None
        return None, self.illegal_op(other)

    # comparison
    def get_comparison(self, op, other):
        if isinstance(other, LumenNumber):
            ops = {
                TT_EQEQ: lambda a, b: a == b,
                TT_NEQ:  lambda a, b: a != b,
                TT_LT:   lambda a, b: a <  b,
                TT_GT:   lambda a, b: a >  b,
                TT_LTE:  lambda a, b: a <= b,
                TT_GTE:  lambda a, b: a >= b,
            }
            return LumenBool(ops[op](self.value, other.value)).set_context(self.context), None
        return None, self.illegal_op(other)

    def is_truthy(self):
        return self.value != 0

    def __repr__(self):
        return str(self.value)


class LumenString(LumenValue):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, LumenString):
            return LumenString(self.value + other.value).set_context(self.context), None
        return None, self.illegal_op(other)

    def get_comparison(self, op, other):
        if isinstance(other, LumenString):
            ops = {
                TT_EQEQ: lambda a, b: a == b,
                TT_NEQ:  lambda a, b: a != b,
            }
            if op not in ops:
                return None, self.illegal_op(other)
            return LumenBool(ops[op](self.value, other.value)).set_context(self.context), None
        return None, self.illegal_op(other)

    def is_truthy(self):
        return len(self.value) > 0

    def __repr__(self):
        return self.value


class LumenBool(LumenValue):
    def __init__(self, value):
        super().__init__()
        self.value = bool(value)

    def get_comparison(self, op, other):
        if isinstance(other, LumenBool):
            ops = {
                TT_EQEQ: lambda a, b: a == b,
                TT_NEQ:  lambda a, b: a != b,
            }
            if op not in ops:
                return None, self.illegal_op(other)
            return LumenBool(ops[op](self.value, other.value)).set_context(self.context), None
        return None, self.illegal_op(other)

    def is_truthy(self):
        return self.value

    def __repr__(self):
        return 'true' if self.value else 'false'


class LumenChar(LumenValue):
    def __init__(self, value):
        super().__init__()
        self.value = value  # single character string

    def get_comparison(self, op, other):
        if isinstance(other, LumenChar):
            ops = {
                TT_EQEQ: lambda a, b: a == b,
                TT_NEQ:  lambda a, b: a != b,
                TT_LT:   lambda a, b: a <  b,
                TT_GT:   lambda a, b: a >  b,
                TT_LTE:  lambda a, b: a <= b,
                TT_GTE:  lambda a, b: a >= b,
            }
            return LumenBool(ops[op](self.value, other.value)).set_context(self.context), None
        return None, self.illegal_op(other)

    def is_truthy(self):
        return True

    def __repr__(self):
        return f"\'{self.value}\'"


class LumenArray(LumenValue):
    ZERO_VALUES = {
        'int':    lambda: LumenNumber(0),
        'float':  lambda: LumenNumber(0.0),
        'bool':   lambda: LumenBool(False),
        'string': lambda: LumenString(''),
        'char':   lambda: LumenChar('\0'),
    }
    TYPE_CHECKS = {
        'int':    lambda v: isinstance(v, LumenNumber) and isinstance(v.value, int),
        'float':  lambda v: isinstance(v, LumenNumber),
        'bool':   lambda v: isinstance(v, LumenBool),
        'string': lambda v: isinstance(v, LumenString),
        'char':   lambda v: isinstance(v, LumenChar),
    }

    def __init__(self, element_type, size, elements):
        super().__init__()
        self.element_type = element_type
        self.is_fixed     = size is not None
        self.size         = size

        zero = self.ZERO_VALUES[element_type]
        if self.is_fixed:
            self.elements = [zero() for _ in range(size)]
            for i, el in enumerate(elements[:size]):
                self.elements[i] = el
        else:
            self.elements = list(elements)

    def check_type(self, value):
        return self.TYPE_CHECKS[self.element_type](value)

    def get_at(self, index, pos_start, pos_end, context):
        if index < 0 or index >= len(self.elements):
            return None, LumenRuntimeError(pos_start, pos_end,
                f"Index {index} out of bounds (size {len(self.elements)})", context)
        return self.elements[index], None

    def set_at(self, index, value, pos_start, pos_end, context):
        if self.is_fixed and (index < 0 or index >= self.size):
            return RuntimeError(pos_start, pos_end,
                f"Index {index} out of bounds (size {self.size})", context)
        if not self.check_type(value):
            return RuntimeError(pos_start, pos_end,
                f"Type mismatch: array is of type '{self.element_type}'", context)
        if self.is_fixed:
            self.elements[index] = value
        else:
            if index < 0 or index >= len(self.elements):
                return RuntimeError(pos_start, pos_end,
                    f"Index {index} out of bounds (size {len(self.elements)})", context)
            self.elements[index] = value
        return None

    def is_truthy(self):
        return len(self.elements) > 0

    def __repr__(self):
        return '{' + ', '.join(repr(e) for e in self.elements) + '}'


class LumenFunction(LumenValue):
    def __init__(self, name, param_names, body_nodes, context):
        super().__init__()
        self.name        = name
        self.param_names = param_names
        self.body_nodes  = body_nodes
        self.def_context = context   # closure: capture definition scope

    def execute(self, args, call_pos_start, call_pos_end):
        res        = RuntimeResult()
        interp     = Interpreter()
        fn_context = Context(self.name, self.def_context, call_pos_start)

        if len(args) != len(self.param_names):
            return res.failure(LumenRuntimeError(
                call_pos_start, call_pos_end,
                f"'{self.name}' expects {len(self.param_names)} argument(s), got {len(args)}",
                fn_context
            ))

        for name, value in zip(self.param_names, args):
            fn_context.symbol_table.set(name, value)

        for node in self.body_nodes:
            rt = interp.visit(node, fn_context)
            if rt.error: return rt
            if rt.throw_value is not None:
                return RuntimeResult().success_throw(rt.throw_value)
            if rt.return_value is not None:
                return RuntimeResult().success(rt.return_value)

        return res.success(LumenNumber(0))   # implicit return 0

    def __repr__(self):
        return f'<func {self.name}>'


class LumenBuiltin(LumenValue):
    def __init__(self, name, fn):
        super().__init__()
        self.name = name
        self.fn   = fn

    def execute(self, args, call_pos_start, call_pos_end):
        res = RuntimeResult()
        try:
            result = self.fn(args, call_pos_start, call_pos_end, self.context)
            return res.success(result)
        except LumenRuntimeError as e:
            return res.failure(e)

    def __repr__(self):
        return f'<builtin {self.name}>'

# ── Built-in functions ────────────────────────────────────────────────────────

def _require_args(name, args, count, pos_start, pos_end, context):
    if len(args) != count:
        raise LumenRuntimeError(pos_start, pos_end,
            f"'{name}' expects {count} argument(s), got {len(args)}", context)

def _lumen_val_to_str(val):
    if isinstance(val, (LumenString, LumenChar)):
        return val.value
    elif isinstance(val, LumenBool):
        return 'true' if val.value else 'false'
    elif isinstance(val, LumenNumber):
        return str(val.value)
    elif isinstance(val, LumenArray):
        return '{' + ', '.join(_lumen_val_to_str(e) for e in val.elements) + '}'
    return repr(val)

def builtin_print(args, pos_start, pos_end, context):
    if len(args) == 0:
        raise LumenRuntimeError(pos_start, pos_end, "'print' expects at least 1 argument", context)
    print(''.join(_lumen_val_to_str(a) for a in args), end='')
    return LumenNumber(0)

def builtin_length(args, pos_start, pos_end, context):
    _require_args('length', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenString):
        raise LumenRuntimeError(pos_start, pos_end, "'length' expects a string", context)
    return LumenNumber(len(args[0].value))

def builtin_upper(args, pos_start, pos_end, context):
    _require_args('upper', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenString):
        raise LumenRuntimeError(pos_start, pos_end, "'upper' expects a string", context)
    return LumenString(args[0].value.upper())

def builtin_lower(args, pos_start, pos_end, context):
    _require_args('lower', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenString):
        raise LumenRuntimeError(pos_start, pos_end, "'lower' expects a string", context)
    return LumenString(args[0].value.lower())

def builtin_substr(args, pos_start, pos_end, context):
    _require_args('substr', args, 3, pos_start, pos_end, context)
    s, a, b = args
    if not isinstance(s, LumenString):
        raise LumenRuntimeError(pos_start, pos_end, "'substr' expects a string as first argument", context)
    if not isinstance(a, LumenNumber) or not isinstance(b, LumenNumber):
        raise LumenRuntimeError(pos_start, pos_end, "'substr' expects numbers as second and third arguments", context)
    return LumenString(s.value[int(a.value):int(b.value)])

def builtin_str(args, pos_start, pos_end, context):
    _require_args('str', args, 1, pos_start, pos_end, context)
    if isinstance(args[0], LumenChar):
        return LumenString(args[0].value)
    return LumenString(repr(args[0]))

def builtin_num(args, pos_start, pos_end, context):
    _require_args('num', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenString):
        raise LumenRuntimeError(pos_start, pos_end, "'num' expects a string", context)
    try:
        val = float(args[0].value)
        return LumenNumber(int(val) if val == int(val) else val)
    except ValueError:
        raise LumenRuntimeError(pos_start, pos_end, f"Cannot convert '{args[0].value}' to number", context)

def builtin_push(args, pos_start, pos_end, context):
    _require_args('push', args, 2, pos_start, pos_end, context)
    arr, val = args
    if not isinstance(arr, LumenArray):
        raise LumenRuntimeError(pos_start, pos_end, "'push' expects an array as first argument", context)
    if arr.is_fixed:
        raise LumenRuntimeError(pos_start, pos_end, "Cannot push to a fixed-size array", context)
    if not arr.check_type(val):
        raise LumenRuntimeError(pos_start, pos_end, f"Type mismatch: array is of type '{arr.element_type}'", context)
    arr.elements.append(val)
    return LumenNumber(0)

def builtin_pop(args, pos_start, pos_end, context):
    _require_args('pop', args, 1, pos_start, pos_end, context)
    arr = args[0]
    if not isinstance(arr, LumenArray):
        raise LumenRuntimeError(pos_start, pos_end, "'pop' expects an array", context)
    if arr.is_fixed:
        raise LumenRuntimeError(pos_start, pos_end, "Cannot pop from a fixed-size array", context)
    if len(arr.elements) == 0:
        raise LumenRuntimeError(pos_start, pos_end, "Cannot pop from empty array", context)
    return arr.elements.pop()

def builtin_dequeue(args, pos_start, pos_end, context):
    _require_args('dequeue', args, 1, pos_start, pos_end, context)
    arr = args[0]
    if not isinstance(arr, LumenArray):
        raise LumenRuntimeError(pos_start, pos_end, "'dequeue' expects an array", context)
    if arr.is_fixed:
        raise LumenRuntimeError(pos_start, pos_end, "Cannot dequeue from a fixed-size array", context)
    if len(arr.elements) == 0:
        raise LumenRuntimeError(pos_start, pos_end, "Cannot dequeue from empty array", context)
    return arr.elements.pop(0)

def builtin_isalpha(args, pos_start, pos_end, context):
    _require_args('isalpha', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenChar):
        raise LumenRuntimeError(pos_start, pos_end, "'isalpha' expects a char", context)
    return LumenBool(args[0].value.isalpha())

def builtin_isdigit(args, pos_start, pos_end, context):
    _require_args('isdigit', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenChar):
        raise LumenRuntimeError(pos_start, pos_end, "'isdigit' expects a char", context)
    return LumenBool(args[0].value.isdigit())

def builtin_charcode(args, pos_start, pos_end, context):
    """charcode('A') -> 65"""
    _require_args('charcode', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenChar):
        raise LumenRuntimeError(pos_start, pos_end, "'charcode' expects a char", context)
    return LumenNumber(ord(args[0].value))

def builtin_tochar(args, pos_start, pos_end, context):
    """tochar(65) -> 'A'"""
    _require_args('tochar', args, 1, pos_start, pos_end, context)
    if not isinstance(args[0], LumenNumber):
        raise LumenRuntimeError(pos_start, pos_end, "'tochar' expects a number", context)
    return LumenChar(chr(int(args[0].value)))

def builtin_input(args, pos_start, pos_end, context):
    if len(args) > 2:
        raise LumenRuntimeError(pos_start, pos_end, "'input' expects at most 2 arguments", context)

    prompt = ''
    type_name = 'string'

    if len(args) >= 1:
        if not isinstance(args[0], LumenString):
            raise LumenRuntimeError(pos_start, pos_end, "'input' first argument must be a string prompt", context)
        prompt = args[0].value

    if len(args) == 2:
        if not isinstance(args[1], LumenType):
            raise LumenRuntimeError(pos_start, pos_end, "'input' second argument must be a type (int, float, bool, string, char)", context)
        type_name = args[1].name

    try:
        raw = input(prompt)
    except EOFError:
        raw = ''

    if type_name == 'string':
        return LumenString(raw)
    elif type_name == 'int':
        try:
            return LumenNumber(int(raw))
        except ValueError:
            raise LumenRuntimeError(pos_start, pos_end, f"Cannot convert '{raw}' to int", context)
    elif type_name == 'float':
        try:
            return LumenNumber(float(raw))
        except ValueError:
            raise LumenRuntimeError(pos_start, pos_end, f"Cannot convert '{raw}' to float", context)
    elif type_name == 'bool':
        if raw.lower() == 'true':  return LumenBool(True)
        if raw.lower() == 'false': return LumenBool(False)
        raise LumenRuntimeError(pos_start, pos_end, f"Cannot convert '{raw}' to bool — use 'true' or 'false'", context)
    elif type_name == 'char':
        if len(raw) == 0:
            raise LumenRuntimeError(pos_start, pos_end, "Cannot convert empty input to char", context)
        return LumenChar(raw[0])
    return LumenString(raw)

def builtin_length_extended(args, pos_start, pos_end, context):
    _require_args('length', args, 1, pos_start, pos_end, context)
    if isinstance(args[0], LumenString):
        return LumenNumber(len(args[0].value))
    if isinstance(args[0], LumenArray):
        return LumenNumber(len(args[0].elements))
    raise LumenRuntimeError(pos_start, pos_end, "'length' expects a string or array", context)

BUILTINS = {
    'print':   builtin_print,
    'length':  builtin_length_extended,
    'upper':   builtin_upper,
    'lower':   builtin_lower,
    'substr':  builtin_substr,
    'str':     builtin_str,
    'num':     builtin_num,
    'input':    builtin_input,
    'push':     builtin_push,
    'pop':      builtin_pop,
    'dequeue':  builtin_dequeue,
    'isalpha':  builtin_isalpha,
    'isdigit':  builtin_isdigit,
    'charcode': builtin_charcode,
    'tochar':   builtin_tochar,
}

# ── Global symbol table ───────────────────────────────────────────────────────

class LumenType(LumenValue):
    """Sentinel value representing a type name e.g. int, float, char"""
    def __init__(self, name):
        super().__init__()
        self.name = name
    def is_truthy(self): return True
    def __repr__(self): return f'<type {self.name}>'

def make_global_table():
    table = SymbolTable()
    for name, fn in BUILTINS.items():
        table.set(name, LumenBuiltin(name, fn))
    table.set('true',   LumenBool(True))
    table.set('false',  LumenBool(False))
    # type sentinels for use as arguments
    for t in ('int', 'float', 'bool', 'string', 'char'):
        table.set(t, LumenType(t))
    return table

GLOBAL_TABLE = make_global_table()

# ── Interpreter ───────────────────────────────────────────────────────────────

class Interpreter:
    def visit(self, node, context):
        method = f'visit_{type(node).__name__}'
        fn     = getattr(self, method, self.no_visit)
        return fn(node, context)

    def no_visit(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    # ── Literals ──────────────────────────────────────────────────────────────

    def visit_NumberNode(self, node, context):
        return RuntimeResult().success(
            LumenNumber(node.tok.value)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )

    def visit_StringNode(self, node, context):
        return RuntimeResult().success(
            LumenString(node.tok.value)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )

    def visit_BoolNode(self, node, context):
        return RuntimeResult().success(
            LumenBool(node.tok.value == 'true')
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )

    def visit_CharNode(self, node, context):
        return RuntimeResult().success(
            LumenChar(node.tok.value)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )

    # ── Variables ─────────────────────────────────────────────────────────────

    def visit_VarAccessNode(self, node, context):
        res      = RuntimeResult()
        name     = node.var_name_tok.value
        entry    = context.symbol_table.get(name)

        if entry is None:
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                f"'{name}' is not defined",
                context
            ))
        value, _ = entry
        value = value.set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)

    def visit_VarAssignNode(self, node, context):
        res      = RuntimeResult()
        name     = node.var_name_tok.value
        value    = res.register(self.visit(node.value_node, context))
        if res.error: return res

        # Check if already declared as final in this scope
        existing = context.symbol_table.get(name)
        if existing is not None:
            _, is_final = existing
            if is_final:
                return res.failure(LumenRuntimeError(
                    node.pos_start, node.pos_end,
                    f"Cannot reassign final variable '{name}'",
                    context
                ))

        context.symbol_table.set(name, value, node.is_final)
        return res.success(value)

    def visit_VarReassignNode(self, node, context):
        res  = RuntimeResult()
        name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error: return res

        entry = context.symbol_table.get(name)
        if entry is None:
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                f"'{name}' is not defined. Use 'let' to declare it first.",
                context
            ))
        _, is_final = entry
        if is_final:
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                f"Cannot reassign final variable '{name}'",
                context
            ))
        context.symbol_table.set(name, value, False)
        return res.success(value)

    # ── Operations ────────────────────────────────────────────────────────────

    def visit_BinOpNode(self, node, context):
        res   = RuntimeResult()
        left  = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        op    = node.op_tok.type
        kw    = node.op_tok.value if node.op_tok.type == TT_KEYWORD else None
        error = None
        result = None

        if op == TT_PLUS:
            result, error = left.added_to(right)
        elif op == TT_MINUS:
            result, error = left.subbed_by(right)
        elif op == TT_MUL:
            result, error = left.multed_by(right)
        elif op == TT_DIV:
            result, error = left.dived_by(right)
        elif op in (TT_EQEQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE):
            result, error = left.get_comparison(op, right)
        elif kw == 'and':
            result = LumenBool(left.is_truthy() and right.is_truthy()).set_context(context)
        elif kw == 'or':
            result = LumenBool(left.is_truthy() or right.is_truthy()).set_context(context)

        if error:
            return res.failure(error)
        return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res   = RuntimeResult()
        value = res.register(self.visit(node.node, context))
        if res.error: return res

        op    = node.op_tok.type
        kw    = node.op_tok.value if node.op_tok.type == TT_KEYWORD else None
        error = None

        if op == TT_MINUS:
            value, error = value.subbed_by(LumenNumber(0)) if False else \
                           (LumenNumber(-value.value).set_context(context) if isinstance(value, LumenNumber) else (None, value.illegal_op()))
        elif op == TT_PLUS:
            pass  # no-op
        elif kw == 'not':
            value = LumenBool(not value.is_truthy()).set_context(context)

        if error:
            return res.failure(error)
        return res.success(value.set_pos(node.pos_start, node.pos_end))

    # ── Control flow ──────────────────────────────────────────────────────────

    def visit_IfNode(self, node, context):
        res = RuntimeResult()

        for condition, body in node.cases:
            cond_val = res.register(self.visit(condition, context))
            if res.error: return res

            if cond_val.is_truthy():
                for stmt in body:
                    res.register(self.visit(stmt, context))
                    if res.should_return(): return res
                return res.success(LumenNumber(0))

        if node.else_case:
            for stmt in node.else_case:
                res.register(self.visit(stmt, context))
                if res.should_return(): return res

        return res.success(LumenNumber(0))

    def visit_ForRangeNode(self, node, context):
        res   = RuntimeResult()
        start = res.register(self.visit(node.start_node, context))
        if res.error: return res
        end   = res.register(self.visit(node.end_node, context))
        if res.error: return res

        if not isinstance(start, LumenNumber) or not isinstance(end, LumenNumber):
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                "Range bounds must be numbers", context
            ))

        for i in range(int(start.value), int(end.value) + 1):
            context.symbol_table.set(node.var_name_tok.value, LumenNumber(i))
            for stmt in node.body_nodes:
                res.register(self.visit(stmt, context))
                if res.should_return(): return res

        return res.success(LumenNumber(0))

    def visit_ForEachNode(self, node, context):
        res = RuntimeResult()
        arr = res.register(self.visit(node.array_node, context))
        if res.error: return res

        # iterate over string as chars
        if isinstance(arr, LumenString):
            for ch in arr.value:
                context.symbol_table.set(node.var_name_tok.value, LumenChar(ch))
                for stmt in node.body_nodes:
                    res.register(self.visit(stmt, context))
                    if res.should_return(): return res
            return res.success(LumenNumber(0))

        if not isinstance(arr, LumenArray):
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                "Can only use 'for item in' with an array or string", context
            ))

        for element in arr.elements:
            context.symbol_table.set(node.var_name_tok.value, element)
            for stmt in node.body_nodes:
                res.register(self.visit(stmt, context))
                if res.should_return(): return res

        return res.success(LumenNumber(0))

    def visit_ForCStyleNode(self, node, context):
        res = RuntimeResult()
        res.register(self.visit(node.init_node, context))
        if res.error: return res

        while True:
            cond = res.register(self.visit(node.condition_node, context))
            if res.error: return res
            if not cond.is_truthy(): break

            for stmt in node.body_nodes:
                res.register(self.visit(stmt, context))
                if res.should_return(): return res

            res.register(self.visit(node.step_node, context))
            if res.error: return res

        return res.success(LumenNumber(0))

    def visit_WhileNode(self, node, context):
        res = RuntimeResult()

        while True:
            cond = res.register(self.visit(node.condition_node, context))
            if res.error: return res
            if not cond.is_truthy(): break

            for stmt in node.body_nodes:
                res.register(self.visit(stmt, context))
                if res.should_return(): return res

        return res.success(LumenNumber(0))

    def visit_DoWhileNode(self, node, context):
        res = RuntimeResult()

        while True:
            for stmt in node.body_nodes:
                res.register(self.visit(stmt, context))
                if res.should_return(): return res

            cond = res.register(self.visit(node.condition_node, context))
            if res.error: return res
            if not cond.is_truthy(): break

        return res.success(LumenNumber(0))

    # ── Functions ─────────────────────────────────────────────────────────────

    def visit_FuncDefNode(self, node, context):
        res       = RuntimeResult()
        name      = node.func_name_tok.value
        params    = [tok.value for tok in node.param_toks]
        func_val  = LumenFunction(name, params, node.body_nodes, context) \
                    .set_pos(node.pos_start, node.pos_end) \
                    .set_context(context)
        context.symbol_table.set(name, func_val)
        return res.success(func_val)

    def visit_CallNode(self, node, context):
        res      = RuntimeResult()
        callee   = res.register(self.visit(node.node_to_call, context))
        if res.error: return res

        args = []
        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error: return res

        callee = callee.set_context(context)

        if isinstance(callee, (LumenFunction, LumenBuiltin)):
            result = res.register(callee.execute(args, node.pos_start, node.pos_end))
            if res.error: return res
            return res.success(result)

        return res.failure(LumenRuntimeError(
            node.pos_start, node.pos_end,
            f"'{callee}' is not callable", context
        ))

    def visit_ArrayLiteralNode(self, node, context):
        res = RuntimeResult()
        TYPE_MAP = {
            'int':    (LumenNumber, int),
            'float':  (LumenNumber, float),
            'bool':   (LumenBool,   None),
            'string': (LumenString, None),
            'char':   (LumenChar,   None),
        }
        lumen_type, _ = TYPE_MAP[node.element_type]

        # evaluate and type-check each element
        evaluated = []
        for el_node in node.element_nodes:
            val = res.register(self.visit(el_node, context))
            if res.error: return res

            # type check
            arr_tmp = LumenArray(node.element_type, None, [])
            if not arr_tmp.check_type(val):
                return res.failure(LumenRuntimeError(
                    el_node.pos_start, el_node.pos_end,
                    f"Type mismatch: expected '{node.element_type}' in array",
                    context
                ))
            evaluated.append(val)

        # fixed size
        size = None
        if node.size_node:
            size = node.size_node.tok.value
            if len(evaluated) > size:
                return res.failure(LumenRuntimeError(
                    node.pos_start, node.pos_end,
                    f"Too many elements: array size is {size} but got {len(evaluated)}",
                    context
                ))

        arr = LumenArray(node.element_type, size, evaluated)
        arr.set_pos(node.pos_start, node.pos_end).set_context(context)

        existing = context.symbol_table.get(node.var_name_tok.value)
        if existing is not None:
            _, is_final = existing
            if is_final:
                return res.failure(LumenRuntimeError(
                    node.pos_start, node.pos_end,
                    f"Cannot reassign final variable '{node.var_name_tok.value}'",
                    context
                ))

        context.symbol_table.set(node.var_name_tok.value, arr, node.is_final)
        return res.success(arr)

    def visit_ArrayAccessNode(self, node, context):
        res = RuntimeResult()
        arr = res.register(self.visit(node.array_node, context))
        if res.error: return res
        idx = res.register(self.visit(node.index_node, context))
        if res.error: return res

        if not isinstance(idx, LumenNumber):
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                "Index must be a number", context
            ))

        # String indexing — returns a LumenChar
        if isinstance(arr, LumenString):
            i = int(idx.value)
            if i < 0 or i >= len(arr.value):
                return res.failure(LumenRuntimeError(
                    node.pos_start, node.pos_end,
                    f"Index {i} out of bounds (string length {len(arr.value)})", context
                ))
            return res.success(
                LumenChar(arr.value[i]).set_pos(node.pos_start, node.pos_end).set_context(context)
            )

        if not isinstance(arr, LumenArray):
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                "Cannot use 'at' on a non-array or non-string value", context
            ))

        val, error = arr.get_at(int(idx.value), node.pos_start, node.pos_end, context)
        if error: return res.failure(error)
        return res.success(val.set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_ArrayAssignNode(self, node, context):
        res  = RuntimeResult()
        name = node.array_name_tok.value

        entry = context.symbol_table.get(name)
        if entry is None:
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                f"'{name}' is not defined", context
            ))
        arr, is_final = entry
        if is_final:
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                f"Cannot modify final array '{name}'", context
            ))
        # String index assignment
        if isinstance(arr, LumenString):
            idx = res.register(self.visit(node.index_node, context))
            if res.error: return res
            val = res.register(self.visit(node.value_node, context))
            if res.error: return res
            if not isinstance(val, LumenChar):
                return res.failure(LumenRuntimeError(
                    node.pos_start, node.pos_end,
                    "Can only assign a char to a string index", context
                ))
            i = int(idx.value)
            s = list(arr.value)
            if i < 0 or i >= len(s):
                return res.failure(LumenRuntimeError(
                    node.pos_start, node.pos_end,
                    f"Index {i} out of bounds (string length {len(s)})", context
                ))
            s[i] = val.value
            new_str = LumenString(''.join(s)).set_context(context)
            context.symbol_table.set(name, new_str, is_final)
            return res.success(val)

        if not isinstance(arr, LumenArray):
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                f"'{name}' is not an array", context
            ))

        idx = res.register(self.visit(node.index_node, context))
        if res.error: return res
        val = res.register(self.visit(node.value_node, context))
        if res.error: return res

        error = arr.set_at(int(idx.value), val, node.pos_start, node.pos_end, context)
        if error: return res.failure(error)
        return res.success(val)

    def visit_ThrowNode(self, node, context):
        res = RuntimeResult()
        value = res.register(self.visit(node.expr_node, context))
        if res.error: return res

        # throw value must be a string
        if not isinstance(value, LumenString):
            return res.failure(LumenRuntimeError(
                node.pos_start, node.pos_end,
                "'throw' expects a string message", context
            ))
        return res.success_throw(value.value)

    def visit_TryCatchNode(self, node, context):
        res = RuntimeResult()

        # ── run try body ──────────────────────────────────────────────────────
        caught_message = None

        for stmt in node.try_body:
            rt = self.visit(stmt, context)

            # runtime error from interpreter — catch it
            if rt.error:
                caught_message = rt.error.details
                break

            # throw from Lumen code — catch it
            if rt.throw_value is not None:
                caught_message = rt.throw_value
                break

            # return propagates out normally — don't catch
            if rt.return_value is not None:
                # still run always block first
                if node.always_body:
                    for s in node.always_body:
                        res.register(self.visit(s, context))
                        if res.error: return res
                return RuntimeResult().success_return(rt.return_value)

        # ── on error block ────────────────────────────────────────────────────
        if caught_message is not None:
            catch_context = Context('catch', context, node.pos_start)
            catch_context.symbol_table = SymbolTable(context.symbol_table)
            catch_context.symbol_table.set(node.err_name_tok.value, LumenString(caught_message))

            for stmt in node.catch_body:
                res.register(self.visit(stmt, catch_context))
                if res.should_return(): break

        # ── always block ──────────────────────────────────────────────────────
        if node.always_body:
            for stmt in node.always_body:
                res.register(self.visit(stmt, context))
                if res.error: return res

        return res.success(LumenNumber(0))

    def visit_ReturnNode(self, node, context):
        res = RuntimeResult()
        if node.return_node:
            value = res.register(self.visit(node.return_node, context))
            if res.error: return res
            return res.success_return(value)
        return res.success_return(LumenNumber(0))