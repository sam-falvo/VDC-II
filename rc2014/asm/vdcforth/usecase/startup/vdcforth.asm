; VDC Forth
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.
;
; Main Behavior:
; 
; 1. User types VDCFORTH at CP/M command prompt.
; 2. VGA screen synchronizes and clears if it hasn't already.
; 3. User sees VDC-Forth banner on the display.
; 4. User sees OK prompt along the top of the screen.
; 5. User sees a text entry cursor.
; 6. There is a stack status line (currently empty) below the OK prompt.
; 
; Exceptional Behavior:
; 
; none.


; This label MUST be named AppInitialize for the main event loop to find it.
; Future releases of the environment will probably rely on a separately loaded
; binary which exposes a jump table.  But, for now, everything is statically
; linked.
AppInitialize:
	; Clear the screen.

	ld	hl,0
	ld	(r0),hl		; left
	ld	(r1),hl		; top
	ld	(r2),hl
	ld	(r3),hl
	ld	a,l
	ld	(vdcLeftMargin),a
	ld	a,(vdcCharWidth)
	ld	(r2),a		; right
	ld	(vdcRightMargin),a
	ld	a,(vdcCharHeight)
	ld	(r3),a		; bottom
	ld	l,20h
	ld	(r4),hl		; Fill screen with spaces
	call	VdcDrawTextSlab

	ld	a,0Fh
	ld	(okAttribs),a
	call	ColorCmdLine

	; color the stack status line

	ld	hl,0
	ld	(r0),hl		; left
	inc	l
	ld	(r1),hl		; top
	ld	a,(vdcCharWidth)
	ld	(r2),a		; right
	ld	a,2Ch		; Make data stack yellow with an underline.
	ld	(r4),a
	call	VdcDrawAttrLine

	; Render the application area

	ld	hl,0		; Print license banner
	ld	(r0),hl		; (Centered vertically on 80x25 screen)
	ld	l,6
	ld	(r1),hl
	ld	hl,banner
	ld	(r2),hl
	call	VdcPutString

	ld	hl,0
	ld	(r0),hl
	ld	l,2
	ld	(r1),hl
	ld	a,(vdcCharWidth)
	ld	(r2),a
	ld	a,(vdcCharHeight)
	ld	(r3),a
	ld	a,0Eh
	ld	(r4),a
	call	VdcDrawAttrSlab

	call	initKeyboard
	call	initDictionary
	call	PaintOK
	jp	PaintCmdLine


banner:	defm	"VDC-Forth Kernel V1",13,10
	defm	"Copyright (c) 2020 Samuel A. Falvo II",13,10
	defm	13,10
	defm	"This program is free software; you can redistribute it and/or modify ",13,10
	defm	"it under the terms of the GNU General Public License as published by ",13,10
	defm	"the Free Software Foundation; either version 3 of the License, or ",13,10
	defm	"(at your option) any later version.",13,10
	defm	13,10
	defm	"This program is distributed in the hope that it will be useful, ",13,10
	defm	"but WITHOUT ANY WARRANTY; without even the implied warranty of ",13,10
	defm	"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the ",13,10
	defm	"GNU General Public License for more details. ",13,10
	defm	13,10
	defm	"You should have received a copy of the GNU General Public License ",13,10
	defm	"along with this program. If not, see http://www.gnu.org/licenses/.",0

