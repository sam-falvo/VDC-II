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


def create_shifter_interface(self, platform=None):
    # CRTC Interface
    ## Inputs
    self.hclken = Signal(1)
    self.den = Signal(1)

    # Register Set Interface
    ## Inputs
    self.hscroll = Signal(4)
    self.hcd = Signal(4)
    self.hct = Signal(4)
    self.fgpen = Signal(4)
    self.bgpen = Signal(4)
    self.attr_enable = Signal(1)

    # Video Interface
    ## Outputs
    self.outpen = Signal(4)

    # Strip Buffer Interface
    ## Inputs
    self.attrpen = Signal(4)

    if platform == 'formal':
        self.fv_reveal_ctr = Signal(4)
        self.fv_conceal_ctr = Signal(4)
        self.fv_chrgate = Signal(1)
        self.fv_dot = Signal(1)


class Shifter(Elaboratable):
    def __init__(self, platform=None):
        create_shifter_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Supporting horizontal scrolling, we use two counters
        # to control when we are displaying a character's main
        # contents (chrgate asserted) or when we're in the
        # inter-character fill (chrgate disabled).
        chrgate = Signal(1)
        reveal_ctr = Signal(4)
        conceal_ctr = Signal(4)

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
            sync += chrgate.eq(1)
        with m.If(conceal_ctr_z & ~reveal_ctr_z):
            sync += chrgate.eq(0)

        # This is the *final* output dot, after processing by
        # blink, cursor, reverse video, and other preprocessing
        # steps.  DEN, ATTR_ENABLE, and this signal determines
        # what colors appear on the output RGBI signals.
        dot = Signal(1)

        # TODO(sfalvo): DEBUG CODE.
        comb += dot.eq(chrgate)

        # Final Color Mux
        with m.If(~self.den):
            comb += self.outpen.eq(0)
        with m.Else():
            with m.If(dot):
                with m.If(self.attr_enable):
                    comb += self.outpen.eq(self.attrpen)
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
            ]

        return m


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
            self.outpen.eq(dut.outpen),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.hclken.eq(self.hclken),
            dut.den.eq(self.den),
            dut.hscroll.eq(self.hscroll),
            dut.hcd.eq(self.hcd),
            dut.hct.eq(self.hct),
            dut.fgpen.eq(self.fgpen),
            dut.bgpen.eq(self.bgpen),
            dut.attr_enable.eq(self.attr_enable),
            dut.attrpen.eq(self.attrpen),
        ]

        #
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
        #

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

        # The output color is black when blanking is in effect.
        with m.If(~self.den):
            comb += Assert(self.outpen == 0)

        # If not blanking, and if the current dot is 0, then we show
        # the current background color.  If the dot is a 1, then we
        # show either the global foreground color or the attribute
        # color, depending on whether or not attributes are enabled.
        with m.If(self.den):
            with m.If(~self.fv_dot):
                comb += Assert(self.outpen == self.bgpen)
            with m.Else():
                with m.If(self.attr_enable):
                    comb += Assert(self.outpen == self.attrpen)
                with m.Else():
                    comb += Assert(self.outpen == self.fgpen)

        return m


class ShifterTestCase(FHDLTestCase):
    def test_shifter(self):
        self.assertFormal(ShifterFormal(), mode='bmc', depth=100)
        self.assertFormal(ShifterFormal(), mode='prove', depth=100)
