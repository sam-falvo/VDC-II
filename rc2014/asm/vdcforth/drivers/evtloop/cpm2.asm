; User Environment
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.
;
; This event loop is inspired by GEOS on the Commodore 64/128.
; It takes control over the machine, and forms the main program.
; It also provides the interface between the host OS and the
; event-driven application environment.
;
; This MUST be the first module included in any new application.
; This software assumes it is running under CP/M 2.2.


	org	0100h

	call	evtInitialize
	call	AppInitialize

	; Main/Centralized Event Loop

.again	call	KbdCheck
	call	VdcVsyncCheck
	jr	again


evtInitialize:
; Initializes the global state to known good, if ineffectual, values.
; Also resets any device drivers to known good states as well.

	ld	hl,defaultKbdHandler
	ld	(kbdHandler),hl

	jp	VdcInitialize


evtReturn:
; Exits the currently running application to return to the user environment.
; (Currently, this means just quitting back to CP/M).

	jp	osalTerminate


KbdCheck:
; Checks the user's console for input.  If any input
; exists, invoke the kbdHandler callback.

	call	osalConsoleGetRaw
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

