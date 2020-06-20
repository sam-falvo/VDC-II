; Terminal Input Buffer


TibSetExtent:
; Inputs:	BC=number of characters already in input buffer
;		DE=maximum capacity of input buffer
;		HL=address of buffer
;
; Outputs:
; Destroys:	HL
	push	hl
	ld	(tibBuffer),hl
	add	hl,de
	ld	(tibBufferEnd),hl
	pop	hl
	add	hl,bc
	ld	(tibInsertionPt),hl
	ret


TibLength:
; Inputs:
; Outputs:	HL=current length of input buffer (0 <= HL < capacity)
; Destroys:	DE
	ld	hl,(tibInsertionPt)
	ld	de,(tibBuffer)
	or	a	; clear carry flag.  NOTE: Opposite of 6502!
	sbc	hl,de
	ret


TibCapacity:
; Inputs:
; Outputs:	HL=maximum capacity of input buffer.
; Destroys:	DE
	ld	de,(tibBuffer)
	ld	hl,(tibBufferEnd)
	or	a
	sbc	hl,de
	ret


TibTypeChar:
; Inputs:	A=character typed
; Outputs:
; Destroys:	HL
	ld	de,(tibBufferEnd)	; Return if there's no room left.
	ld	hl,(tibInsertionPt)
	or	a
	sbc	hl,de
	ret	z
	ret	nc

	ld	hl,(tibInsertionPt)
	ld	(hl),a
	inc	hl
	ld	(tibInsertionPt),hl
	ret


TibBackspace:
; Inputs:
; Outputs:
; Destroys:
	call	TibLength		; Return if there's nothing to backspace.
	ret	z
	ret	c

	ld	hl,(tibInsertionPt)
	dec	hl
	ld	(tibInsertionPt),hl
	ret


tibBuffer:	defw	0
tibBufferEnd:	defw	0
tibInsertionPt:	defw	0

