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


defc RVS = 40h

defc BLACK = 00h
defc RED = 09h
defc YELLOW = 0Ch

defc PAUSED_FLAG = RED


	include	"ue.asm"
	include "log.asm"
	include "bdos.asm"
	include "vdc.asm"


AppInitialize:
	; Initialize our custom keyboard handler.

	ld	hl,ClockKbdHandler
	ld	(kbdHandler),hl

	; Clear the screen.

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

	; Print our title bar.

	ld	hl,33		; Left edge of title text
	ld	(r0),hl
	ld	l,h		; Top edge
	ld	(r1),hl
	ld	hl,helloMsg	; Text to print in title bar
	ld	(r2),hl
	ld	hl,helloLen
	ld	(r3),hl
	call	VdcPrintRawText

	; Color the title bar.

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

	; Color the rest of the screen.

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

	; Set paused flag and reset the clock to 00:00:00.

	ld	a,PAUSED_FLAG
	ld	(paused),a
	xor	a
	ld	(h0),a
	ld	(h1),a
	ld	(m0),a
	ld	(m1),a
	ld	(s0),a
	ld	(s1),a

	ld	hl,0
	ld	(vdcVSHandler),hl

	; Draw clock

	call	_RedrawPaused
	call	_RedrawClock

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
	cp	'q'
	jr	z,doQuit

	cp	'Q'
	jr	z,doQuit

	cp	'p'
	jr	z,TogglePause

	cp	'P'
	jr	z,TogglePause

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


TogglePause:
	ld	a,(paused)
	xor	a,PAUSED_FLAG
	ld	(paused),a
	jr	z,notpaused

	ld	hl,0
	ld	(vdcVSHandler),hl
	jp	_RedrawPaused

notpaused:
	ld	hl,ClockVSYNCHandler
	ld	(vdcVSHandler),hl
	jp	_RedrawPaused


; Approximately 60 times a second, this procedure should be called by the UE event loop.
; It's triggered off the VGA's vertical sync pulse.
;
; Unfortunately, the asynchronous nature of the UE's event loop and probably my lack-luster
; programming skills means that we miss a lot of VSYNCs in the process.  So, after carefully
; observing program behavior, it looks like we need to respond after only 16-ish frames that
; we can actually see, ignoring the remainder that fly by unnoticed.
;
; Note that the 16 frames limit is calibrated against *my* RC2014, which uses a Z80 processor
; running at 7.3728MHz.  If you're running a Z180, Z280, Z380, or Rabbit processor of some
; kind, you'll need to customize this calibration for your hardware.

ClockVSYNCHandler:
	ld	a,(frames)
	inc	a
	cp	17		; In a perfect world, this would be 60.  But, ...
	jr	z,bumpS0
	ld	(frames),a
	ret

bumpS0:
	xor	a
	ld	(frames),a

	ld	a,(s0)
	inc	a
	cp	10
	jr	z,bumpS1
	ld	(s0),a
	jp	_RedrawClock

bumpS1:
	xor	a
	ld	(s0),a

	ld	a,(s1)
	inc	a
	cp	6
	jr	z,bumpM0
	ld	(s1),a
	jp	_RedrawClock


bumpM0:
	xor	a
	ld	(s1),a

	ld	a,(m0)
	inc	a
	cp	10
	jr	z,bumpM1
	ld	(m0),a
	jp	_RedrawClock

bumpM1:
	xor	a
	ld	(m0),a

	ld	a,(m1)
	inc	a
	cp	6
	jr	z,bumpH0
	ld	(m1),a
	jp	_RedrawClock


bumpH0:
	xor	a
	ld	(m1),a

	ld	a,(h0)
	inc	a
	cp	10
	jr	z,bumpH1
	ld	(h0),a
	jp	_RedrawClock

bumpH1:
	xor	a
	ld	(h0),a

	ld	a,(h1)
	inc	a
	cp	10
	jr	z,rollOver
	ld	(h1),a
	jp	_RedrawClock

rollOver:
	xor	a
	ld	(h1),a
	jp	_RedrawClock


_RedrawPaused:
	ld	hl,32
	ld	(r0),hl
	ld	hl,12
	ld	(r1),hl
	ld	hl,pausedMsg
	ld	(r2),hl
	ld	hl,pausedLen
	ld	(r3),hl
	call	VdcPrintRawText

	ld	hl,32
	ld	(r0),hl
	ld	de,pausedLen
	add	hl,de
	ld	(r2),hl
	ld	hl,12
	ld	(r1),hl
	inc	hl
	ld	(r3),hl

	ld	a,(paused)
	ld	(r4),a
	jp	VdcDrawAttrSlab

.pausedMsg
	defm	"  P A U S E D  "
defc pausedLen = ASMPC - pausedMsg


_RedrawClock:
	ld	hl,2
	ld	(digitT),hl
	dec	hl
	dec	hl
	ld	(digitL),hl
	
	ld	a,(h1)
	call	dodig
	ld	a,(h0)
	call	dodig
	call	docolon

	ld	a,(m1)
	call	dodig
	ld	a,(m0)
	call	dodig

	ld	a,(s1)
	or	a,30H
	ld	(secondsBuf+2),a
	ld	a,(s0)
	or	a,30H
	ld	(secondsBuf+3),a

	ld	hl,(digitL)
	inc	hl
	inc	hl
	ld	(r0),hl
	ld	hl,10
	ld	(r1),hl
	ld	hl,secondsBuf
	ld	(r2),hl
	ld	hl,4
	ld	(r3),hl
	call	VdcPrintRawText

	ld	hl,(digitL)
	inc	hl
	inc	hl
	ld	(r0),hl
	inc	hl
	inc	hl
	inc	hl
	inc	hl
	ld	(r2),hl
	ld	hl,10
	ld	(r1),hl
	inc	hl
	ld	(r3),hl
	ld	a,YELLOW
	ld	(r4),a
	jp	VdcDrawAttrSlab


.secondsBuf
	defm	": XX"

.dodig	and	a,0Fh
	ld	e,a
	ld	d,0
	ld	hl,segtab
	add	hl,de
	ld	a,(hl)
	ld	(digitState),a
	call	_DrawLED
	ld	hl,(digitL)
	ld	de,14
	add	hl,de
	ld	(digitL),hl
	ret

.docolon
	ld	hl,(digitL)
	ld	(r0),hl
	inc	hl
	inc	hl
	ld	(r2),hl
	ld	hl,(digitT)
	inc	hl
	inc	hl
	ld	(r1),hl
	ld	de,5
	add	hl,de
	ld	(r3),hl
	ld	a,YELLOW | RVS
	ld	(r4),a
	call	VdcDrawAttrSlab

	ld	hl,(digitT)
	inc	hl
	inc	hl
	inc	hl
	ld	(r1),hl
	inc	hl
	inc	hl
	inc	hl
	ld	(r3),hl
	ld	a,BLACK
	ld	(r4),a
	call	VdcDrawAttrSlab

	ld	hl,(digitL)
	inc	hl
	inc	hl
	inc	hl
	inc	hl
	ld	(digitL),hl
	ret


.segtab	defb	@00111111 ; 0 0gfedcba
	defb	@00000110 ; 1
	defb	@01011011 ; 2
	defb	@01001111 ; 3
	defb	@01100110 ; 4
	defb	@01101101 ; 5
	defb	@01111101 ; 6
	defb	@00000111 ; 7
	defb	@01111111 ; 8
	defb	@01101111 ; 9

_DrawLED:
	call	_DrawA
	call	_DrawB
	call	_DrawC
	call	_DrawD
	call	_DrawE
	call	_DrawF
	jp	_DrawG

_DrawA:
	call	lfrt1
	call	topbot0
	ld	a,(digitState)	; R4 = attribute to draw with
	bit	0,a
.drawseg
	jr	nz,drawa0
	xor	a
	jr	drawa1
.drawa0	ld	a,YELLOW | RVS
.drawa1	ld	(r4),a
	jp	VdcDrawAttrSlab

_DrawB:
	call	lfrt2
	call	topbot1
	ld	a,(digitState)
	bit	1,a
	jr	drawseg

_DrawC:
	call	lfrt2
	call	topbot3
	ld	a,(digitState)
	bit	2,a
	jr	drawseg

_DrawD:
	call	lfrt1
	call	topbot4
	ld	a,(digitState)
	bit	3,a
	jr	drawseg

_DrawE:
	call	lfrt0
	call	topbot3
	ld	a,(digitState)
	bit	4,a
	jr	drawseg

_DrawF:
	call	lfrt0
	call	topbot1
	ld	a,(digitState)
	bit	5,a
	jr	drawseg

_DrawG:
	call	lfrt1
	call	topbot2
	ld	a,(digitState)
	bit	6,a
	jr	drawseg

; 7 segment LEDs can be broken up into three horizontal columns (left, middle, and right),
; and 5 rows.  Each lfrtX procedure configures the left and right edges to use for the
; three columns.  Correspondingly, the topbotX procedures do the same for the different
; rows.

.lfrt0
	ld	hl,(digitL)	; R0 = left edge of segment
	ld	(r0),hl
	inc	hl		; R2 = right edge
	inc	hl
	ld	(r2),hl
	ret

.lfrt1
	ld	hl,(digitL)	; R0 = left edge of segment
	inc	hl
	inc	hl
	ld	(r0),hl
	ld	de,8		; R2 = right edge of segment
	add	hl,de
	ld	(r2),hl
	ret

.lfrt2
	ld	hl,(digitL)	; R0 = left edge of segment
	ld	de,10
	add	hl,de
	ld	(r0),hl
	inc	hl		; R2 = right edge
	inc	hl
	ld	(r2),hl
	ret

.topbot0
	ld	hl,(digitT)	; R1 = top edge of segment
	ld	(r1),hl
	inc	hl
	ld	(r3),hl		; R3 = bottom edge of segment
	ret

.topbot1
	ld	hl,(digitT)	; R1 = top edge of segment
	inc	hl
	ld	(r1),hl
	inc	hl
	inc	hl
	inc	hl
	ld	(r3),hl		; R3 = bottom edge of segment
	ret

.topbot2
	ld	hl,(digitT)	; R1 = top edge of segment
	ld	de,4
	add	hl,de
	ld	(r1),hl
	inc	hl
	ld	(r3),hl		; R3 = bottom edge of segment
	ret

.topbot3
	ld	hl,(digitT)	; R1 = top edge of segment
	ld	de,5
	add	hl,de
	ld	(r1),hl
	inc	hl
	inc	hl
	inc	hl
	ld	(r3),hl		; R3 = bottom edge of segment
	ret

.topbot4
	ld	hl,(digitT)	; R1 = top edge of segment
	ld	de,8
	add	hl,de
	ld	(r1),hl
	inc	hl
	ld	(r3),hl		; R3 = bottom edge of segment
	ret

.digitState
	defb	0
.digitL
	defw	0
.digitT
	defw	0
.paused defb	0
.h0	defb	0
.m0	defb	0
.s0	defb	0
.h1	defb	0
.m1	defb	0
.s1	defb	0
.frames	defb	0

