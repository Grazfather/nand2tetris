SEGMENT_MAP = {
    "argument": "ARG",
    "local": "LCL",
    "this": "THIS",
    "that": "THAT",
}

filename = ""
count = 0


def get_addr(segment, offset):
    """Return instructions to set both A and D to the address specified by
    the segment and offset provided.
    """
    ins = []
    # Get target address
    # -- Get base
    if segment in SEGMENT_MAP:
        segment = SEGMENT_MAP[segment]
        ins.extend(deref_pointer(segment))
    else:
        if segment == "pointer":
            ins.append("@3")
        elif segment == "temp":
            ins.append("@5")
        elif segment == "static":
            ins.append("@{}.{}".format(filename, offset))

        ins.append("D=A")

    if offset:
        ins.append("@{}".format(offset))
        ins.append("AD=D+A")

    return ins


def deref_pointer(base):
    return [
        "@{}".format(base),
        "D=M",
    ]


def push_constant(value):
    return [
        "@{}".format(value),
        "D=A",
        *push_d(),
    ]


def push_command(command):
    if command.arg1 == "constant":
        return push_constant(command.arg2)

    return [
        *get_addr(command.arg1, command.arg2),
        "D=M",
        *push_d(),
    ]


def pop_command(command):
    return [
        # Get target address
        # -- Get address
        *get_addr(command.arg1, command.arg2),
        # -- Write it to register
        "@R13",
        "M=D",
        # Pop value into D
        *pop_d(),
        # Write D into address
        "@R13",
        "A=M",
        "M=D",
    ]


def add_command(command):
    return [
        # Pop second arg into temp
        *pop_into_addr("R13"),
        # Pop second arg into temp
        *pop_into_addr("R14"),
        # Calculate and push result
        "@R13",
        "D=M+D",
        *push_d(),
    ]


def sub_command(command):
    return [
        # Pop second arg into temp
        *pop_into_addr("R14"),
        # Pop first arg into temp
        *pop_into_addr("R13"),
        # Calculate and push result
        "@R14",
        "D=D-M",
        *push_d(),
    ]


def neg_command(command):
    return [
        *pop_into_addr("R13"),
        "D=-D",
        *push_d(),
    ]


def cmp_command(comparison, command):
    true_label = "{}_TRUE_{}".format(comparison, count)
    end_label = "{}_END_{}".format(comparison, count)
    return [
        *pop_into_addr("R13"),
        *pop_into_addr("R14"),
        "@13",
        "D=D-M",
        "@{}".format(true_label),
        "D;J{}".format(comparison), # If equal, set D to 0xFFFF
        "D=0", # Otherwise, set D to 0
        "@{}".format(end_label),
        "0;JMP",
        "({})".format(true_label),
        "D=-1",
        "({})".format(end_label),
        *push_d(),
    ]


def boolean_command(op, command):
    return [
        *pop_into_addr("R13"),
        *pop_into_addr("R14"),
        "@13",
        "D=D{}M".format(op),
        *push_d(),
    ]


def not_command(command):
    return [
        *pop_into_addr("R13"),
        "D=!D",
        *push_d(),
    ]


def pop_d():
    """Return the list of instructions required to pop the top value of the
    stack into the D register.
    """
    return [
        "@SP",
        "AM=M-1",
        "D=M",
    ]


def pop_into_addr(addr):
    """Return the list of instructions required to pop the top value of the
    stack into memory at the specified address.
    """
    return [
        *pop_d(),
        "@{}".format(addr),
        "M=D",
    ]

def push_d():
    """Return the list of instructions required to push the D register onto
    the stack.
    """
    return [
        # Increment SP
        "@SP",
        "M=M+1",
        # Stack is 'empty': SP points at open slot, so we need to get the old slot
        "A=M-1",
        # write value
        "M=D",
    ]

