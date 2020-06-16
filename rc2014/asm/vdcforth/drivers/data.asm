;========================================
; VDC Data

vdcPort:	defw	0		; VDC base address
vdcVSHandler:	defw	0		; Vertical Sync handler
vdcPutCharFault:defw	0

vdcCharWidth:	defb	0		; Display width in characters
vdcCharHeight:	defb	0		; Display height in characters
vdcFontBase:	defb	0		; only bits 7-5 are valid.
vdcVSFlag:	defb	0		; only 00h and 20h allowed.
vdcLeftMargin:	defb	0		; (may be widened later)
vdcRightMargin: defb	0		; (may be widened later)

;================
; Variables for the User Environment

kbdHandler:	defw	0

; Generic parameter pseudo-registers (can be used by a wide variety of
; system services).

r0:		defw	0
r1:		defw	0
r2:		defw	0
r3:		defw	0
r4:		defw	0
r5:		defw	0
r6:		defw	0
r7:		defw	0

