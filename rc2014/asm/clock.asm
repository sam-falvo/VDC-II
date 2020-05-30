; VDC Clock Demo
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.
;
; This code implements a simple clock.  It is a vehicle by
; which I may learn to invoke CP/M system calls; but, also,
; by which I may also develop Z80 code for working with my
; VDC-II core.
;
; This program is the first Z80 code I've written in maybe
; 30 years.  Forgive any style demerits; it's been a while.


	include	"ue.asm"
	include "log.asm"
	include "bdos.asm"
	include "vdc.asm"


AppInitialize:
	; Initialize our custom keyboard handler.

	ld	hl,ClockKbdHandler
	ld	(kbdHandler),hl

	; Initialize the state of the screen.  First, we clear the
	; screen.  Then, we print our title across the top of the screen.
	; Beneath that, a menu of options available to the user.

	ld	hl,0
	ld	(r0),hl		; left
	ld	(r1),hl		; top
	ld	l,80
	ld	(r2),hl		; right
	ld	l,30
	ld	(r3),hl		; bottom
	ld	l,20h
	ld	(r4),hl		; Fill screen with spaces
	call	VdcDrawTextSlab

	ld	hl,33		; Left edge of title text
	ld	(r0),hl
	ld	l,h		; Top edge
	ld	(r1),hl
	ld	hl,helloMsg	; Text to print in title bar
	ld	(r2),hl
	ld	hl,helloLen
	ld	(r3),hl
	call	VdcPrintRawText

	ld	hl,0
	ld	(r0),hl		; left
	ld	(r1),hl		; top
	ld	l,80
	ld	(r2),hl		; right
	ld	l,1
	ld	(r3),hl		; bottom
	ld	l,46h
	ld	(r4),hl		; Make titlebar cyan, reverse video
	call	VdcDrawAttrSlab

	ld	hl,0
	ld	(r0),hl		; left
	inc	hl
	ld	(r1),hl		; top
	ld	l,80
	ld	(r2),hl		; right
	ld	l,30
	ld	(r3),hl		; bottom
	ld	l,06h
	ld	(r4),hl		; Make everything cyan
	call	VdcDrawAttrSlab


	
	; Show the user we're now running by printing our banner.
	; Return to the User Environment's event loop once we've
	; finished.

	ld	de,helloMsg
	jp	BdosPrintString

.helloMsg
	defm	"VDC Clock Demo"
defc helloLen = ASMPC - helloMsg
	defm	13,10
	defm	"Press Q to exit.",13,10
	defm	"$"


ClockKbdHandler:
	; If the user presses anything except either 'q' or 'Q',
	; print the key event to the screen to tell the user we're
	; still alive and well.

	cp	'q'
	jr	z,doQuit

	cp	'Q'
	jr	z,doQuit

	push	af
	ld	de,keyPressedMsg
	call	BdosPrintString
	pop	af
	ld	e,a
	call	BdosConsoleOut
	ld	de,crMsg
	jp	BdosPrintString

.doQuit	jp	ueReturn


keyPressedMsg:
	defm	"You just pressed this key: $"
crMsg:	defm	"   ",13,"$"

