import re
from collections import namedtuple

COMMENT_RE = r"(?P<comment>/\*.+?\*/|//.+?$)"
KEYWORDS = [
    "class", "constructor", "function", "method", "field",
    "static", "var", "int", "char", "boolean", "void",
    "true", "false", "null", "this", "let", "do", "if",
    "else", "while", "return",
]
KEYWORD_RE = r"(?P<keyword>{})".format(r"|".join(r"\b{}\b".format(kw) for kw in KEYWORDS))
IDENTIFIER_RE = r"(?P<identifier>\b[a-zA-Z_]\w*\b)"
SYMBOLS = [
    "\{", "\}", "\(", "\)", "\[", "\]", "\.", ",", ";", "\+",
    "-", "\*", "/", "\&", "\|", "<", ">", "=", "~",
]
SYMBOL_RE = r"(?P<symbol>{})".format(r"|".join(symbol for symbol in SYMBOLS))
STRING_RE = r"(?<!\\)\"(?P<stringConstant>[^\n]+?)(?<!\\)\""
INTEGER_RE = r"(?P<integerConstant>\b\d+\b)"
JACK_TOKEN_RE = r"|".join([COMMENT_RE, KEYWORD_RE, IDENTIFIER_RE, SYMBOL_RE, STRING_RE, INTEGER_RE])

"""
1. Compile class declaration
2. Compile its subroutines

# Maintain a symbol table linked list
Class vars: Field, static
Subroutine level: argument, local
Scope: class or subroutine
Symbol table:
    name type kind   #
    x    int  field  0
    y    int  field  1
    bla  int  static 0
* Methods always have a 'this' argument added to the table (arg 0)
* Class tables start fresh on compilation since they aren't shared across.
* Var declarations build the table
* Never need more than two: Current class and current function/method/constructor.

expressions and let and such lookup the variable in the table. first subroutine table, then the class table
`let` statements check the symbol table for the symbol, find the segment, and then push/pop
To go from syntax tree to stack based, do a post order traversal
* 'codewrite' algo can skip the syntax tree walking step: (actually it basically IS post order tree walking)
  * if number output push number
  * if variable outupt push var (lookup in table)
  * if expression is a op b
    * codewrite a
    * codewrite b
    * output op
  * if expersion is op a (unary)
    * codewrite a
    * output op
  * if f(a, b, ...)
    * codewrite a
    * codewrite b
    * ...
    * output call f
Flow control: (While and If => goto, goto if, label)
* Negate the expression: If true then jump, otherwise fall through
* Need to generate unique labels
Allocating space for objects
* Use the class-level symbol table's size to determine required space (field type only)
* We are provided `Memory.alloc`, pop that into this (pop pointer 0), return this.
Object manipulation
* Object itself (pointer) is pushed first as the implicit `this`.
* Pop intos THIS (`pop pointer 0`)
Methods
* Implicit push arg 0 and pop pointer 0 to anchor `this`.
* On the call, the object is pushed FIRST.
* Must return a value: If void, push constant 0, in caller pop temp 0
Arrays
* Construction is like any other object:
  * Declaration just updates the symbol table
  * Calling the constructor assigns a pointer
  * Set THAT (`pop pointer 1`) for array access.
  * No matter the index, always `pop that 0` to write
    * To get arr[10]: push arr, push 10, add, pop pointer 1, push that 0, pop <wherever>
    * Otherwise you can't use variable indices.
    * Need to use temp for array to array access since they both need to set `that`
VM Mapping:
* *.jack => *.vm
* subroutine "sub" in file "class" will be named "class.sub" in the .vm
* Methods map to functions with 1 extra argument
* subroutines and constructors map to functions with the same number of arguments
Constants:
* null and false are 0
* true is -1: push 1; neg
"""

Token = namedtuple("Token", "type, value")

class Tokenizer():
    def __init__(self, filename):
        with open(filename, "r") as f:
            self._code = f.read()
        self._cleancode = ""

    def lex(self):
        """Yield Tokens: Token(<type>, <value>)."""
        for m in re.finditer(JACK_TOKEN_RE, self._code, re.MULTILINE | re.DOTALL):
            typ = m.lastgroup
            if typ != "comment":
                yield Token(typ, m.group(typ))
