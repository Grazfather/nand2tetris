import glob
from os import path as op
import re
import sys
import xml.etree.ElementTree as ET

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

class Tokenizer():
    def __init__(self, filename):
        with open(filename, "r") as f:
            self._code = f.read()
        self._cleancode = ""

    def lex(self):
        """Yield tuple pairs (<type>, <value>)."""
        for m in re.finditer(JACK_TOKEN_RE, self._code, re.MULTILINE | re.DOTALL):
            name = m.lastgroup
            if name != "comment":
                yield name, m.group(name)

    def peek(self):
        """Return the next token without removing it."""
        pass


def main(filepath):
    xml = []
    if op.isdir(filepath):
        path = filepath
        files = glob.glob("{}/*.jack".format(filepath))
    else:
        path = op.dirname(filepath)
        files = [filepath]

    for fn in files:
        # Read in lines
        tokenizer = Tokenizer(fn)
        root = ET.Element('tokens')
        lex = tokenizer.lex()
        for typ, token in lex:
            ET.SubElement(root, typ).text=token
        # xml = CompilationEngine.compile(tokenizer)

        # Write a new xml file
        classname = op.splitext(op.basename(op.normpath(op.realpath(fn))))[0]
        tree = ET.ElementTree(root)
        # For now save them in the current dir
        tree.write("{}T.xml".format(classname))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <input>".format(sys.argv[0]))
        sys.exit(1)

    main(sys.argv[1])
