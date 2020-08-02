include(`testdefs.asm.m4')

	org	0100h


	call	words_not_starting_with_digit_cannot_be_numbers
	call	zero_length_words_are_never_numbers
	call	words_starting_with_a_digit_
	call	single_digit_numbers_are_converted
	call	multi_digit_numbers_are_converted
	call	signed_numbers_are_recognized
	call	signed_numbers_are_converted
	call	positive_numbers_are_recognized
	call	positive_numbers_are_converted
	jp	osalTerminate


	include "drivers/osal/cpm2.asm"
	include "drivers/data.asm"
	include "drivers/math.asm"
	include "utils.asm"
	include "tester.asm"
	include "usecase/cmdline/strings.asm"
	include "usecase/cmdline/tib.asm"
	include "usecase/cmdline/interp.asm"


words_not_starting_with_digit_cannot_be_numbers:
	Test("Words not starting with a digit cannot be numbers")
	ld	hl,testWord1
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual
	ret

testWord1:
	defb	3,"BYE"


zero_length_words_are_never_numbers:
	Test("Zero-length words are never numbers.")
	ld	hl,testWord3
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual
	ret

testWord3:
	defb	0,'9'


words_starting_with_a_digit_:
	call	_followed_by_all_digits_are_numbers
	call	_but_with_nondigit_characters_are_never_numbers
	ret


_followed_by_all_digits_are_numbers:
	Test("Words starting with a digit and followed by all digits are numbers.")
	ld	hl,testWord2
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	call	TestSetActualB
	ExpectB(1)
	call	TestEqual
	ret

testWord2:
	defb	1,"9"


_but_with_nondigit_characters_are_never_numbers:
	Test("Words starting with a digit but with nondigit characters are never numbers.")
	ld	hl,testWord4
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual
	ret

testWord4:
	defb	2,"2/"		; arithmetic right-shift operation in Forth


single_digit_numbers_are_converted:
	Test("Single-digit numbers are converted.")
	ld	hl,testWord2
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	ld	(testActual),hl
	ExpectB(9)
	call	TestEqual
	ret


multi_digit_numbers_are_converted:
	Test("Multi-digit numbers are converted.")
	ld	hl,testWord5
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	ld	(testActual),hl
	ld	hl,12345
	ld	(testExpected),hl
	call	TestEqual
	ret

testWord5:
	defb	5,"12345"


signed_numbers_are_recognized:
	Test("Signed numbers are recognized.")
	ld	hl,testWord6
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	call	TestSetActualB
	ExpectB(1)
	call	TestEqual
	ret

testWord6:
	defb	6,"-12345"


signed_numbers_are_converted:
	Test("Signed numbers are converted.")
	ld	hl,testWord6
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	ld	(testActual),hl
	ld	hl,-12345
	ld	(testExpected),hl
	call	TestEqual
	ret


positive_numbers_are_recognized:
	Test("Positive numbers are recognized.")
	ld	hl,testWord7
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	call	TestSetActualB
	ExpectB(1)
	call	TestEqual
	ret

testWord7:
	defb	6,"+12345"


positive_numbers_are_converted:
	Test("Positive numbers are converted.")
	ld	hl,testWord7
	ld	(interpHerePtr),hl
	call	InterpConvertNumber
	ld	(testActual),hl
	ld	hl,12345
	ld	(testExpected),hl
	call	TestEqual
	ret

