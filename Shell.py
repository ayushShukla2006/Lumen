import sys
import os
from Lexer import Lexer
from Parser import Parser
from Interpreter import Interpreter, Context, GLOBAL_TABLE, LumenNumber, _last_print_had_newline

VERSION = "1.0"
AUTHOR  = "Lumen Language"

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
    if not path.endswith('.lm'):
        print(f"Warning: Lumen files should use the .lm extension (got '{path}')")

    if not os.path.exists(path):
        print(f"Error: file '{path}' not found")
        return

    with open(path, 'r') as f:
        text = f.read()

    result, error = run(path, text)
    if error:
        print(error.as_string())


def read_input():
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

        for word in line.split():
            word = word.strip('(),:')
            if word in OPENERS:
                depth += 1
            elif word in CLOSERS:
                depth -= 1

        if depth <= 0:
            break

    return '\n'.join(lines)


def print_version():
    print(f"Lumen v{VERSION}")
    print("A high-level interpreted scripting language.")
    print("Type 'exit' to quit the shell.")


def print_help():
    print(f"""
Lumen v{VERSION} — Usage:

  lumen                  Start interactive shell
  lumen <file.lm>        Run a Lumen script
  lumen --version        Show version info
  lumen --help           Show this help message
""")


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args:
        print_version()
        print()
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
            # if last print didn't end with newline, add one so prompt is on new line
            from Interpreter import _last_print_had_newline
            if not _last_print_had_newline:
                print()

    elif args[0] == '--version':
        print_version()

    elif args[0] == '--help':
        print_help()

    elif args[0].startswith('--'):
        print(f"Unknown option: {args[0]}")
        print("Run 'lumen --help' for usage.")

    else:
        run_file(args[0])