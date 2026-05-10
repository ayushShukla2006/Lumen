# Lumen Language Documentation
### Version 1.0

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
11. [Structs](#structs)
12. [Error Handling](#error-handling)
13. [Built-in Functions](#built-in-functions)
14. [Escape Sequences](#escape-sequences)
15. [Execution Model](#execution-model)
16. [Full Example Programs](#full-example-programs)
17. [Glossary — Keywords](#glossary--keywords)
18. [Glossary — Built-in Functions](#glossary--built-in-functions)

---

## Overview

Lumen is a high-level, interpreted scripting language designed to read like English while keeping the structure and explicitness of C and Java. It uses keyword-based block delimiters (`then...end`), dynamic typing with optional type enforcement on arrays, and an English-style logical operator set.

Lumen is a prototype hobby language devolped for understanding how language works

---

## Running Lumen

### Installation

Build the executable from source using PyInstaller:

```
pip install pyinstaller
pyinstaller --onefile shell.py --name lumen
```

This produces `dist/lumen.exe` on Windows or `dist/lumen` on Linux/Mac. Move it somewhere permanent and add it to your PATH.

### Usage

**Show version:**
```
lumen --version
```

**Show help:**
```
lumen --help
```

**Run a script:**
```
lumen script.lm
```

Lumen scripts use the `.lm` extension. A warning is shown if a different extension is used.

**Interactive shell:**
```
lumen
```

**Shell prompt:**
```
Lumen v1.0
A high-level interpreted scripting language.
Type 'exit' to quit the shell.

Lumen > let x = 10
Lumen > func greet(name) then
      |     print("Hello ", name, "\n")
      | end
```

The shell automatically detects multiline blocks and shows `      | ` as a continuation prompt until the block is closed with `end`. Type `exit` to quit.

---

## Variables

Lumen has three tiers of variable declaration.

### Dynamic (default)

Type and value can both change freely.

```
let x = 10
let name = "Lumen"
let active = true
```

Reassignment:
```
let x = 10
x = 20          # valid
x = "hello"     # valid — type can change
x = x + 5      # valid
```

### Static Typed

Declared with `of type`. Value can change, type cannot.

```
let x of int = 10
let ratio of float = 3.14
let name of string = "Lumen"
let flag of bool = true
let ch of char = 'A'
```

Reassignment:
```
let x of int = 10
x = 99          # valid — still int
x = 3.14        # ERROR: type mismatch, 'x' is declared as 'int'
x = "hello"     # ERROR: type mismatch

let x of float = 3.14   # valid — redeclares with new type
```

### Final (Const)

Declared with `final`. Nothing can change — value or type.

```
final let PI = 3.14159
final let APP_NAME = "Lumen"
final let MAX of int = 100
```

```
PI = 3          # ERROR: Cannot reassign final variable 'PI'
MAX = 200       # ERROR: Cannot redeclare final variable 'MAX'
```

`final` can be combined with `of` to be both const and explicitly typed:
```
final let x of int = 10    # const AND typed
final let y = 10           # const, type inferred from value
```

### Summary

| Declaration | Value Mutable | Type Mutable |
|-------------|--------------|--------------|
| `let x = 10` | yes | yes |
| `let x of int = 10` | yes | no |
| `final let x = 10` | no | no |
| `final let x of int = 10` | no | no |

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
let a = 10 + 5    # 15  — addition
let b = 10 - 3    # 7   — subtraction
let c = 4 * 3     # 12  — multiplication
let d = 10 / 2    # 5.0 — division
let e = 10 // 3   # 3   — floor division
let f = 10 % 3    # 1   — modulo
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

`not` is strictly a prefix boolean negation operator. Use `!=` for inequality comparisons — not `not`.

### String Concatenation

```
let full = "Hello" + " " + "World"
```

---

## Control Flow

### If / Otherwise / Otherwise (fallback)

All conditional branches use `otherwise`. With a condition it acts like `otherwise`. Without a condition (`otherwise then`) it acts as the final fallback. All forms close with a single `end`.

```
if x > 10 then
    print("big\n")
otherwise x == 10 then
    print("ten\n")
otherwise then
    print("small\n")
end
```

Just an `if`:
```
if x == 5 then
    print("five\n")
end
```

`if` with a fallback:
```
if x > 10 then
    print("big\n")
otherwise then
    print("not big\n")
end
```

---

## Loops

### While Loop

```
let i = 0
while i != 10 then
    print(i, "\n")
    i = i + 1
end
```

### Range For Loop

Inclusive on both ends — `1 to 10` iterates 1, 2, 3 ... 10.

```
for i in 1 to 10 then
    print(i, "\n")
end
```

### Foreach Loop

Iterates directly over arrays or strings.

```
let scores of int[] = {10, 20, 30}

for score in scores then
    print(score, "\n")
end

let name = "lumen"
for ch in name then
    print(ch, "\n")
end
```

### Do-While Loop

Runs the body at least once, then checks the condition. `end` closes the block, `while condition` follows on the next line.

```
let i = 0
do then
    print(i, "\n")
    i = i + 1
end
while i != 5
```

### C-Style For Loop

```
for (let i = 0; i < 10; i = i + 1) then
    print(i, "\n")
end
```

### Break and Continue

`break` exits the loop immediately. `continue` skips to the next iteration. Both work in all loop types.

```
let i = 0
while i != 10 then
    if i == 5 then
        break
    end
    print(i, "\n")
    i = i + 1
end

# print only odd numbers
for i in 1 to 10 then
    if i % 2 == 0 then
        continue
    end
    print(i, "\n")
end
```

---

## Functions

### Declaration

```
func greet(name) then
    print("Hello ", name, "\n")
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

### Supported Element Types

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
| `char` | null character |

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
let name = "Hello" + " World"
```

### String Indexing

Returns a `char` value.

```
let ch = name at 0     # 'H'
```

### String Index Assignment

```
name at 0 = 'h'        # modifies character in place
```

### String Iteration

```
for ch in name then
    print(ch, "\n")
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
tochar(65)          # 'A' — char from ASCII code
```

---

## Structs

Structs are Lumen's way of grouping related data and behavior. They support fields with optional types and defaults, methods, and `final` fields. There is no inheritance.

### Definition

```
struct Vector2 then
    let x of float = 0.0
    let y of float = 0.0
end
```

### Instantiation

Fields are filled positionally. Unprovided fields use their declared default, or `null` if no default is declared.

```
let v1 = Vector2()          # x = 0.0, y = 0.0
let v2 = Vector2(3.0, 4.0)  # x = 3.0, y = 4.0
```

### Field Access and Assignment

```
print(v2.x, "\n")    # 3.0
v2.x = 10.0
print(v2.x, "\n")    # 10.0
```

### Field Types and Defaults

Fields follow the same rules as variables — dynamic, typed with `of`, or `final`:

```
struct Player then
    let name = "unknown"        # dynamic field
    let health of int = 100     # typed field
    final let id of int = 0     # final typed field
    let tag                     # no default — starts as null
end
```

### Methods and `its`

Methods are defined with `func` inside the struct body. Use `its` to access the current instance's fields and methods:

```
struct Vector2 then
    let x of float = 0.0
    let y of float = 0.0

    func scale(factor) then
        its.x = its.x * factor
        its.y = its.y * factor
    end

    func length() then
        return its.x * its.x + its.y * its.y
    end
end

let v = Vector2(2.0, 3.0)
v.scale(2.0)
print(v.x, "\n")         # 4.0
print(v.length(), "\n")  # 52.0
```

### Null

Fields with no default and no provided argument are `null`. Null is also a valid value in dynamic fields.

```
let n = Node()
print(n.next, "\n")   # null
```

### Rules

- No inheritance.
- Fields can be dynamic, typed (`of`), or `final`.
- `final` fields cannot be reassigned after instantiation.
- Typed fields enforce their type on assignment.
- Methods always use `its` to refer to the current instance.

---

## Error Handling

### Try / On Error / Always

```
try then
    let result = riskyFunction()
on error err then
    print("Something went wrong: ", err, "\n")
always then
    print("This always runs\n")
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
    print("Caught: ", err, "\n")
end
```

Throws propagate out of functions into the nearest enclosing `try` block.

---

## Built-in Functions

### Output

| Function | Description |
|----------|-------------|
| `print(...)` | Print one or more values. No automatic newline — use `\n` or `\newline` to break lines. |

```
print("Hello ", "World", "\n")
print("Value: ", 42, "\n")
print(true, "\n")
```

### Input

| Function | Description |
|----------|-------------|
| `input(prompt)` | Read a line from the user as a string |
| `input(prompt, type)` | Read and convert to a specific type |

```
let name  = input("Enter name: ")
let age   = input("Enter age: ", int)
let ratio = input("Enter ratio: ", float)
let flag  = input("Enter bool: ", bool)
let ch    = input("Enter char: ", char)
```

Valid types: `int`, `float`, `bool`, `string`, `char`. Invalid conversions give a runtime error.

### Type Conversion

| Function | Description |
|----------|-------------|
| `str(value)` | Convert any value to a string |
| `int(value)` | Convert a number, string, or bool to an integer |
| `float(value)` | Convert a number, string, or bool to a float |

```
str(42)          # "42"
str(true)        # "true"
int(3.7)         # 3
int("42")        # 42
int(true)        # 1
float(10)        # 10.0
float("3.14")    # 3.14
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
| | `\space` | Space character |

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

The interpreter maintains a symbol table per scope. Functions create their own scope. Variables declared in a function are local to that function. Variables declared at the top level are global.

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

### Loop Control

```
# print only odd numbers using continue
for i in 1 to 20 then
    if i % 2 == 0 then
        continue
    end
    print(i, "\n")
end

# stop when input is 0 using break
while true then
    let x = input("Enter number (0 to quit): ", int)
    if x == 0 then
        break
    end
    print("You entered: ", x, "\n")
end
```

### String Manipulation

```
let name = input("Enter a name: ")
print("Original:  ", name, "\n")
print("Uppercase: ", upper(name), "\n")
print("Length:    ", length(name), "\n")

print("Characters:\n")
for ch in name then
    if isalpha(ch) then
        print(ch, "\n")
    end
end
```

---

## Glossary — Keywords

Every keyword in Lumen and what it does.

| Keyword | Category | Description |
|---------|----------|-------------|
| `let` | Variables | Declares a mutable variable. `let x = 10` |
| `final` | Variables | Modifier that makes a variable immutable. Used before `let`. `final let x = 10` |
| `of` | Variables / Arrays | Specifies the type of a variable or array. `let x of int = 10` locks the type of `x` to int. `let scores of int[]` declares a typed array. |
| `true` | Values | Boolean literal true |
| `false` | Values | Boolean literal false |
| `if` | Control Flow | Starts a conditional block. Must be followed by a condition and `then` |
| `otherwise` | Control Flow | Additional branch inside an `if` block. With a condition: `otherwise x == 10 then`. Without a condition: `otherwise then` — acts as the final fallback |
| `then` | Blocks | Opens a code block. Used after `if`, `otherwise`, `for`, `while`, `do`, `func`, `try`, `on error`, `always` |
| `end` | Blocks | Closes any block |
| `for` | Loops | Starts a range loop or foreach loop |
| `in` | Loops | Used in range and foreach loops. `for i in 1 to 10` or `for item in array` |
| `to` | Loops | Defines the upper bound of a range loop. `1 to 10` |
| `while` | Loops | Starts a while loop, or defines the condition check in a do-while loop |
| `do` | Loops | Starts a do-while block — body runs at least once |
| `break` | Loops | Exits the current loop immediately |
| `continue` | Loops | Skips the rest of the current iteration and moves to the next |
| `func` | Functions | Declares a function. `func name(params) then` |
| `return` | Functions | Returns a value from a function. Optional — functions return `0` implicitly |
| `and` | Logical | True only if both conditions are true |
| `or` | Logical | True if at least one condition is true |
| `not` | Logical | Prefix boolean negation. `not true` evaluates to `false` |
| `try` | Error Handling | Starts a try block — code that might fail |
| `on` | Error Handling | Part of `on error` — introduces the catch block |
| `error` | Error Handling | Part of `on error` — follows `on` |
| `always` | Error Handling | Optional block that always runs whether or not an error occurred |
| `throw` | Error Handling | Raises an error from Lumen code. Must throw a string. `throw "message"` |
| `int` | Types | Integer type — used in array declarations and `input()` |
| `float` | Types | Float type — used in array declarations and `input()` |
| `bool` | Types | Boolean type — used in array declarations and `input()` |
| `string` | Types | String type — used in array declarations and `input()` |
| `char` | Types | Character type — used in array declarations and `input()` |
| `at` | Arrays / Strings | Index access or assignment. `scores at 0` reads, `scores at 0 = 99` writes |
| `struct` | Structs | Declares a struct type. `struct Name then ... end` |
| `its` | Structs | Reference to the current struct instance inside a method. `its.x`, `its.health` |
| `null` | Values | Represents an uninitialized or absent value. Default for fields with no default declared. |

---

## Glossary — Built-in Functions

Every built-in function in Lumen.

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `print` | `print(val, ...)` | nothing | Prints one or more values with no automatic newline. Use `\n` to add line breaks. Accepts any type. |
| `input` | `input(prompt)` | `string` | Displays a prompt and reads a line from the user. Returns a string. |
| `input` | `input(prompt, type)` | `type` | Reads a line and converts to the given type. Valid types: `int`, `float`, `bool`, `string`, `char`. Errors on invalid input. |
| `str` | `str(value)` | `string` | Converts any value to its string representation. |
| `int` | `int(value)` | `int` | Converts a number, string, or bool to an integer. Truncates floats. Errors on invalid strings. |
| `float` | `float(value)` | `float` | Converts a number, string, or bool to a float. Errors on invalid strings. |
| `length` | `length(string)` | `int` | Returns the number of characters in a string. |
| `length` | `length(array)` | `int` | Returns the number of elements in an array. |
| `upper` | `upper(string)` | `string` | Returns an uppercase copy of the string. |
| `lower` | `lower(string)` | `string` | Returns a lowercase copy of the string. |
| `substr` | `substr(string, start, end)` | `string` | Returns a slice of the string from index `start` up to but not including `end`. |
| `push` | `push(array, value)` | nothing | Appends a value to a dynamic array. Errors on fixed-size arrays or type mismatch. |
| `pop` | `pop(array)` | element | Removes and returns the last element of a dynamic array. Errors if empty. |
| `dequeue` | `dequeue(array)` | element | Removes and returns the first element of a dynamic array. Errors if empty. |
| `isalpha` | `isalpha(char)` | `bool` | Returns true if the character is alphabetic (a-z or A-Z). |
| `isdigit` | `isdigit(char)` | `bool` | Returns true if the character is a digit (0-9). |
| `charcode` | `charcode(char)` | `int` | Returns the ASCII integer code of the character. |
| `tochar` | `tochar(int)` | `char` | Returns the character corresponding to the given ASCII code. |