from nmigen import (
    Elaboratable,
    Module,
    Signal,
)

from interfaces import create_shifter_interface


class Shifter(Elaboratable):
    def __init__(self, platform=None):
        create_shifter_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Support for the blink attribute.

        blink_state = Signal(1)
        blink_ctr = Signal(5)

        with m.FSM() as blink_fsm:
            with m.State("WaitVS"):
                with m.If(self.vs):
                    m.next = "WaitField"

            with m.State("WaitField"):
                with m.If(~self.vs):
                    m.next = "WaitVS"
                    sync += blink_ctr.eq(blink_ctr + 1)

        with m.If(self.blink_rate):
            comb += blink_state.eq(blink_ctr[3])
        with m.Else():
            comb += blink_state.eq(blink_ctr[4])

        # Supporting horizontal scrolling, we use two counters
        # to control when we are displaying a character's main
        # contents (chrgate asserted) or when we're in the
        # inter-character fill (chrgate disabled).
        chrgate = Signal(1)
        reveal_ctr = Signal(4)
        conceal_ctr = Signal(4)
        pixctr = Signal(3)

        reveal_ctr_z = Signal(1)
        conceal_ctr_z = Signal(1)

        comb += [
            reveal_ctr_z.eq(reveal_ctr == 0),
            conceal_ctr_z.eq(conceal_ctr == 0),
        ]

        with m.If(self.hclken):
            sync += [
                reveal_ctr.eq(self.hscroll),
                conceal_ctr.eq(self.hcd),
            ]
        with m.Else():
            with m.If(reveal_ctr_z):
                sync += reveal_ctr.eq(self.hct)
            with m.Else():
                sync += reveal_ctr.eq(reveal_ctr - 1)

            with m.If(conceal_ctr_z):
                sync += conceal_ctr.eq(self.hct)
            with m.Else():
                sync += conceal_ctr.eq(conceal_ctr - 1)

        with m.If(reveal_ctr_z):
            sync += [
                chrgate.eq(1),
                pixctr.eq(7),
            ]
        with m.If(conceal_ctr_z & ~reveal_ctr_z):
            sync += chrgate.eq(0)

        with m.If(~reveal_ctr_z & chrgate):
            sync += pixctr.eq(pixctr - 1)

        # Strip Buffer State Machine
        #
        # This state machine is responsible for routing the video
        # data to the final output mux at the correct times.  A
        # necessary part of this process is coordinating when to
        # start video memory fetches as well.

        comb += [
            self.go_prefetch.eq(0),
            self.swap_strip.eq(0),
            self.padr.eq(0),
        ]
        
        with m.FSM() as sbsm:
            with m.State("WaitHS"):
                with m.If(self.hs):
                    m.next = "WaitVDEN"

            with m.State("WaitVDEN"):
                with m.If(~self.hs):
                    with m.If(self.vden):
                        m.next = "Prefetch"
                        comb += self.go_prefetch.eq(1)
                        sync += self.atrptr.eq(self.atrbase)
                    with m.Else():
                        m.next = "WaitHS"

            with m.State("Prefetch"):
                with m.If(self.done_prefetch):
                    m.next = "WaitDEN"
                    comb += self.swap_strip.eq(1)
                with m.Else():
                    m.next = "Prefetch"

            with m.State("WaitDEN"):
                with m.If(self.den):
                    with m.If(reveal_ctr_z):
                        m.next = "Column1"
                    with m.Else():
                        m.next = "Column0"
                    comb += self.go_prefetch.eq(1)

            with m.State("Column0"):
                with m.If(~self.den):
                    m.next = "WaitHS"
                with m.Else():
                    with m.If(reveal_ctr_z):
                        m.next = "Column1"

            with m.State("Column1"):
                comb += self.padr.eq(1)
                with m.If(~self.den):
                    m.next = "WaitHS"
                with m.Else():
                    with m.If(reveal_ctr_z):
                        m.next = "Column2"

            with m.State("Column2"):
                comb += self.padr.eq(2)
                with m.If(~self.den):
                    m.next = "WaitHS"
                with m.Else():
                    with m.If(reveal_ctr_z):
                        m.next = "Column3"

            with m.State("Column3"):
                comb += self.padr.eq(3)
                with m.If(~self.den):
                    m.next = "WaitHS"
                with m.Else():
                    with m.If(reveal_ctr_z):
                        m.next = "Column0"
                        comb += [
                            self.go_prefetch.eq(1),
                            self.swap_strip.eq(1),
                        ]

            if platform == 'formal':
                comb += [
                    self.fv_sbsm_wait_hs.eq(sbsm.ongoing("WaitHS")),
                    self.fv_sbsm_wait_vden.eq(sbsm.ongoing("WaitVDEN")),
                    self.fv_sbsm_prefetch.eq(sbsm.ongoing("Prefetch")),
                    self.fv_sbsm_wait_den.eq(sbsm.ongoing("WaitDEN")),
                    self.fv_lpic.eq(reveal_ctr_z),
                    self.fv_sbsm_column0.eq(sbsm.ongoing("Column0")),
                    self.fv_sbsm_column1.eq(sbsm.ongoing("Column1")),
                    self.fv_sbsm_column2.eq(sbsm.ongoing("Column2")),
                    self.fv_sbsm_column3.eq(sbsm.ongoing("Column3")),
                ]

        # Hi-res dot from character bitmap data.
        char_bm_dot = Signal(1)

        with m.If(pixctr == 7):
            comb += char_bm_dot.eq(self.char_bm[7])
        with m.Elif(pixctr == 6):
            comb += char_bm_dot.eq(self.char_bm[6])
        with m.Elif(pixctr == 5):
            comb += char_bm_dot.eq(self.char_bm[5])
        with m.Elif(pixctr == 4):
            comb += char_bm_dot.eq(self.char_bm[4])
        with m.Elif(pixctr == 3):
            comb += char_bm_dot.eq(self.char_bm[3])
        with m.Elif(pixctr == 2):
            comb += char_bm_dot.eq(self.char_bm[2])
        with m.Elif(pixctr == 1):
            comb += char_bm_dot.eq(self.char_bm[1])
        with m.Else():
            comb += char_bm_dot.eq(self.char_bm[0])

        # Dot after application of attribute modifiers, if enabled.
        attr_dot = Signal(1)
        swap_fg_bg = Signal(1)

        comb += [
            swap_fg_bg.eq(
                (self.attr_rvs | (self.attr_blink & blink_state)) & self.attr_enable
            ),
            attr_dot.eq((chrgate & char_bm_dot) ^ swap_fg_bg ^ self.reverse_screen),
        ]

        # Final Color Mux
        #
        ## This is the *final* output dot, after processing by
        ## blink, cursor, reverse video, and other preprocessing
        ## steps.  DEN, ATTR_ENABLE, and this signal determines
        ## what colors appear on the output RGBI signals.
        dot = Signal(1)
        comb += dot.eq(attr_dot)
        
        with m.If(~self.den):
            comb += self.outpen.eq(0)
        with m.Else():
            with m.If(dot):
                with m.If(self.attr_enable):
                    comb += self.outpen.eq(self.attr_pen)
                with m.Else():
                    comb += self.outpen.eq(self.fgpen)
            with m.Else():
                comb += self.outpen.eq(self.bgpen)

        if platform == 'formal':
            comb += [
                self.fv_dot.eq(dot),
                self.fv_reveal_ctr.eq(reveal_ctr),
                self.fv_conceal_ctr.eq(conceal_ctr),
                self.fv_chrgate.eq(chrgate),
                self.fv_pixctr.eq(pixctr),
            ]

        return m
