include(`testdefs.asm.m4')

	org	0100h


	call	an_empty_tib_has_nothing_to_interpret
	call	outer_interpreter_

	jp	osalTerminate


	include "drivers/osal/cpm2.asm"
	include	"drivers/data.asm"
	include "utils.asm"
	include "tester.asm"
	include "usecase/cmdline/tib.asm"
	include "usecase/cmdline/strings.asm"
	include "usecase/cmdline/interp.asm"


outer_interpreter_:
	call	_skips_whitespace
	call	_fills_in_counted_string_at_here
	ret


outer_interpreter_setup:
	ld	bc,tib1Length
	ld	de,tib1Length
	ld	hl,tib1
	call	TibSetExtent

	ld	hl,testHereBuf
	ld	(interpHerePtr),hl

	xor	a
	ld	(interpIndex),a
	ret


an_empty_tib_has_nothing_to_interpret:
	Test("An empty TIB has nothing to interpret")
	ld	bc,0
	ld	de,0
	ld	hl,tib0
	call	TibSetExtent

	ld	hl,testHereBuf
	ld	(interpHerePtr),hl

	xor	a
	ld	(interpIndex),a

	call	InterpNextWord
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual

	ret


_skips_whitespace:
	Test("Outer interpreter skips whitespace")
	call	outer_interpreter_setup
	call	InterpNextWord

	call	TestSetActualB
	ExpectB(0)
	jp	TestNotEqual


_fills_in_counted_string_at_here:
	Test("Outer interpreter fills in counted-string at HERE")
	call	outer_interpreter_setup
	call	InterpNextWord

	ld	hl,(interpHerePtr)
	ld	(r0),hl
	ld	hl,testAWord1
	ld	(r1),hl
	call	StrCompare
	call	TestSetActualB
	ExpectB(0)
	jp	TestEqual


tib1:		defb	"        "	; 8 spaces
tib0:		defb	"aWord1"
defc tib1Length = asmpc - tib1

testHereBuf:	defs	64
testAWord1:	defb	6,"aWord1"

