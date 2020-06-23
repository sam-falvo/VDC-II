; VDC Driver/Library for C128
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.


VdcInitialize:
; Restores VDC to known-good condition for the UE.
;
; Inputs:	(vdcport) refers to I/O port of VDC-II core.
; Outputs:
; Destroys:	A, BC, DE, HL

	ld	hl,0D600H
	ld	(vdcPort),hl

	ld	a,20H
	ld	(vdcFontBase),a

	call	VdcInitMode
	call	VdcInitFont
	call	VdcInitCursor
	ret


VdcInitCursor:
	; Set a block cursor for all 8 scanlines.
	; NOTE: We set R11 to 8 instead of 7 because the 8563
	; and 8568 has a bug where if you set it to 7, then the
	; final line of the cursor will not be displayed.  This
	; "workaround" should be compatible with the VDC-II as
	; well, even though it does not have this bug.

	ld	a,10
	ld	e,0
	call	VdcOutByte
	ld	a,11
	ld	e,8
	jp	VdcOutByte


VdcInitFont:
; Uploads the system font to VDC memory.
; Only glyphs 32-127 are guaranteed to be valid.
; Other glyphs are possible in the future.
;
; The font is loaded at base address determined by
; (vdcFontBase << 8) & 0E000H.
;
; Inputs:	(vdcport) refers to I/O port of VDC-II core.
;		(vdcFontBase) points to the base page of
;		the font; bits 4-0 are ignored and assumed to
;		be zero.
; Outputs:
; Destroys:	A, HL

	ld	a,(vdcFontBase)
	and	0E0h
	ld	d,a
	ld	e,0
	ld	hl,32*16	; First glyph is space
	add	hl,de
	ex	de,hl
	call	VdcSetUpdatePtr

	ld	hl,fontBase
.vdcinitfontloop
	ld	a,(hl)		; The C128 uses progressively scanned, 8px tall characters.
	inc	hl		; We fill the top half of each character cell, and skip the
	call	VdcWriteByte	; bottom half by filling those rows with garbage values.
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte
	ld	a,(hl)
	inc	hl
	call	VdcWriteByte

	call	VdcWriteByte
	call	VdcWriteByte
	call	VdcWriteByte
	call	VdcWriteByte
	call	VdcWriteByte
	call	VdcWriteByte
	call	VdcWriteByte
	call	VdcWriteByte

	ld	a,h
	cp	fontEnd / 256
	jr	nz,vdcinitfontloop
	ld	a,l
	cp	fontEnd & 0FFH
	jr	nz,vdcinitfontloop
	ret

.fontBase
	include	"drivers/vdc/glyphs.inc"
.fontEnd


VdcInitMode:
; Resets the VDC to the UE's default video mode.
; As of this writing, this sets an 80x30 text mode display mode,
; with text appearing at VDC address 0000H, attributes at 0C00H,
; and the character font appearing at 2000H.
;
; This procedure does not clear the screen or affect other
; attributes of the VDC driver.
;
; Inputs:	(vdcPort) refers to I/O port of VDC-II core.
; Outputs:
; Destroys:	A, BC, DE, HL

	; The C128 should already have initialized the display
	; to an 80x25 video mode.
	ld	a,80
	ld	(vdcCharWidth),a
	ld	a,25
	ld	(vdcCharHeight),a
	ret


VdcWaitReady:
; Some registers of the VDC, when written to, commences background
; tasks which the CPU must wait for before using the VDC again.
; This procedure waits until the VDC is ready for more interaction.
;
; Inputs:	(vdcPort) refers to I/O port of VDC-II core.
; Outputs:
; Destroys:

	push	af
	push	bc

	ld	bc,(vdcPort)
.vdcwaitloop
	in	a,(c)
	and	80H
	jr	z,vdcwaitloop

	pop	bc
	pop	af
	ret


VdcOutByte:
; Inputs:	A = VDC Register to write
;		E = byte to write into addressed register
; Outputs:
; Destroys: A

	push	bc
	call	VdcWaitReady
	ld	bc,(vdcPort)
	out	(c),a
	inc	c
	ld	a,e
	out	(c),a
	pop	bc
	ret


VdcOutWord:
; Inputs:	A = VDC Register to write
;		DE = word to write into addressed register.
;		Note that VDC registers are big-endian, so
;		D is written to the address in A, and E is
;		written at A+1!
; Outputs:
; Destroys: A, BC

	push	de
	push	af
	ld	e,d
	call	VdcOutByte
	pop	af
	inc	a
	pop	de
	jp	VdcOutByte


VdcSetUpdatePtr:
; Inputs:	DE = address to write to the update pointer address.
; Outputs:
; Destroys:	A
	ld	a,18
	jp	VdcOutWord


VdcSetCursorPtr:
; Inputs:	DE = address to write to the update pointer address.
; Outputs:
; Destroys:	A
	ld	a,14
	jp	VdcOutWord


VdcWriteByte:
; Inputs:	A = Byte to write to VDC memory
; Outputs:
; Destroys:	A, DE
	ld	e,a
	ld	a,31
	jp	VdcOutByte


VdcDrawTextSlab:
; Draws a solid rectangle filled with the character in (r4).
; The upper left-hand corner is specified in (r0,r1).
; The lower right-hand corner is in (r2,r3).
;
; Inputs:
; Outputs:
; Destroys:	AF, (r1)

	ld	a,(r1)	; Return if we've reached or exceeded the bottom edge.
.drawtextslabloop
	ld	bc,(r3)
	cp	c
	ret	z
	ret	nc

	call	VdcDrawTextLine
	ld	a,(r1)
	inc	a
	ld	(r1),a
	jr	drawtextslabloop


VdcDrawAttrSlab:
; Paints a rectangular region on the screen with the specified attributes.
; The upper left-hand corner is specified in (r0,r1).
; The lower right-hand corner is in (r2,r3).
; Attributes in r4.
;
; Inputs:
; Outputs:
; Destroys:	AF, (r1)

	ld	a,(r1)	; Return if we've reached or exceeded the bottom edge.
.drawattrslabloop
	ld	bc,(r3)
	cp	c
	ret	z
	ret	nc

	call	VdcDrawAttrLine
	ld	a,(r1)
	inc	a
	ld	(r1),a
	jr	drawattrslabloop


VdcDrawTextLine:
; Draws a line of characters starting at (r0,r1) and ending
; at (r2,r1).  R0 must be less than r2.  The character to draw
; is in (r4).
;
; Inputs:	(vdcPort) refers to VDC-II core to use.
; Outputs:
; Destroys:	AF, BC, DE, HL

	ld	de,0000h
.drawtextattrline
	call	_CalcUpdatePtr

	ld	a,(r2)	; B := width of the line
	ld	de,(r0)
	sub	a,e
	ld	b,a
	ret	z	; Exit if we have nothing to do

	ld	a,(r4)
.drawtextlineloop
	call	VdcWriteByte
	djnz	drawtextlineloop
	ret


VdcDrawAttrLine:
; Paints a line of attributes starting at (r0,r1) and ending
; at (r2,r1).  R0 must be less than r2.  The attribute to use
; is in (r4).
;
; Inputs:	(vdcPort) refers to VDC-II core to use.
; Outputs:
; Destroys:	AF, BC, DE, HL

	ld	de,2048
	jp	drawtextattrline


_CalcUpdatePtr:
; Inputs:	DE = base address (0 for text, 0C00H for attrs)
; Destroys: 	AF, DE, HL
	call	_CalcAddress
	jp	VdcSetUpdatePtr


_CalcCursorPtr:
; Inputs:	DE = base address (typically, 0 for text)
; Destroys: 	AF, DE, HL
	call	_CalcAddress
	jp	VdcSetCursorPtr


_CalcAddress:
	push	de
	ld	a,(r1)			; HL := r1 * 80
	and	a,1FH
	add	a,a
	ld	e,a
	ld	d,0
	ld	hl,times80table
	add	hl,de
	ld	a,(hl)
	inc	hl
	ld	h,(hl)
	ld	l,a
	ld	de,(r0)			; HL := (r1 * 80) + r0
	add	hl,de
	pop	de
	add	hl,de
	ex	de,hl
	ret

.times80table
	defw	0, 80, 160, 240, 320, 400, 480, 560
	defw	640, 720, 800, 880, 960, 1040, 1120, 1200
	defw	1280, 1360, 1440, 1520, 1600, 1680, 1760, 1840
	defw	1920, 2000, 2080, 2160, 2240, 2320, 2400, 2480


VdcPrintRawText:
; Prints a string of a given length.  If the text runs off the right-hand
; edge of the screen, it will wrap around to the other side, and/or if at the
; bottom of the screen, it'll overflow into memory beyond the text buffer.
; Use this function with care.
;
; Inputs:	(r0) Left edge of the text to print.
;		(r1) Top edge of the text to print.
;		(r2) Address of the text to print.
;		(r3) Length of the text to print.
; Outputs:
; Destroys:	AF, BC, DE, HL

	; If no more characters are left to print, just return.
	ld	a,(r3)
	ld	b,a
	ld	a,(r3+1)
	or	b
	ret	z

	; Otherwise, print the next character, and repeat.
	ld	hl,(r2)
	ld	a,(hl)
	inc	hl
	ld	(r2),hl
	call	VdcPutChar

	ld	hl,(r3)
	dec	hl
	ld	(r3),hl
	jr	VdcPrintRawText

; 	ld	de,0000h
; 	call	_CalcUpdatePtr
; 	ld	hl,(r2)
; 	ld	a,(r3)
; 	ld	b,a
; 
; .printrawtextloop
; 	ld	a,(hl)
; 	inc	hl
; 	call	VdcWriteByte
; 	djnz	printrawtextloop
; 	ret

VdcVsyncCheck:
; Checks for a VSYNC event and, if it happens, invokes the VSYNC event
; handler, if any.
;
; Inputs:	(vdcPort) refers to the VDC-II core to check.
;		(vdcVSHandler) points to the current VSYNC handler, if any.
;		Set to 0 if none.
; Outputs:
; Destroys:	AF, BC, HL

	ld	hl,(vdcVSHandler)	; First, check to make sure we even have a handler installed.
	ld	a,h			; There's no point in doing anything unless we have a handler to
	or	l			; call in the first place.
	ret	z

	; Check for the *falling edge* of VSYNC.  That is, when VSYNC goes from 1->0.  We ignore the
	; 0->1 case.

	ld	bc,(vdcPort)
	in	a,(c)
	and	a,20h			; Isolate current VSYNC flag.
	ld	c,a
	xor	a,20h			; Set only if flag is 0
	ld	b,a
	ld	a,(vdcVSFlag)
	and	b			; non-zero only if VSYNC flag transitioned from 1->0.
	jr	z,vdcvschk0

	; If we're here, we know that VSYNC transitioned from 1 to 0.  Record the VSYNC flag for
	; later use and invoke the handler.

	ld	a,c
	ld	(vdcVSFlag),a
	ld	hl,(vdcVSHandler)	; Call VSYNC handler and return.
	jp	(hl)

	; If we're here, we know that VSYNC either remained stable or transitioned from 0 to 1.
	; We don't do anything under these circumstances.

.vdcvschk0
	ld	a,c
	ld	(vdcVSFlag),a
	ret


VdcPutString:
; Prints out a string, interpreting control codes along the way.  The string must be
; NUL-terminated.
;
; Inputs:	(vdcPort) refers to the VDC-II core to use.
;		(r0) left edge of first line of string to print.
;		(r1) top edge/baseline of first line of string to print.
;		(r2) points to a NUL-terminated string to print.
;		(vdcLeftMargin) holds the coordinate of the left-edge of text.
;		(vdcRightMargin) holds the right-hand boundary for text.
; Outputs:	(r0, r1) coordinates where the next string or character will
;		be printed.
; Destroys:	A, BC, DE, HL

	ld	hl,(r2)
	ld	a,(hl)
	inc	hl
	ld	(r2),hl
	or	a
	ret	z

	call	VdcPutChar
	jr	VdcPutString


VdcPutChar:
; Prints out a string, interpreting control codes along the way.  The string must be
; NUL-terminated.
;
; If the string fault handler is called, its interface conforms to the following:
; Fault Handler Inputs:
;	(r0, r1)	left/baseline of the cursor's current location
;	(r4)		character to print
;
; Inputs:	(vdcPort) refers to the VDC-II core to use.
;		(r0) left edge of first line of string to print.
;		(r1) top edge/baseline of first line of string to print.
;		A contains the character to print or interpret (excepting NUL).
;		(vdcLeftMargin) holds the coordinate of the left-edge of text.
;		(vdcRightMargin) holds the right-hand boundary for text.
; Outputs:	(r0, r1) coordinates where the next string or character will
;		be printed.
; Destroys:	A, BC, DE, HL, (r4)

	; Handle control codes first.

	ld	(r4),a

	cp	0Dh
	jr	z,vdcputcharCR

	cp	0Ah
	jr	z,vdcputcharLF

	; Check for fault conditions and handle them.

	ld	a,(vdcRightMargin)
	ld	b,a
	ld	a,(r0)
	cp	b
	jr	nc,vdcputcharFault

	; Graphic character; print it and advance cursor position.

	ld	de,0			; Write the character to the screen.
	call	_CalcUpdatePtr
	ld	a,(r4)
	call	VdcWriteByte

	ld	a,(r0)			; Advance cursor position.
	inc	a
	ld	(r0),a
	ret

vdcputcharCR:
	ld	a,(vdcLeftMargin)
	ld	(r0),a
	ret

vdcputcharLF:
	ld	a,(r1)
	inc	a
	ld	(r1),a
	ret

vdcputcharFault:
	ld	hl,(vdcPutCharFault)
	ld	a,h
	or	l
	ret	z
	jp	(hl)


VdcPlaceCursor:
; Moves the hardware cursor to the location specified in (r0,r1).
;
; Inputs:	(r0) X coordinate for cursor.
;		(r1) Y coordinate for cursor.
; Outputs:
; Destroys:

	ld	de,0000h
	call	_CalcCursorPtr
	ret

