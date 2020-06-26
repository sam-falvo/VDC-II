include(`testdefs.asm.m4')

	org	0100h


	call	two_strings_of_unequal_length_
	call	two_strings_of_equal_length_
	jp	osalTerminate


	include "drivers/osal/cpm2.asm"
	include "drivers/data.asm"
	include "utils.asm"
	include "tester.asm"
	include "usecase/cmdline/strings.asm"


two_strings_of_unequal_length_:
	call	_must_not_be_equal_1
	ret


_must_not_be_equal_1:
	ld	hl,str1
	ld	(r0),hl
	ld	hl,str2
	ld	(r1),hl
	call	StrCompare
	Test("Two strings of unequal length must never be equal.")
	call	TestSetActualB
	ExpectB(0)
	call	TestNotEqual
	ret


str1:	defb	1,"!"
str2:	defb	5,"!!!!!"


two_strings_of_equal_length_:
	call	_and_equal_contents_
	call	_and_unequal_contents_
	ret


_and_equal_contents_:
	call	_must_compare_as_equal
	ret


_and_unequal_contents_:
	call	_must_not_be_equal_2
	ret


_must_compare_as_equal:
	ld	hl,str3
	ld	(r0),hl
	ld	hl,str4
	ld	(r1),hl
	call	StrCompare
	Test("Two strings of equal length and equal contents must compare as equal")
	call	TestSetActualB
	ExpectB(0)
	call	TestEqual
	ret


_must_not_be_equal_2:
	ld	hl,str5
	ld	(r0),hl
	ld	hl,str2
	ld	(r1),hl
	call	StrCompare
	Test("Two strings of equal length but unequal content must never be equal.")
	call	TestSetActualB
	ExpectB(0)
	call	TestNotEqual
	ret


str3:	defb	2,"!!"
str4:	defb	2,"!!"
str5:	defb	5,"!!!!$"
