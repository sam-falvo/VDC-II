from nmigen.test.utils import FHDLTestCase
from nmigen import (
    Elaboratable,
    Module,
    ResetSignal,
    Signal,
    Const,
)
from nmigen.hdl.ast import (
    Assert,
    Assume,
    Past,
    Stable,
)

from interfaces import COUNTER_WIDTH


def create_crtc_interface(self, platform="", ctr_width=COUNTER_WIDTH):
    # inputs
    #
    # Inputs come from the following sources in the
    # VDC register set:
    #
    #              X-Axis    Y-Axis
    #              --------  --------
    # ht, vt       R00       R04
    # hd, vd       R01       R06
    # hsp, vsp     R02       R07
    # hsw, vsw     R03[0:4]  R03[4:8]
    # hct, vct     R22[0:4]  R09[0:5]

    self.hct = Signal(4)
    self.ht = Signal(8)
    self.hsp = Signal(8)
    self.hsw = Signal(4)
    self.hd = Signal(8)

    # outputs
    self.hclken = Signal(1)
    self.hs = Signal(1)
    self.hden = Signal(1)

    # FV outputs
    if platform == 'formal':
        self.fv_hdot = Signal(4)
        self.fv_hchr = Signal(8)
        self.fv_htotal = Signal(1)
        self.fv_go_hsync = Signal(1)
        self.fv_hsctr = Signal(4)
        self.fv_hdctr = Signal(8)


class CRTC(Elaboratable):
    """
    Implements the core logic that would define a typical MC6845 or
    MOS 6545 CRTC device.  Note that this does NOT define the bus
    interface for the core logic; register settings are taken as
    explicit inputs, and the bus interface logic is free to use the
    outputs as it sees fit.

    Inputs:
    - hct -- Horizontal Character Total; this sets the number of pixels
      per character along the X-axis.  For example, a font with 5 pixels
      and no inter-character gaps would set this to 4.  A font 8-pixels
      wide with a one pixel inter-character gap would set this to 8.

    - ht -- Horizontal Total; this sets the maximum number of characters
      in a single scanline.

    - hsp -- Horizontal Sync Position; relative to the left-edge of the
      visible playfield, sets how far to the right the horizontal sync
      pulse sits.

    - hsw -- Horizontal Sync Width, in characters.

    - hd -- Horizontal Displayed; determines how wide the visible playfield
      is in characters.

    Outputs:
    - hclken -- Asserted while the display is painting the right-most dot
      of a character.  The falling edge of this signal demarcates the end
      of one character and the start of the next.

    - hs -- Horizontal Sync.

    - hden -- Horizontal Display Enable.  Asserted during the portion of
      the scanline which will show the visible playfield.
    """

    def __init__(self, platform=""):
        super().__init__()
        create_crtc_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        #
        # Horizontal Character Clocking
        #

        hdot = Signal(4)
        hclken = Signal(1)

        comb += [
            hclken.eq(hdot == self.hct),
            self.hclken.eq(hclken),
        ]

        with m.If(hclken):
            sync += hdot.eq(0)
        with m.Else():
            sync += hdot.eq(hdot + 1)

        #
        # Horizontal Line Clocking
        #

        hchr = Signal(8)
        htotal = Signal(1)

        comb += [
            htotal.eq(hchr == self.ht),
        ]

        with m.If(hclken & ~htotal):
            sync += hchr.eq(hchr + 1)
        with m.If(hclken & htotal):
            sync += hchr.eq(0)

        #
        # Horizontal Sync Generator
        #

        hsctr = Signal(4)
        go_hsync = Signal(1)

        comb += [
            go_hsync.eq(hchr == self.hsp),
            self.hs.eq(hsctr != 0),
        ]

        with m.If(hclken & go_hsync):
            sync += hsctr.eq(self.hsw)
        with m.If(hclken & ~go_hsync & self.hs):
            sync += hsctr.eq(hsctr - 1)

        #
        # Horizontal Display Enable Generator
        #

        hdctr = Signal(8)

        comb += [
            self.hden.eq(hdctr != 0),
        ]

        with m.If(hclken & htotal):
            sync += hdctr.eq(self.hd)
        with m.If(hclken & ~htotal & self.hden):
            sync += hdctr.eq(hdctr - 1)

        if platform == 'formal':
            comb += [
                self.fv_hdot.eq(hdot),
                self.fv_hchr.eq(hchr),
                self.fv_htotal.eq(htotal),
                self.fv_go_hsync.eq(go_hsync),
                self.fv_hsctr.eq(hsctr),
                self.fv_hdctr.eq(hdctr),
            ]

        return m


class CRTCFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_crtc_interface(self, platform="formal")

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

        dut = CRTC(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.hclken.eq(dut.hclken),
            self.hs.eq(dut.hs),
            self.hden.eq(dut.hden),

            self.fv_hdot.eq(dut.fv_hdot),
            self.fv_hchr.eq(dut.fv_hchr),
            self.fv_htotal.eq(dut.fv_htotal),
            self.fv_go_hsync.eq(dut.fv_go_hsync),
            self.fv_hsctr.eq(dut.fv_hsctr),
            self.fv_hdctr.eq(dut.fv_hdctr),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.hct.eq(self.hct),
            dut.ht.eq(self.ht),
            dut.hsp.eq(self.hsp),
            dut.hsw.eq(self.hsw),
            dut.hd.eq(self.hd),
        ]

        #
        # The horizontal clock is typically driven by the dot clock.
        # But, the 6545 works in terms of characters, which is typically
        # 5 to 8 pixels wide.  FPGAs can handle multiple clock domains,
        # but it's usually more convenient to work with a really fast
        # master clock (which for us will be the dot clock) and "slow
        # things down" using enables.
        #
        # For this reason, this CRTC takes a dot clock and is responsible
        # for generating its own horizontal clock enable output.  The
        # horizontal clock enable is a pulse output, which asserts on the
        # ultimate dot of each character cell along the X-axis.
        #
        # Upon the start of a new character column, the character dot
        # counter resets to 0.
        #

        with m.If(self.fv_hdot == self.hct):
            comb += Assert(self.hclken)

        with m.If(self.fv_hdot != self.hct):
            comb += Assert(~self.hclken)

        with m.If(past_valid & ~Past(self.hclken)):
            sync += Assert(self.fv_hdot == (Past(self.fv_hdot)+1)[0:4])

        with m.If(past_valid & Past(self.hclken)):
            sync += Assert(self.fv_hdot == 0)

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

        with m.If(self.fv_hchr == self.ht):
            comb += Assert(self.fv_htotal)

        with m.If(self.fv_hchr != self.ht):
            comb += Assert(~self.fv_htotal)

        with m.If(past_valid & ~Past(self.hclken) & ~Past(self.fv_htotal)):
            sync += Assert(Stable(self.fv_hchr))

        with m.If(past_valid & Past(self.hclken) & ~Past(self.fv_htotal)):
            sync += Assert(self.fv_hchr == (Past(self.fv_hchr) + 1)[0:COUNTER_WIDTH])

        with m.If(past_valid & Past(self.hclken) & Past(self.fv_htotal)):
            sync += Assert(self.fv_hchr == 0)

        #
        # When the horizontal sync position has been reached, we must
        # assert the horizontal sync pulse for the right duration.
        #

        with m.If(self.hclken & (self.fv_hchr != self.hsp)):
            comb += Assert(~self.fv_go_hsync)

        with m.If(self.hclken & (self.fv_hchr == self.hsp)):
            comb += Assert(self.fv_go_hsync)

        with m.If(past_valid & Past(self.fv_go_hsync) & ~Past(self.hclken)):
            sync += Assert(Stable(self.fv_hsctr))

        with m.If(past_valid & Past(self.fv_go_hsync) & Past(self.hclken)):
            sync += Assert(self.fv_hsctr == Past(self.hsw))

        with m.If(self.fv_hsctr != 0):
            comb += Assert(self.hs)

        with m.If(past_valid & ~Past(self.hclken)):
            sync += Assert(Stable(self.fv_hsctr))

        with m.If(past_valid & Past(self.hclken) & (Past(self.fv_hsctr) != 0) & ~Past(self.fv_go_hsync)):
            sync += Assert(self.fv_hsctr == (Past(self.fv_hsctr) - 1))

        with m.If(past_valid & Past(self.hclken) & (Past(self.fv_hsctr) == 0) & ~Past(self.fv_go_hsync)):
            sync += Assert(Stable(self.fv_hsctr))

        #
        # When the horizontal total is reached, the hchr counter resets to zero.
        # This provides the means by which we detect when to assert the horizontal
        # sync pulse.  However, when hchr resets to 0, we also begin to generate
        # video data as well; this commences the start of the visible playfield.
        #
        # The horizontal display counter tracks how long to enable the display for.
        #

        with m.If(self.fv_hdctr != 0):
            comb += Assert(self.hden)

        with m.If(self.fv_hdctr == 0):
            comb += Assert(~self.hden)

        with m.If(past_valid & ~Past(self.hclken)):
            sync += Assert(Stable(self.fv_hdctr))

        with m.If(past_valid & Past(self.hclken) & Past(self.hden) & ~Past(self.fv_htotal)):
            sync += Assert(self.fv_hdctr == (Past(self.fv_hdctr) - 1))

        with m.If(past_valid & Past(self.hclken) & Past(self.fv_htotal)):
            sync += Assert(self.fv_hdctr == Past(self.hd))

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

        return m


class CRTCTestCase(FHDLTestCase):
    def test_crtc(self):
        self.assertFormal(CRTCFormal(), mode='bmc', depth=100)
        self.assertFormal(CRTCFormal(), mode='prove', depth=100)
