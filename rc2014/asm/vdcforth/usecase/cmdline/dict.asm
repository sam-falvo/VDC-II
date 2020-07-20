initDictionary:
	ld	hl,xt_PLUS
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

name_ONE:	defb	3,"ONE"
xt_ONE:		defw	name_ONE
		defw	xt_PAGE
	ld	(stkReturn),sp
	ld	sp,(stkData)
	ld	hl,1
	push	hl
	ld	(stkData),sp
	ld	sp,(stkReturn)
	ret


name_K:	defb	1,"K"
xt_K:		defw	name_K
		defw	xt_ONE
	ld	(stkReturn),sp
	ld	sp,(stkData)
	ld	hl,1000
	push	hl
	ld	(stkData),sp
	ld	sp,(stkReturn)
	ret

name_PLUS:	defb	1,"+"
xt_PLUS:	defw	name_PLUS
		defw	xt_K
	ld	(stkReturn),sp
	ld	sp,(stkData)
	pop	hl
	pop	de
	add	hl,de
	push	hl
	ld	(stkData),sp
	ld	sp,(stkReturn)
	ret


start_of_free_space:	; MUST be the last symbol in the program.
		defb	0

