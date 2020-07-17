; VDC Forth
; Version 1
;
; Copyright (c) 2020 Samuel A. Falvo II
; This software is licensed under MPLv2 terms.
;
; This code implements a simple clock.  It is a vehicle by
; which I may learn to invoke CP/M system calls; but, also,
; by which I may also develop Z80 code for working with my
; VDC-II core.
;
; This program is the first Z80 code I've written in maybe
; 30 years.  Forgive any style demerits; it's been a while.


	include	"drivers/evtloop/cpm2.asm"
	include "drivers/osal/cpm2.asm"
	include "drivers/vdc/c128.asm"
	include "drivers/data.asm"

	include	"consts.asm"
	include "usecase/startup/vdcforth.asm"
	include "usecase/cmdline/tib.asm"		; model
	include "usecase/cmdline/view.asm"		; view
	include "usecase/cmdline/control.asm"		; controller
	include "usecase/cmdline/strings.asm"
	include "usecase/cmdline/interp.asm"
	include "usecase/cmdline/dict.asm"		; MUST be last include.

