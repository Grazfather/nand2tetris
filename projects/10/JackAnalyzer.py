from os import path as op
import collections
import glob
import re
import sys
import xml.etree.ElementTree as ET

from tokenizer import Tokenizer
import compilation_engine


class PeekaheadIterator():
    def __init__(self, it):
        self.it = it
        self.items = collections.deque()

    def __iter__(self):
        return self

    def __next__(self):
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

        # Create tokens XML
        root = ET.Element('tokens')
        lex = tokenizer.lex()
        for typ, token in lex:
            ET.SubElement(root, typ).text=token

        # Write a new xml file
        tree = ET.ElementTree(root)
        # For now save them in the current dir
        tree.write("{}T.xml".format(classname))

        # Now create the parser xml
        root = compilation_engine.dispatch_compile(PeekaheadIterator(tokenizer.lex()))
        tree = ET.ElementTree(root)
        tree.write("{}.xml".format(classname))
        # HACK: Their compare script is broken, need to post-process to match
        with open("{}.xml".format(classname), "r") as f:
            x = f.read().replace("><", ">\n<")
        with open(op.join(path, "{}.xml".format(classname)), "w") as f:
            f.write(x)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <input>".format(sys.argv[0]))
        sys.exit(1)

    main(sys.argv[1])
