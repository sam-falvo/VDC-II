; User Environment
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.
;
; This UE is inspired by GEOS on the Commodore 64/128.
;
; This MUST be the first module included in any new application.
; This software assumes it is running under CP/M 2.2.


	org	0100h

	call	ueInitialize
	call	VdcInitialize
	call	AppInitialize

	; Main/Centralized Event Loop

.again	call	KbdCheck
	call	VdcVsyncCheck
	jr	again


ueInitialize:
; Initializes the global state to known good, if ineffectual, values.

	ld	hl,defaultKbdHandler
	ld	(kbdHandler),hl

	ld	a,110
	ld	(vdcPort),a		; Default VDC-II port.
	ld	a,20H
	ld	(vdcFontBase),a		; Set system font at 2000H in VDC memory.

	ret


ueReturn:
; Exits the currently running application to return to the user environment.
; (Currently, this means just quitting back to CP/M).

	jp	BdosTerminate


KbdCheck:
; Checks the user's console for input.  If any input
; exists, invoke the kbdHandler callback.

	call	BdosConsoleGetRaw
	or	a
	ret	z
	jp	CallKeyboardHandler

.defaultKbdHandler
	ret


CallKeyboardHandler:
; Invokes the keyboard handler pointed at by kbdHandler.
;
; Inputs:	A=key code to process.
; Outputs:
; Destroys:	A,BC,DE,HL

	ld	hl,(kbdHandler)
	jp	(hl)


;================
; Variables for the User Environment

kbdHandler:
	defw	0
