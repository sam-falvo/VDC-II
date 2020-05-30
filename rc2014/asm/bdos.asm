; BDOS System Call Library
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.


BdosPrintString:
; Inputs:	DE points to "$"-terminated string.
; Outputs:
; Destroys:	BC

	ld	c,9
	jp	5

BdosTerminate:
	jp	0


BdosConsoleStatus:
; Inputs:
; Outputs:	A=0 if no console characters are pending; non-zero otherwise.
; Destroys:	BC

	ld	c,11
	jp	5


BdosConsoleGetRaw:
; Inputs:
; Outputs:	A=0 if no character pending; otherwise, the next available
;		character.  The character is *not* echoed.
; Destroys:	BC, DE

	ld	c,6
	ld	e,0FFH
	jp	5


BdosConsoleOut:
; Inputs:	E=character to print to the console.
; Outputs:
; Destroys:	BC

	ld	c,2
	jp	5

