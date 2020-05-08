from nmigen.test.utils import FHDLTestCase
from nmigen.back.pysim import Simulator

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
            self.rd_o.eq(dut.rd_o),

            self.fv_old_cssync.eq(dut.fv_old_cssync),
            self.fv_cssync.eq(dut.fv_cssync),
            self.fv_rdsync.eq(dut.fv_rdsync),
            self.fv_we_ports.eq(dut.fv_we_ports),
            self.fv_rd_ports.eq(dut.fv_rd_ports),
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

        with m.If(past_valid & Past(self.fv_we_ports)):
            sync += Assert(~self.fv_we_ports)

        # I/O port read strobe pulses only when a read cycle concludes.
        # This strobe is needed to detect when to auto-increment the
        # update location register pair.
        with m.If(~self.fv_old_cssync & self.fv_cssync & self.fv_rdsync):
            comb += Assert(self.fv_rd_ports)

        with m.If(~self.fv_old_cssync & ~self.fv_cssync & self.fv_rdsync):
            comb += Assert(~self.fv_rd_ports)

        with m.If(self.fv_we_ports):
            comb += Assert(~self.fv_rd_ports)

        with m.If(past_valid & Past(self.fv_rd_ports)):
            sync += Assert(~self.fv_rd_ports)

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

        # The register set read strobe pulse should only assert when
        # the host processor has finished reading the data port.
        with m.If(self.fv_rd_ports & self.fv_async):
            comb += Assert(self.rd_o)

        with m.If(~self.fv_rd_ports):
            comb += Assert(~self.rd_o)

        with m.If(~self.fv_async):
            comb += Assert(~self.rd_o)

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

    def write_addr_port(self, m, byte):
        yield m.a.eq(0)
        yield m.cs.eq(1)
        yield m.rd.eq(0)
        yield
        yield
        yield
        yield m.db.eq(byte)
        yield
        yield
        yield
        yield m.cs.eq(0)
        yield m.db.eq(0)
        yield
        yield
        yield

    def write_data_port(self, m, byte):
        yield m.a.eq(1)
        yield m.cs.eq(1)
        yield m.rd.eq(0)
        yield
        yield
        yield
        yield m.db.eq(byte)
        yield
        yield
        yield
        yield m.cs.eq(0)
        yield m.db.eq(0)
        yield
        yield
        yield

    def test_write_txn(self):
        from regset8bit import RegSet8Bit

        m = Module()

        m.a = Signal(1)
        m.db = Signal(8)
        m.cs = Signal(1)
        m.rd = Signal(1)
        m.q = Signal(8)
        m.qoe = Signal(1)

        hb = m.submodules.hb = HostBus()
        rs = m.submodules.rs = RegSet8Bit()

        m.d.comb += [
            hb.a.eq(m.a),
            hb.d.eq(m.db),
            hb.cs.eq(m.cs),
            hb.rd.eq(m.rd),

            m.q.eq(hb.q),
            m.qoe.eq(hb.qoe),

            rs.dat_i.eq(hb.dat_o),
            rs.adr_i.eq(hb.adr_o),
            rs.we_i.eq(hb.we_o),
            hb.dat_i.eq(rs.dat_o),
        ]

        sim = Simulator(m)
        sim.add_clock(1e-6)
        with sim.write_vcd("hostbus.vcd"):
            def process():
                yield m.a.eq(1)
                yield m.db.eq(0)
                yield m.cs.eq(0)
                yield m.rd.eq(0)
                yield
                yield
                yield
                yield
                self.assertEqual((yield m.qoe), 0)

                yield from self.write_addr_port(m, 0)
                yield from self.write_data_port(m, 6)
                yield from self.write_addr_port(m, 0)

                # read back data port value
                yield m.a.eq(1)
                yield m.cs.eq(1)
                yield m.rd.eq(1)
                yield
                yield
                yield
                self.assertEqual((yield m.qoe), 1)
                # Data not yet valid because of synchronized inputs
                yield
                yield
                yield
                self.assertEqual((yield m.qoe), 1)
                self.assertEqual((yield m.q), 6)
                yield m.cs.eq(0)
                yield
                yield
                yield
                self.assertEqual((yield m.qoe), 0)
                yield
                yield
                yield

            sim.add_sync_process(process)
            sim.run()
