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


interpWordStart:defw	0
interpWordEnd:	defw	0
interpHerePtr:	defw	0

interpLength:	defb	0
interpIndex:	defb	0
interpIndex00:	defb	0	; always keep this 0!

