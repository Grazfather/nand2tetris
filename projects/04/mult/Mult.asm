// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

    // Init vars
    @i
    M=0

    @R2 // sum
    M=0

    @BOTTOM_LOOP
    0;JMP

(TOP_LOOP)
    // sum += x
    @R0
    D=M
    @R2
    M=D+M
    // i += 1
    @i
    M=M+1

(BOTTOM_LOOP)
    // If i < y, redo the loop
    @R1
    D=M
    @i
    D=D-M
    @TOP_LOOP
    D;JGT


    @HALT
(HALT)
    0;JMP
