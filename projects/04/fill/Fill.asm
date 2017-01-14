// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed.
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.


(READ_KBR)
    @KBD
    D=M
    @FILL
    D;JLE

(CLEAR)
    D=-1
    @COLOUR
    M=D
    @DRAW
    0;JMP
(FILL)
    D=0
    @COLOUR
    M=D
    @DRAW
    0;JMP


(DRAW)
    // Pos to start of SCREEN
    @SCREEN
    D=A
    @pos
    M=D
(DRAW_LOOP)

    // Write white or black
    @COLOUR
    D=M
    @pos
    A=M
    M=D

    // Write to current block
    @pos
    M=M+1

    // Check if done
    D=M
    @KBD // If the pos reaches the keyboard, it's past the screen
    D=D-A
    @DRAW_LOOP
    D; JNE

    @READ_KBR
    0;JMP
