LogByte:
	push	af
	push	bc
	push	de
	push	hl
	push	ix
	push	iy

	push	af
	sra	a
	sra	a
	sra	a
	sra	a
	call	lognyb
	pop	af
	call	lognyb

	pop	iy
	pop	ix
	pop	hl
	pop	de
	pop	bc
	pop	af
	ret

.bytehextab
	defm	"0123456789ABCDEF"

.lognyb	and	a,0Fh
	ld	l,a
	ld	h,0
	ld	de,bytehextab
	add	hl,de
	ld	a,(hl)
	ld	e,a
	jp	BdosConsoleOut

LogNL:	push	af
	push	bc
	push	de
	push	hl
	ld	e,13
	call	BdosConsoleOut
	ld	e,10
	call	BdosConsoleOut
	pop	hl
	pop	de
	pop	bc
	pop	af
	ret

