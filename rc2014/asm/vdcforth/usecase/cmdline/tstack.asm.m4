include(`testdefs.asm.m4')

	org	0100h


	call	an_empty_stack_has_no_values_to_view
	call	single_stack_element_appears_flush_right
	call	elements_are_separated_by_spaces
	call	elements_can_be_longer_than_a_single_digit
	call	view_cannot_underflow_buffer
	call	deep_stacks_cannot_underflow_buffer
	call	zero_values_produce_a_single_digit
	jp	osalTerminate


	include "drivers/osal/cpm2.asm"
	include "drivers/data.asm"
	include "drivers/math.asm"
	include "utils.asm"
	include "tester.asm"
	include "usecase/cmdline/stack.asm"


setup:
	; reset buffer with bogus contents.
	ld	a,2AH
	ld	(testBuffer),a
	ld	hl,testBuffer
	ld	de,testBuffer+1
	ld	bc,79
	ldir

	; Configure buffer and stack pointers.
	ld	hl,testBuffer
	ld	(stkviewBuffer),hl
	ld	hl,testBuffer+79
	ld	(stkviewBufPos),hl
	ld	hl,stackTop
	ld	(stkData),hl
	ld	(stkDBottom),hl
	ret

setup_for_buffer_underflow:
	call	setup
	ld	hl,testBuffer+3
	ld	(stkviewBuffer),hl
	ld	hl,testBuffer+5
	ld	(stkviewBufPos),hl
	ret


an_empty_stack_has_no_values_to_view:
	Test("An empty stack has no values to view.")
	call	setup
	call	StackBuildView
	ExpectW(testBuffer+79)
	ActualW((stkviewBufPos))
	call	TestEqual
	ret


single_stack_element_appears_flush_right:
	Test("A single stack element appears flush right.")
	call	setup

	ld	(stkReturn),sp
	ld	sp,(stkData)

	ld	hl,1
	push	hl

	ld	(stkData),sp
	ld	sp,(stkReturn)

	call	StackBuildView
	ExpectW(testBuffer+77)	; Numeral plus separating space
	ActualW((stkviewBufPos))
	call	TestEqual
	ret


elements_are_separated_by_spaces:
	call	setup

	ld	(stkReturn),sp
	ld	sp,(stkData)

	ld	hl,1
	push	hl
	ld	hl,2
	push	hl
	ld	hl,3
	push	hl

	ld	(stkData),sp
	ld	sp,(stkReturn)

	call	StackBuildView

	Test("Elements are separated by spaces")
	ExpectB(33H)
	ActualB((testBuffer+79))
	call	TestEqual
	Test("Elements are separated by spaces")
	ExpectB(20H)
	ActualB((testBuffer+78))
	call	TestEqual
	Test("Elements are separated by spaces")
	ExpectB(32H)
	ActualB((testBuffer+77))
	call	TestEqual
	Test("Elements are separated by spaces")
	ExpectB(20H)
	ActualB((testBuffer+76))
	call	TestEqual
	Test("Elements are separated by spaces")
	ExpectB(31H)
	ActualB((testBuffer+75))
	call	TestEqual
	Test("Elements are separated by spaces")
	ExpectB(20H)
	ActualB((testBuffer+74))
	call	TestEqual
	ret


elements_can_be_longer_than_a_single_digit:
	call	setup

	ld	(stkReturn),sp
	ld	sp,(stkData)

	ld	hl,32767
	push	hl

	ld	(stkData),sp
	ld	sp,(stkReturn)

	call	StackBuildView

	Test("Elements can be longer than a single digit")
	ExpectB(37H)
	ActualB((testBuffer+79))
	call	TestEqual

	Test("Elements can be longer than a single digit")
	ExpectB(36H)
	ActualB((testBuffer+78))
	call	TestEqual

	Test("Elements can be longer than a single digit")
	ExpectB(37H)
	ActualB((testBuffer+77))
	call	TestEqual

	Test("Elements can be longer than a single digit")
	ExpectB(32H)
	ActualB((testBuffer+76))
	call	TestEqual

	Test("Elements can be longer than a single digit")
	ExpectB(33H)
	ActualB((testBuffer+75))
	call	TestEqual

	Test("Elements can be longer than a single digit")
	ExpectB(20H)
	ActualB((testBuffer+74))
	call	TestEqual

	ret


view_cannot_underflow_buffer:
	call	setup_for_buffer_underflow

	ld	(stkReturn),sp
	ld	sp,(stkData)

	ld	hl,32767
	push	hl

	ld	(stkData),sp
	ld	sp,(stkReturn)

	call	StackBuildView

	Test("View cannot underflow buffer")
	ExpectB(37H)
	ActualB((testBuffer+5))
	call	TestEqual

	Test("View cannot underflow buffer")
	ExpectB(36H)
	ActualB((testBuffer+4))
	call	TestEqual

	Test("View cannot underflow buffer")
	ExpectB(37H)
	ActualB((testBuffer+3))
	call	TestEqual

	Test("View cannot underflow buffer")
	ExpectB(2AH)
	ActualB((testBuffer+2))
	call	TestEqual

	Test("View cannot underflow buffer")
	ExpectB(2AH)
	ActualB((testBuffer+1))
	call	TestEqual

	Test("View cannot underflow buffer")
	ExpectB(2AH)
	ActualB((testBuffer+0))
	call	TestEqual

	ret


deep_stacks_cannot_underflow_buffer:
	call	setup_for_buffer_underflow

	ld	(stkReturn),sp
	ld	sp,(stkData)

	ld	hl,32767
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl
	push	hl

	ld	(stkData),sp
	ld	sp,(stkReturn)

	call	StackBuildView

	Test("Deep stacks cannot underflow buffer")
	ExpectW(testBuffer+2)
	ActualW((stkviewBufPos))
	call	TestEqual

	ret


zero_values_produce_a_single_digit:
	call	setup

	ld	(stkReturn),sp
	ld	sp,(stkData)

	ld	hl,0
	push	hl

	ld	(stkData),sp
	ld	sp,(stkReturn)

	call	StackBuildView

	Test("Zero values produce a single digit")
	ExpectB(30H)
	ActualB((testBuffer+79))
	call	TestEqual

	Test("Zero values produce a single digit")
	ExpectB(20H)
	ActualB((testBuffer+78))
	call	TestEqual

	ret


testBuffer:	defs	80

myDataStack:	defs	64
stackTop:	defb	0

