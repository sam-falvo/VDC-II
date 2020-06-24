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

	cp	a,RETURN
	jr	z,doReturn

	cp	a,27
	ret	nz
	jp	osalTerminate


doBackspace:
	call	TibBackspace
	jp	PaintCmdLine


doReturn:
	ld	a,00h
	ld	(okAttribs),a
	call	ColorOK
	call	interpretCmdLine
	ld	a,0Fh
	ld	(okAttribs),a
	jp	ColorOK


interpretCmdLine:
	ld	hl,0FFFFh
lp:	ld	a,h
	or	l
	ret	z
	dec	hl
	jp	lp


cmdlineBuffer:
	defs	CMDBUFLEN

