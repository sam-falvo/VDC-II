i_UtilInitWords:
; Initializes a collection of 16-bit words with literal values.
; Although slower than explicit LD HL,xxx; LD (var),HL instructions,
; it uses less space when you have 3 or more variables to initialize,
; and is more convenient to write.
;
; Inputs:
; Outputs:
; Destroys:	A, BC, DE, HL

	pop	hl	;HL contains the return address
	ld	b,(hl)	;Set B to the number of variables to initialize
	inc	hl

uiwAgain:
	ld	e,(hl)
	inc	hl
	ld	d,(hl)
	inc	hl
	ld	a,(hl)
	inc	hl
	ld	(de),a
	inc	de
	ld	a,(hl)
	inc	hl
	ld	(de),a
	djnz	uiwAgain

	jp	(hl)

i_UtilInitBytes:
; Initializes a collection of 8-bit bytes with literal values.
; Although slower than explicit LD A,xxx; LD (var),A instructions,
; it uses less space when you have 3 or more variables to initialize,
; and is more convenient to write.
;
; Inputs:
; Outputs:
; Destroys:	A, BC, DE, HL

	pop	hl	;HL contains the return address
	ld	b,(hl)	;Set B to the number of variables to initialize
	inc	hl

uibAgain:
	ld	e,(hl)
	inc	hl
	ld	d,(hl)
	inc	hl
	ld	a,(hl)
	inc	hl
	ld	(de),a
	djnz	uibAgain

	jp	(hl)

