InterpNextWord:
; Parses the next white-space-delimited word from the TIB, and places it in
; counted-string form at HERE.  Skips leading whitespace.
;
; Inputs:	0 <= (interpIndex) < (tibInsertionPt)
;		indexes the next character to parse.
; Outputs:	A=0 if TIB exhausted; non-zero otherwise.
;		old(interpIndex) <= (interpIndex) <= (tibInsertionPt).
; Destroys:	BC, DE, HL

	call	TibLength
	ld	a,l
	ld	(interpLength),a	; for buffers < 256 bytes only!

	call	InterpSkipWS

	ld	hl,(tibBuffer)
	ld	de,(interpIndex)
	add	hl,de
	ld	(interpWordStart),hl

	call	InterpSkipGraphic

	ld	hl,(tibBuffer)
	ld	de,(interpIndex)
	add	hl,de
	ld	(interpWordEnd),hl

	call	InterpEatWS

	ld	hl,(interpWordEnd)
	ld	de,(interpWordStart)
	or	a,a
	sbc	hl,de
	ld	a,h
	or	l
	ret	z

	ld	b,h
	ld	c,l
	ld	hl,(interpHerePtr)
	ld	(hl),c
	inc	hl
	ex	de,hl
	ld	hl,(interpWordStart)
	ldir

	ld	a,1
	ret


InterpSkipSetup:
	ld	hl,(interpIndex)
	ld	a,(interpLength)
	ld	d,a
	ld	bc,(tibBuffer)
	ret

InterpSkipWS:
	call	InterpSkipSetup

InterpSkipWS_again:
	ld	a,l
	cp	d
	ret	z
	ret	nc

	add	hl,bc
	ld	a,(hl)
	cp	21H
	ret	z
	ret	nc
	sbc	hl,bc	; HL=HL-BC-1 b/c carry is known to be set
	inc	hl	; HL=HL-BC=(interpIndex)
	inc	hl	; compute next index offset

	ld	(interpIndex),hl
	jr	InterpSkipWS_again


InterpSkipGraphic:
	call	InterpSkipSetup

InterpSkipGraphic_again:
	ld	a,l
	cp	d
	ret	z
	ret	nc

	add	hl,bc
	ld	a,(hl)
	cp	21H
	ret	c
	sbc	hl,bc	; HL=HL-BC-0=(interpIndex) b/c carry is known to be clear
	inc	hl	; compute next index offset

	ld	(interpIndex),hl
	jr	InterpSkipGraphic_again


InterpEatWS:
	call	InterpSkipSetup
	ld	a,l
	cp	d
	ret	z
	ret	nc
	inc	hl
	ld	(interpIndex),hl
	ret


InterpFindWord:
; Locates a word in the current search dictionary.
;
; Inputs:	(interpDictPtr) - points to the head of the current
;		search dictionary.
;		(interpHerePtr) - points to the word name to look for.
; Outputs:	A=0 if the word is not found.  HL undefined.
;		A=-1 if the word is found; HL is the execution token.
; Destroys:	BC, DE

	ld	hl,(interpDictPtr)

InterpFindWord_tryAgain:
	; If we've reached the end of the dictionary chain,
	; the word cannot be found.  Return 0.
	ld	a,h
	or	l
	ret	z

	; HL (our candidate execution token) points to a word header.
	; Dereference the name field address and compare against the
	; word at HERE.
	ld	e,(hl)
	inc	hl
	ld	d,(hl)
	; leave HL pointing at XT+1.
	ld	(r0),de
	ld	de,(interpHerePtr)
	ld	(r1),de
	push	hl
	call	StrCompare
	pop	hl

	; If comparison indicates equality, return the candidate execution
	; token.
	or	a
	jr	z,InterpFindWord_found

	; Otherwise, advance to the next dictionary definition and try
	; again.
	inc	hl		; Remember HL=XT+1 from above.
	ld	e,(hl)
	inc	hl
	ld	d,(hl)
	ex	de,hl
	jr	InterpFindWord_tryAgain

InterpFindWord_found:
	dec	hl
	ld	a,-1
	ret


InterpExecute:
; Given an execution token, execute the code for the definition.
;
; Inputs:	HL=execution token (e.g., from InterpFindWord).
; Outputs:	anything.
; Destroys:	AF, BC, DE, HL, IX, IY

	inc	hl
	inc	hl
	inc	hl
	inc	hl
	jp	(hl)


InterpConvertNumber:
; Attempt to interpret a word representing a number, pointed to by the
; HERE pointer.
;
; Zero-length words are never numbers.
;
; Inputs:	(interpHerePtr) points to the word, as it would be returned
;		by a call to InterpNextWord.
; Outputs:	A=0 if the word is not a recognizable number.  A is non-zero
;		if it is.
;		HL=the number if A is non-zero; otherwise, undefined.
; Destroys:	BC, DE

	ld	hl,(interpHerePtr)

	; Zero-length words are never numbers.
	ld	a,(hl)
	or	a,a
	ret	z
	ld	b,a

	; Starting at the first digit
	inc	hl
	ld	de,0			; numeric accumulator

	; Check for sign signifier
	ld	a,(hl)
	cp	a,'+'
	jr	nz,InterpConvertNumber_tryNegative

	xor	a,a
	inc	a
	push	af			; push clear Z flag for negative sign
	jr	InterpConvertNumber_skipSign

InterpConvertNumber_tryNegative:
	cp	a,'-'
	push	af			; push set Z flag for negative sign
	jr	nz,InterpConvertNumber_anotherDigit

InterpConvertNumber_skipSign:
	inc	hl		; Skip over '-' character.
	dec	b		; Decrement length to compensate.

InterpConvertNumber_anotherDigit:
	ld	a,(hl)
	inc	hl
	sub	a,'0'
	jr	c,InterpConvertNumber_NaN
	cp	a,10
	jr	nc,InterpConvertNumber_NaN

	push	hl
	push	bc
	push	af
	ld	h,d
	ld	l,e
	ld	bc,10
	call	UMultiplyHLbyBC
	ex	de,hl
	pop	af
	pop	bc
	pop	hl

	add	a,e
	ld	e,a
	ld	a,d
	adc	a,0
	ld	d,a

	djnz	InterpConvertNumber_anotherDigit

	pop	af
	jr	nz,InterpConvertNumber_unsigned
	ld	hl,0
	or	a,a		; clear carry
	sbc	hl,de		; HL := 0-HL
	ex	de,hl

InterpConvertNumber_unsigned:
	ex	de,hl
	ld	a,1
	ret

InterpConvertNumber_NaN:
	pop	af
	xor	a,a
	ret


interpWordStart:defw	0
interpWordEnd:	defw	0
interpHerePtr:	defw	0
interpDictPtr:  defw	0

interpLength:	defb	0
interpIndex:	defb	0
interpIndex00:	defb	0	; always keep this 0!

