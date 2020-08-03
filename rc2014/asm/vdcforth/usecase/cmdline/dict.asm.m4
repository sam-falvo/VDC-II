define(`header_common',`
name_$1:	defb	$2,"$3"
xt_$1:		defw	name_$1,$4
code_$1:
define(`PREVXT',`xt_$1')dnl')dnl
define(`header_start',`header_common($1,len($1),$1,0)')dnl
define(`header2',`header_common($2,len($1),$1,PREVXT)')dnl
define(`header1',`header_common($1,len($1),$1,PREVXT)')dnl
define(`DSTK',`ld	(stkReturn),sp
	ld	sp,(stkData)')dnl
define(`RSTK',`ld	(stkData),sp
	ld	sp,(stkReturn)')dnl


header_start(`BYE')
	jp	evtReturn	; return back to the system event loop.


include(`usecase/cmdline/words/core.m4')


header1(`PAGE')
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

header1(`ONE')
	ld	(stkReturn),sp
	ld	sp,(stkData)
	ld	hl,1
	push	hl
	ld	(stkData),sp
	ld	sp,(stkReturn)
	ret


header1(`K')
	ld	(stkReturn),sp
	ld	sp,(stkData)
	ld	hl,1000
	push	hl
	ld	(stkData),sp
	ld	sp,(stkReturn)
	ret

initDictionary:
	ld	hl,PREVXT
	ld	(interpDictPtr),hl
	ld	hl,start_of_free_space
	ld	(interpHerePtr),hl
	ret


start_of_free_space:	; MUST be the last symbol in the program.
		defb	0

