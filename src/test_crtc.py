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


def create_syncgen_interface(
    self, platform="",
    char_total_bits=4, total_bits=8, sync_pos_bits=8, sync_width_bits=4,
    disp_bits=8, adj_bits=4
):
    # inputs
    #
    # Inputs come from the following sources in the
    # VDC register set:
    #
    #              X-Axis    Y-Axis
    #              --------  --------
    # xt           R00       R04
    # xta          -         R05
    # xd           R01       R06
    # xsp          R02       R07
    # xsw          R03[0:4]  R03[4:8]
    # xct          R22[0:4]  R09[0:5]

    self.dotclken = Signal(1)
    self.syncen = Signal(1)
    self.xct = Signal(char_total_bits)
    self.xt = Signal(total_bits)
    self.xsp = Signal(sync_pos_bits)
    self.xsw = Signal(sync_width_bits)
    self.xd = Signal(disp_bits)
    self.xta = Signal(adj_bits)

    # outputs
    self.xclken = Signal(1)
    self.xs = Signal(1)
    self.xden = Signal(1)
    self.rastclken = Signal(1)

    # FV outputs
    if platform == 'formal':
        self.fv_xdot = Signal(len(self.xct))
        self.fv_xchr = Signal(len(self.xt))
        self.fv_xtotal = Signal(1)
        self.fv_go_xsync = Signal(1)
        self.fv_xsctr = Signal(len(self.xsw))
        self.fv_xdctr = Signal(len(self.xd))
        self.fv_adj = Signal(1)
        self.fv_adjctr = Signal(len(self.xta))


class SyncGen(Elaboratable):
    """
    Implements the core logic that would define a typical MC6845 or
    MOS 6545 sync generator.  Note that this does NOT define the bus
    interface for the core logic; register settings are taken as
    explicit inputs, and the external logic is free to use the outputs
    as it sees fit.

    Inputs:
    - dotclken -- Dot Clock Enable.  If negated, the module's clock has
      neglible or no effect.  Only when this signal is asserted are the
      SyncGen counters altered.  For horizontal sync generators, this
      would probably be tied to 1.  For vertical sync generators, this
      would be tied to the rastclken output of a horizontal sync generator.

    - syncen -- Sync Clock Enable.  If negated, sync generation will never
      complete.  Typically, for horizontal sync generators, this is tied
      to the xclk output, to give sync generation character resolution.
      For vertical sync generators, this is typically tied to 1 to give
      sync generation line resolution.

    - xct -- Character Total; this sets the number of pixels
      per character along the X-axis, or the number of raster lines in the
      Y-axis.  For example, a font with 5 pixels and no inter-character gaps
      would set this to 4.  A font 8-pixels wide with a one pixel inter-
      character gap would set this to 8.

    - xt -- Total; this sets the maximum number of characters
      in a single scanline or playfield.

    - xsp -- Sync Position; relative to the left-edge of the visible
      playfield, sets how far to the right the horizontal sync pulse sits.
      Relative to the top of the playfield, it sets how far below the
      vertical sync pulse sits.

    - xsw -- Sync Width, in characters (horizontal) or lines (vertical).

    - xd -- Horizontal Displayed; determines how wide the visible playfield
      is in characters.

    Outputs:
    - xclken -- Asserted while the display is painting the right-most (resp.,
      bottom-most) dot (line) of a character.  The falling edge of this signal
      demarcates the end of one character and the start of the next.

    - xs -- Sync.

    - xden -- Display Enable.  Asserted during the portion of
      the playfield which will show the frame buffer contents.

    - rastclken -- Raster Clock Enable.  When asserted it grants the next
      sync generator permission to count.
    """

    def __init__(self, platform=""):
        super().__init__()
        create_syncgen_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        #
        # Horizontal Total Adjust support.
        #
        # Note: adjctr is reloaded later on in the source.
        #

        adjctr = Signal(len(self.xta))
        adj = Signal(1)

        comb += adj.eq(adjctr != 0)

        with m.If(self.dotclken):
            with m.If(adj):
                sync += adjctr.eq(adjctr - 1)

        #
        # Horizontal Character Clocking
        #

        xdot = Signal(len(self.xct))
        xclken = Signal(1)

        comb += [
            xclken.eq(xdot == self.xct),
            self.xclken.eq(xclken),
        ]

        with m.If(self.dotclken):
            with m.If(xclken):
                sync += xdot.eq(0)

            with m.If(~xclken & ~adj):
                sync += xdot.eq(xdot + 1)

        #
        # Horizontal Line Clocking
        #

        xchr = Signal(len(self.xt))
        xtotal = Signal(1)

        comb += [
            xtotal.eq(xchr == self.xt),
        ]

        with m.If(self.dotclken):
            with m.If(~adj):
                with m.If(xclken & ~xtotal):
                    sync += xchr.eq(xchr + 1)
                with m.If(xclken & xtotal):
                    with m.If(self.xta == 0):
                        sync += xchr.eq(0)
                    with m.If(self.xta != 0):
                        sync += adjctr.eq(self.xta)

            with m.If(adjctr == 1):
                sync += xchr.eq(0)

        #
        # Horizontal Sync Generator
        #

        xsctr = Signal(len(self.xsw))
        go_xsync = Signal(1)

        comb += [
            self.rastclken.eq(xsctr == 1),
            go_xsync.eq(xchr == self.xsp),
            self.xs.eq(xsctr != 0),
        ]

        with m.If(self.dotclken):
            with m.If(self.syncen & go_xsync):
                sync += xsctr.eq(self.xsw)
            with m.If(self.syncen & ~go_xsync & self.xs):
                sync += xsctr.eq(xsctr - 1)

        #
        # Horizontal Display Enable Generator
        #

        xdctr = Signal(len(self.xd))

        comb += [
            self.xden.eq(xdctr != 0),
        ]

        with m.If(self.dotclken):
            with m.If(xclken & xtotal):
                sync += xdctr.eq(self.xd)
            with m.If(xclken & ~xtotal & self.xden):
                sync += xdctr.eq(xdctr - 1)

        if platform == 'formal':
            comb += [
                self.fv_xdot.eq(xdot),
                self.fv_xchr.eq(xchr),
                self.fv_xtotal.eq(xtotal),
                self.fv_go_xsync.eq(go_xsync),
                self.fv_xsctr.eq(xsctr),
                self.fv_xdctr.eq(xdctr),
                self.fv_adj.eq(adj),
                self.fv_adjctr.eq(adjctr),
            ]

        return m


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
