SEGMENT_MAP = {
    "argument": "ARG",
    "local": "LCL",
    "this": "THIS",
    "that": "THAT",
}

filename = ""
count = 0
current_function = ""


def bootstrap():
    """Boilerplate bootstrapping code.
    """
    return [
        "@256",
        "D=A",
        "@SP",
        "M=D",
        *call_function("Sys.init", 0)
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


def arith_command(op, _):
    return [
        # Pop second argument
        *pop_d(),
        # <op> it from the value now at the top of the stack
        *get_stack_top_addr(),
        "M=M{}D".format(op),
    ]


def neg_command(_):
    return [
        *get_stack_top_addr(),
        "M=-M",
    ]


def cmp_command(comparison, command):
    true_label = label("{}_TRUE_{}".format(comparison, count))
    end_label = label("{}_END_{}".format(comparison, count))
    return [
        *pop_d(),  # Read second arg
        *get_stack_top_addr(), # Addr of first arg
        "D=M-D",  # cmp
        "@{}".format(true_label),
        "D;J{}".format(comparison),  # If equal, set D to 0xFFFF
        "D=0",  # Otherwise, set D to 0
        "@{}".format(end_label),
        "0;JMP",
        "({})".format(true_label),
        "D=-1",
        "({})".format(end_label),
        *get_stack_top_addr(),
        "M=D",
    ]


def boolean_command(op, _):
    return [
        *pop_into_addr("R13"),
        *pop_into_addr("R14"),
        "@R13",
        "D=D{}M".format(op),
        *push_d(),
    ]


def not_command(_):
    return [
        *get_stack_top_addr(),
        "M=!M",
    ]


def goto_command(command):
    return [
        *jmp_address(label(command.arg1)),
    ]


def if_goto_command(command):
    return [
        *pop_d(),
        "@{}".format(label(command.arg1)),
        "D;JNE",
    ]


def label_command(command):
    return [
        *add_label(label(command.arg1)),
    ]


def call_command(command):
    func = command.arg1
    num_args = int(command.arg2)

    return [
        *call_function(func, num_args)
    ]


def call_function(function, num_args):
    return_label = "{}$ret.{}".format(current_function, count)
    return [
        # Save old state
        # -- Push RA
        *push_constant(return_label),
        # -- Push LCL
        *push_register("LCL"),
        # -- Push ARG
        *push_register("ARG"),
        # -- Push THIS
        *push_register("THIS"),
        # -- Push THAT
        *push_register("THAT"),
        # Set new state
        # -- Set ARG (ARG = SP - num_args - 5)
        *deref_pointer_d("SP"),
        "@5",
        "D=D-A",
        "@{}".format(num_args),
        "D=D-A",
        *write_d_into_addr("ARG"),

        # -- Set LCL
        *deref_pointer_d("SP"),
        *write_d_into_addr("LCL"),

        # Jump to function
        *jmp_address(function),
        *add_label(return_label),
    ]


def function_command(command):
    global current_function
    name = command.arg1
    current_function = name
    num_locals = int(command.arg2)
    return [
        *add_label(name),
        # Make room for locals
        *(push_constant(0) * num_locals)
    ]


def return_command(_):
    end_frame = "R13"
    ret_addr = "R14"
    return [
        # End frame = LCL
        *deref_pointer_d("LCL"),
        *write_d_into_addr(end_frame),
        # ret_addr = *(endFrame - 5)
        *get_pointer_offset("LCL", -5),
        "D=M",
        *write_d_into_addr(ret_addr),
        # ARG[0] = pop()
        *pop_d(),
        "@ARG",
        "A=M",
        "M=D",
        # SP = ARG + 1
        "@ARG",
        "D=M",
        "D=D+1",
        "@SP",
        "M=D",
        # Restore THAT
        *get_pointer_offset(end_frame, -1),
        "D=M",
        *write_d_into_addr("THAT"),
        # Restore THIS
        *get_pointer_offset(end_frame, -2),
        "D=M",
        *write_d_into_addr("THIS"),
        # Restore ARG
        *get_pointer_offset(end_frame, -3),
        "D=M",
        *write_d_into_addr("ARG"),
        # Restore LCL
        *get_pointer_offset(end_frame, -4),
        "D=M",
        *write_d_into_addr("LCL"),
        # Goto retaddr
        "@{}".format(ret_addr),
        "A=M",
        "0;JMP",
    ]


def jmp_address(addr):
    """Jump to the address or label specified.
    """
    return [
        "@{}".format(addr),
        "0;JMP",
    ]


def jmp_d():
    """Jump to the address in D.
    """
    return [
        "A=D",
        "0;JMP",
    ]


def get_addr(segment, offset):
    """Set A & D to the address specified by the segment and offset provided.
    """
    ins = []
    # Get target address
    # -- Get base
    if segment in SEGMENT_MAP:
        segment = SEGMENT_MAP[segment]
        ins.extend(deref_pointer_d(segment))
    else:
        if segment == "pointer":
            ins.append("@3")
        elif segment == "temp":
            ins.append("@5")
        elif segment == "static":
            ins.append("@{}.{}".format(filename, offset))
            offset = None

        ins.append("D=A")

    if offset:
        ins.append("@{}".format(offset))
        ins.append("AD=D+A")

    return ins


def get_pointer_offset(ptr, offset):
    """Set A to the value at ptr, plus offset.
    """
    if offset < 0:
        offset = -offset
        sign = "-"
    else:
        sign = "+"

    return [
        *deref_pointer_d(ptr),
        "@{}".format(offset),
        "A=D{}A".format(sign),
    ]


def deref_pointer_d(addr):
    """Read value from addr and set D.
    """
    return [
        "@{}".format(addr),
        "D=M",
    ]


def deref_pointer_a(addr):
    """Read value from addr and set A.
    """
    return [
        "@{}".format(addr),
        "A=M",
    ]


def deref_d():
    """Read value from memory at D and set D.
    """
    return [
        "A=D",
        "D=M",
    ]


def incr_d():
    """Increment D.
    """
    return [
        "D=D+1",
    ]


def get_stack_top_addr():
    """Set A to the address of the top of the stack (full).
    """
    return [
        "@SP",
        "A=M",
        "A=A-1",
    ]


def pop_d():
    """Pop the top value from the stack into D.
    """
    return [
        "@SP",
        "AM=M-1",
        "D=M",
    ]


def pop_into_addr(addr):
    """Pop value from stack and write to memory at addr.
    """
    return [
        *pop_d(),
        *write_d_into_addr(addr),
    ]

def write_d_into_addr(addr):
    """Write D into memory at addr.
    """
    return [
        "@{}".format(addr),
        "M=D",
    ]

def push_d():
    """Push D onto the stack
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


def push_a():
    """Push A onto the stack.
    """
    return [
        "D=A",
        *push_d(),
    ]


def push_constant(value):
    """Push value onto stack.
    """
    return [
        "@{}".format(value),
        *push_a(),
    ]


def push_register(addr):
    """Push the value stored in register as addr.
    """
    return [
        *deref_pointer_d(addr),
        *push_d(),
    ]


def add_label(name):
    """Add the named label.
    """
    return ["({})".format(name)]


def label(label):
    """Make a label unique to the function where it appears.
    """
    return "{}${}".format(current_function, label)
