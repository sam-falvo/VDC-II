initKeyboard:
        ld      hl,onKey
        ld      (kbdHandler),hl

reset0CmdlineBuffer:
        ld      bc,0
resetCmdlineBuffer:
        ld      de,CMDBUFLEN
        ld      hl,cmdlineBuffer
        jp      TibSetExtent


onKey:
        cp      a,20H
        jr      c,doCtrlChar
        cp      a,7FH
        jr      nc,doCtrlChar
        call    TibTypeChar
        jp      PaintCmdLine

doCtrlChar:
        cp      a,BACKSPACE
        jr      z,doBackspace

        cp      a,RETURN
        jr      z,doReturn

        cp      a,27
        ret     nz
        jp      osalTerminate


doBackspace:
        call    TibBackspace
        jp      PaintCmdLine


doReturn:
        ld      a,00h
        ld      (okAttribs),a
        call    ColorOK
        call    interpretCmdLine
        ld      a,0Fh
        ld      (okAttribs),a
        jp      ColorOK


interpretCmdLine:
; Interprets the current contents of the TIB.  Upon completion, or upon
; an error, the TIB is cleared, and we return.  The state of the data stack
; may be different.
;
; Inputs:
; Outputs:
; Destroys:     AF, BC, DE, HL

        ; Originally in interp.asm, it created an unwanted dependency for its
        ; test program.  So, this code remains in control.asm for now.

        ld      hl,0
        ld      (interpIndex),hl

interpretCmdLine_Again:
        call    InterpNextWord
        or      a
        jr      z,interpretCmdLine_finished
	call	InterpConvertNumber
	or	a
	jr	nz,interpretCmdLine_pushHLontoDStack
        call    InterpFindWord
        or      a
        jr      z,interpretCmdLine_undefined
        call    InterpExecute
        jr      interpretCmdLine_Again

interpretCmdLine_finished:
        call    reset0CmdlineBuffer
	call	PaintStackLine
        jp      PaintCmdLine

interpretCmdLine_pushHLontoDStack:
	ld	(stkReturn),sp
	ld	sp,(stkData)
	push	hl
	ld	(stkData),sp
	ld	sp,(stkReturn)
	jr	interpretCmdLine_Again

interpretCmdLine_undefined:
        ; Copy error-inducing word into the head of the TIB buffer.

        ld      bc,(interpWordStart)
        ld      hl,(interpWordEnd)
        or      a               ; clear carry
        sbc     hl,bc
        ld      b,h
        ld      c,l             ; BC=word length
        push    bc
        ld      de,cmdlineBuffer
        ld      hl,(interpWordStart)
        ldir

        pop     bc
        call    resetCmdlineBuffer
        jp      PaintCmdLine


cmdlineBuffer:
        defs    CMDBUFLEN

