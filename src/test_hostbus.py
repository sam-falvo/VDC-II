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

from interfaces import VDC_VERSION, create_hostbus_interface
from hostbus import HostBus


class HostBusFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_hostbus_interface(self, platform="formal")

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

        dut = HostBus(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.q.eq(dut.q),
            self.qoe.eq(dut.qoe),
            self.adr_o.eq(dut.adr_o),
            self.we_o.eq(dut.we_o),

            self.fv_old_cssync.eq(dut.fv_old_cssync),
            self.fv_cssync.eq(dut.fv_cssync),
            self.fv_rdsync.eq(dut.fv_rdsync),
            self.fv_we_ports.eq(dut.fv_we_ports),
            self.fv_async.eq(dut.fv_async),
            self.fv_dsync.eq(dut.fv_dsync),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.d.eq(self.d),
            dut.cs.eq(self.cs),
            dut.rd.eq(self.rd),
            dut.a.eq(self.a),
            dut.ready_i.eq(self.ready_i),
            dut.vblank_i.eq(self.vblank_i),
            dut.lp_i.eq(self.lp_i),
            dut.dat_i.eq(self.dat_i),
        ]

        # qoe should only be asserted during a valid read transaction.
        # It should remain negated when we're not selected and when
        # the transaction is a write transaction.
        with m.If(self.cs & self.rd):
            comb += Assert(self.qoe)

        with m.If(~self.cs):
            comb += Assert(~self.qoe)

        with m.If(~self.rd):
            comb += Assert(~self.qoe)

        # I/O port write enable pulses only when a write cycle concludes.
        with m.If(~self.fv_old_cssync & self.fv_cssync & ~self.fv_rdsync):
            comb += Assert(self.fv_we_ports)

        with m.If(~self.fv_old_cssync & ~self.fv_cssync & ~self.fv_rdsync):
            comb += Assert(~self.fv_we_ports)

        with m.If(self.fv_rdsync):
            comb += Assert(~self.fv_we_ports)

        # Register Select port must take on a new value when written.
        with m.If(past_valid & Past(self.fv_we_ports) & ~Past(self.fv_async)):
            sync += Assert(self.adr_o == Past(self.fv_dsync)[0:6])

        # The register set write enable pulse should only assert when
        # the host processor is writing to the data port.
        with m.If(self.fv_we_ports & self.fv_async):
            comb += Assert(self.we_o)

        with m.If(~self.fv_we_ports):
            comb += Assert(~self.we_o)

        with m.If(~self.fv_async):
            comb += Assert(~self.we_o)

        # When reading the status port, we should see the status bit
        # and version, at the very least.  Light-pen is not supported.
        with m.If(self.cs & self.rd & ~self.fv_async):
            comb += Assert(self.q == Cat(
                Const(VDC_VERSION, 3),
                Const(0b11, 2),
                self.vblank_i, self.lp_i, self.ready_i
            ))

        # When reading the data port, we should see the value of the
        # currently addressed register.
        with m.If(self.cs & self.rd & self.fv_async):
            comb += Assert(self.q == self.dat_i)

        return m


class HostBusTestCase(FHDLTestCase):
    def test_hostbus(self):
        self.assertFormal(HostBusFormal(), mode='bmc', depth=100)
        self.assertFormal(HostBusFormal(), mode='prove', depth=100)
