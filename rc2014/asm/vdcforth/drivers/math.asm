SDivideHLbyBC:
; Performs a *signed* division, calculating DE=HL/BC.
;
; N.B.:
; This code was transliterated from a public web forum post located at
; https://www.omnimaga.org/asm-language/(z80)-16-by-16-signed-division/msg353139/#msg353139
; The author is Xeda112358.
;
; Speed:	1315-2b cycles
;		add 24 if HL is negative
;		add 24 if BC is negative
;		add 28 if only one is negative
;
; Inputs:	HL is the numerator
;		BC is the denominator
;
; Outputs:	DE is the quotient
;		HL is the remainder
;		BC is not changed
;		z flag is set
;		c flag is reset
;
; Destroys:	AF

	ld	a,h	; Bit 7 of A=1 iff signs differ.
	xor	b
	push	af

	xor	b	; Restore high byte of HL
	jp	p,SDivideHLbyBC_HLalreadyPositive
	xor	a	; HL = 0-HL
	sub	l
	ld	l,a
	sbc	a,a
	sub	h
	ld	h,a

SDivideHLbyBC_HLalreadyPositive:
	; At this point, bit 7 of A is guaranteed to be 0.
	; XOR B puts the sign of B into A (we don't care about
	; the remaining bits).
	xor	b
	jp	p,SDivideHLbyBC_BCalreadyPositive
	xor	a	; BC = 0-BC
	sub	c
	ld	c,a
	sbc	a,a
	sub	b
	ld	b,a

SDivideHLbyBC_BCalreadyPositive:
	add	hl,hl	; Drop unused sign bit...
	ld	a,15	; ... and only consider the bottom 15 bits.
	ld	de,0
	ex	de,hl	; Bits 15-1 of DE is now the numerator.
	jp	SDivideHLbyBC_jumpin

SDivideHLbyBC_Loop1:
	; If we're here, we tried subtracting the denominator from the
	; candidate partial numerator.  It didn't work as we'd hoped, so
	; we must restore the partial numerator by re-adding the
	; denominator.
	add	hl,bc

SDivideHLbyBC_Loop2:
	dec	a
	jr	z,SDivideHLbyBC_EndSDiv

SDivideHLbyBC_jumpin:
	sla	e	; shift next bit of numerator into partial numerator.
	rl	d
	adc	hl,hl
	sbc	hl,bc	; Can we divide?  If not, undo and shift again.
	jr	c,SDivideHLbyBC_Loop1
	inc	e	; Otherwise, record the success and shift again.
	jp	SDivideHLbyBC_Loop2

SDivideHLbyBC_EndSDiv:
	pop	af	; A[7] set if numerator and denominator signs differ.
	ret	p	; Nothing to do if they're the same.
	xor	a	; DE = 0-DE otherwise.
	sub	e
	ld	e,a
	sbc	a,a
	sub	d
	ld	d,a
	ret


UDivideHLbyBC:
; Performs an *unsigned* division, calculating DE=HL/BC.
;
; N.B.:
; This code is based on the SDivideHLbyBC procedure above, modified to
; remove all sign-related logic.
;
; Inputs:	HL is the numerator
;		BC is the denominator
;
; Outputs:	DE is the quotient
;		HL is the remainder
;		BC is not changed
;		z flag is set
;		c flag is reset
;
; Destroys:	AF

	ld	a,16	; All 16 bits are valid.
	ld	de,0
	ex	de,hl	; Bits 15-0 of DE is now the numerator.
	jp	UDivideHLbyBC_jumpin

UDivideHLbyBC_Loop1:
	; If we're here, we tried subtracting the denominator from the
	; candidate partial numerator.  It didn't work as we'd hoped, so
	; we must restore the partial numerator by re-adding the
	; denominator.
	add	hl,bc

UDivideHLbyBC_Loop2:
	dec	a
	ret	z	; Return if no further bits to consider.

UDivideHLbyBC_jumpin:
	sla	e	; shift next bit of numerator into partial numerator.
	rl	d
	adc	hl,hl
	sbc	hl,bc	; Can we divide?  If not, undo and shift again.
	jr	c,UDivideHLbyBC_Loop1
	inc	e	; Otherwise, record the success and shift again.
	jp	UDivideHLbyBC_Loop2


UMultiplyHLbyBC:
; Answers with the unsigned product of the unsigned multiplicands.
;
; Inputs:	BC=multiplicand
;		HL=multiplicand
; Outputs:	DE:HL=product (DE having the most significant 32-bits).
; Destroys:	AF, BC
;
; Based on code found at
; https://wikiti.brandonw.net/index.php?title=Z80_Routines:Math:Multiplication#16.2A16_multiplication

	ld	a,16

UMultiplyHLbyBC_again:
	add	hl,hl
	rl	e
	rl	d
	jr	nc,UMultiplyHLbyBC_0bit
	add	hl,bc
	jr	nc,UMultiplyHLbyBC_0bit
	inc	de
UMultiplyHLbyBC_0bit:
	dec	a
	jr	nz,UMultiplyHLbyBC_again

	ret

