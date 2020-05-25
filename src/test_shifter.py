from nmigen.test.utils import FHDLTestCase
from nmigen import (
    Cat,
    Const,
    Elaboratable,
    Module,
    ResetSignal,
    Signal,
)
from nmigen.hdl.ast import (
    Assert,
    Assume,
    Fell,
    Past,
    Stable,
)

from interfaces import create_shifter_interface

from shifter import Shifter


class ShifterFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_shifter_interface(self, platform="formal")

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # This flag indicates when it's safe to use Past(), Stable(), etc.
        # Required so we can detect the start of simulation and prevent literal
        # edge cases from giving false negatives concerning the behavior of the
        # Past and Stable functions.
        z_past_valid = Signal(1, reset=0)
        sync += z_past_valid.eq(1)

        dut = Shifter(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.fv_reveal_ctr.eq(dut.fv_reveal_ctr),
            self.fv_conceal_ctr.eq(dut.fv_conceal_ctr),
            self.fv_chrgate.eq(dut.fv_chrgate),
            self.fv_dot.eq(dut.fv_dot),
            self.fv_sbsm_wait_hs.eq(dut.fv_sbsm_wait_hs),
            self.fv_sbsm_wait_vden.eq(dut.fv_sbsm_wait_vden),
            self.fv_sbsm_prefetch.eq(dut.fv_sbsm_prefetch),
            self.fv_sbsm_wait_den.eq(dut.fv_sbsm_wait_den),
            self.fv_lpic.eq(dut.fv_lpic),
            self.fv_sbsm_column0.eq(dut.fv_sbsm_column0),
            self.fv_sbsm_column1.eq(dut.fv_sbsm_column1),
            self.fv_sbsm_column2.eq(dut.fv_sbsm_column2),
            self.fv_sbsm_column3.eq(dut.fv_sbsm_column3),
            self.fv_pixctr.eq(dut.fv_pixctr),
            self.fv_lastrow.eq(dut.fv_lastrow),
            self.fv_bump_atrptr.eq(dut.fv_bump_atrptr),
            self.fv_bump_chrptr.eq(dut.fv_bump_chrptr),

            self.outpen.eq(dut.outpen),
            self.go_prefetch.eq(dut.go_prefetch),
            self.go_ldptr.eq(dut.go_ldptr),
            self.swap_strip.eq(dut.swap_strip),
            self.padr.eq(dut.padr),
            self.atrptr.eq(dut.atrptr),
            self.chrptr.eq(dut.chrptr),
            self.ra.eq(dut.ra),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.hclken.eq(self.hclken),
            dut.den.eq(self.den),
            dut.hs.eq(self.hs),
            dut.vden.eq(self.vden),
            dut.hscroll.eq(self.hscroll),
            dut.hcd.eq(self.hcd),
            dut.hct.eq(self.hct),
            dut.fgpen.eq(self.fgpen),
            dut.bgpen.eq(self.bgpen),
            dut.attr_enable.eq(self.attr_enable),
            dut.attr_pen.eq(self.attr_pen),
            dut.done_prefetch.eq(self.done_prefetch),
            dut.char_bm.eq(self.char_bm),
            dut.attr_rvs.eq(self.attr_rvs),
            #dut.attr_underline.eq(self.attr_underline),
            dut.attr_blink.eq(self.attr_blink),
            dut.atrbase.eq(self.atrbase),
            dut.chrbase.eq(self.chrbase),
            dut.vscroll.eq(self.vscroll),
            dut.vct.eq(self.vct),
            dut.bitmap_mode.eq(self.bitmap_mode),
        ]

        # Assumption: hclken is a pulse, and is never asserted more than
        # one clock in a row.  If this assumption is ever to fail, then
        # we break horizontal smooth scroll functionality.

        with m.If(past_valid & Past(self.hclken)):
            sync += Assume(~self.hclken)

        # To support vertical smooth scrolling, the "row address" (ra)
        # output is reset to the vscroll input upon rising edge of VDEN.
        # Each HSYNC thereafter, it is incremented monotonically;
        # however, it will reset to 0 whenever the ra setting matches
        # the vertical character total.

        vden1 = Signal(1)
        hs1 = Signal(1)

        sync += [
            vden1.eq(self.vden),
            hs1.eq(self.hs),
        ]

        with m.If(
            past_valid &
            ~Past(vden1) &
            Past(self.vden)
        ):
            sync += [
                Assert(self.ra == Past(self.vscroll)),
            ]
        with m.Else():
            with m.If(past_valid & Past(hs1) & ~Past(self.hs)):
                with m.If(~Past(self.fv_lastrow)):
                    sync += Assert(self.ra == (Past(self.ra) + 1)[0:5])
                with m.Else():
                    sync += Assert(self.ra == 0)

        with m.If(self.fv_lastrow):
            comb += Assert(self.ra == self.vct)

        # Attribute pointer is reset to atrbase when starting a new frame
        # starts.  It increments only when displaying the last line of a
        # character row.

        with m.If(
            past_valid &
            ~Past(vden1) &
            Past(self.vden)
        ):
            sync += Assert(self.atrptr == Past(self.atrbase))
        with m.Elif(past_valid & Past(self.fv_bump_atrptr)):
            sync += Assert(self.atrptr == (Past(self.atrptr) + 1)[0:16])

        # Character pointer is reset to chrbase when starting a new frame.
        # It increments only when displaying the last line of a character
        # row; OR, when in bitmapped mode, for every character fetched.

        with m.If(
            past_valid &
            ~Past(vden1) &
            Past(self.vden)
        ):
            sync += Assert(self.chrptr == Past(self.chrbase))
        with m.Elif(past_valid & Past(self.fv_bump_chrptr)):
            sync += Assert(self.chrptr == (Past(self.chrptr) + 1)[0:16])

        # To support horizontal smooth scrolling, the shifter relies upon
        # two counters, called the reveal_counter and conceal_counter.
        # At each character boundary on the display, the reveal_counter is
        # set to the current horizontal scroll register setting, and
        # the conceal_counter is set to the character display horizontal
        # register.  IN ADDITION, when the reveal_counter reaches zero,
        # it resets to the character total horizontal register setting.
        # Similarly with the conceal_counter.
        #
        # The character display is enabled (chrgate is asserted) when the
        # reveal_counter reaches 0.  The character display is disabled
        # (chrgate is negated) when the conceal_counter reaches 0.  If they
        # *both* reach 0 at the same time, the character display remains
        # *enabled*.
        #
        # This rather complex set of interactions works together to implement
        # horizontal smooth scrolling on a video architecture that is
        # otherwise ignorant of this feature.
        #
        # Note that we cannot know the state of chrgate at the start of the
        # current scanline.  Especially since the host processor might alter
        # the horizontal scroll settings mid-line, causing the gate to be
        # enabled or disabled for longer than desired.  We rely on chrgate
        # settling to a stable and usable pattern by the time DEN is
        # asserted.

        ## The reveal and conceal counters must reset at the start of
        ## ever character column.
        with m.If(past_valid & Past(self.hclken)):
            sync += [
                Assert(self.fv_reveal_ctr == Past(self.hscroll)),
                Assert(self.fv_conceal_ctr == Past(self.hcd)),
            ]

        ## The character gate can only be asserted when the reveal counter
        ## reaches 0.  Likewise, the gate must only negate when the conceal
        ## counter reaches 0.  EXCEPT when both reach 0 at the same time,
        ## in which case the gate remains enabled.  This supports smooth-
        ## scrolling of characters with inter-character gaps.
        with m.If(past_valid):
            with m.If(Past(self.hclken)):
                sync += Assert(self.fv_reveal_ctr == Past(self.hscroll))
            with m.Elif(Past(self.fv_reveal_ctr) == 0):
                sync += Assert(self.fv_reveal_ctr == Past(self.hct))
            with m.Else():
                sync += Assert(self.fv_reveal_ctr == (Past(self.fv_reveal_ctr) - 1))

            with m.If(Past(self.hclken)):
                sync += Assert(self.fv_conceal_ctr == Past(self.hcd))
            with m.Elif(Past(self.fv_conceal_ctr) == 0):
                sync += Assert(self.fv_conceal_ctr == Past(self.hct))
            with m.Else():
                sync += Assert(self.fv_conceal_ctr == (Past(self.fv_conceal_ctr) - 1))

            with m.If(Past(self.fv_reveal_ctr) == 0):
                sync += Assert(self.fv_chrgate)
            with m.Elif(Past(self.fv_conceal_ctr) == 0):
                sync += Assert(~self.fv_chrgate)
            with m.Else():
                sync += Assert(Stable(self.fv_chrgate))

        # Output Color Mux
        #
        ## The output color is black when blanking is in effect.
        with m.If(~self.den):
            comb += Assert(self.outpen == 0)

        ## If not blanking, and if the current dot is 0, then we show
        ## the current background color.  If the dot is a 1, then we
        ## show either the global foreground color or the attribute
        ## color, depending on whether or not attributes are enabled.
        with m.If(self.den):
            with m.If(~self.fv_dot):
                comb += Assert(self.outpen == self.bgpen)
            with m.Else():
                with m.If(self.attr_enable):
                    comb += Assert(self.outpen == self.attr_pen)
                with m.Else():
                    comb += Assert(self.outpen == self.fgpen)

        ## Whenever the reveal counter is reset to the hscroll value,
        ## we must be displaying the first pixel of the character.
        with m.If(past_valid):
            with m.If(Past(self.fv_lpic)):
                sync += Assert(self.fv_pixctr == 7)
            with m.Elif(Past(self.fv_chrgate)):
                sync += Assert(self.fv_pixctr == (Past(self.fv_pixctr) - 1)[0:3])
            with m.Else():
                sync += Assert(Stable(self.fv_pixctr))

        # Strip Buffer State Machine
        #
        ## The Strip Buffer State Machine waits for a horizontal sync
        ## pulse.  If the current scanline isn't blanked, then we fetch
        ## video data.

        with m.If(past_valid):
            with m.If(Past(self.fv_sbsm_wait_hs)):
                with m.If(~Past(self.hs)):
                    sync += Assert(self.fv_sbsm_wait_hs)
                with m.Else():
                    sync += Assert(self.fv_sbsm_wait_vden)

            with m.If(Past(self.fv_sbsm_wait_vden)):
                with m.If(Past(self.hs)):
                    sync += Assert(self.fv_sbsm_wait_vden)
                with m.Else():
                    with m.If(Past(self.vden)):
                        sync += Assert(self.fv_sbsm_prefetch)
                        comb += [
                            Assert(Past(self.go_prefetch)),
                            Assert(Past(self.go_ldptr)),
                        ]
                    with m.Else():
                        sync += Assert(self.fv_sbsm_wait_hs)

            with m.If(Past(self.fv_sbsm_prefetch)):
                with m.If(~Past(self.done_prefetch)):
                    sync += Assert(self.fv_sbsm_prefetch)
                with m.Else():
                    sync += Assert(self.fv_sbsm_wait_den)
                    comb += Assert(Past(self.swap_strip))

            with m.If(Past(self.fv_sbsm_wait_den)):
                with m.If(~Past(self.den)):
                    sync += Assert(self.fv_sbsm_wait_den)
                    comb += Assert(~Past(self.go_prefetch))
                with m.Else():
                    comb += Assert(Past(self.go_prefetch))
                    with m.If(Past(self.fv_lpic)):
                        sync += Assert(self.fv_sbsm_column1)
                    with m.Else():
                        sync += Assert(self.fv_sbsm_column0)

            with m.If(Past(self.fv_sbsm_column0)):
                comb += [
                    Assert(Past(self.padr) == 0),
                    Assert(~Past(self.go_prefetch)),
                    Assert(~Past(self.swap_strip)),
                ]
                with m.If(~Past(self.den)):
                    sync += Assert(self.fv_sbsm_wait_hs)
                with m.Else():
                    with m.If(~Past(self.fv_lpic)):
                        sync += Assert(self.fv_sbsm_column0)
                    with m.Else():
                        sync += Assert(self.fv_sbsm_column1)

            with m.If(Past(self.fv_sbsm_column1)):
                comb += [
                    Assert(Past(self.padr) == 1),
                    Assert(~Past(self.go_prefetch)),
                    Assert(~Past(self.swap_strip)),
                ]
                with m.If(~Past(self.den)):
                    sync += Assert(self.fv_sbsm_wait_hs)
                with m.Else():
                    with m.If(~Past(self.fv_lpic)):
                        sync += Assert(self.fv_sbsm_column1)
                    with m.Else():
                        sync += Assert(self.fv_sbsm_column2)

            with m.If(Past(self.fv_sbsm_column2)):
                comb += [
                    Assert(Past(self.padr) == 2),
                    Assert(~Past(self.go_prefetch)),
                    Assert(~Past(self.swap_strip)),
                ]
                with m.If(~Past(self.den)):
                    sync += Assert(self.fv_sbsm_wait_hs)
                with m.Else():
                    with m.If(~Past(self.fv_lpic)):
                        sync += Assert(self.fv_sbsm_column2)
                    with m.Else():
                        sync += Assert(self.fv_sbsm_column3)

            with m.If(Past(self.fv_sbsm_column3)):
                comb += Assert(Past(self.padr) == 3)
                with m.If(~Past(self.den)):
                    sync += Assert(self.fv_sbsm_wait_hs)
                with m.Else():
                    with m.If(~Past(self.fv_lpic)):
                        sync += Assert(self.fv_sbsm_column3)
                        comb += [
                            Assert(~Past(self.go_prefetch)),
                            Assert(~Past(self.swap_strip)),
                        ]
                    with m.Else():
                        sync += Assert(self.fv_sbsm_column0)
                        comb += [
                            Assert(Past(self.go_prefetch)),
                            Assert(Past(self.swap_strip)),
                        ]

        return m


class ShifterTestCase(FHDLTestCase):
    def test_shifter(self):
        self.assertFormal(ShifterFormal(), mode='bmc', depth=100)
        self.assertFormal(ShifterFormal(), mode='prove', depth=100)
