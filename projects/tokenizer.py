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
