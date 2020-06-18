TestFailed:
; Prints diagnostic to the console telling the user
; which test failed.  This procedure assumes that the
; test is identified with the Test() macro.

	ld	de,(testFileName)
	call	osalPrintString
	ld	de,(testFileLine)
	call	osalPrintString
	ld	de,(testReason)
	call	osalPrintString
	ld	de,testExpMsg
	call	osalPrintString
	ld	hl,(testExpected)
	call	osalPrintHex16
	ld	de,testActMsg
	call	osalPrintString
	ld	hl,(testActual)
	call	osalPrintHex16
	jp	osalTerminate


TestSetExpectedB:
; Stores the value in A in testExpected as a sign-extended
; 16-bit integer.

	ld	hl,testExpected
	jr	testsetb

TestSetActualB:
; Stores the value in A in testActual as a sign-extended
; 16-bit integer.

	ld	hl,testActual
testsetb:
	ld	(hl),a
	sra	a
	sra	a
	sra	a
	sra	a
	sra	a
	sra	a
	sra	a
	sra	a
	inc	hl
	ld	(hl),a
	ret


TestEqual:
; Asserts equality between the expected and actual values.
; Use the Expected() and Actual() macros to set these values.
; If the assertion fails, the program quits immediately with
; an error message.

	ld	a,(testExpected)
	ld	hl,testActual
	cp	a,(hl)
	jr	nz,TestFailed
	ld	a,(testExpected+1)
	inc	hl
	cp	a,(hl)
	jr	nz,TestFailed
	ret


TestNotEqual:
; As above, except testing for non-equality.

	ld	a,(testExpected)
	ld	hl,testActual
	cp	a,(hl)
	ret	nz
	ld	a,(testExpected+1)
	inc	hl
	cp	a,(hl)
	ret	nz
	jr	TestFailed


testFileName:	defw	0
testFileLine:	defw	0
testReason:	defw	0
testExpected:	defw	0
testActual:	defw	0

testExpMsg:	defm	13,10," Expected: $"
testActMsg:	defm	13,10,"   Actual: $"

