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
	call	_can_parse_words_sequentially
	ret


outer_interpreter_setup_1:
	ld	bc,tib1Length
	ld	de,tib1Length
	ld	hl,tib1

outer_interpreter_setup_common:
	call	TibSetExtent

	ld	hl,testHereBuf
	ld	(interpHerePtr),hl

	xor	a
	ld	(interpIndex),a
	ret


outer_interpreter_setup_2:
	ld	bc,tib2Length
	ld	de,tib2Length
	ld	hl,tib2
	jp	outer_interpreter_setup_common


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
	call	outer_interpreter_setup_1
	call	InterpNextWord

	call	TestSetActualB
	ExpectB(0)
	jp	TestNotEqual


_fills_in_counted_string_at_here:
	Test("Outer interpreter fills in counted-string at HERE")
	call	outer_interpreter_setup_1
	call	InterpNextWord

	ld	hl,(interpHerePtr)
	ld	(r0),hl
	ld	hl,testAWord1
	ld	(r1),hl
	call	StrCompare
	call	TestSetActualB
	ExpectB(0)
	jp	TestEqual

_can_parse_words_sequentially:
	call	outer_interpreter_setup_2

	Test("Outer interpreter can parse words sequentially: Word 1")
	call	InterpNextWord
	call	TestSetActualB
	ExpectB(1)
	call	TestEqual

	ld	hl,(interpHerePtr)
	ld	(r0),hl
	ld	hl,testAWord1
	ld	(r1),hl
	call	StrCompare
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual

	Test("Outer interpreter can parse words sequentially: Word 2")
	call	InterpNextWord
	call	TestSetActualB
	ExpectB(1)
	call	TestEqual

	ld	hl,(interpHerePtr)
	ld	(r0),hl
	ld	hl,testWord2
	ld	(r1),hl
	call	StrCompare
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual

	Test("Outer interpreter can parse words sequentially: Word 3")
	call	InterpNextWord
	call	TestSetActualB
	ExpectB(1)
	call	TestEqual

	ld	hl,(interpHerePtr)
	ld	(r0),hl
	ld	hl,testWord3
	ld	(r1),hl
	call	StrCompare
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual

	Test("Outer interpreter can parse words sequentially: No more words")
	call	InterpNextWord
	call	TestSetActualB
	ExpectB(0)
	jp	TestEqual


tib1:		defb	"        "	; 8 spaces
tib0:		defb	"aWord1"
defc tib1Length = asmpc - tib1

tib2:		defb	"  aWord1  word2",9,"     w3    "
defc tib2Length = asmpc - tib2

testHereBuf:	defs	64
testAWord1:	defb	6,"aWord1"
testWord2:	defb	5,"word2"
testWord3:	defb	2,"w3"
