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

from interfaces import create_syncgen_interface

from syncgen import SyncGen


class SyncGenFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_syncgen_interface(self, platform="formal")

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

        dut = SyncGen(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.xclken.eq(dut.xclken),
            self.xs.eq(dut.xs),
            self.xden.eq(dut.xden),
            self.rastclken.eq(dut.rastclken),

            self.fv_xdot.eq(dut.fv_xdot),
            self.fv_xchr.eq(dut.fv_xchr),
            self.fv_xtotal.eq(dut.fv_xtotal),
            self.fv_go_xsync.eq(dut.fv_go_xsync),
            self.fv_xsctr.eq(dut.fv_xsctr),
            self.fv_xdctr.eq(dut.fv_xdctr),
            self.fv_adj.eq(dut.fv_adj),
            self.fv_adjctr.eq(dut.fv_adjctr),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.dotclken.eq(self.dotclken),
            dut.syncen.eq(self.syncen),
            dut.xct.eq(self.xct),
            dut.xt.eq(self.xt),
            dut.xsp.eq(self.xsp),
            dut.xsw.eq(self.xsw),
            dut.xd.eq(self.xd),
            dut.xta.eq(self.xta),
        ]

        #
        # The original 6845, 6545, and even 8563/8568 chips did not support anything
        # like a horizontal total adjust.  However, this could be a useful feature.
        # Consider the case of having a 25.2MHz dot clock, but you want 9-pixel wide
        # characters for easier legibility.  Instead of a horizontal total of 100,
        # this would require a horizontal total of 88.88... characters.  It would be
        # nice if you could set HT=(88-1)=87 and a hypothetical HTA=(0.888*9)=8.
        #
        # It would also let us re-use the same logic description for both horizontal
        # and vertical sync generators.  ;)
        #

        with m.If(~self.fv_adj):
            comb += Assert(self.fv_adjctr == 0)

        with m.If(self.fv_adj):
            comb += Assert(self.fv_adjctr != 0)

        with m.If(past_valid & ~Past(self.dotclken)):
            comb += Assert(Stable(self.fv_adjctr))

        with m.If(past_valid & Past(self.dotclken) & Past(self.fv_adj)):
            sync += Assert(self.fv_adjctr == (Past(self.fv_adjctr) - 1))

        #
        # The horizontal clock is typically driven by the dot clock.
        # But, the 6545 works in terms of characters, which is typically
        # 5 to 8 pixels wide.  FPGAs can handle multiple clock domains,
        # but it's usually more convenient to work with a really fast
        # master clock (which for us will be the dot clock) and "slow
        # things down" using enables.
        #
        # For this reason, this SyncGen takes a dot clock and is responsible
        # for generating its own horizontal clock enable output.  The
        # horizontal clock enable is a pulse output, which asserts on the
        # ultimate dot of each character cell along the X-axis.
        #
        # Upon the start of a new character column, the character dot
        # counter resets to 0.
        #

        with m.If(self.fv_xdot == self.xct):
            comb += Assert(self.xclken)

        with m.If(self.fv_xdot != self.xct):
            comb += Assert(~self.xclken)

        with m.If(past_valid & ~Past(self.dotclken)):
            sync += Assert(Stable(self.fv_xdot))

        with m.If(past_valid & Past(self.dotclken)):
            with m.If(~Past(self.xclken) & ~Past(self.fv_adj)):
                sync += Assert(self.fv_xdot == (Past(self.fv_xdot)+1)[0:4])

            with m.If(~Past(self.xclken) & Past(self.fv_adj)):
                sync += Assert(Stable(self.fv_xdot))

            with m.If(Past(self.xclken)):
                sync += Assert(self.fv_xdot == 0)

        #
        # Once we have the concept of character-based synchronization,
        # we must count characters to know where we are on the scanline.
        # When we're displaying the last character in a line, we must
        # start over from 0.
        #
        # If there is a non-zero horizontal total adjustment, we must
        # additionally let that pass before resuming normal character
        # matrix activities.
        #

        with m.If(self.fv_xchr == self.xt):
            comb += Assert(self.fv_xtotal)

        with m.If(self.fv_xchr != self.xt):
            comb += Assert(~self.fv_xtotal)

        with m.If(past_valid & ~Past(self.dotclken)):
            with m.If(Past(self.fv_adj)):
                sync += Assert(Stable(self.fv_xchr))

        with m.If(past_valid & Past(self.dotclken)):
            with m.If(~Past(self.fv_adj)):
                with m.If(~Past(self.xclken) & ~Past(self.fv_xtotal)):
                    sync += Assert(Stable(self.fv_xchr))

                with m.If(Past(self.xclken) & ~Past(self.fv_xtotal)):
                    sync += Assert(self.fv_xchr == (Past(self.fv_xchr) + 1)[0:len(self.fv_xchr)])

                with m.If(Past(self.xclken) & Past(self.fv_xtotal) & (Past(self.xta) == 0)):
                    sync += [
                        Assert(self.fv_xchr == 0),
                        Assert(~self.fv_adj),
                    ]

                with m.If(past_valid & Past(self.xclken) & Past(self.fv_xtotal) & (Past(self.xta) != 0)):
                    sync += Assert(self.fv_adj)

            with m.If(Fell(self.fv_adj)):
                sync += Assert(self.fv_xchr == 0)

        #
        # When the horizontal sync position has been reached, we must
        # assert the horizontal sync pulse for the right duration.
        # We increment raster counters only when the sync pulse ends.
        #

        with m.If(self.xclken & (self.fv_xchr != self.xsp)):
            comb += Assert(~self.fv_go_xsync)

        with m.If(self.xclken & (self.fv_xchr == self.xsp)):
            comb += Assert(self.fv_go_xsync)

        with m.If(self.fv_xsctr != 0):
            comb += Assert(self.xs)

        with m.If(past_valid & ~Past(self.syncen)):
            sync += Assert(Stable(self.fv_xsctr))

        with m.If(past_valid & Past(self.syncen) & (Past(self.fv_xsctr) == 0) & ~Past(self.fv_go_xsync)):
            sync += Assert(Stable(self.fv_xsctr))

        with m.If(past_valid & Past(self.dotclken) & Past(self.syncen)):
            with m.If(Past(self.fv_go_xsync)):
                sync += Assert(self.fv_xsctr == Past(self.xsw))

            with m.If(Past(self.xs) & ~Past(self.fv_go_xsync)):
                sync += Assert(self.fv_xsctr == (Past(self.fv_xsctr) - 1))

            with m.If(Past(self.rastclken) & ~Past(self.fv_go_xsync)):
                sync += [
                    Assert(Fell(self.xs)),
                    Assert(~self.rastclken),
                ]

        #
        # When the horizontal total is reached, the xchr counter resets to zero.
        # This provides the means by which we detect when to assert the horizontal
        # sync pulse.  However, when xchr resets to 0, we also begin to generate
        # video data as well; this commences the start of the visible playfield.
        #
        # The horizontal display counter tracks how long to enable the display for.
        #

        with m.If(self.fv_xdctr != 0):
            comb += Assert(self.xden)

        with m.If(self.fv_xdctr == 0):
            comb += Assert(~self.xden)

        with m.If(past_valid & ~Past(self.xclken)):
            sync += Assert(Stable(self.fv_xdctr))

        with m.If(past_valid & Past(self.dotclken)):
            with m.If(Past(self.xclken) & Past(self.xden) & ~Past(self.fv_xtotal)):
                sync += Assert(self.fv_xdctr == (Past(self.fv_xdctr) - 1))

            with m.If(Past(self.xclken) & Past(self.fv_xtotal)):
                sync += Assert(self.fv_xdctr == Past(self.xd))

        return m


class SyncGenTestCase(FHDLTestCase):
    def test_syncgen(self):
        self.assertFormal(SyncGenFormal(), mode='bmc', depth=100)
        self.assertFormal(SyncGenFormal(), mode='prove', depth=100)
