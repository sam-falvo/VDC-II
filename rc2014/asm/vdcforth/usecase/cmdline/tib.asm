; Terminal Input Buffer


TibReset:
	ret


TibChar:
	ld	hl,tibLength
	inc	(hl)
	ret


tibLength:	defb	0

