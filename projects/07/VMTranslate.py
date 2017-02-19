#!/bin/env python

import sys
import os
from collections import namedtuple

import translations

Command = namedtuple("Command", "line type command arg1 arg2")
# from abc import ABCMeta
# class Command(metaclass=ABCMeta):
    # pass

# class ArithmeticCommand(Command):
    # pass

ARITH_COMMANDS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
MEM_COMMANDS = {"pop", "push"}
COMMAND_MAP = {
    "add": translations.add_command,
    "sub": translations.sub_command,
    "push": translations.push_command,
    "pop": translations.pop_command,
    "neg": translations.neg_command,
    "eq": translations.eq_command,
    "gt": translations.gt_command,
    "lt": translations.lt_command,
    "and": translations.and_command,
    "or": translations.or_command,
    "not": translations.not_command,
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
    else:
        return Command(line, "ARITH", tokens[0], None, None)
    # TODO: Add support for other command types


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
    # Read in lines
    with open(filepath, "r") as f:
        lines = f.readlines()

    asm = []
    # Parse and translate each line
    for line in lines:
        command = parse_line(line)
        asm.extend(translate_command(command))

    # Write a new asm file
    fn = os.path.splitext(filepath)[0]
    with open("{}.asm".format(fn), "w") as f:
        f.write("\n".join(asm))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <vm file>".format(sys.argv[0]))
        sys.exit(1)

    main(sys.argv[1])
