import collections
import xml.etree.ElementTree as ET

TYPES = {"int", "char", "boolean", "void"}
IDENTIFIER_KEYWORDS = {"this"}
INFIX_OPS = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
UNARY_OPS = {"-", "~"}
KEYWORD_CONSTANTS = {"true", "false", "null", "this"}


class JackSyntaxError(Exception):
    """An exception raised when the compiler hits an unexpected case."""

Symbol = collections.namedtuple("Symbol", "name, type, kind, index")

class SymbolTable():
    class_kinds = {"static", "field"}
    sub_kinds = {"argument", "var"}

    def __init__(self):
        self.class_table = {}
        self.sub_table = {}
        self.syms = {}
        self.counts = collections.defaultdict(lambda: 0)

    def start_subroutine(self, method=False):
        # Remove subroutine symbols from shared table
        for sym_name in self.sub_table:
            del self.syms[sym_name]
        # Reset counts for subroutine kinds
        for kind in self.sub_kinds:
            self.counts[kind] = 0
        # Start new sub table
        self.sub_table = {}
        # If the new subroutine is a method, add 'this'
        if method:
            self.add_symbol("this", "object", "sub")

    def add_symbol(self, name, typ, kind):
        s = Symbol(name, typ, kind, self.counts[kind])
        self.counts[kind] += 1
        if kind in self.class_kinds:
            self.class_table[name] = s
        else:
            self.sub_table[name] = s
        self.syms[name] = s

    def varcount(self, kind):
        return self.counts[kind]

    def kindof(self, name):
        return self.syms[name].kind

    def typeof(self, name):
        return self.syms[name].type

    def indexof(self, name):
        return self.syms[name].index


def expect(token, value):
    if token.value != value:
        raise JackSyntaxError("Expected '{}', got '{}'".format(value, token.value))


def expect_type(token, typ):
    if token.type != typ:
        raise JackSyntaxError("Expected type '{}', got '{}'".format(typ, token.type))

st = None

# TODO: How are we going to write the code?
def dispatch_compile(_classname, tokengen, writer):
    global st, classname
    st = SymbolTable()
    classname = _classname
    token = next(tokengen)
    typ, value = token
    if typ == "keyword" and value == "class":
        root = compile_class(token, tokengen)
    else:
        raise JackSyntaxError

    # writer.write(ET.tostring(root))


def compile_class(t, tokengen):
    """
    'class' className '{' classVarDec* subroutineDec* '}'
    """
    # class keyword
    t = next(tokengen)
    # className
    name = t[1]
    t = next(tokengen)
    # '{' symbol
    t = next(tokengen)

    # classvars
    while t[0] == "keyword" and (t[1] == "static" or t[1] == "field"):
        compile_classvardec(t, tokengen)
        t = next(tokengen)

    # subroutines
    while t[0] == "keyword" and (t[1] == "constructor" or t[1] == "function" or t[1] == "method"):
        compile_subroutine(t, tokengen)
        t = next(tokengen)

    # '}' symbol
    expect(t, "}")
    # Does it need to return anything?
    # return root


def compile_subroutine(t, tokengen):
    """
    ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')'
    subroutineBody
    """
    root = ET.Element("subroutineDec")
    # constructor, function, or method
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    if node.text == "constructor" or node.text == "method":
        is_method = True
    else:
        is_method = False
    t = next(tokengen)
    # type
    if t[0] == "identifier":
        node = ET.SubElement(root, "identifier-CLASS")
    else:
        node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # subroutineName
    node = ET.SubElement(root, "identifier-SUBROUTINE")
    node.text = t[1]
    t = next(tokengen)
    # '(' parameterList ')'
    st.start_subroutine(method=is_method)
    # TODO: Will it need to return anything?
    compile_parameter_list(t, tokengen)
    # node = compile_parameter_list(t, tokengen)
    root.extend(node)
    t = next(tokengen)
    # subroutineBody
    # TODO: Does it need to know whether the subroutine is a method?
    node = compile_subroutine_body(t, tokengen)
    # node = compile_subroutine_body(t, tokengen, is_method)
    root.append(node)
    return root


def compile_subroutine_body(t, tokengen):
    """
    '{' varDec* statements '}'
    """
    root = ET.Element("subroutineBody")
    # '{'
    expect(t, "{")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    while t[1] == "var":
        node = compile_vardec(t, tokengen)
        root.append(node)
        t = next(tokengen)
    t, node = compile_statements(t, tokengen)
    root.append(node)
    expect(t, "}")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    return root


def compile_classvardec(t, tokengen):
    return compile_vardec(t, tokengen)


def compile_vardec(t, tokengen):
    """
    Normal:
    'var' type varName (',', varName)* ';'
    Class:
    ('static' | 'field') type varName (',' varName)* ';'
    """
    # var, static, or field
    kind = node.text
    t = next(tokengen)
    # type
    typ = node.text
    t = next(tokengen)
    # varName
    st.add_symbol(node.text, typ, kind)
    t = next(tokengen)
    while t[1] == ",":
        # comma symbol
        t = next(tokengen)
        # varName
        st.add_symbol(t[1], typ, kind)
        t = next(tokengen)
    # Semicolon
    return root


def compile_parameter_list(t, tokengen):
    """
    ((type varName)(',' type varName)*)?
    """
    # We include the surrounding parens
    # '('
    t = next(tokengen)
    # parameterList
    while t[1] in TYPES or t[0] == "identifier":
        # type
        typ = t[1]
        t = next(tokengen)
        # varName
        st.add_symbol(t[1], typ, "arg")
        t = next(tokengen)

        while t[1] == ",":
            # comma
            t = next(tokengen)
            # type
            typ = t[1]
            t = next(tokengen)
            # varName
            st.add_symbol(t[1], typ, "arg")
            t = next(tokengen)
    # ')'
    expect(t, ")")

    # TODO: Will it need to return anything?
    # return nodes


def compile_do(t, tokengen):
    """
    'do' subroutineCall ';'
         subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
    """
    root = ET.Element("doStatement")
    # let keyword
    expect(t, "do")
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # Either a subroutineName directly or an object or varName followed by a dot and a subroutine name
    # Either way, it's first an identifier
    # -- subroutineName OR className | varName
    first_ident = node = ET.SubElement(root, "identifier-SUBROUTINE")
    node.text = t[1]
    t = next(tokengen)
    if t[1] == ".":  # Method call
        # -- '.' symbol
        expect(t, ".")
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)
        # subroutineName
        node = ET.SubElement(root, "identifier-SUBROUTINE")
        first_ident.tag = "identifier-BLA"
        # TODO: Check symbol table to determine if the first identifier is a symbol or a class
        node.text = t[1]
        t = next(tokengen)

    # '(' symbol
    expect(t, "(")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)

    # expressionList
    t, node = compile_expression_list(t, tokengen)
    root.append(node)

    # ')' symbol
    expect(t, ")")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)

    # ';' symbol
    expect(t, ";")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]

    return root


def compile_let(t, tokengen):
    """
    'let' varName( '[' expression ']' )? '=' expression ';'
    """
    # let keyword
    t = next(tokengen)
    # varName
    name = t[1]
    t = next(tokengen)
    # Allow square brackets
    if t[1] == "[":
        # TODO: Array!
        # '[' symbol
        t = next(tokengen)
        # single expression
        t, node = compile_expression(t, tokengen)
        root.append(node)
        # ']' symbol
        expect(t, "]")
        t = next(tokengen)
    # '='
    expect(t, "=")
    t = next(tokengen)
    # single expression
    t, node = compile_expression(t, tokengen)
    # ';'
    expect(t, ";")

    return root


def compile_while(t, tokengen):
    """
    'while' '(' expression ')' '{' statements '}'
    """
    root = ET.Element("whileStatement")
    # while keyword
    expect(t, "while")
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # '(' symbol
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    # single expression
    t, node = compile_expression(t, tokengen)
    root.append(node)
    # ')' symbol
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    # statements
    t, node = compile_statements(t, tokengen)
    root.append(node)
    # '}' symbol
    expect(t, "}")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]

    return root


def compile_return(t, tokengen):
    """
    'return' expression? ';'
    """
    root = ET.Element("returnStatement")
    # return keyword
    t = next(tokengen)
    # 1 or 0 expressions
    if t[1] != ";":
        t = compile_expression(t, tokengen)
    # Semicolon

    return root


def compile_if(t, tokengen):
    """
    'if' '(' expression ')' '{' statements '}'
    ('else' '{' statements '}')?
    """
    # if keyword
    expect(t, "if")
    t = next(tokengen)
    # '(' symbol
    expect(t, "(")
    t = next(tokengen)
    # single expression
    t= compile_expression(t, tokengen)
    root.append(node)
    # ')' symbol
    expect(t, ")")
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    t= compile_statements(t, tokengen)
    # '}' symbol
    expect(t, "}")

    tp = tokengen.peek()
    if tp[1] != "else":
        return root

    t = next(tokengen)
    # else keyword
    expect(t, "else")
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    # statements
    t, node = compile_statements(t, tokengen)
    root.append(node)
    # '}' symbol
    expect(t, "}")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]

    return root


STATEMENT_TYPES = {
    "let": compile_let,
    "if": compile_if,
    "while": compile_while,
    "do": compile_do,
    "return": compile_return,
}


def compile_statements(t, tokengen):
    root = ET.Element("statements")
    while t[1] != '}': # TODO: Better test?
        node = compile_statement(t, tokengen)
        root.append(node)
        t = next(tokengen)

    return t, root


def compile_statement(t, tokengen):
    return STATEMENT_TYPES[t[1]](t, tokengen)


def compile_term(t, tokengen):
    """
    integerConstant | stringConstant | keywordConstant |
    varName | varName '[' expression ']' | subroutineCall |
    '(' expression ')' | unaryOp term
    This has to do a look ahead to distinguish between:
    varName
    varName '[' expression ']'
    subroutine call:
      subroutineName '(' expressionList ')' |
      (className | varName) '.' subroutineName '(' expressionList ')'
    """
    root = ET.Element("term")
    if t[0] in {"integerConstant", "stringConstant"}:
        node = ET.SubElement(root, t[0])
        node.text = t[1]
    elif t[1] in KEYWORD_CONSTANTS:
        node = ET.SubElement(root, "keyword")
        node.text = t[1]
    elif t[1] in UNARY_OPS:
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)
        node = compile_term(t, tokengen)
        root.append(node)
    elif t[1] == "(":
        # '(' symbol
        expect(t, "(")
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)

        # expression
        t, node = compile_expression(t, tokengen)
        root.append(node)

        # ')' symbol
        expect(t, ")")
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
    else:  # an identifier, with either possibly a call or indexing
        expect_type(t, "identifier")
        node = ET.SubElement(root, "identifier")
        node.text = t[1]
        tp = tokengen.peek()
        if tp[1] == ".":  # Method call
            t = next(tokengen)
            # -- '.' symbol
            expect(t, ".")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)
            # subroutineName
            node = ET.SubElement(root, "identifier")
            node.text = t[1]
            t = next(tokengen)

            # '(' symbol
            expect(t, "(")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)

            # expressionList
            t, node = compile_expression_list(t, tokengen)
            root.append(node)

            # ')' symbol
            expect(t, ")")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
        elif tp[1] == "[":  # Array access
            t = next(tokengen)
            # '[' symbol
            expect(t, "[")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)

            # expression
            t, node = compile_expression(t, tokengen)
            root.append(node)

            # ']' symbol
            expect(t, "]")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
        elif tp[1] == "(":  # Function call
            t = next(tokengen)
            # '(' symbol
            expect(t, "(")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)

            # expressionList
            t, node = compile_expression_list(t, tokengen)
            root.append(node)

            # ')' symbol
            expect(t, ")")
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            # t = next(tokengen)
        else:  # Just a reference
            # In this case we DON'T pop the peeked token
            pass

    return root


def compile_expression_list(t, tokengen):
    """
    (expression (',' expression)*)?
    """
    root = ET.Element("expressionList")
    root.text = "\n"
    while t[1] != ")":
        t, node = compile_expression(t, tokengen)
        root.append(node)
        while t[1] == ",":
            # comma symbol
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)
            t, node = compile_expression(t, tokengen)
            root.append(node)

    return t, root


def compile_expression(t, tokengen):
    """
    term (op term)*
    """
    root = ET.Element("expression")
    # term
    node = compile_term(t, tokengen)
    root.append(node)
    t = next(tokengen)
    while t[1] in INFIX_OPS:
        # op
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)
        # term
        node = compile_term(t, tokengen)
        root.append(node)
        t = next(tokengen)

    return t, root
