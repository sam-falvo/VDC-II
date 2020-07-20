PaintStackLine:
	ld	a,20H			; Blank contents of the stack line
	ld	(stackBuffer),a
	ld	hl,stackBuffer
	ld	(stkviewBuffer),hl
	ld	de,stackBuffer+1
	ld	bc,79
	ldir
	ld	hl,stackBuffer+79	; before repainting it anew.
	ld	(stkviewBufPos),hl
	call	StackBuildView

	ld	hl,0
	ld	(r0),hl
	ld	l,1
	ld	(r1),hl
	ld	hl,stackBuffer
	ld	(r2),hl
	ld	hl,80
	ld	(r3),hl
	jp	VdcPrintRawText


PaintCmdLine:
	ld	hl,LEFTMARGIN
	ld	(r0),hl
	ld	l,0
	ld	(r1),hl
	ld	l,RIGHTMARGIN
	ld	(r2),hl
	ld	l,1
	ld	(r3),hl
	ld	a,20H
	ld	(r4),a
	call	VdcDrawTextSlab

	ld	hl,LEFTMARGIN
	ld	(r0),hl
	ld	l,0
	ld	(r1),hl
	ld	hl,cmdlineBuffer
	ld	(r2),hl
	call	TibLength
	ld	(r3),hl
	call	VdcPrintRawText
	ld	de,0
	jp	_CalcCursorPtr


ColorCmdLine:
	; Color the command line line

	ld	hl,0
	ld	(r0),hl		; left
	ld	(r1),hl		; top
	ld	a,(vdcCharWidth)
	ld	(r2),a		; right
	ld	a,0Eh
	ld	(r4),a		; Make command-line text bright grey
	call	VdcDrawAttrLine

	; fall through to ColorOK

ColorOK:
	ld	hl,0
	ld	(r0),hl		; left
	ld	(r1),hl		; top
	ld	a,okLen
	ld	(r2),a		; right
	ld	a,(okAttribs)
	ld	(r4),a		; Make OK prompt itself white.
	jp	VdcDrawAttrLine


PaintOK:
; Print or hide OK prompt.

	ld	hl,0		; Place OK prompt at top of the screen.
	ld	(r0),hl
	ld	(r1),hl
	ld	hl,okMsg
	ld	(r2),hl
	ld	hl,okLen
	ld	(r3),hl
	call	VdcPrintRawText


okMsg:	defm	"OK "
defc okLen = ASMPC - okMsg


okAttribs:
	defb	0FH		; XOR with 0FH to toggle visibility.


stackBuffer:	defs	80

