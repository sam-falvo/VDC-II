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
            self.hp.eq(dut.hp),
            self.hw.eq(dut.hw),
            self.vw.eq(dut.vw),
            self.cdh.eq(dut.cdh),
            self.cth.eq(dut.cth),

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
        # are offered on the do bus.  Otherwise, do must be 0xFF.
        with m.If(self.adr_i == 0):
            sync += Assert(self.dat_o == self.ht)

        with m.If(self.adr_i == 2):
            sync += Assert(self.dat_o == self.hp)

        with m.If(self.adr_i == 3):
            sync += Assert(self.dat_o == Cat(self.hw, self.vw))

        with m.If(self.adr_i == 22):
            sync += Assert(self.dat_o == Cat(self.cdh, self.cth))

        with m.If(self.adr_i == 63):
            sync += Assert(self.dat_o == Const(-1, len(self.dat_o)))

        return m


class RegSet8BitTestCase(FHDLTestCase):
    def test_regset8bit(self):
        self.assertFormal(RegSet8BitFormal(), mode='bmc', depth=100)
        self.assertFormal(RegSet8BitFormal(), mode='prove', depth=100)
