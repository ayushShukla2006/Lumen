# Lumen Language Documentation
### Version 0.1 — Not Finalized

---

## Table of Contents

1. [Overview](#overview)
2. [Running Lumen](#running-lumen)
3. [Variables](#variables)
4. [Data Types](#data-types)
5. [Operators](#operators)
6. [Control Flow](#control-flow)
7. [Loops](#loops)
8. [Functions](#functions)
9. [Arrays](#arrays)
10. [Strings and Characters](#strings-and-characters)
11. [Error Handling](#error-handling)
12. [Built-in Functions](#built-in-functions)
13. [Escape Sequences](#escape-sequences)
14. [Execution Model](#execution-model)

---

## Overview

Lumen is a high-level, interpreted scripting language designed to read like English while keeping the structure and explicitness of C and Java. It uses keyword-based block delimiters (`then...end`), dynamic typing with optional type enforcement on arrays, and an English-style logical operator set.

Lumen is designed to be embeddable in game engines as a scripting layer.

---

## Running Lumen

**Interactive shell:**
```
python shell.py
```

**Run a file:**
```
python shell.py myprogram.lumen
```

**Shell prompt:**
```
Lumen > let x = 10
Lumen > func greet(name) then
      |     print("Hello ", name)
      | end
```

The shell automatically detects multiline blocks and shows `      | ` as a continuation prompt until the block is closed with `end`.

---

## Variables

### Declaration

```
let x = 10
let name = "the user"
let active = true
```

### Reassignment

```
let x = 10
x = 20          # reassign without let
x = x + 5      # arithmetic reassignment
```

### Final (Immutable)

Once declared with `final`, the variable cannot be reassigned.

```
final let PI = 3.14159
final let APP_NAME = "Lumen"

PI = 3   # ERROR: Cannot reassign final variable 'PI'
```

### Rules

- Identifiers must start with a letter. Can contain letters, digits, and underscores.
- No semicolons required — statements are delimited by newlines.
- Comments start with `#`.

```
# this is a comment
let x = 10   # inline comment
```

---

## Data Types

| Type | Example | Notes |
|------|---------|-------|
| `int` | `42` | Integer number |
| `float` | `3.14` | Decimal number |
| `bool` | `true` / `false` | Boolean |
| `string` | `"hello"` | Text in double quotes |
| `char` | `'A'` | Single character in single quotes |

Lumen is dynamically typed — a variable declared without a type annotation can hold any type.

```
let x = 10
x = "hello"    # valid — type can change
x = true       # valid
```

---

## Operators

### Arithmetic

```
let a = 10 + 5    # 15
let b = 10 - 3    # 7
let c = 4 * 3     # 12
let d = 10 / 2    # 5
```

### Comparison

```
5 == 5     # true
5 != 3     # true
5 > 3      # true
5 < 10     # true
5 >= 5     # true
5 <= 4     # false
```

### Logical

```
true and false    # false
true or false     # true
not true          # false
```

`not` is strictly a prefix boolean negation operator. Use `!=` for inequality — not `not`.

### String Concatenation

```
let full = "Hello" + " " + "World"
```

---

## Control Flow

### If / Elseif / Else

```
if x > 10 then
    print("big")
elseif x == 10 then
    print("ten")
else
    print("small")
end
```

All branches close with a single `end`.

---

## Loops

### While Loop

```
let i = 0
while i != 10 then
    print(i)
    i = i + 1
end
```

### Range For Loop

```
for i in 1 to 10 then
    print(i)
end
```

Inclusive on both ends — `1 to 10` iterates 1, 2, 3 ... 10.

### Foreach Loop

Iterates over arrays or strings directly.

```
let scores of int[] = {10, 20, 30}

for score in scores then
    print(score)
end

let name = "the user"
for ch in name then
    print(ch)
end
```

### Do-While Loop

Runs the body at least once, then checks the condition.

```
let i = 0
do then
    print(i)
    i = i + 1
end
while i != 5
```

`end` closes the block. `while condition` on the next line is the termination check.

### C-Style For Loop

```
for (let i = 0; i < 10; i = i + 1) then
    print(i)
end
```

---

## Functions

### Declaration

```
func greet(name) then
    print("Hello ", name)
end
```

### Return Values

```
func add(a, b) then
    return a + b
end

let result = add(3, 7)   # result = 10
```

### Recursion

```
func fib(n) then
    if n <= 1 then
        return n
    end
    return fib(n - 1) + fib(n - 2)
end
```

### Rules

- Functions are declared with `func`, opened with `then`, closed with `end`.
- Parameters are comma-separated identifiers — no types required.
- `return` is optional. Functions implicitly return `0` if no return is hit.
- Functions support recursion and closures.

---

## Arrays

Arrays in Lumen are typed. Every array must declare its element type using `of`.

### Fixed-Size Array

Size is locked. Empty slots fill with the zero value of the declared type.

```
let scores of int[5] = {10, 20, 30, 40, 50}
let flags of bool[3] = {true}       # {true, false, false}
let names of string[2] = {}         # {"", ""}
```

### Dynamic Array

No size limit. Elements can be pushed and popped freely.

```
let scores of int[] = {1, 2, 3}
let words of string[] = {}
```

### Supported Types

`int`, `float`, `bool`, `string`, `char`

### Element Access

```
let first = scores at 0
```

### Element Assignment

```
scores at 0 = 99
```

### Zero Values by Type

| Type | Zero Value |
|------|------------|
| `int` | `0` |
| `float` | `0.0` |
| `bool` | `false` |
| `string` | `""` |
| `char` | `\0` |

### Array Operations

```
push(scores, 6)         # append to dynamic array
pop(scores)             # remove and return last element
dequeue(scores)         # remove and return first element
length(scores)          # number of elements
```

Pushing to a fixed-size array is an error. Type mismatches are caught at runtime.

```
let scores of int[] = {}
push(scores, "hello")   # ERROR: Type mismatch: array is of type 'int'
```

---

## Strings and Characters

### Strings

Strings are declared with double quotes. Concatenation uses `+`.

```
let name = "the user" + " Shukla"
```

### String Indexing

Returns a `char` value.

```
let ch = name at 0     # 'A'
```

### String Index Assignment

```
name at 0 = 'a'        # modifies character in place
```

### String Iteration

```
for ch in name then
    print(ch)
end
```

### Chars

Single characters are declared with single quotes.

```
let c = 'A'
let digit = '7'
```

### Char Arrays

```
let letters of char[] = {'h', 'e', 'l', 'l', 'o'}
push(letters, '!')
```

### Char Operations

```
isalpha('a')        # true — is alphabetic
isdigit('3')        # true — is digit
charcode('A')       # 65  — ASCII code
tochar(65)          # 'A' — from ASCII code
```

---

## Error Handling

### Try / On Error / Always

```
try then
    let result = riskyFunction()
on error err then
    print("Something went wrong: ", err)
always then
    print("This always runs")
end
```

- `on error err` — catches both runtime errors and thrown errors. `err` is a string message.
- `always then` — optional. Runs whether or not an error occurred.

### Throw

Raises an error from Lumen code. Must be a string.

```
func divide(a, b) then
    if b == 0 then
        throw "Cannot divide by zero"
    end
    return a / b
end

try then
    let r = divide(10, 0)
on error err then
    print("Caught: ", err)
end
```

Throws propagate out of functions into the nearest enclosing `try` block.

---

## Built-in Functions

### Output

| Function | Description |
|----------|-------------|
| `print(...)` | Print one or more values with no automatic newline. Use `\n` or `\newline` to add line breaks. |

```
print("Hello ", name, "\n")
print("Value: ", 42, "\n")
print(true, "\n")
```

### Input

| Function | Description |
|----------|-------------|
| `input(prompt)` | Read a line from the user as a string |
| `input(prompt, type)` | Read and convert to a specific type |

```
let name = input("Enter name: ")
let age  = input("Enter age: ", int)
let ratio = input("Enter ratio: ", float)
let flag = input("Enter bool: ", bool)
let ch   = input("Enter char: ", char)
```

Valid types: `int`, `float`, `bool`, `string`, `char`.
Invalid conversions (e.g. typing `"hello"` for `int`) give a runtime error.

### Type Conversion

| Function | Description |
|----------|-------------|
| `str(value)` | Convert any value to a string |
| `num(string)` | Convert a string to a number |

```
str(42)         # "42"
str(true)       # "true"
num("3.14")     # 3.14
```

### String Operations

| Function | Description |
|----------|-------------|
| `length(string)` | Number of characters |
| `upper(string)` | Uppercase copy |
| `lower(string)` | Lowercase copy |
| `substr(string, start, end)` | Substring slice |

```
length("hello")         # 5
upper("hello")          # "HELLO"
lower("HELLO")          # "hello"
substr("hello", 1, 4)   # "ell"
```

### Array Operations

| Function | Description |
|----------|-------------|
| `length(array)` | Number of elements |
| `push(array, value)` | Append to dynamic array |
| `pop(array)` | Remove and return last element |
| `dequeue(array)` | Remove and return first element |

### Char Operations

| Function | Description |
|----------|-------------|
| `isalpha(char)` | True if alphabetic |
| `isdigit(char)` | True if digit |
| `charcode(char)` | ASCII code as int |
| `tochar(int)` | Char from ASCII code |

---

## Escape Sequences

Both short and long forms are supported inside strings.

| Short | Long | Result |
|-------|------|--------|
| `\n` | `\newline` | Newline |
| `\t` | `\tab` | Tab |
| `\r` | `\return` | Carriage return |
| `\"` | `\quote` | Double quote |
| `\\` | | Backslash |
| | `\space` | Space |

```
print("Line 1\newlineLine 2")
print("Column 1\tabColumn 2")
print("a\spaceb")
print("She said \"hello\"")
```

---

## Execution Model

Lumen is an interpreted language. Source code goes through three stages:

1. **Lexer** — scans source text and produces a stream of tokens.
2. **Parser** — consumes tokens and builds an Abstract Syntax Tree (AST).
3. **Interpreter** — traverses and directly executes the AST nodes.

The interpreter maintains a **symbol table** per scope. Functions create their own scope. Variables declared in a function are local to that function. Variables declared at the top level are global.

---

## Full Example Programs

### Fibonacci

```
func fib(n) then
    if n <= 1 then
        return n
    end
    return fib(n - 1) + fib(n - 2)
end

let i = input("How many terms: ", int)
let j = 0
while j != i then
    print(fib(j), "\n")
    j = j + 1
end
```

### Alphabet Generator

```
let letters of char[] = {}
let i = 65
while i != 91 then
    push(letters, tochar(i))
    i = i + 1
end

for ch in letters then
    print(ch, "\n")
end
```

### Safe Division with Error Handling

```
func divide(a, b) then
    if b == 0 then
        throw "Cannot divide by zero"
    end
    return a / b
end

try then
    let a = input("Enter numerator: ", int)
    let b = input("Enter denominator: ", int)
    let result = divide(a, b)
    print("Result: ", result, "\n")
on error err then
    print("Error: ", err, "\n")
always then
    print("Done.\n")
end
```

### String Manipulation

```
let name = input("Enter your name: ")
print("Original:  ", name, "\n")
print("Uppercase: ", upper(name), "\n")
print("Length:    ", length(name), "\n")

name at 0 = upper(name at 0)
print("Capitalized: ", name, "\n")

print("Characters:\n")
for ch in name then
    if isalpha(ch) then
        print(ch, "\n")
    end
end
```