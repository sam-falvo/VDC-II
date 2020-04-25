from nmigen.test.utils import FHDLTestCase
from nmigen import (
    Elaboratable,
    Module,
    ResetSignal,
    Signal,
    Cat,
    Const,
)
from nmigen.hdl.ast import (
    Assert,
    Assume,
    Past,
    Stable,
)


from interfaces import create_regset8bit_interface
from regset8bit import RegSet8Bit


class RegSet8BitFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_regset8bit_interface(self, platform="formal")

    def elaborate(self, platform=''):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # This flag indicates when it's safe to use Past(), Stable(), etc.
        # Required so we can detect the start of simulation and prevent literal
        # edge cases from giving false negatives concerning the behavior of the
        # Past and Stable functions.
        z_past_valid = Signal(1, reset=0)
        sync += z_past_valid.eq(1)

        dut = RegSet8Bit(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.ht.eq(dut.ht),
            self.hd.eq(dut.hd),
            self.hsp.eq(dut.hsp),
            self.vsw.eq(dut.vsw),
            self.hsw.eq(dut.hsw),
            self.vt.eq(dut.vt),
            self.vta.eq(dut.vta),
            self.vd.eq(dut.vd),
            self.vsp.eq(dut.vsp),
            self.vct.eq(dut.vct),
            self.hcd.eq(dut.hcd),
            self.hct.eq(dut.hct),
            self.hsync_xor.eq(dut.hsync_xor),
            self.vsync_xor.eq(dut.vsync_xor),

            self.dat_o.eq(dut.dat_o),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.adr_i.eq(self.adr_i),
            dut.dat_i.eq(self.dat_i),
            dut.we_i.eq(self.we_i),
        ]

        # When the register selected is valid, only that register's results
        # are offered on the dat_o bus.  Otherwise, dat_o must be 0xFF.
        with m.If(self.adr_i == 0):
            sync += Assert(self.dat_o == self.ht)

        with m.If(self.adr_i == 1):
            sync += Assert(self.dat_o == self.hd)

        with m.If(self.adr_i == 2):
            sync += Assert(self.dat_o == self.hsp)

        with m.If(self.adr_i == 3):
            sync += Assert(self.dat_o == Cat(self.hsw, self.vsw))

        with m.If(self.adr_i == 4):
            sync += Assert(self.dat_o == self.vt)

        with m.If(self.adr_i == 5):
            sync += Assert(self.dat_o == Cat(self.vta, Const(-1, 3)))

        with m.If(self.adr_i == 6):
            sync += Assert(self.dat_o == self.vd)

        with m.If(self.adr_i == 7):
            sync += Assert(self.dat_o == self.vsp)

        with m.If(self.adr_i == 9):
            sync += Assert(self.dat_o == Cat(self.vct, Const(-1, 3)))

        with m.If(self.adr_i == 22):
            sync += Assert(self.dat_o == Cat(self.hcd, self.hct))

        with m.If(self.adr_i == 37):
            sync += Assert(self.dat_o == Cat(Const(-1, 6), self.vsync_xor, self.hsync_xor))

        with m.If(self.adr_i == 63):
            sync += Assert(self.dat_o == Const(-1, len(self.dat_o)))

        # After reset, HSYNC and VSYNC polarity bits should be 1.
        with m.If(Past(rst) & ~rst):
            sync += [
                Assert(self.hsync_xor == 1),
                Assert(self.vsync_xor == 1),
            ]

        return m


class RegSet8BitTestCase(FHDLTestCase):
    def test_regset8bit(self):
        self.assertFormal(RegSet8BitFormal(), mode='bmc', depth=100)
        self.assertFormal(RegSet8BitFormal(), mode='prove', depth=100)
