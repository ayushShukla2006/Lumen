from Lexer import (
    TT_LBRACE, TT_RBRACE, TT_LBRACKET, TT_RBRACKET, TT_CHAR,
    TT_INT, TT_FLOAT, TT_STRING, TT_IDENTIFIER, TT_KEYWORD,
    TT_PLUS, TT_MINUS, TT_MUL, TT_DIV,
    TT_EQ, TT_EQEQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE,
    TT_LPAREN, TT_RPAREN, TT_COMMA, TT_NEWLINE, TT_EOF,
)
from Nodes import (
    ArrayLiteralNode, ArrayAccessNode, ArrayAssignNode,
    VarReassignNode, ForEachNode, CharNode,
    ThrowNode, TryCatchNode,
    NumberNode, StringNode, BoolNode,
    VarAccessNode, VarAssignNode,
    BinOpNode, UnaryOpNode,
    IfNode, ForRangeNode, ForCStyleNode, WhileNode, DoWhileNode,
    FuncDefNode, CallNode, ReturnNode,
)
from Errors import InvalidSyntaxError

# ── Parse Result ─────────────────────────────────────────────────────────────

class ParseResult:
    def __init__(self):
        self.error          = None
        self.node           = None
        self.advance_count  = 0

    def register_advancement(self):
        self.advance_count += 1

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error:
                self.error = res.error
            self.advance_count += res.advance_count
            return res.node
        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

# ── Parser ───────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens      = tokens
        self.tok_idx     = -1
        self.current_tok = None
        self.advance()

    # ── Navigation ───────────────────────────────────────────────────────────

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def peek(self, offset=1):
        idx = self.tok_idx + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def skip_newlines(self, res):
        while self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

    # ── Entry point ───────────────────────────────────────────────────────────

    def parse(self):
        res = self.statements()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Unexpected token"
            ))
        return res

    # ── Statement list ────────────────────────────────────────────────────────

    def statements(self):
        """Parse a sequence of statements separated by newlines."""
        res   = ParseResult()
        nodes = []
        self.skip_newlines(res)

        node = res.register(self.statement())
        if res.error: return res
        nodes.append(node)

        while True:
            # require at least one newline between statements
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1

            if newline_count == 0:
                break

            # stop if we hit a block-closing keyword or EOF
            if self.current_tok.type == TT_EOF:
                break
            if self.current_tok.matches(TT_KEYWORD, 'end'):
                break
            if self.current_tok.matches(TT_KEYWORD, 'else'):
                break
            if self.current_tok.matches(TT_KEYWORD, 'elseif'):
                break
            if self.current_tok.matches(TT_KEYWORD, 'while') and self._in_do_while:
                break
            if self.current_tok.matches(TT_KEYWORD, 'on'):
                break
            if self.current_tok.matches(TT_KEYWORD, 'always'):
                break

            node = res.register(self.statement())
            if res.error: return res
            nodes.append(node)

        return res.success(nodes)

    # ── Single statement ──────────────────────────────────────────────────────

    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start

        # throw
        if self.current_tok.matches(TT_KEYWORD, 'throw'):
            res.register_advancement(); self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(ThrowNode(expr, pos_start, self.current_tok.pos_end))

        # try
        if self.current_tok.matches(TT_KEYWORD, 'try'):
            node = res.register(self.try_expr())
            if res.error: return res
            return res.success(node)

        # return
        if self.current_tok.matches(TT_KEYWORD, 'return'):
            res.register_advancement(); self.advance()
            # optional expression on same line
            if self.current_tok.type not in (TT_NEWLINE, TT_EOF):
                expr = res.register(self.expr())
                if res.error: return res
                return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_end))
            return res.success(ReturnNode(None, pos_start, self.current_tok.pos_end))

        # if
        if self.current_tok.matches(TT_KEYWORD, 'if'):
            node = res.register(self.if_expr())
            if res.error: return res
            return res.success(node)

        # for
        if self.current_tok.matches(TT_KEYWORD, 'for'):
            node = res.register(self.for_expr())
            if res.error: return res
            return res.success(node)

        # while
        if self.current_tok.matches(TT_KEYWORD, 'while'):
            node = res.register(self.while_expr())
            if res.error: return res
            return res.success(node)

        # do
        if self.current_tok.matches(TT_KEYWORD, 'do'):
            node = res.register(self.do_while_expr())
            if res.error: return res
            return res.success(node)

        # func
        if self.current_tok.matches(TT_KEYWORD, 'func'):
            node = res.register(self.func_def())
            if res.error: return res
            return res.success(node)

        # let / final let
        if self.current_tok.matches(TT_KEYWORD, 'let') or \
           self.current_tok.matches(TT_KEYWORD, 'final'):
            node = res.register(self.var_assign())
            if res.error: return res
            return res.success(node)

        # bare reassignment: identifier = expr
        if self.current_tok.type == TT_IDENTIFIER and self.peek().type == TT_EQ:
            var_name = self.current_tok
            res.register_advancement(); self.advance()  # consume identifier
            res.register_advancement(); self.advance()  # consume =
            value = res.register(self.expr())
            if res.error: return res
            return res.success(VarReassignNode(var_name, value, pos_start, self.current_tok.pos_end))

        expr = res.register(self.expr())
        if res.error: return res
        return res.success(expr)

    # ── Variable assignment ───────────────────────────────────────────────────

    def var_assign(self):
        res       = ParseResult()
        is_final  = False
        pos_start = self.current_tok.pos_start

        if self.current_tok.matches(TT_KEYWORD, 'final'):
            is_final = True
            res.register_advancement(); self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'let'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'let' after 'final'"
            ))
        res.register_advancement(); self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected identifier"
            ))
        var_name = self.current_tok
        res.register_advancement(); self.advance()

        # Array declaration: let name of type[size] = {...}  or  let name of type[] = {...}
        if self.current_tok.matches(TT_KEYWORD, 'of'):
            return self.array_declare(var_name, is_final, pos_start, res)

        if self.current_tok.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '=' or 'of'"
            ))
        res.register_advancement(); self.advance()

        value = res.register(self.expr())
        if res.error: return res
        return res.success(VarAssignNode(var_name, value, is_final))

    def array_declare(self, var_name, is_final, pos_start, res):
        VALID_TYPES = ('int', 'float', 'bool', 'string', 'char')

        # consume 'of'
        res.register_advancement(); self.advance()

        # type name
        if self.current_tok.value not in VALID_TYPES:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected type: int, float, bool, string, or char"
            ))
        element_type = self.current_tok.value
        res.register_advancement(); self.advance()

        # [size] or []
        if self.current_tok.type != TT_LBRACKET:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '['"
            ))
        res.register_advancement(); self.advance()

        size_node = None
        if self.current_tok.type == TT_INT:
            size_node = NumberNode(self.current_tok)
            res.register_advancement(); self.advance()

        if self.current_tok.type != TT_RBRACKET:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ']'"
            ))
        res.register_advancement(); self.advance()

        # = { elements }
        if self.current_tok.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '='"
            ))
        res.register_advancement(); self.advance()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))
        res.register_advancement(); self.advance()

        elements = []
        if self.current_tok.type != TT_RBRACE:
            elements.append(res.register(self.expr()))
            if res.error: return res
            while self.current_tok.type == TT_COMMA:
                res.register_advancement(); self.advance()
                elements.append(res.register(self.expr()))
                if res.error: return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}'"
            ))
        pos_end = self.current_tok.pos_end
        res.register_advancement(); self.advance()

        return res.success(ArrayLiteralNode(
            var_name, element_type, size_node, elements, is_final, pos_start, pos_end
        ))

    # ── Expressions ───────────────────────────────────────────────────────────

    def expr(self):
        """Handles: comparison (and|or comparison)*"""
        return self.bin_op(
            self.comparison,
            ops_kw=['and', 'or']
        )

    def comparison(self):
        """Handles: arith (== != < > <= >=) arith  |  not comparison"""
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'not'):
            op_tok = self.current_tok
            res.register_advancement(); self.advance()
            node = res.register(self.comparison())
            if res.error: return res
            return res.success(UnaryOpNode(op_tok, node))

        return self.bin_op(
            self.arith_expr,
            ops_tt=[TT_EQEQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE]
        )

    def arith_expr(self):
        """Handles: term ((+ | -) term)*"""
        return self.bin_op(self.term, ops_tt=[TT_PLUS, TT_MINUS])

    def term(self):
        """Handles: factor ((* | /) factor)*"""
        return self.bin_op(self.factor, ops_tt=[TT_MUL, TT_DIV])

    def factor(self):
        """Handles: unary +/-, atoms, parentheses"""
        res = ParseResult()
        tok = self.current_tok

        # unary + / -
        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_advancement(); self.advance()
            f = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, f))

        return self.call()

    def call(self):
        """Handles: atom (arg_list)?  |  atom at index  |  atom at index = value"""
        res       = ParseResult()
        atom      = res.register(self.atom())
        if res.error: return res

        # Array access / assign:  name at index  /  name at index = value
        if self.current_tok.matches(TT_KEYWORD, 'at'):
            pos_start = atom.pos_start
            res.register_advancement(); self.advance()
            index = res.register(self.expr())
            if res.error: return res

            # Assignment: name at index = value
            if self.current_tok.type == TT_EQ:
                res.register_advancement(); self.advance()
                value = res.register(self.expr())
                if res.error: return res
                # atom must be a VarAccessNode to get the name
                if not isinstance(atom, VarAccessNode):
                    return res.failure(InvalidSyntaxError(
                        pos_start, self.current_tok.pos_end,
                        "Left side of 'at' assignment must be an array name"
                    ))
                return res.success(ArrayAssignNode(
                    atom.var_name_tok, index, value, pos_start, self.current_tok.pos_end
                ))

            return res.success(ArrayAccessNode(atom, index, pos_start, self.current_tok.pos_end))

        # Function call
        if self.current_tok.type == TT_LPAREN:
            pos_start = self.current_tok.pos_start
            res.register_advancement(); self.advance()
            args = []

            if self.current_tok.type == TT_RPAREN:
                res.register_advancement(); self.advance()
            else:
                args.append(res.register(self.expr()))
                if res.error: return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')' or expression"
                ))
                while self.current_tok.type == TT_COMMA:
                    res.register_advancement(); self.advance()
                    args.append(res.register(self.expr()))
                    if res.error: return res
                if self.current_tok.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ',' or ')'"
                    ))
                res.register_advancement(); self.advance()

            return res.success(CallNode(atom, args, pos_start, self.current_tok.pos_end))

        return res.success(atom)

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            res.register_advancement(); self.advance()
            return res.success(NumberNode(tok))

        if tok.type == TT_STRING:
            res.register_advancement(); self.advance()
            return res.success(StringNode(tok))

        if tok.matches(TT_KEYWORD, 'true') or tok.matches(TT_KEYWORD, 'false'):
            res.register_advancement(); self.advance()
            return res.success(BoolNode(tok))

        if tok.type == TT_CHAR:
            res.register_advancement(); self.advance()
            return res.success(CharNode(tok))

        # type keywords used as arguments e.g. input("prompt", int)
        if tok.type == TT_KEYWORD and tok.value in ('int', 'float', 'bool', 'string', 'char'):
            res.register_advancement(); self.advance()
            return res.success(VarAccessNode(tok))

        if tok.type == TT_IDENTIFIER:
            res.register_advancement(); self.advance()
            return res.success(VarAccessNode(tok))

        if tok.type == TT_LPAREN:
            res.register_advancement(); self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))
            res.register_advancement(); self.advance()
            return res.success(expr)

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, string, identifier, 'true', 'false', or '('"
        ))

    # ── Control flow ──────────────────────────────────────────────────────────

    def if_expr(self):
        res       = ParseResult()
        cases     = []
        else_case = None
        pos_start = self.current_tok.pos_start

        # if condition then
        res.register_advancement(); self.advance()
        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))
        res.register_advancement(); self.advance()

        body = res.register(self.statements())
        if res.error: return res
        cases.append((condition, body))

        # elseif branches
        while self.current_tok.matches(TT_KEYWORD, 'elseif'):
            res.register_advancement(); self.advance()
            condition = res.register(self.expr())
            if res.error: return res
            if not self.current_tok.matches(TT_KEYWORD, 'then'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'then'"
                ))
            res.register_advancement(); self.advance()
            body = res.register(self.statements())
            if res.error: return res
            cases.append((condition, body))

        # else
        if self.current_tok.matches(TT_KEYWORD, 'else'):
            res.register_advancement(); self.advance()
            else_case = res.register(self.statements())
            if res.error: return res

        # end
        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end'"
            ))
        pos_end = self.current_tok.pos_end
        res.register_advancement(); self.advance()

        return res.success(IfNode(cases, else_case, pos_start, pos_end))

    def for_expr(self):
        res       = ParseResult()
        pos_start = self.current_tok.pos_start
        res.register_advancement(); self.advance()   # consume 'for'

        # C-style: for (init; cond; step) then
        if self.current_tok.type == TT_LPAREN:
            res.register_advancement(); self.advance()

            init = res.register(self.var_assign())
            if res.error: return res

            # expect semicolon — Lumen uses ; only inside C-style for
            if not (self.current_tok.type == TT_NEWLINE):
                # consume optional newline or semicolons represented as newlines
                pass

            # We separate parts by newline inside parens — but the spec uses ;
            # Accept either a NEWLINE or attempt to parse directly
            cond = res.register(self.expr())
            if res.error: return res

            step = res.register(self.statement())
            if res.error: return res

            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))
            res.register_advancement(); self.advance()

            if not self.current_tok.matches(TT_KEYWORD, 'then'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'then'"
                ))
            res.register_advancement(); self.advance()

            body = res.register(self.statements())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, 'end'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'end'"
                ))
            pos_end = self.current_tok.pos_end
            res.register_advancement(); self.advance()

            return res.success(ForCStyleNode(init, cond, step, body, pos_start, pos_end))

        # Range-style: for i in start to end then
        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected identifier"
            ))
        var_name = self.current_tok
        res.register_advancement(); self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'in'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'in'"
            ))
        res.register_advancement(); self.advance()

        # peek ahead: if after the expr there's a 'to', it's a range loop
        # otherwise it's a foreach loop over an array
        # We parse the expression first, then decide
        iterable = res.register(self.expr())
        if res.error: return res

        # foreach: for item in array then
        if not self.current_tok.matches(TT_KEYWORD, 'to'):
            if not self.current_tok.matches(TT_KEYWORD, 'then'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'then'"
                ))
            res.register_advancement(); self.advance()
            body = res.register(self.statements())
            if res.error: return res
            if not self.current_tok.matches(TT_KEYWORD, 'end'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'end'"
                ))
            pos_end = self.current_tok.pos_end
            res.register_advancement(); self.advance()
            return res.success(ForEachNode(var_name, iterable, body, pos_start, pos_end))

        # range: for i in start to end then
        res.register_advancement(); self.advance()  # consume 'to'
        end = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))
        res.register_advancement(); self.advance()

        body = res.register(self.statements())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end'"
            ))
        pos_end = self.current_tok.pos_end
        res.register_advancement(); self.advance()

        return res.success(ForRangeNode(var_name, iterable, end, body, pos_start, pos_end))

    def while_expr(self):
        res       = ParseResult()
        pos_start = self.current_tok.pos_start
        res.register_advancement(); self.advance()   # consume 'while'

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))
        res.register_advancement(); self.advance()

        body = res.register(self.statements())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end'"
            ))
        pos_end = self.current_tok.pos_end
        res.register_advancement(); self.advance()

        return res.success(WhileNode(condition, body, pos_start, pos_end))

    def do_while_expr(self):
        res       = ParseResult()
        pos_start = self.current_tok.pos_start
        res.register_advancement(); self.advance()   # consume 'do'

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))
        res.register_advancement(); self.advance()

        self._in_do_while = True
        body = res.register(self.statements())
        self._in_do_while = False
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end'"
            ))
        res.register_advancement(); self.advance()

        # newlines between end and while are allowed
        self.skip_newlines(res)

        if not self.current_tok.matches(TT_KEYWORD, 'while'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'while' after 'end' in do-while"
            ))
        res.register_advancement(); self.advance()

        condition = res.register(self.expr())
        if res.error: return res
        pos_end = self.current_tok.pos_end

        return res.success(DoWhileNode(body, condition, pos_start, pos_end))

    # ── Function definition ───────────────────────────────────────────────────

    def func_def(self):
        res       = ParseResult()
        pos_start = self.current_tok.pos_start
        res.register_advancement(); self.advance()   # consume 'func'

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected function name"
            ))
        func_name = self.current_tok
        res.register_advancement(); self.advance()

        if self.current_tok.type != TT_LPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '('"
            ))
        res.register_advancement(); self.advance()

        params = []
        if self.current_tok.type == TT_IDENTIFIER:
            params.append(self.current_tok)
            res.register_advancement(); self.advance()
            while self.current_tok.type == TT_COMMA:
                res.register_advancement(); self.advance()
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected parameter name"
                    ))
                params.append(self.current_tok)
                res.register_advancement(); self.advance()

        if self.current_tok.type != TT_RPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ')'"
            ))
        res.register_advancement(); self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))
        res.register_advancement(); self.advance()

        body = res.register(self.statements())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end'"
            ))
        pos_end = self.current_tok.pos_end
        res.register_advancement(); self.advance()

        return res.success(FuncDefNode(func_name, params, body, pos_start, pos_end))

    # ── Try / on error / always ──────────────────────────────────────────────

    def try_expr(self):
        res       = ParseResult()
        pos_start = self.current_tok.pos_start
        res.register_advancement(); self.advance()   # consume 'try'

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then' after 'try'"
            ))
        res.register_advancement(); self.advance()

        try_body = res.register(self.statements())
        if res.error: return res

        # on error err then
        if not self.current_tok.matches(TT_KEYWORD, 'on'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'on error' after try block"
            ))
        res.register_advancement(); self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'error'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'error' after 'on'"
            ))
        res.register_advancement(); self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected error variable name (e.g. 'err')"
            ))
        err_name_tok = self.current_tok
        res.register_advancement(); self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))
        res.register_advancement(); self.advance()

        catch_body = res.register(self.statements())
        if res.error: return res

        # optional: always then
        always_body = None
        if self.current_tok.matches(TT_KEYWORD, 'always'):
            res.register_advancement(); self.advance()
            if not self.current_tok.matches(TT_KEYWORD, 'then'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'then' after 'always'"
                ))
            res.register_advancement(); self.advance()
            always_body = res.register(self.statements())
            if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end'"
            ))
        pos_end = self.current_tok.pos_end
        res.register_advancement(); self.advance()

        return res.success(TryCatchNode(try_body, err_name_tok, catch_body, always_body, pos_start, pos_end))

    # ── Binary op helper ──────────────────────────────────────────────────────

    def bin_op(self, func, ops_tt=None, ops_kw=None):
        res  = ParseResult()
        left = res.register(func())
        if res.error: return res

        while True:
            tok = self.current_tok
            matched = False
            if ops_tt and tok.type in ops_tt:
                matched = True
            if ops_kw and tok.type == TT_KEYWORD and tok.value in ops_kw:
                matched = True
            if not matched:
                break
            res.register_advancement(); self.advance()
            right = res.register(func())
            if res.error: return res
            left = BinOpNode(left, tok, right)

        return res.success(left)

    # ── Internal state ────────────────────────────────────────────────────────

    _in_do_while = False