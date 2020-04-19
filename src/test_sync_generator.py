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

from interfaces import create_syncgen_interface, COUNTER_WIDTH
from sync_generator import SyncGenerator


class SyncGeneratorFormal(Elaboratable):
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

        dut = SyncGenerator(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.counter.eq(dut.counter),
            self.total_reached.eq(dut.total_reached),
            self.xsync.eq(dut.xsync),
            self.last.eq(dut.last),

            self.fv_sync_width_ctr.eq(dut.fv_sync_width_ctr),
            self.fv_unit_ctr.eq(dut.fv_unit_ctr),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.total.eq(self.total),
            dut.sync_pos.eq(self.sync_pos),
            dut.sync_width.eq(self.sync_width),
            dut.char_total.eq(self.char_total),
        ]

        # The counter must monotonically decrement with each
        # character shown, until the maximum possible along its axis.
        with m.If(past_valid & Past(rst)):
            sync += Assert(self.counter == Past(self.total))

        with m.If(past_valid & Past(self.total_reached) & Past(self.last)):
            sync += Assert(self.counter == Past(self.total))

        with m.If(past_valid & ~Past(self.total_reached) & Past(self.last)):
            sync += Assert(self.counter == (Past(self.counter) - 1)[0:COUNTER_WIDTH])

        with m.If(past_valid & ~Past(self.last)):
            sync += Assert(Stable(self.counter))

        # The sync pulse must assert when we reach the SYNC start
        # boundary.  The sync pulse must negate when we reach the stopping
        # boundary.  If these boundaries overlap, the state of SYNC must remain
        # stable.
        with m.If(
            past_valid &
            (~Past(self.xsync)) &
            (Past(self.counter) == Past(self.sync_pos)) &
            Past(self.last) &
            (Past(self.sync_width) != 0)
        ):
            sync += Assert(self.xsync)

        with m.If(
            past_valid &
            (~Past(self.xsync)) &
            (Past(self.counter) == Past(self.sync_pos)) &
            (Past(self.sync_width) == 0)
        ):
            sync += Assert(~self.xsync)

        with m.If(
            past_valid &
            (self.fv_sync_width_ctr == 0)
        ):
            sync += Assert(~self.xsync)

        with m.If(
            past_valid &
            (self.fv_sync_width_ctr != 0)
        ):
            sync += Assert(self.xsync)

        # The sync width counter must decrement in units of characters.
        with m.If(
            past_valid &
            (Past(self.fv_sync_width_ctr) != 0) &
            ~Past(self.last)
        ):
            sync += Assert(Stable(self.fv_sync_width_ctr))

        with m.If(
            past_valid &
            (Past(self.fv_sync_width_ctr) != 0) &
            Past(self.last)
        ):
            sync += Assert(
                self.fv_sync_width_ctr == (Past(self.fv_sync_width_ctr) - 1)
            )

        # The character pixel counter should decrement with each pixel pushed to the display.
        # When it reaches 0, it should reset to its maximum value.
        with m.If(
            past_valid &
            (Past(self.fv_unit_ctr) == 0)
        ):
            sync += Assert(self.fv_unit_ctr == Past(self.char_total))

        with m.If(
            past_valid &
            (Past(self.fv_unit_ctr) != 0)
        ):
            sync += Assert(self.fv_unit_ctr == (Past(self.fv_unit_ctr) - 1))

        return m


class SyncGeneratorTestCase(FHDLTestCase):
    def test_sync_generator(self):
        self.assertFormal(SyncGeneratorFormal(), mode='bmc', depth=100)
        self.assertFormal(SyncGeneratorFormal(), mode='prove', depth=100)
