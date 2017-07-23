import collections
import xml.etree.ElementTree as ET

TYPES = {"int", "char", "boolean", "void"}
IDENTIFIER_KEYWORDS = {"this"}
INFIX_OPS = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
UNARY_OPS = {
    "-": "neg",
    "~": "not"
}
KEYWORD_CONSTANTS = {
    "true": 1,
    "false": 0,
    "null": 0,
    "this": 0
}


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
            self.add_symbol("this", "object", "argument")

    def add_symbol(self, name, typ, kind):
        s = Symbol(name, typ, kind, self.counts[kind])
        self.counts[kind] += 1
        if kind in self.class_kinds:
            self.class_table[name] = s
        else:
            self.sub_table[name] = s
        self.syms[name] = s

    def get(self, name):
        try:
            return self.syms[name]
        except KeyError:
            raise Exception("Symbol {} not defined!".format(name))

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
        s = compile_class(token, tokengen)
    else:
        raise JackSyntaxError("Class file must begin with class declaration")


def compile_class(t, tokengen):
    """
    'class' className '{' classVarDec* subroutineDec* '}'
    """
    s = []
    # class keyword
    t = next(tokengen)
    # className
    name = t.value
    t = next(tokengen)
    # '{' symbol
    t = next(tokengen)

    # classvars
    while t.type == "keyword" and (t.value == "static" or t.value == "field"):
        build_classvars(t, tokengen)
        t = next(tokengen)

    # subroutines
    while t.type == "keyword" and (t.value == "constructor" or t.value == "function" or t.value == "method"):
        s += compile_subroutine(t, tokengen)
        t = next(tokengen)

    # '}' symbol
    expect(t, "}")

    return s


def compile_subroutine(t, tokengen):
    """
    ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')'
    subroutineBody
    """
    s = []
    # constructor, function, or method
    if t.value == "constructor" or t.value == "method":
        is_method = True
    else:
        is_method = False
    t = next(tokengen)
    # type
    t = next(tokengen)
    # subroutineName
    # TODO: Figure out the right name, if method, num locals, etc
    s.append("function {} x".format(t.value))
    t = next(tokengen)
    # '(' parameterList ')'
    st.start_subroutine(method=is_method)
    # TODO: Will it need to return anything?
    build_parameter_list(t, tokengen)
    t = next(tokengen)
    # subroutineBody
    # TODO: Does it need to know whether the subroutine is a method?
    s += compile_subroutine_body(t, tokengen)

    return s


def compile_subroutine_body(t, tokengen):
    """
    '{' varDec* statements '}'
    """
    s = []
    # '{'
    expect(t, "{")

    # Add all declarations to the symbol table
    t = next(tokengen)
    while t.value == "var":
        build_vars(t, tokengen)
        t = next(tokengen)

    s += compile_statements(t, tokengen)
    t = next(tokengen)
    expect(t, "}")
    # TODO: Clear out local symbols?
    return s


def build_classvars(t, tokengen):
    return build_vars(t, tokengen)


def build_vars(t, tokengen):
    """
    Normal:
    'var' type varName (',', varName)* ';'
    Class:
    ('static' | 'field') type varName (',' varName)* ';'
    This function only modifies the symbol table, it does not generate code.
    """
    # var, static, or field
    kind = t.value
    t = next(tokengen)
    # type
    type = t.value
    t = next(tokengen)
    # varName
    st.add_symbol(t.value, type, kind)
    t = next(tokengen)
    while t.value == ",":
        # comma symbol
        t = next(tokengen)
        # varName
        st.add_symbol(t.value, type, kind)
        t = next(tokengen)


def build_parameter_list(t, tokengen):
    """
    ((type varName)(',' type varName)*)?
    This function only modifies the symbol table, it does not generate code.
    """
    # We include the surrounding parens
    # '('
    t = next(tokengen)
    # parameterList
    while t.value in TYPES or t.type == "identifier":
        # type
        typ = t.value
        t = next(tokengen)
        # varName
        st.add_symbol(t.value, typ, "argument")
        t = next(tokengen)

        while t.value == ",":
            # comma
            t = next(tokengen)
            # type
            typ = t.value
            t = next(tokengen)
            # varName
            st.add_symbol(t.value, typ, "argument")
            t = next(tokengen)
    # ')'
    expect(t, ")")


def compile_do(t, tokengen):
    """
    'do' subroutineCall ';'
         subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
    """
    s = []
    # let keyword
    expect(t, "do")
    t = next(tokengen)
    name = t.value
    # Either a subroutineName directly or an object or varName followed by a dot and a subroutine name
    # Either way, it's first an identifier
    # -- subroutineName OR className | varName
    t = next(tokengen)
    if t.value == ".":  # Method call
        # -- '.' symbol
        expect(t, ".")
        t = next(tokengen)
        # subroutineName
        name = name + "." + t.value
        # TODO: Check symbol table to determine if the first identifier is a symbol or a class
        t = next(tokengen)

    # '(' symbol
    expect(t, "(")
    t = next(tokengen)

    # expressionList
    s += compile_expression_list(t, tokengen)
    t = next(tokengen)

    # ')' symbol
    expect(t, ")")
    t = next(tokengen)

    # ';' symbol
    expect(t, ";")

    s.append("call {}".format(name))

    return s


def compile_let(t, tokengen):
    """
    'let' varName( '[' expression ']' )? '=' expression ';'
    """
    s = []
    # let keyword
    expect(t, "let")
    # varName
    t = next(tokengen)
    name = t.value

    t = next(tokengen)
    # TODO: Find the variable in the symbol table
    # Allow square brackets
    if t.value == "[":
        # TODO: Array!
        # '[' symbol
        t = next(tokengen)
        # single expression
        s += compile_expression(t, tokengen)
        t = next(tokengen)
        # ']' symbol
        expect(t, "]")
        t = next(tokengen)
    # '='
    expect(t, "=")
    t = next(tokengen)
    # single expression
    s += compile_expression(t, tokengen)
    t = next(tokengen)
    # ';'
    expect(t, ";")

    # TODO: pop it into the target variable
    s.append("pop {}".format(name))

    return s


def compile_while(t, tokengen):
    """
    'while' '(' expression ')' '{' statements '}'
    """
    s = []
    # while keyword
    expect(t, "while")
    t = next(tokengen)
    # '(' symbol
    t = next(tokengen)
    # single expression
    s += compile_expression(t, tokengen)
    t = next(tokengen)
    # ')' symbol
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    s += compile_statements(t, tokengen)
    t = next(tokengen)
    # '}' symbol
    expect(t, "}")

    return s


def compile_return(t, tokengen):
    """
    'return' expression? ';'
    """
    s = []
    # return keyword
    t = next(tokengen)

    # 1 or 0 expressions
    if t.value != ";":
        s += compile_expression(t, tokengen)
        t = next(tokengen)
    # Semicolon already removed

    s.append("return")

    return s


def compile_if(t, tokengen):
    """
    'if' '(' expression ')' '{' statements '}'
    ('else' '{' statements '}')?
    """
    s = []
    # if keyword
    expect(t, "if")
    t = next(tokengen)
    # '(' symbol
    expect(t, "(")
    t = next(tokengen)
    # single expression
    compile_expression(t, tokengen)
    t = next(tokengen)
    # ')' symbol
    expect(t, ")")
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    compile_statements(t, tokengen)
    t = next(tokengen)
    # '}' symbol
    expect(t, "}")

    tp = tokengen.peek()
    if tp.value != "else":
        return s

    t = next(tokengen)
    # else keyword
    expect(t, "else")
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    compile_statements(t, tokengen)
    t = next(tokengen)
    # '}' symbol
    expect(t, "}")

    return s


STATEMENT_TYPES = {
    "let": compile_let,
    "if": compile_if,
    "while": compile_while,
    "do": compile_do,
    "return": compile_return,
}


def compile_statements(t, tokengen):
    s = []
    while t.value != '}': # TODO: Better test?
        s += compile_statement(t, tokengen)
        t = next(tokengen)

    tokengen.pushback(t)
    return s

def compile_statement(t, tokengen):
    return STATEMENT_TYPES[t.value](t, tokengen)


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
    s = []

    if t.type in {"integerConstant", "stringConstant"}:
        # type = number
        # TODO: How to do get string address?
        s.append("push {}".format(t.value))
    elif t.value in KEYWORD_CONSTANTS:
        # type = number
        # TODO: How do we handle `this`?
        s.append("push constant {}".format(t.value))
    elif t.value in UNARY_OPS:
        # type = unary
        op = t.value
        t = next(tokengen)
        s += compile_term(t, tokengen)
        s.append(UNARY_OPS[op])
    elif t.value == "(":
        # '(' symbol
        t = next(tokengen)

        # expression
        s += compile_expression(t, tokengen)
        t = next(tokengen)

        # ')' symbol
        expect(t, ")")
    else:  # an identifier, with either possibly a call or indexing
        # TODO: Pull these from the symbol table that was built in the class and method declaration
        expect_type(t, "identifier")
        name = t.value
        tp = tokengen.peek()
        if tp.value == ".":  # Method call
            t = next(tokengen)
            # -- '.' symbol
            expect(t, ".")
            t = next(tokengen)
            # subroutineName
            name = name + "." + t.value
            t = next(tokengen)

            # '(' symbol
            expect(t, "(")
            t = next(tokengen)

            # expressionList
            s += compile_expression_list(t, tokengen)
            t = next(tokengen)

            # ')' symbol
            expect(t, ")")

            # Now with the args set up call the method
            s.append("call {}".format(name))
        elif tp.value == "[":  # Array access
            t = next(tokengen)
            # '[' symbol
            expect(t, "[")
            t = next(tokengen)

            # expression
            s += compile_expression(t, tokengen)
            t = next(tokengen)

            # ']' symbol
            expect(t, "]")
        elif tp.value == "(":  # Function call
            t = next(tokengen)
            # '(' symbol
            expect(t, "(")
            t = next(tokengen)

            # expressionList
            s += compile_expression_list(t, tokengen)
            t = next(tokengen)

            # ')' symbol
            expect(t, ")")

            # Now with args set up call the function
            s.append("call {}".format(name))
        else:  # Just a reference
            # In this case we DON'T pop the peeked token
            # TODO: Find section and index
            s.append("push {}".format(name))
            pass

    return s


def compile_expression_list(t, tokengen):
    """
    (expression (',' expression)*)?
    """
    s = []
    while t.value != ")":
        s += compile_expression(t, tokengen)
        t = next(tokengen)
        while t.value == ",":
            t = next(tokengen)
            s += compile_expression(t, tokengen)
            t = next(tokengen)

    tokengen.pushback(t)
    return s

def compile_expression(t, tokengen):
    """
    term (op term)*
    """
    # TODO: Build tree
    # left = first term
    # parent = op
    # right = second term (recurse here)
    # Better algo: 'codewrite'
    """
    class Expression:
        def __init__(self):
            self.type = {"number", "var", "binary", "unary", "call"}
            self.op = None
            self.exprs = []

        def write(self):
            s = []
            if self.type == "number":
                s += "push <number>"
            elif self.type == "var":
                s += "push <var>"
            elif self.type == "binary":
                s += self.exp[0].write()
                s += self.exp[1].write()
                s += "<op>"
            elif self.type == "unary":
                s += self.exp[0].write()
                s += "<op>"
            elif self.type == "call":
                for exp in self.exprs:
                    s += exp.write()
                s += "call <func>"
            else:
                raise Exception("wtf is going on?")

            return s
    """

    s = []
    # term
    s += compile_term(t, tokengen)
    t = tokengen.peek()
    if t.value in INFIX_OPS:
    # while t.value in INFIX_OPS:
        # Remove peeked value
        next(tokengen)
        op = t.value
        t = next(tokengen)
        # term
        # TODO: Should we consider this next term a new expression (and not need the loop?)
        s += compile_expression(t, tokengen)
        # s += compile_term(t, tokengen)
        t = tokengen.peek()
        # Emit op last
        s.append(op) # TODO: Is this a call?

    return s
    # TODO: Post-order walk the tree, pushing terms, calling ops
