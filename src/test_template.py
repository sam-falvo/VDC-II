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


def create_xxxx_interface(self, platform=None):
    # Inputs

    # Outputs

    if platform == 'formal':
        pass


class XxXx(Elaboratable):
    def __init__(self, platform=None):
        super().__init__()
        create_xxxx_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        return m


class XxXxFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_xxxx_interface(self, platform="formal")

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

        dut = XxXx(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.dat_o.eq(dut.dat_o),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.dat_i.eq(self.dat_i),
            dut.we_i.eq(self.we_i),
            dut.aadr_i.eq(self.aadr_i),
            dut.cadr_i.eq(self.cadr_i),
            dut.padr_i.eq(self.padr_i),
        ]

        return m


class XxXxTestCase(FHDLTestCase):
    def test_xxxx(self):
        self.assertFormal(XxXxFormal(), mode='bmc', depth=100)
        self.assertFormal(XxXxFormal(), mode='prove', depth=100)
