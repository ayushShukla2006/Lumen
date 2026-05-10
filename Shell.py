import sys
from Lexer import Lexer
from Parser import Parser
from Interpreter import Interpreter, Context, GLOBAL_TABLE, LumenNumber

# One persistent global context across the whole session
global_context = Context('<global>')
global_context.symbol_table = GLOBAL_TABLE


def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    parser = Parser(tokens)
    result = parser.parse()
    if result.error:
        return None, result.error

    interpreter = Interpreter()
    last = None
    for node in result.node:
        rt = interpreter.visit(node, global_context)
        if rt.error:
            return None, rt.error
        last = rt.value

    return last, None


def run_file(path):
    try:
        with open(path, 'r') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: file '{path}' not found")
        return
    result, error = run(path, text)
    if error:
        print(error.as_string())


def read_input():
    """Read one logical chunk — handles multiline blocks automatically."""
    lines = []
    depth = 0

    OPENERS = {'then', 'do'}
    CLOSERS = {'end'}

    while True:
        prompt = 'Lumen > ' if not lines else '      | '
        try:
            line = input(prompt)
        except KeyboardInterrupt:
            print()
            return None

        lines.append(line)

        # count block depth from this line's words
        for word in line.split():
            # strip punctuation so 'then,' etc still match
            word = word.strip('(),:')
            if word in OPENERS:
                depth += 1
            elif word in CLOSERS:
                depth -= 1

        # also handle do-while: 'while' after 'end' on its own line closes nothing
        # depth <= 0 means all opened blocks are closed
        if depth <= 0:
            break

    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        print("Lumen v0.1 — type 'exit' to quit")
        while True:
            text = read_input()

            if text is None:
                continue
            if not text.strip():
                continue
            if text.strip() == 'exit':
                print('Bye.')
                break

            result, error = run('<stdin>', text)
            if error:
                print(error.as_string())
            elif result is not None:
                if not (isinstance(result, LumenNumber) and result.value == 0):
                    print(result)