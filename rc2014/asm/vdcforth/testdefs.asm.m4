define(testid, `0')dnl
define(bumpid, `define(`testid',eval(testid + 1))dnl')dnl
define(fnl, `_filnam_`'testid')dnl
define(fll, `_fillin_`'testid')dnl
define(rsl, `_reason_`'testid')dnl
define(gol, `_goto_`'testid')dnl
define(Test,`ld	hl,fnl
	ld	(testFileName),hl
	ld	hl,fll
	ld	(testFileLine),hl
	ld	hl,rsl
	ld	(testReason),hl
	jr	gol
fnl:	defm	"__file__:$"
fll:	defm	"__line__:$"
rsl:	defm	$1,"$"
gol:	bumpid
')dnl
define(`ExpectB',`ld	a,$1
	call	TestSetExpectedB
')dnl
define(`ActualB', `ld	a,$1
	call	TestSetActualB
')dnl
