; This table of bytes are to be loaded into the VDC registers to set an 80x30
; text mode display with attributes enabled.  Character memory sits at address
; 0000H, while attribute memory sits at 0C00H.  Glyph memory sits at address
; 2000H.

	DEFB	38		; There are 38 registers to set here.

	DEFB	99		; R00  Horizontal Total
	DEFB	80		; R01  Horizontal Displayed
	DEFB	82		; R02  Horizontal Sync Position
	DEFB	2CH		; R03  H/V Sync Widths
	DEFB	31		; R04  Vertical Total
	DEFB	13		; R05  Vertical Total Adjust
	DEFB	30		; R06  Vertical Displayed
	DEFB	31		; R07  Vertical Sync Position
	DEFB	0FCH		; R08  Interlace Control
	DEFB	15		; R09  Vertical Character Total
	DEFB	20H		; R10  Cursor Mode (no cursor), Start Scanline
	DEFB	0EFH		; R11  Cursor Stop Scanline
	DEFB	00H		; R12  Display Start Address High
	DEFB	00H		; R13  Display Start Address Low
	DEFB	00H		; R14  Cursor Address High
	DEFB	00H		; R15  Cursor Address Low
	DEFB	00H		; R16  Light Pen Position (not used in VDC-II)
	DEFB	00H		; R17  Light Pen Position (not used in VDC-II)
	DEFB	00H		; R18  Update Address High
	DEFB	00H		; R19  Update Address Low
	DEFB	0CH		; R20  Attribute Start Address High
	DEFB	00H		; R21  Attribute Start Address Low
	DEFB	78H		; R22  Horizontal Character Total/Displayed
	DEFB	0FH		; R23  Vertical Character Displayed
	DEFB	20H		; R24  1/32 character blink rate; vertical scroll
	DEFB	47H		; R25  Horiz. scroll, attributes enabled
	DEFB	00H		; R26  Background color is black
	DEFB	00H		; R27  Address Increment (not yet supported)
	DEFB	3FH		; R28  Font Base Address (2000H)
	DEFB	0EEH		; R29  Underline Scanline (not yet supported)
	DEFB	00H		; R30  Byte Count
	DEFB	00H		; R31  Data Port
	DEFB	00H		; R32  Block Copy Source Address High
	DEFB	00H		; R33  Block Copy Source Address Low
	DEFB	00H		; R34  Display Enable Begin (not used in VDC-II)
	DEFB	00H		; R35  Display Enable End (not used in VDC-II)
	DEFB	00H		; R36  RAM Refresh/Scan Line (not used in VDC-II)
	DEFB	0FFH		; R37  HSYNC/VSYNC Polarity

