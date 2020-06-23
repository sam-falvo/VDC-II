include(`testdefs.asm.m4')

	org	0100h


	call	an_empty_tib_
	call	a_typed_character_
	jp	osalTerminate

	include "drivers/osal/cpm2.asm"
	include "utils.asm"
	include "tester.asm"
	include "usecase/cmdline/tib.asm"


setup0:
	ld	bc,0		; Start with empty TIB
	jr	setupN
setup1:
	ld	bc,1		; Start with one byte in the TIB
setupN:
	ld	de,8		; .. of 8 bytes in length
	ld	hl,myBuffer	; .. located at myBuffer
	jp	TibSetExtent


myBuffer:
	defm	"........."




an_empty_tib_:
	call	_has_zero_length
	call	_ignores_backspace
	ret


_has_zero_length:
	call	setup0
	Test("An empty TIB has zero length")
	ExpectW(0)
	call	TibLength
	ld	(testActual),hl
	jp	TestEqual


_ignores_backspace:
	call	setup0
	Test("An empty TIB cannot backspace")
	call	TibBackspace
	ExpectW(0)
	call	TibLength
	ld	(testActual),hl
	jp	TestEqual




a_typed_character_:
	call	_is_placed_at_insertion_point
	call	_advances_the_insertion_point_if_space_allows
	call	_is_ignored_if_no_space_left
	call	_can_be_backspaced
	ret


_is_placed_at_insertion_point:
	call	setup0
	Test("A typed character is placed at insertion point")
	ld	a,41H
	call	TibTypeChar
	ExpectB(41H)
	ActualB((myBuffer))
	jp	TestEqual


_advances_the_insertion_point_if_space_allows:
	call	setup1
	Test("A typed character advances the insertion point")
	ld	a,42H
	call	TibTypeChar
	ExpectB(42H)
	ActualB((myBuffer+1))
	jp	TestEqual


_is_ignored_if_no_space_left:
	call	setup0
	ld	a,41H
	call	TibTypeChar
	ld	a,42H
	call	TibTypeChar
	ld	a,43H
	call	TibTypeChar
	ld	a,44H
	call	TibTypeChar
	ld	a,45H
	call	TibTypeChar
	ld	a,46H
	call	TibTypeChar
	ld	a,47H
	call	TibTypeChar
	ld	a,48H
	call	TibTypeChar
	ld	a,49H		; should be ignored
	call	TibTypeChar
	Test("A typed character is ignored if no more space is left for it")
	ExpectB(41H)
	ActualB((myBuffer+0))
	call	TestEqual
	ExpectB(42H)
	ActualB((myBuffer+1))
	call	TestEqual
	ExpectB(43H)
	ActualB((myBuffer+2))
	call	TestEqual
	ExpectB(44H)
	ActualB((myBuffer+3))
	call	TestEqual
	ExpectB(45H)
	ActualB((myBuffer+4))
	call	TestEqual
	ExpectB(46H)
	ActualB((myBuffer+5))
	call	TestEqual
	ExpectB(47H)
	ActualB((myBuffer+6))
	call	TestEqual
	ExpectB(48H)
	ActualB((myBuffer+7))
	call	TestEqual
	ExpectB(2EH)
	ActualB((myBuffer+8))
	call	TestEqual

	Test("A full buffer should have a length equal to its capacity")
	call	TibCapacity
	ld	(testExpected),hl
	call	TibLength
	ld	(testActual),hl
	jp	TestEqual


_can_be_backspaced:
	call	setup1
	call	TibBackspace
	Test("A typed character can be backspaced")
	ExpectW(0)
	call	TibLength
	ld	(testActual),hl
	jp	TestEqual

