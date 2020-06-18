include(`testdefs.asm.m4')

	org	0100h

	call	testPutChar
	jp	osalTerminate


testPutChar:
	call	afterCR
	call	afterLF
	call	afterChar
	call	afterCharAfterRightMargin
	ret


setup:
	call	i_UtilInitWords
	defb	4
	defw	vdcPort,0D600h	; for C128; use 006Eh for RC2014
	defw	r0, 10
	defw	r1, 20
	defw	vdcPutCharFault, ourFaultHandler

	call	i_UtilInitBytes
	defb	4
	defw	vdcLeftMargin
	defb	5
	defw	vdcRightMargin
	defb	100
	defw	faultCalled
	defb	0
	defw	faultChar
	defb	0

	ret


ourFaultHandler:
	ld	a,(r4)
	ld	(faultChar),a
	ld	a,1
	ld	(faultCalled),a
	ret


afterCR:
	call	setup

	ld	a,0Dh
	call	VdcPutChar

	Test("CR should return to the left margin")
	ExpectB((vdcLeftMargin))
	ActualB((r0))
	call	TestEqual

	Test("CR should not adjust the cursor's vertical position")
	ExpectB(20)
	ActualB((r1))
	jp	TestEqual


afterLF:
	call	setup

	ld	a,0Ah
	call	VdcPutChar

	Test("LF should maintain the horizontal position of the cursor")
	ExpectB(10)
	ActualB((r0))
	call	TestEqual

	Test("LF should advance the vertical position")
	ExpectB(21)
	ActualB((r1))
	jp	TestEqual


afterChar:
	call	setup

	ld	a,41h
	call	VdcPutChar

	Test("Printing a character should advance the cursor to the right")
	ExpectB(11)
	ActualB((r0))
	call	TestEqual

	Test("Printing a character should not fault")
	ExpectB(0)
	ActualB((faultCalled))
	jp	TestEqual


afterCharAfterRightMargin:
	call	setup
	ld	a,(vdcRightMargin)
	ld	(r0),a

	ld	a,41h
	call	VdcPutChar

	Test("Printing a chr at/beyond right margin should not advance anything")
	ExpectB((vdcRightMargin))
	ActualB((r0))
	call	TestEqual

	Test("Printing a chr at/beyond right margin should fault")
	ExpectB(1)
	ActualB((faultCalled))
	call	TestEqual

	Test("The fault handler should be passed the character to print.")
	ExpectB(41H)
	ActualB((faultChar))
	call	TestEqual

	ret


faultCalled:	defb	0
faultChar:	defb	0


	include "drivers/osal/cpm2.asm"
	include "drivers/vdc/c128.asm"
	include "drivers/data.asm"
	include "utils.asm"
	include "tester.asm"
