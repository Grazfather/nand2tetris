#!/bin/env python

import sys
import os
from collections import namedtuple

# Sets bits a, c1, c2, c3, c4, c5, c6
COMP_TABLE = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}

# Sets bits d1, d2, d3
DEST_TABLE = {
    "null": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

# Sets bits j1, j2, j3
JUMP_TABLE = {
    "null": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

BUILTIN_SYMBOLS = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
}

FIRST_FREE_ADDR = 16
CODE_START = 0

AInstruction = namedtuple("AInstruction", "symbol")
CInstruction = namedtuple("CInstruction", "dest comp jump")


def parse_a_instruction(line):
    symbol = line[1:]

    return AInstruction(symbol)


def parse_c_instruction(line):
    if "=" in line:
        dest, rest = line.split("=")
    else:
        dest = "null"
        rest = line

    if ";" in rest:
        comp, jump = rest.split(";")
    else:
        comp = rest
        jump = "null"

    return CInstruction(dest, comp, jump)


def encode_a_instruction(insn, symbols):
    """Take an AInstruction and return its ascii/binary representation."""
    try:
        addr = int(insn.symbol)
    except:
        addr = symbols[insn.symbol]

    if addr >= (1 << 15):
        raise ValueError("Address {} cannot be encoded in 15 bits".format(addr))

    return "0{:015b}".format(addr)


def encode_c_instruction(insn):
    """Take an CInstruction and return its ascii/binary representation."""
    dest_bits = DEST_TABLE[insn.dest]
    comp_bits = COMP_TABLE[insn.comp]
    jump_bits = JUMP_TABLE[insn.jump]
    return "111{}{}{}".format(comp_bits, dest_bits, jump_bits)


def main(fn):
    # Iterate through
    with open(fn, "r") as f:
        lines = f.readlines()

    symbols = {}
    symbols.update(BUILTIN_SYMBOLS)

    # First pass
    code_addr = 0
    for line in lines:
        line = line.strip()
        # Trim off comments
        line = line.split(" ")[0]
        if line == "" or line.startswith("//"):
            continue
        if line.startswith("("):
            symbol = line.lstrip("(").rstrip(")")
            symbols[symbol] = code_addr
        else:
            code_addr += 1

    # Second pass
    next_addr = FIRST_FREE_ADDR
    code_addr = CODE_START
    output = []
    for line in lines:
        line = line.strip()
        # Trim off comments
        line = line.split(" ")[0]
        if line == "" or line.startswith("//") or line.startswith("("):
            continue
        else:
            if line.startswith("@"):  # 'A' instruction
                ainst = parse_a_instruction(line)
                try:
                    int(ainst.symbol)
                except:
                    if ainst.symbol not in symbols:
                        symbols[ainst.symbol] = next_addr
                        next_addr += 1
                insn = encode_a_instruction(ainst, symbols)
            else:  # 'C' instruction
                cinst = parse_c_instruction(line)
                insn = encode_c_instruction(cinst)

            output.append(insn)

            code_addr += 1  # needed?

    fnroot = os.path.splitext(fn)[0]
    with open("{}.hack".format(fnroot), "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <assembly file>".format(sys.argv[0]))
        sys.exit(1)

    main(sys.argv[1])
