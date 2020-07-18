include(`testdefs.asm.m4')

	org	0100h


	call	dividing_unsigned_65535_by_10_
	call	dividing_signed_32767_by_24_
	jp	osalTerminate


	include "drivers/osal/cpm2.asm"
	include "utils.asm"
	include "tester.asm"
	include "drivers/math.asm"


dividing_unsigned_65535_by_10_:
	call	_must_answer_6553
	call	_must_answer_remainder_5
	ret

dividing_signed_32767_by_24_:
	call	_must_answer_1365
	call	_must_answer_remainder_2
	ret


_must_answer_6553:
	Test("Dividing 65535 by 10 should answer 6553.")
	ld	hl,65535
	ld	bc,10
	call	UDivideHLbyBC
	ld	(testActual),de
	ExpectW(6553)
	jp	TestEqual

_must_answer_remainder_5:
	Test("Dividing 65535 by 10 should answer remainder 5.")
	ld	hl,65535
	ld	bc,10
	call	UDivideHLbyBC
	ld	(testActual),hl
	ExpectW(5)
	jp	TestEqual


_must_answer_1365:
	Test("Dividing 32767 (signed) by 24 must answer 1365")
	ld	hl,32767
	ld	bc,24
	call	SDivideHLbyBC
	ld	(testActual),de
	ExpectW(1365)
	jp	TestEqual

_must_answer_remainder_2:
	Test("Dividing 32767 (signed) by 24 must answer remainder 7")
	ld	hl,32767
	ld	bc,24
	call	SDivideHLbyBC
	ld	(testActual),hl
	ExpectW(7)
	jp	TestEqual

