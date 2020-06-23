defc BACKSPACE = 127		; Is this C128-specific??

defc LEFTMARGIN = 3
defc RIGHTMARGIN = 80
defc CMDBUFLEN = RIGHTMARGIN - LEFTMARGIN


initKeyboard:
	ld	hl,onKey
	ld	(kbdHandler),hl

	ld	bc,0
	ld	de,CMDBUFLEN
	ld	hl,cmdlineBuffer
	jp	TibSetExtent


onKey:
	cp	a,20H
	jr	c,doCtrlChar
	cp	a,7FH
	jr	nc,doCtrlChar
	call	TibTypeChar
	jp	PaintCmdLine
	
doCtrlChar:
	cp	a,BACKSPACE
	jr	z,doBackspace

	cp	a,27
	ret	nz
	jp	osalTerminate


doBackspace:
	call	TibBackspace
	jp	PaintCmdLine


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


cmdlineBuffer:
	defs	CMDBUFLEN

