initDictionary:
	ld	hl,xt_PAGE
	ld	(interpDictPtr),hl
	ld	hl,start_of_free_space
	ld	(interpHerePtr),hl
	ret


name_BYE:	defb	3,"BYE"
xt_BYE:		defw	name_BYE
		defw	0
	jp	evtReturn	; return back to the system event loop.

name_PAGE:	defb	4,"PAGE"
xt_PAGE:	defw	name_PAGE
		defw	xt_BYE
	ld	hl,0
	ld	(r0),hl
	ld	(r1),hl
	ld	(r2),hl
	ld	(r3),hl
	ld	a,2
	ld	(r1),a
	ld	a,(vdcCharWidth)
	ld	(r2),a
	ld	a,(vdcCharHeight)
	ld	(r3),a
	ld	l,20H
	ld	(r4),hl
	call	VdcDrawTextSlab
	ret


start_of_free_space:	; MUST be the last symbol in the program.
		defb	0

