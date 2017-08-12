from collections import namedtuple
from os import path as op
import collections
import glob
import re
import sys
import xml.etree.ElementTree as ET

import compilation_engine
from tokenizer import Tokenizer
"""
class VMWriter():
    def __init__(self, file):
        self.file = file

    def write_push
    def write_pop
    def write_arith
    def write_label
    def write_goto
    def write_if
    def write_call
    def write_function
    def write_return
    def close
"""

"""
class CompilationEngine()
# Takes tokens from tokenizer and writes output using VMWriter
Read next token, dispatch to correct compilexxx method, emit vm code
    def __init__
    def compile_class
    def compile_class_var_dec
    def compile_subroutine_dec
    def compile_parameter_list
    def compile_subroutine_body
    def compile_vardec
    def compile_statements
    def compile_do
    def compile_let
    def compile_while
    def compile_return
    def compile_if
    def compile_expression
    def compile_term
    def compile_expression_list
    """
class PeekaheadIterator():
    def __init__(self, it):
        self.count = 0
        self.it = it
        self.items = collections.deque()

    def __iter__(self):
        return self

    def __next__(self):
        # Yuck. Needed to guarantee unique labels
        self.count += 1
        if self.items:
            return self.items.popleft()
        return next(self.it)

    def pushback(self, *items):
        self.items.extendleft(items)

    def peek(self):
        """Return the next token without removing it."""
        item = next(self)
        self.pushback(item)
        return item


def main(filepath):
    xml = []
    if op.isdir(filepath):
        path = filepath
        files = glob.glob("{}/*.jack".format(filepath))
    else:
        path = op.dirname(filepath)
        files = [filepath]

    for fn in files:
        classname = op.splitext(op.basename(op.normpath(op.realpath(fn))))[0]
        # Read in lines
        tokenizer = Tokenizer(fn)

        with open(op.join(path, "{}.vm".format(classname)), "w") as f:
            compilation_engine.dispatch_compile(classname, PeekaheadIterator(tokenizer.lex()), f)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <input>".format(sys.argv[0]))
        sys.exit(1)

    main(sys.argv[1])
