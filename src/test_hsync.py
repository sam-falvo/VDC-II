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

from interfaces import create_hsync_interface, HCOUNTER_WIDTH
from hsync import HSync


class HSyncFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_hsync_interface(self, platform="formal")

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

        dut = HSync(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.hcounter.eq(dut.hcounter),
            self.htotal_reached.eq(dut.htotal_reached),
            self.hsync.eq(dut.hsync),

            self.fv_sync_width_ctr.eq(dut.fv_sync_width_ctr),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.htotal.eq(self.htotal),
            dut.hsync_pos.eq(self.hsync_pos),
            dut.hsync_width.eq(self.hsync_width),
        ]

        # The horizontal counter must monotonically increment with each pixel shown,
        # until the maximum possible for each raster.
        with m.If(past_valid & Past(rst)):
            sync += Assert(self.hcounter == 0)

        with m.If(past_valid & Past(self.htotal_reached)):
            sync += Assert(self.hcounter == 0)

        with m.If(past_valid & ~Past(self.htotal_reached)):
            sync += Assert(self.hcounter == (Past(self.hcounter) + 1)[0:HCOUNTER_WIDTH])

        # The horizontal sync pulse must assert when we reach the HSYNC start
        # boundary.  The sync pulse must negate when we reach the stopping
        # boundary.  If these boundaries overlap, the state of HSYNC must remain
        # stable.
        with m.If(
            past_valid &
            (~Past(self.hsync)) &
            (Past(self.hcounter) == Past(self.hsync_pos)) &
            (Past(self.hsync_width) != 0)
        ):
            sync += Assert(self.hsync)

        with m.If(
            past_valid &
            (~Past(self.hsync)) &
            (Past(self.hcounter) == Past(self.hsync_pos)) &
            (Past(self.hsync_width) == 0)
        ):
            sync += Assert(~self.hsync)

        with m.If(
            past_valid &
            (self.fv_sync_width_ctr == 0)
        ):
            sync += Assert(~self.hsync)

        with m.If(
            past_valid &
            (self.fv_sync_width_ctr != 0)
        ):
            sync += Assert(self.hsync)

        return m


class HSyncTestCase(FHDLTestCase):
    def test_hsync(self):
        self.assertFormal(HSyncFormal(), mode='bmc', depth=100)
        self.assertFormal(HSyncFormal(), mode='prove', depth=100)
