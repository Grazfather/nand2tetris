import collections
import xml.etree.ElementTree as ET

TYPES = {"int", "char", "boolean", "void"}
IDENTIFIER_KEYWORDS = {"this"}
INFIX_OPS = {
    "+": "add",
    "-": "sub",
    "*": "call Math.multiply 2",
    "/": "call Math.divide 2",
    "&": "and",
    "|": "or",
    "<": "lt",
    ">": "gt",
    "=": "eq"
}
UNARY_OPS = {
    "-": "neg",
    "~": "not"
}
KEYWORD_CONSTANTS = {
    "true": "constant 0\nnot", # barf
    "false": "constant 0",
    "null": "constant 0",
    "this": "pointer 0"
}


class JackSyntaxError(Exception):
    """An exception raised when the compiler hits an unexpected case."""

Symbol = collections.namedtuple("Symbol", "name, type, kind, section, index")

class SymbolTable():
    CLASS_KINDS = {"static", "field"}
    SUB_KINDS = {"argument", "var"}
    KIND_SECTION = {
        "static": "static",
        "field": "this",
        "argument": "argument",
        "var": "local",
    }

    def __init__(self):
        self.class_table = {}
        self.sub_table = {}
        self.counts = collections.defaultdict(lambda: 0)

    def start_subroutine(self, method=False):
        # Reset counts for subroutine kinds
        for kind in self.SUB_KINDS:
            self.counts[kind] = 0
        # Start new sub table
        self.sub_table = {}
        # If the new subroutine is a method, add implicit 'this'
        if method:
            self.add_symbol("this", "object", "argument")

    def add_symbol(self, name, typ, kind):
        section = self.KIND_SECTION[kind]
        s = Symbol(name, typ, kind, section, self.counts[kind])
        self.counts[kind] += 1
        if kind in self.CLASS_KINDS:
            self.class_table[name] = s
        else:
            self.sub_table[name] = s

    def get(self, name):
        try:
            return self.sub_table[name]
        except KeyError:
            try:
                return self.class_table[name]
            except KeyError:
                raise Exception("Symbol {} not defined!".format(name)) from None

    def varcount(self, kind):
        return self.counts[kind]


def push_symbol(symbol):
    return "push {0.section} {0.index}\t// {0.name}".format(symbol)


def pop_symbol(symbol):
    return "pop {0.section} {0.index}\t// {0.name}".format(symbol)


def write_label(label):
    return "label {}".format(label)


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
    writer.write("\n".join(s))


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
    while t.type == "keyword" and t.value in ("static", "field"):
        build_classvars(t, tokengen)
        t = next(tokengen)

    # subroutines
    while t.type == "keyword" and t.value in ("constructor", "function", "method"):
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
    kind = t.value
    t = next(tokengen)
    # type
    t = next(tokengen)
    # subroutineName
    name = t.value
    t = next(tokengen)
    # '(' parameterList ')'
    st.start_subroutine(method=kind == "method")
    build_parameter_list(t, tokengen)
    s.append("function {}.{} {{}}".format(classname, name))
    index = len(s) - 1

    t = next(tokengen)
    # subroutineBody
    if kind == "method":
        s += compile_method(t, tokengen)
    elif kind == "constructor":
        s += compile_constructor(t, tokengen)
    else:
        s += compile_subroutine_body(t, tokengen)

    # Yuck: Since we don't know the number of locals until we compile the
    # subroutine, we go back and adjust the function declaration
    num = st.varcount("var")
    s[index] = s[index].format(num)
    return s


def compile_method(t, tokengen):
    s = []
    # Methods have implied 'this' argument
    s.append("push argument 0")
    s.append("pop pointer 0")
    # Constructors always end in "return this" so rv is handled
    s += compile_subroutine_body(t, tokengen)
    return s


def compile_constructor(t, tokengen):
    s = []
    # Constructors have implied call to Memory.alloc
    size = st.varcount("field")
    s.append("push constant {}".format(size))
    s.append("call Memory.alloc 1")
    s.append("pop pointer 0")
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
    Return the number of parameters.
    """
    num = 0
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
        num += 1
        t = next(tokengen)

        while t.value == ",":
            # comma
            t = next(tokengen)
            # type
            typ = t.value
            t = next(tokengen)
            # varName
            st.add_symbol(t.value, typ, "argument")
            num += 1
            t = next(tokengen)
    # ')'
    expect(t, ")")
    return num


def compile_do(t, tokengen):
    """
    'do' subroutineCall ';'
         subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
    """
    s = []
    numargs = 0
    # do keyword
    expect(t, "do")
    t = next(tokengen)
    name = t.value
    # Either a subroutineName directly or an object or varName followed by a dot and a subroutine name
    # Either way, it's first an identifier
    # -- subroutineName OR className | varName
    t = next(tokengen)
    if t.value == ".":  # Function or method call on object
        # -- '.' symbol
        expect(t, ".")
        t = next(tokengen)
        # subroutineName
        try:
            # If the identifier is a symbol, get its type to namespace the
            # call and its name to push as 'this'
            symbol = st.get(name)
            name = symbol.type + "." + t.value
            s.append(push_symbol(symbol))
            numargs += 1
        except:
            # Otherwise, must be a class function call, no extra args
            name = name + "." + t.value
        t = next(tokengen)
    else:  # If the object or class isn't specified, it's a 'thismethod'
        s.append("push pointer 0")
        numargs += 1
        name = classname + "." + name

    # '(' symbol
    expect(t, "(")
    t = next(tokengen)

    # expressionList
    args, n = compile_expression_list(t, tokengen)
    s += args
    numargs += n
    t = next(tokengen)

    # ')' symbol
    expect(t, ")")
    t = next(tokengen)

    # ';' symbol
    expect(t, ";")

    s.append("call {} {}".format(name, numargs))
    # Throw away the return value
    s.append("pop temp 0")

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
    symbol = st.get(name)

    poptarget = []

    t = next(tokengen)
    # Array access
    if t.value == "[":
        # '[' symbol
        t = next(tokengen)
        # single expression (offset into array)
        s += compile_expression(t, tokengen)
        # push symbol
        s.append(push_symbol(symbol))
        # add the offset
        s.append("add")
        # can't pop it into `that` yet: there might be other array access that'll trash `that`.
        t = next(tokengen)
        # ']' symbol
        expect(t, "]")
        t = next(tokengen)
        poptarget.append("pop temp 0\t// pop expression to assign")
        poptarget.append("pop pointer 1\t// pop target pointer into that")
        poptarget.append("push temp 0\t// push expression back")
        poptarget.append("pop that 0\t// pop into that[0]")
    else:
        poptarget.append(pop_symbol(symbol))
    # '='
    expect(t, "=")
    t = next(tokengen)
    # single expression
    s += compile_expression(t, tokengen)
    t = next(tokengen)
    # ';'
    expect(t, ";")
    s += poptarget


    return s


def compile_while(t, tokengen):
    """
    'while' '(' expression ')' '{' statements '}'
    """
    top_label = "WHILE_TOP_{}".format(tokengen.count)
    end_label = "WHILE_END_{}".format(tokengen.count)
    s = []
    # while keyword
    expect(t, "while")
    t = next(tokengen)
    # '(' symbol
    t = next(tokengen)
    s.append(write_label(top_label))
    # single expression
    s += compile_expression(t, tokengen)
    t = next(tokengen)
    # ')' symbol
    # Negate the expression since we jump if it ISN'T true
    s.append("not")
    s.append("if-goto {}".format(end_label))
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    s += compile_statements(t, tokengen)
    t = next(tokengen)
    # '}' symbol
    expect(t, "}")
    s.append("goto {}".format(top_label))
    s.append(write_label(end_label))

    return s


def compile_return(t, tokengen):
    """
    'return' expression? ';'
    """
    s = []
    # return keyword
    t = next(tokengen)

    # optional expression
    if t.value != ";":
        s += compile_expression(t, tokengen)
        t = next(tokengen)
    else:
        s.append("push constant 0")
    # Semicolon already removed
    expect(t, ";")

    s.append("return")

    return s


def compile_if(t, tokengen):
    """
    'if' '(' expression ')' '{' statements '}'
    ('else' '{' statements '}')?
    """
    else_label = "IF_ELSE_{}".format(tokengen.count)
    end_label = "IF_END_{}".format(tokengen.count)
    s = []
    # if keyword
    expect(t, "if")
    t = next(tokengen)
    # '(' symbol
    expect(t, "(")
    t = next(tokengen)
    # single expression
    s += compile_expression(t, tokengen)
    t = next(tokengen)
    # ')' symbol
    expect(t, ")")
    # Negate the expression since we jump if it ISN'T true
    s.append("not")
    s.append("if-goto {}".format(else_label))
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    s += compile_statements(t, tokengen)
    t = next(tokengen)
    # '}' symbol
    expect(t, "}")

    # If there's no else, then we're done
    tp = tokengen.peek()
    if tp.value != "else":
        s.append(write_label(else_label))
        return s

    # Done the if block, jump over the else
    s.append("goto {}".format(end_label))
    s.append(write_label(else_label))

    t = next(tokengen)
    # else keyword
    expect(t, "else")
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    t = next(tokengen)
    # statements
    s += compile_statements(t, tokengen)
    t = next(tokengen)
    # '}' symbol
    expect(t, "}")
    s.append(write_label(end_label))

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

    if t.type == "integerConstant":
        # type = number
        # TODO: How to do get string address?
        s.append("push constant {}".format(t.value))
    elif t.type == "stringConstant":
        l = len(t.value)
        s.append("push constant {}\t// Creating string \"{}\"".format(l, t.value))
        s.append("call String.new 1")
        for c in t.value:
            s.append("push constant {}".format(ord(c)))
            s.append("call String.appendChar 2")
    elif t.value in KEYWORD_CONSTANTS:
        # type = number
        # TODO: How do we handle 'this'?
        s.append("push {}".format(KEYWORD_CONSTANTS[t.value]))
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
        if tp.value == ".":  # Method/class function call
            numargs = 0
            try:
                # If the identifier is a symbol, get its type to namespace the
                # call and its name to push 'this'
                symbol = st.get(name)
                name = symbol.type
                s.append(push_symbol(symbol))
                numargs += 1
            except:
                # Otherwise, must be a function or constructor call
                pass
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
            args, n = compile_expression_list(t, tokengen)
            s += args
            numargs += n
            t = next(tokengen)

            # ')' symbol
            expect(t, ")")

            # Now with the args set up call the method
            s.append("call {} {}".format(name, numargs))
        elif tp.value == "[":  # Array access
            t = next(tokengen)
            # '[' symbol
            expect(t, "[")
            t = next(tokengen)

            # expression for index
            s += compile_expression(t, tokengen)
            symbol = st.get(name)
            s.append(push_symbol(symbol))
            # add array base to index
            s.append("add")
            # pop into that
            s.append("pop pointer 1")
            # push value at that[0]
            s.append("push that 0")
            t = next(tokengen)

            # ']' symbol
            expect(t, "]")
        elif tp.value == "(":  # This method call
            # Push 'this'
            s.append("push pointer 0")
            numargs = 1
            t = next(tokengen)
            # '(' symbol
            expect(t, "(")
            t = next(tokengen)

            # expressionList
            args, n = compile_expression_list(t, tokengen)
            s += args
            numargs += n
            t = next(tokengen)

            # ')' symbol
            expect(t, ")")

            # Now with args set up call the function
            s.append("call {} {}".format(name, numargs))
        else:  # Just a reference
            # In this case we DON'T pop the peeked token
            # TODO: Find section and index
            symbol = st.get(name)
            s.append(push_symbol(symbol))
            pass

    return s


def compile_expression_list(t, tokengen):
    """
    (expression (',' expression)*)?
    """
    s = []
    n = 0
    while t.value != ")":
        s += compile_expression(t, tokengen)
        n += 1
        t = next(tokengen)
        while t.value == ",":
            t = next(tokengen)
            s += compile_expression(t, tokengen)
            n += 1
            t = next(tokengen)

    tokengen.pushback(t)
    return s, n

def compile_expression(t, tokengen):
    """
    term (op term)*
    """

    s = []
    # term
    s += compile_term(t, tokengen)
    t = tokengen.peek()
    if t.value in INFIX_OPS:
        # Remove peeked value
        next(tokengen)
        op = INFIX_OPS[t.value]
        t = next(tokengen)
        # term
        # TODO: Should we consider this next term a new expression (and not need the loop?)
        s += compile_expression(t, tokengen)
        t = tokengen.peek()
        # Emit op last
        s.append(op)

    return s
