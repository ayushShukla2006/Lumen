from Errors import IllegalCharError, ExpectedCharError

# ── Constants ────────────────────────────────────────────────────────────────

DIGITS      = '0123456789'
LETTERS     = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTERS_DIGITS = LETTERS + DIGITS + '_'

KEYWORDS = {
    'let', 'final', 'func', 'return',
    'of', 'at',
    'if', 'then', 'elseif', 'else', 'end',
    'for', 'in', 'to', 'while', 'do',
    'and', 'or', 'not',
    'true', 'false',
    'char',
    'try', 'on', 'error', 'always', 'throw',
}

# ── Token types ──────────────────────────────────────────────────────────────

TT_INT        = 'INT'
TT_FLOAT      = 'FLOAT'
TT_STRING     = 'STRING'
TT_CHAR       = 'CHAR'
TT_IDENTIFIER = 'IDENTIFIER'
TT_KEYWORD    = 'KEYWORD'

TT_PLUS       = 'PLUS'
TT_MINUS      = 'MINUS'
TT_MUL        = 'MUL'
TT_DIV        = 'DIV'

TT_EQ         = 'EQ'          # =
TT_EQEQ       = 'EQEQ'        # ==
TT_NEQ        = 'NEQ'         # !=
TT_LT         = 'LT'          # <
TT_GT         = 'GT'          # >
TT_LTE        = 'LTE'         # <=
TT_GTE        = 'GTE'         # >=

TT_LPAREN     = 'LPAREN'      # (
TT_RPAREN     = 'RPAREN'      # )
TT_COMMA      = 'COMMA'
TT_LBRACE     = 'LBRACE'
TT_RBRACE     = 'RBRACE'
TT_LBRACKET   = 'LBRACKET'
TT_RBRACKET   = 'RBRACKET'
TT_NEWLINE    = 'NEWLINE'
TT_EOF        = 'EOF'

# ── Position ─────────────────────────────────────────────────────────────────

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx  = idx
        self.ln   = ln
        self.col  = col
        self.fn   = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1
        if current_char == '\n':
            self.ln  += 1
            self.col  = 0
        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

# ── Token ────────────────────────────────────────────────────────────────────

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type  = type_
        self.value = value
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end   = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value is not None:
            return f'{self.type}:{self.value}'
        return self.type

# ── Lexer ────────────────────────────────────────────────────────────────────

class Lexer:
    def __init__(self, fn, text):
        self.fn           = fn
        self.text         = text
        self.pos          = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    # ── Main tokeniser ───────────────────────────────────────────────────────

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            ch = self.current_char

            if ch in ' \t':
                self.advance()

            elif ch == '#':                         # comment — skip rest of line
                self.skip_comment()

            elif ch == '\n':
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()

            elif ch in DIGITS:
                tokens.append(self.make_number())

            elif ch in LETTERS or ch == '_':
                tokens.append(self.make_identifier())

            elif ch == '"':
                tok, err = self.make_string()
                if err: return [], err
                tokens.append(tok)
            elif ch == "'":
                tok, err = self.make_char()
                if err: return [], err
                tokens.append(tok)

            elif ch == '+':
                tokens.append(Token(TT_PLUS,   pos_start=self.pos)); self.advance()
            elif ch == '-':
                tokens.append(Token(TT_MINUS,  pos_start=self.pos)); self.advance()
            elif ch == '*':
                tokens.append(Token(TT_MUL,    pos_start=self.pos)); self.advance()
            elif ch == '/':
                tokens.append(Token(TT_DIV,    pos_start=self.pos)); self.advance()
            elif ch == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos)); self.advance()
            elif ch == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos)); self.advance()
            elif ch == ',':
                tokens.append(Token(TT_COMMA,   pos_start=self.pos)); self.advance()
            elif ch == '{':
                tokens.append(Token(TT_LBRACE,  pos_start=self.pos)); self.advance()
            elif ch == '}':
                tokens.append(Token(TT_RBRACE,  pos_start=self.pos)); self.advance()
            elif ch == '[':
                tokens.append(Token(TT_LBRACKET,pos_start=self.pos)); self.advance()
            elif ch == ']':
                tokens.append(Token(TT_RBRACKET,pos_start=self.pos)); self.advance()

            elif ch == '=':
                tokens.append(self.make_equals())
            elif ch == '!':
                tok, err = self.make_not_equals()
                if err: return [], err
                tokens.append(tok)
            elif ch == '<':
                tokens.append(self.make_less_than())
            elif ch == '>':
                tokens.append(self.make_greater_than())

            else:
                pos_start = self.pos.copy()
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{ch}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def skip_comment(self):
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def make_number(self):
        num_str   = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT,   int(num_str),   pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_identifier(self):
        id_str    = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS:
            id_str += self.current_char
            self.advance()

        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_string(self):
        string    = ''
        pos_start = self.pos.copy()
        self.advance()  # skip opening "

        escape_chars = {
                # short forms
                'n':       '\n',
                't':       '\t',
                'r':       '\r',
                '"':      '"',
                "'":      "'",
                '\\':    '\\',
                # long forms  e.g. \newline
                'newline': '\n',
                'tab':     '\t',
                'space':   ' ',
                'return':  '\r',
                'quote':   '"',
            }

        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char and self.current_char in LETTERS:
                    # read characters until we match a known long escape or run out of letters
                    LONG_ESCAPES = ('newline', 'tab', 'space', 'return', 'quote')
                    word = ''
                    matched = None
                    while self.current_char and self.current_char in LETTERS:
                        word += self.current_char
                        self.advance()
                        if word in LONG_ESCAPES:
                            matched = word
                            break
                    if matched:
                        # long escape matched — any remaining letters are plain text
                        string += escape_chars[matched]
                    elif len(word) >= 1 and word[0] in escape_chars:
                        # short escape e.g. n, t — rest is plain text
                        string += escape_chars[word[0]] + word[1:]
                    else:
                        # unknown escape
                        string += '\\' + word
                else:
                    ch = self.current_char if self.current_char else ''
                    string += escape_chars.get(ch, ch)
                    if self.current_char:
                        self.advance()
            else:
                string += self.current_char
                self.advance()

        if self.current_char != '"':
            return None, ExpectedCharError(pos_start, self.pos, 'Closing \'"\'')

        self.advance()  # skip closing "
        return Token(TT_STRING, string, pos_start, self.pos), None

    def make_char(self):
        pos_start = self.pos.copy()
        self.advance()  # skip opening '

        if self.current_char is None or self.current_char == "'":
            return None, ExpectedCharError(pos_start, self.pos, 'Character inside single quotes')

        if self.current_char == '\\':
            self.advance()
            escape_chars = {'n': '\n', 't': '\t', "'": "'", '\\': '\\'}
            ch = escape_chars.get(self.current_char, self.current_char)
        else:
            ch = self.current_char
        self.advance()

        if self.current_char != "'":
            return None, ExpectedCharError(pos_start, self.pos, "Closing \"'\"  — char must be a single character")

        self.advance()  # skip closing '
        return Token(TT_CHAR, ch, pos_start, self.pos), None

    def make_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_EQEQ, pos_start=pos_start, pos_end=self.pos)
        return Token(TT_EQ, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_NEQ, pos_start=pos_start, pos_end=self.pos), None
        return None, ExpectedCharError(pos_start, self.pos, "'=' after '!'")

    def make_less_than(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_LTE, pos_start=pos_start, pos_end=self.pos)
        return Token(TT_LT, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_GTE, pos_start=pos_start, pos_end=self.pos)
        return Token(TT_GT, pos_start=pos_start, pos_end=self.pos)