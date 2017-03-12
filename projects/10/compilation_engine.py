import xml.etree.ElementTree as ET

TYPES = {"int", "char", "boolean", "void"}
IDENTIFIER_KEYWORDS = {"this"}


class JackSyntaxError(Exception):
    """An exception raised when the compiler hits an unexpected case."""


def expect(token, value):
    if token[1] != value:
        raise JackSyntaxError("Expected '{}', got '{}'".format(value, token[1]))


def dispatch_compile(tokengen):
    token = next(tokengen)
    ttype, value = token
    if ttype == "keyword":
        if value == "class":
            return compile_class(token, tokengen)
        elif value == "static" or value == "field":
            return compile_classvardec(token, tokengen)
        elif value == "constructor" or value == "function" or value == "method":
            return compile_subroutine(token, tokengen)
        elif value == "var":
            return compile_vardec(token, tokengen)
    else:
        raise JackSyntaxError


def compile_class(t, tokengen):
    """
    'class' className '{' classVarDec* subroutineDec* '}'
    """
    # class keyword
    root = ET.Element("class")
    node = ET.SubElement(root, "keyword")
    node.text = "class"
    t = next(tokengen)
    # className
    node = ET.SubElement(root, "identifier")
    node.text = t[1]
    t = next(tokengen)
    # '{' symbol
    expect(t, "{")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)

    # classvars
    while t[0] == "keyword" and (t[1] == "static" or t[1] == "field"):
        node = compile_classvardec(t, tokengen)
        root.append(node)
        t = next(tokengen)

    # subroutines
    while t[0] == "keyword" and (t[1] == "constructor" or t[1] == "function" or t[1] == "method"):
        node = compile_subroutine(t, tokengen)
        root.append(node)
        t = next(tokengen)

    # '}' symbol
    expect(t, "}")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    return root


def compile_subroutine(t, tokengen):
    """
    ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')'
    subroutineBody
    """
    print("subroutine {}".format(t))
    root = ET.Element("subroutineDec")
    # constructor, function, or method
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # type
    if t[0] == "identifier":
        node = ET.SubElement(root, "identifier")
    else:
        node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # subroutineName
    node = ET.SubElement(root, "identifier")
    node.text = t[1]
    t = next(tokengen)
    # '(' parameterList ')'
    node = compile_parameter_list(t, tokengen)
    root.extend(node)
    t = next(tokengen)
    # subroutineBody
    node = compile_subroutine_body(t, tokengen)
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
    # while t[1] != '}': # TODO: Better test?
        # node = compile_statement(t, tokengen)
        # root.append(node)
        # t = next(tokengen)
    # '}'
    expect(t, "}")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    return root


def compile_classvardec(t, tokengen):
    return compile_vardec(t, tokengen, el="classVarDec")


def compile_vardec(t, tokengen, el="varDec"):
    """
    Normal:
    'var' type varName (',', varName)* ';'
    Class:
    ('static' | 'field') type varName (',' varName)* ';'
    """
    root = ET.Element(el)
    # var, static, or field
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # type
    if t[1] in TYPES:
        node = ET.SubElement(root, "keyword")
        node.text = t[1]
    else:
        node = ET.SubElement(root, "identifier")
        node.text = t[1]
    t = next(tokengen)
    # varName
    node = ET.SubElement(root, "identifier")
    node.text = t[1]
    t = next(tokengen)
    while t[1] == ",":
        # comma symbol
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)
        # varName
        node = ET.SubElement(root, "identifier")
        node.text = t[1]
        t = next(tokengen)
    # Semicolon
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    return root


def compile_parameter_list(t, tokengen):
    """
    ((type varName)(',' type varName)*)?
    """
    # We include the surrounding parens
    # '('
    nodes = []
    node = ET.Element("symbol")
    node.text = t[1]
    nodes.append(node)
    t = next(tokengen)
    # parameterList
    root = ET.Element("parameterList")
    root.text = "\n"
    while t[1] in TYPES or t[0] == "identifier":
        # type
        if t[1] in TYPES:
            node = ET.SubElement(root, "keyword")
            node.text = t[1]
        else:
            node = ET.SubElement(root, "identifier")
            node.text = t[1]
        t = next(tokengen)
        # varName
        node = ET.SubElement(root, "identifier")
        node.text = t[1]
        t = next(tokengen)

        while t[1] == ",":
            # comma
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)
            # type
            if t[1] in TYPES:
                node = ET.SubElement(root, "keyword")
                node.text = t[1]
            else:
                node = ET.SubElement(root, "identifier")
                node.text = t[1]
            t = next(tokengen)
            # varName
            node = ET.SubElement(root, "identifier")
            node.text = t[1]
            t = next(tokengen)
    nodes.append(root)
    # ')'
    expect(t, ")")
    node = ET.Element("symbol")
    node.text = t[1]
    nodes.append(node)

    return nodes


def compile_do(t, tokengen):
    """
    'do' subroutineCall ';'
         subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
    """
    print("In compile do {}".format(t))
    root = ET.Element("doStatement")
    # let keyword
    expect(t, "do")
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # Either a subroutineName directly or an object or varName followed by a dot and a subroutine name
    # Either way, it's first an identifier
    # -- subroutineName OR className | varName
    node = ET.SubElement(root, "identifier")
    node.text = t[1]
    t = next(tokengen)
    if t[1] == ".":  # Method call
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
    # TODO: Handle expressions
    t, node = compile_expression_list(t, tokengen)
    root.append(node)
    while t[1] != ")": t = next(tokengen)

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
    root = ET.Element("letStatement")
    # let keyword
    expect(t, "let")
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # varName
    node = ET.SubElement(root, "identifier")
    node.text = t[1]
    t = next(tokengen)
    # Allow square brackets
    if t[1] == "[":
        # '[' symbol
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)
        # single expression
        node = compile_expression(t, tokengen)
        root.append(node)
        t = next(tokengen)
        # ']' symbol
        expect(t, "]")
        node = ET.SubElement(root, "symbol")
        node.text = t[1]
        t = next(tokengen)
    # '='
    expect(t, "=")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    # single expression
    node = compile_expression(t, tokengen)
    root.append(node)
    t = next(tokengen)
    # ';'
    expect(t, ";")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]

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
    node = compile_expression(t, tokengen)
    root.append(node)
    t = next(tokengen)
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
    # '}' symbol
    expect(t, "}")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)


def compile_return(t, tokengen):
    """
    'return' expression? ';'
    """
    root = ET.Element("returnStatement")
    # return keyword
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # 1 or 0 expressions
    if t[1] != ";":
        node = compile_expression(t, tokengen)
        root.append(node)
        t = next(tokengen)
    # Semicolon
    node = ET.SubElement(root, "symbol")
    node.text = t[1]

    return root


def compile_if(t, tokengen):
    """
    'if' '(' expression ')' '{' statements '}'
    ('else' '{' statements '}')?
    """
    root = ET.Element("ifStatement")
    # if keyword
    expect(t, "if")
    node = ET.SubElement(root, "keyword")
    node.text = t[1]
    t = next(tokengen)
    # '(' symbol
    expect(t, "(")
    node = ET.SubElement(root, "symbol")
    node.text = t[1]
    t = next(tokengen)
    # single expression
    node = compile_expression(t, tokengen)
    root.append(node)
    t = next(tokengen)
    # ')' symbol
    expect(t, ")")
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
    print("statement {}".format(t))
    return STATEMENT_TYPES[t[1]](t, tokengen)


def compile_term(tokengen):
    """
    """
    # This has to do a look ahead to distinguish between:
    # varName
    # varName '[' expression ']'
    # subroutine call:
    #   subroutineName '(' expressionList ')' |
    #   (className | varName) '.' subroutineName '(' expressionList ')'
    pass
    # Include subroutine calls here


def compile_expression_list(t, tokengen):
    """
    (expression (',' expression)*)?
    """
    root = ET.Element("expressionList")
    root.text = "\n"
    # TODO: For now these are all identifiers or keywords
    while t[0] == "identifier" or t[1] in IDENTIFIER_KEYWORDS:
        node = compile_expression(t, tokengen)
        root.append(node)
        t = next(tokengen)
        while t[1] == ",":
            # comma symbol
            node = ET.SubElement(root, "symbol")
            node.text = t[1]
            t = next(tokengen)
            node = compile_expression(t, tokengen)
            root.append(node)
            t = next(tokengen)

    return t, root


def compile_expression(t, tokengen):
    """
    term (op term)*
    """
    root = ET.Element("expression")
    # TODO: Do this last: There are test files that have no expressions.
    # For now assume it has a single term that is an identifier
    term = ET.SubElement(root, "term")
    if t[1] in IDENTIFIER_KEYWORDS:
        node = ET.SubElement(term, "keyword")
    else:
        node = ET.SubElement(term, "identifier")
    node.text = t[1]

    return root
