include(`testdefs.asm.m4')

	org	0100h


	call	resetTib
	call	typedChar
	jp	osalTerminate

	include "drivers/osal/cpm2.asm"
	include "utils.asm"
	include "tester.asm"
	include "usecase/cmdline/tib.asm"


resetTib:
	call	TibReset

	Test("An empty TIB has zero length")
	ExpectB(0)
	ActualB((tibLength))
	call	TestEqual

	ret


typedChar:
	call	TibReset

	ld	a,41h
	call	TibChar

	Test("A non-empty TIB has a length")
	ExpectB(0)
	ActualB((tibLength))
	call	TestNotEqual

	ret

