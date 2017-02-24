#!/bin/env python

import sys
import glob
import os.path as op
from collections import namedtuple
from functools import partial

import translations

Command = namedtuple("Command", "line type command arg1 arg2")

ARITH_COMMANDS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
MEM_COMMANDS = {"pop", "push"}
BRANCH_COMMANDS = {"goto", "if-goto", "label"}

COMMAND_MAP = {
    "add": translations.add_command,
    "sub": translations.sub_command,
    "push": translations.push_command,
    "pop": translations.pop_command,
    "neg": translations.neg_command,
    "eq": partial(translations.cmp_command, "EQ"),
    "gt": partial(translations.cmp_command, "GT"),
    "lt": partial(translations.cmp_command, "LT"),
    "and": partial(translations.boolean_command, "&"),
    "or": partial(translations.boolean_command, "|"),
    "not": translations.not_command,
    "goto": translations.goto_command,
    "if-goto": translations.if_goto_command,
    "label": translations.label_command,
    "function": translations.function_command,
    "call": translations.call_command,
    "return": translations.return_command,
}


def parse_line(line):
    line = line.strip()
    # Ignore comments and blank lines
    if not line or line.startswith("//"):
        return None
    # Remove comments
    line = line.split("//")[0].rstrip()
    # Split into tokens
    tokens = line.split(" ")
    # Get command type
    if tokens[0] in MEM_COMMANDS:
        return Command(line, "MEM", tokens[0], tokens[1], tokens[2])
    elif tokens[0] in ARITH_COMMANDS:
        return Command(line, "ARITH", tokens[0], None, None)
    elif tokens[0] in BRANCH_COMMANDS:
        return Command(line, "BRANCH", tokens[0], tokens[1], None)
    elif tokens[0] in {"function", "call"}:
        return Command(line, "FUNC", tokens[0], tokens[1], tokens[2])
    else:  # return
        return Command(line, "FUNC", tokens[0], None, None)



def translate_command(command):
    """Takes a VM command and translates it to hack assembly.
    Return a list of assembly instructions.
    """
    if not command:
        return []

    ins = []
    # Add the original VM command as a comment
    ins.append("// {}".format(command.line))
    # Translate the command into assembly
    asm = COMMAND_MAP[command.command](command)

    ins.extend(asm)

    return ins


def main(filepath):
    if op.isdir(filepath):
        path = filepath
        module = op.basename(op.normpath(op.realpath(filepath)))
        files = glob.glob("{}/*.vm".format(filepath))
    else:
        path = op.dirname(filepath)
        module = op.splitext(op.basename(filepath))[0]
        files = [filepath]

    asm = []

    for fn in files:
        # UGLY: Filename must communicated with the translator
        translations.filename = op.basename(op.splitext(fn)[0])
        # Read in lines
        with open(fn, "r") as f:
            lines = f.readlines()

        # Parse and translate each line
        translations.count = 0
        for line in lines:
            command = parse_line(line)
            translations.count += 1
            asm.extend(translate_command(command))

    # Write a new asm file
    with open(op.join(path, "{}.asm".format(module)), "w") as f:
        f.write("\n".join(asm))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <vm file or path>".format(sys.argv[0]))
        sys.exit(1)

    main(sys.argv[1])
