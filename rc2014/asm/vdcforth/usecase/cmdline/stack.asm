; This module provides a view into the current data stack.


StackBuildView:
	ld	hl,(stkData)
stackBuildView_loop:
	ld	bc,(stkDBottom)
	or	a
	sbc	hl,bc	; hl is now biased!
	ret	nc
	add	hl,bc	; Unbias HL
	call	StackBuildView_DumpItem
	inc	hl
	inc	hl
	jr	stackBuildView_loop

StackBuildView_DumpItem:
	push	hl

	xor	a,a
	ld	(stkviewZeroBlank),a

	ld	a,(hl)
	inc	hl
	ld	h,(hl)
	ld	l,a

StackBuildView_DumpItem_NextDigit:
	ld	a,h
	or	a,l
	jr	nz,StackBuildView_DumpItem_NotDone
	ld	a,(stkviewZeroBlank)
	or	a,a
	jr	nz,StackBuildView_DumpItem_Done
StackBuildView_DumpItem_NotDone:
	ld	a,1
	ld	(stkviewZeroBlank),a
	ld	bc,10
	call	UDivideHLbyBC
	ld	a,l
	add	a,30H
	call	StackBuildView_Hold
	ex	de,hl
	jr	StackBuildView_DumpItem_NextDigit

StackBuildView_DumpItem_Done:
	ld	a,20H
	call	StackBuildView_Hold
	pop	hl
	ret


StackBuildView_Hold:
	ld	hl,(stkviewBufPos)
	ld	bc,(stkviewBuffer)
	or	a
	sbc	hl,bc
	ret	c
	add	hl,bc
	ld	(hl),a
	dec	hl
	ld	(stkviewBufPos),hl
	ret


stkData:	defw	0	; current top of data stack.
stkReturn:	defw	0	; current top of return stack.
stkDBottom:	defw	0	; bottom of data stack.
stkviewBufPos:	defw	0
stkviewBuffer:	defw	0
stkviewZeroBlank:defb	0

