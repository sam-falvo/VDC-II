; BDOS Operating System Adaptation Layer
; Version 1
;
; The OSAL is intended to isolate the event loop and Forth
; system services from CP/M 2.2 specifically, and allow greater
; portability to, e.g., bare metal or other operating environments
; (e.g., TRS-DOS perhaps?).
;
; This OSAL is a thin veneer over CP/M 2.2's BDOS services.
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.


osalPrintString:
; Inputs:	DE points to "$"-terminated string.
; Outputs:
; Destroys:	BC

	ld	c,9
	jp	5

osalTerminate:
	jp	0


osalConsoleStatus:
; Inputs:
; Outputs:	A=0 if no console characters are pending; non-zero otherwise.
; Destroys:	BC

	ld	c,11
	jp	5


osalConsoleGetRaw:
; Inputs:
; Outputs:	A=0 if no character pending; otherwise, the next available
;		character.  The character is *not* echoed.
; Destroys:	BC, DE

	ld	c,6
	ld	e,0FFH
	jp	5


osalPrintHex16:
; Inputs:	HL=16-bit word to print to the console.
; Outputs:
; Destroys:	A, BC, HL

	push	hl
	ld	a,h
	call	osalPrintHex8
	pop	hl
	ld	a,l
	; fall-through to osalPrintHex8

osalPrintHex8:
	push	af
	srl	a
	srl	a
	srl	a
	srl	a
	call	osalPrintHex4
	pop	af
	; fall-through to osalPrintHex4

osalPrintHex4:
	and	0Fh
	ld	e,a
	ld	d,0
	ld	hl,osalhextab
	add	hl,de
	ld	e,(hl)

	; fall-through to osalConsoleOut

osalConsoleOut:
; Inputs:	E=character to print to the console.
; Outputs:
; Destroys:	BC

	ld	c,2
	jp	5

osalhextab:	defm	"0123456789ABCDEF"

