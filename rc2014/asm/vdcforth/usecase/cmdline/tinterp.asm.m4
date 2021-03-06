include(`testdefs.asm.m4')

        org     0100h


        call    an_empty_tib_has_nothing_to_interpret
        call    outer_interpreter_

        jp      osalTerminate


        include "drivers/osal/cpm2.asm"
        include "drivers/data.asm"
	include "drivers/math.asm"
        include "utils.asm"
        include "tester.asm"
        include "usecase/cmdline/tib.asm"
        include "usecase/cmdline/strings.asm"
        include "usecase/cmdline/interp.asm"


outer_interpreter_:
        call    _skips_whitespace
        call    _fills_in_counted_string_at_here
        call    _can_parse_words_sequentially
        call    _can_find_most_recent_definition
        call    _cannot_find_undefined_words
        call    _can_find_older_definitions
        call    _can_invoke_a_definition
        ret


outer_interpreter_setup_1:
        ld      bc,tib1Length
        ld      de,tib1Length
        ld      hl,tib1

outer_interpreter_setup_common:
        call    TibSetExtent

        ld      hl,testHereBuf
        ld      (interpHerePtr),hl

        xor     a
        ld      (interpIndex),a
        ret


outer_interpreter_setup_2:
        ld      bc,tib2Length
        ld      de,tib2Length
        ld      hl,tib2
        jp      outer_interpreter_setup_common


an_empty_tib_has_nothing_to_interpret:
        Test("An empty TIB has nothing to interpret")
        ld      bc,0
        ld      de,0
        ld      hl,tib0
        call    TibSetExtent

        ld      hl,testHereBuf
        ld      (interpHerePtr),hl

        xor     a
        ld      (interpIndex),a

        call    InterpNextWord
        call    TestSetActualB
        ExpectB(0)
        call    TestEqual

        ret


_skips_whitespace:
        Test("Outer interpreter skips whitespace")
        call    outer_interpreter_setup_1
        call    InterpNextWord

        call    TestSetActualB
        ExpectB(0)
        jp      TestNotEqual


_fills_in_counted_string_at_here:
        Test("Outer interpreter fills in counted-string at HERE")
        call    outer_interpreter_setup_1
        call    InterpNextWord

        ld      hl,(interpHerePtr)
        ld      (r0),hl
        ld      hl,testAWord1
        ld      (r1),hl
        call    StrCompare
        call    TestSetActualB
        ExpectB(0)
        jp      TestEqual

_can_parse_words_sequentially:
        call    outer_interpreter_setup_2

        Test("Outer interpreter can parse words sequentially: Word 1")
        call    InterpNextWord
        call    TestSetActualB
        ExpectB(1)
        call    TestEqual

        ld      hl,(interpHerePtr)
        ld      (r0),hl
        ld      hl,testAWord1
        ld      (r1),hl
        call    StrCompare
        call    TestSetActualB
        ExpectB(0)
        call    TestEqual

        Test("Outer interpreter can parse words sequentially: Word 2")
        call    InterpNextWord
        call    TestSetActualB
        ExpectB(1)
        call    TestEqual

        ld      hl,(interpHerePtr)
        ld      (r0),hl
        ld      hl,testWord2
        ld      (r1),hl
        call    StrCompare
        call    TestSetActualB
        ExpectB(0)
        call    TestEqual

        Test("Outer interpreter can parse words sequentially: Word 3")
        call    InterpNextWord
        call    TestSetActualB
        ExpectB(1)
        call    TestEqual

        ld      hl,(interpHerePtr)
        ld      (r0),hl
        ld      hl,testWord3
        ld      (r1),hl
        call    StrCompare
        call    TestSetActualB
        ExpectB(0)
        call    TestEqual

        Test("Outer interpreter can parse words sequentially: No more words")
        call    InterpNextWord
        call    TestSetActualB
        ExpectB(0)
        jp      TestEqual

_can_find_most_recent_definition:
        Test("Outer interpreter can find most recent definition")

        ; Given that a call to InterpNextWord parses out a word
        ; named 'aWord1' ...
        ld      hl,testAWord1
        ld      (interpHerePtr),hl

        ; And our dictionary structure looks like the example below...
        ld      hl,testDict1
        ld      (interpDictPtr),hl

        ; When we try to find the execution token for the word...
        ; Then we get back a word-found flag.
        call    InterpFindWord
        call    TestSetActualB
        ExpectB(-1)
        jp      TestEqual
        
_cannot_find_undefined_words:
        Test("Outer interpreter cannot find undefined words")
        ld      hl,testWord100
        ld      (interpHerePtr),hl
        ld      hl,testDict1
        ld      (interpDictPtr),hl
        call    InterpFindWord
        call    TestSetActualB
        ExpectB(0)
        jp      TestEqual

_can_find_older_definitions:
        Test("Outer interpreter can find older definitions")
        ld      hl,testWord3
        ld      (interpHerePtr),hl
        ld      hl,testDict1
        ld      (interpDictPtr),hl
        call    InterpFindWord
        call    TestSetActualB
        ExpectB(-1)
        jp      TestEqual
        
_can_invoke_a_definition:
        Test("Outer interpreter can invoke a definition")
        xor     a
        ld      (wordExecuted),a
        ld      hl,testWord3
        ld      (interpHerePtr),hl
        ld      hl,testDict1
        ld      (interpDictPtr),hl
        call    InterpFindWord
        call    InterpExecute
        ExpectB(1)
        ActualB((wordExecuted))
        jp      TestEqual
        

tib1:           defb    "        "      ; 8 spaces
tib0:           defb    "aWord1"
defc tib1Length = asmpc - tib1

tib2:           defb    "  aWord1  word2",9,"     w3    "
defc tib2Length = asmpc - tib2


testHereBuf:    defs    64
testAWord1:     defb    6,"aWord1"
testWord2:      defb    5,"word2"
testWord3:      defb    2,"w3"
testWord100:    defb    7,"word100"


td1_name_w3:    defb    2,"w3"
td1_word_w3:    defw    td1_name_w3
                defw    0               ; end of dictionary chain
		ld	a,1
		ld	(wordExecuted),a
                ret

td1_name_w2:    defb    5,"word2"
td1_word_w2:    defw    td1_name_w2
                defw    td1_word_w3
                ret

td1_name_w1:    defb    6,"aWord1"
testDict1:      defw    td1_name_w1     ; NFA
                defw    td1_word_w2     ; LFA
                ret                     ; Code Field

wordExecuted:   defb    0

