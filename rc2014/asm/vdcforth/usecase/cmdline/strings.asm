StrCompare:
; Compares two counted-strings, pointed to respectively by
; pointers R0 and R1.
;
; Inputs:	(r0) points to first string's length byte.
; 		(r1) points to second string's length byte.
; Outputs:	A=0 if strings are equal; non-zero otherwise.
; Destroys:	BC, DE, HL, (r0), (r1)

        ld	de,(r0)
	ld	a,(de)
	ld	hl,(r1)
	cp	(hl)
	jr	nz,StrCompare_NotEqual
	inc	hl
	inc	de
	ld	b,a

StrCompare_Loop:
	ld	a,(de)
	inc	de
	cp	(hl)
	inc	hl
	jr	nz,StrCompare_NotEqual
	djnz	StrCompare_Loop

StrCompare_Equal:
	xor	a,a		; Also sets Z flag.
	ret

StrCompare_NotEqual:
	ld	a,1
	or	a		; Convenience: clear Z flag.
	ret
