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

from interfaces import create_blockram_arbiter_interface

from blockram_arbiter import BlockRamArbiter


class BlockRamArbiterFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_blockram_arbiter_interface(self, platform="formal")

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

        dut = BlockRamArbiter(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.vfe_ack_o.eq(dut.vfe_ack_o),
            self.vfe_dat_o.eq(dut.vfe_dat_o),
            self.vfe_stall_o.eq(dut.vfe_stall_o),

            self.mpe_ack_o.eq(dut.mpe_ack_o),
            self.mpe_dat_o.eq(dut.mpe_dat_o),
            self.mpe_stall_o.eq(dut.mpe_stall_o),

            self.adr_o.eq(dut.adr_o),
            self.dat_o.eq(dut.dat_o),
            self.we_o.eq(dut.we_o),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.vfe_adr_i.eq(self.vfe_adr_i),
            dut.vfe_cyc_i.eq(self.vfe_cyc_i),
            dut.vfe_dat_i.eq(self.vfe_dat_i),
            dut.vfe_stb_i.eq(self.vfe_stb_i),
            dut.vfe_we_i.eq(self.vfe_we_i),

            dut.mpe_adr_i.eq(self.mpe_adr_i),
            dut.mpe_cyc_i.eq(self.mpe_cyc_i),
            dut.mpe_dat_i.eq(self.mpe_dat_i),
            dut.mpe_stb_i.eq(self.mpe_stb_i),
            dut.mpe_we_i.eq(self.mpe_we_i),

            dut.dat_i.eq(self.dat_i),
        ]

        # As long as the video fetch engine (VFE) isn't trying to access
        # video RAM, then the Memory Port Engine (MPE) has free reign over
        # video RAM.  Otherwise, all hands on deck for the VFE.
        with m.If(~self.vfe_cyc_i):
            with m.If(self.mpe_cyc_i):
                comb += [
                    Assert(self.vfe_stall_o),
                    Assert(self.adr_o == self.mpe_adr_i),
                    Assert(self.we_o == self.mpe_we_i),
                    Assert(self.dat_o == self.mpe_dat_i),
                ]

        with m.If(self.vfe_cyc_i):
            comb += [
                Assert(self.mpe_stall_o),
                Assert(self.adr_o == self.vfe_adr_i),
                Assert(self.we_o == self.vfe_we_i),
                Assert(self.dat_o == self.vfe_dat_i),
            ]

        # Block RAM is trusted to be synchronous.  Thus, the ACK for a given
        # STB will occur one clock later, along with the corresponding data
        # (if the transaction was a read).
        with m.If(past_valid & Past(self.vfe_cyc_i) & Past(self.vfe_stb_i)):
            sync += [
                Assert(self.vfe_ack_o),
                Assert(~self.mpe_ack_o),
                Assert(self.vfe_dat_o == self.dat_i),
            ]

        with m.If(past_valid & ~Past(self.vfe_cyc_i) & Past(self.mpe_cyc_i) & Past(self.mpe_stb_i)):
            sync += [
                Assert(self.mpe_ack_o),
                Assert(~self.vfe_ack_o),
                Assert(self.mpe_dat_o == self.dat_i),
            ]

        return m


class BlockRamArbiterTestCase(FHDLTestCase):
    def test_blockram_arbiter(self):
        self.assertFormal(BlockRamArbiterFormal(), mode='bmc', depth=100)
        self.assertFormal(BlockRamArbiterFormal(), mode='prove', depth=100)
