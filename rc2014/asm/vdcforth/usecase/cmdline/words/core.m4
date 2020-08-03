header2(`!',`STORE')
        DSTK()
        pop     de
        pop     hl
        ld      (hl),e
        inc     hl
        ld      (hl),d
        RSTK()
        ret


header2(`UM/MOD',`UMSLASHMOD')
        DSTK()
        pop     bc      ; BC=divisor
        pop     hl      ; HLDE=dividend (note: NOT DEHL)
        pop     de
	call	UDivideHLDEbyBC
        push    hl     ; push remainder
        push    bc
        RSTK()
        ret


header1(`2DUP')
	DSTK()
	pop	hl
	pop	de
	push	de
	push	hl
	push	de
	push	hl
	RSTK()
	ret


header1(`DUP')
	DSTK()
	pop	hl
	push	hl
	push	hl
	RSTK()
	ret


header1(`DROP')
	DSTK()
	pop	hl
	RSTK()
	ret


header1(`2DROP')
	DSTK()
	pop	hl
	pop	hl
	RSTK()
	ret


header1(`NIP')
	DSTK()
	pop	hl
	pop	bc
	push	hl
	RSTK()
	ret

header1(`ROT')
	DSTK()
	pop	hl
	pop	de
	pop	bc

	push	de
	push	hl
	push	bc
	RSTK()
	ret


header2(`-ROT',`NROT')
	DSTK()
	pop	hl
	pop	de
	pop	bc

	push	hl
	push	bc
	push	de
	RSTK()
	ret


header1(`XOR')
	DSTK()
	pop	hl
	pop	de
	ld	a,h
	xor	a,d
	ld	h,a
	ld	a,l
	xor	a,e
	ld	l,a
	push	hl
	RSTK()
	ret


header1(`OR')
	DSTK()
	pop	hl
	pop	de
	ld	a,h
	or	a,d
	ld	h,a
	ld	a,l
	or	a,e
	ld	l,a
	push	hl
	RSTK()
	ret


header1(`AND')
	DSTK()
	pop	hl
	pop	de
	ld	a,h
	and	a,d
	ld	h,a
	ld	a,l
	and	a,e
	ld	l,a
	push	hl
	RSTK()
	ret


header2(`2*',`2STAR')
	DSTK()
	pop	hl
	add	hl,hl
	push	hl
	RSTK()
	ret


header2(`2/',`2SLASH')
	DSTK()
	pop	hl
	sra	h
	rr	l
	push	hl
	RSTK()
	ret


header2(`>R',`TOR')
	pop	bc
	DSTK()
	pop	hl
	RSTK()
	push	hl
	push	bc
	ret


header1(`OVER')
	DSTK()
	pop	hl
	pop	de
	push	de
	push	hl
	push	de
	RSTK()
	ret


header1(`ABS')
	DSTK()
	pop	hl
	ld	a,h
	or	a,a	; also clears carry
	jp	p,abs_positive
	ld	e,l
	ld	d,h
	ld	hl,0
	sbc	hl,de
abs_positive:
	push	hl
	RSTK()
	ret


header1(`DABS')
	DSTK()
	pop	hl	; HL=high word
	ld	a,h
	or	a,a	; also clears carry
	jp	p,abs_positive

	ld	b,h	; BC=high word
	ld	c,l
	pop	de	; DE=low word
	ld	hl,0
	sbc	hl,de
	push	hl
	
	ld	hl,0
	sbc	hl,bc
	push	hl

	RSTK()
	ret


header2(`R>',`RFROM')
	pop	bc
	pop	hl
	DSTK()
	push	hl
	RSTK()
	push	bc
	ret


header1(`SWAP')
	DSTK()
	pop	hl
	pop	de
	push	hl
	push	de
	RSTK()
	ret


header1(`NEGATE')
	DSTK()
	pop	de
	ld	hl,0
	or	a,a
	sbc	hl,de
	push	hl
	RSTK()
	ret


header2(`?NEGATE',`QNEGATE')
	DSTK()
	pop	de
	bit	7,d
	jr	z,qnegate_l1
	pop	de
	ld	hl,0
	or	a,a	; clear carry
	sbc	hl,de
	push	hl
qnegate_l1:
	RSTK()
	ret

header2(`SM/MOD',`SMSLASHMOD')
	call	code_2DUP
	call	code_XOR
	call	code_TOR
	call	code_OVER
	call	code_TOR
	call	code_ABS
	call	code_TOR
	call	code_DABS
	call	code_RFROM
	call	code_UMSLASHMOD
	call	code_SWAP
	call	code_RFROM
	call	code_QNEGATE
	call	code_SWAP
	call	code_RFROM
	jp	code_QNEGATE


header2(`+',`PLUS')
        DSTK()
        pop     hl
        pop     de
        add     hl,de
        push    hl
        RSTK()
        ret


header2(`-',`MINUS')
	DSTK()
	pop	de
	pop	hl
	or	a,a
	sbc	hl,de
	push	hl
	RSTK()
	ret

header2(`*',`TIMES')
	DSTK()
	pop	bc
	pop	hl
	call	UMultiplyHLbyBC		; TODO: for now; change to SMultiplyHLbyBC
	push	hl
	RSTK()
	ret
