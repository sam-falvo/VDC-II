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
            self.vscroll.eq(dut.vscroll),
            self.blink_rate.eq(dut.blink_rate),
            self.reverse_screen.eq(dut.reverse_screen),
            self.block_copy.eq(dut.block_copy),

            self.dat_o.eq(dut.dat_o),

            self.update_location.eq(dut.update_location),
            self.copysrc.eq(dut.copysrc),
            self.bytecnt.eq(dut.bytecnt),
            self.go_wr_updloc.eq(dut.go_wr_updloc),
            self.go_rd_cpudatar.eq(dut.go_rd_cpudatar),
            self.go_wr_cpudataw.eq(dut.go_wr_cpudataw),
            self.go_wr_bytecnt.eq(dut.go_wr_bytecnt),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.adr_i.eq(self.adr_i),
            dut.dat_i.eq(self.dat_i),
            dut.we_i.eq(self.we_i),
            dut.rd_i.eq(self.rd_i),

            dut.cpudatar.eq(self.cpudatar),
            dut.incr_updloc.eq(self.incr_updloc),
            dut.incr_copysrc.eq(self.incr_copysrc),
            dut.decr_bytecnt.eq(self.decr_bytecnt),
        ]

        # When the register selected is valid, only that register's results
        # are offered on the dat_o bus.  Otherwise, dat_o must be 0xFF.

        ## Positive Tests
        with m.If(self.adr_i == 0):
            comb += Assert(self.dat_o == self.ht)

        with m.If(self.adr_i == 1):
            comb += Assert(self.dat_o == self.hd)

        with m.If(self.adr_i == 2):
            comb += Assert(self.dat_o == self.hsp)

        with m.If(self.adr_i == 3):
            comb += Assert(self.dat_o == Cat(self.hsw, self.vsw))

        with m.If(self.adr_i == 4):
            comb += Assert(self.dat_o == self.vt)

        with m.If(self.adr_i == 5):
            comb += Assert(self.dat_o == Cat(self.vta, Const(-1, 3)))

        with m.If(self.adr_i == 6):
            comb += Assert(self.dat_o == self.vd)

        with m.If(self.adr_i == 7):
            comb += Assert(self.dat_o == self.vsp)

        with m.If(self.adr_i == 9):
            comb += Assert(self.dat_o == Cat(self.vct, Const(-1, 3)))

        with m.If(self.adr_i == 18):
            comb += Assert(self.dat_o == self.update_location[8:16])
            with m.If(self.we_i):
                comb += Assert(self.go_wr_updloc)
            with m.Else():
                comb += Assert(~self.go_wr_updloc)

        with m.If(self.adr_i == 19):
            comb += Assert(self.dat_o == self.update_location[0:8])
            with m.If(self.we_i):
                comb += Assert(self.go_wr_updloc)
            with m.Else():
                comb += Assert(~self.go_wr_updloc)

        with m.If(self.adr_i == 22):
            comb += Assert(self.dat_o == Cat(self.hcd, self.hct))

        with m.If(self.adr_i == 24):
            comb += Assert(self.dat_o == Cat(
                self.vscroll,
                self.blink_rate,
                self.reverse_screen,
                self.block_copy,
            ))

        with m.If(self.adr_i == 30):
            comb += Assert(self.dat_o == self.bytecnt)

        with m.If(self.adr_i == 31):
            comb += Assert(self.dat_o == self.cpudatar)
            with m.If(self.rd_i):
                comb += Assert(self.go_rd_cpudatar)

        with m.If(self.adr_i == 32):
            comb += Assert(self.dat_o == self.copysrc[8:16])

        with m.If(self.adr_i == 33):
            comb += Assert(self.dat_o == self.copysrc[0:8])

        with m.If(self.adr_i == 37):
            comb += Assert(self.dat_o == Cat(Const(-1, 6), self.vsync_xor, self.hsync_xor))

        with m.If(self.adr_i == 63):
            comb += Assert(self.dat_o == Const(-1, len(self.dat_o)))

        ## Negative Tests
        with m.If(self.adr_i != 31):
            comb += Assert(~self.go_rd_cpudatar)

        # After reset, HSYNC and VSYNC polarity bits should be 1.
        with m.If(Past(rst) & ~rst):
            sync += [
                Assert(self.hsync_xor == 1),
                Assert(self.vsync_xor == 1),
            ]

        # After reading from the CPU Data port,
        # the pointer must auto-increment.
        with m.If(past_valid & (Past(self.adr_i) == 31)):
            with m.If(Past(self.rd_i)):
                sync += Assert(self.update_location == (Past(self.update_location) + 1)[0:16])

            with m.If(Past(self.we_i) & ~Past(self.rd_i) & ~Past(self.incr_updloc)):
                sync += Assert(Stable(self.update_location))

        # Pointers must also increment when instructed by the MPE.
        with m.If(past_valid & Past(self.incr_updloc)):
            sync += Assert(self.update_location == (Past(self.update_location) + 1)[0:16])

        with m.If(past_valid & Past(self.incr_copysrc)):
            sync += Assert(self.copysrc == (Past(self.copysrc) + 1)[0:16])

        # The byte counter is the only register which the MPE instructs to decrement.
        # The MPE is responsible for not underflowing the counter.
        with m.If(past_valid & Past(self.decr_bytecnt)):
            sync += Assert(self.bytecnt == (Past(self.bytecnt) - 1)[0:8])

        return m


class RegSet8BitTestCase(FHDLTestCase):
    def test_regset8bit(self):
        self.assertFormal(RegSet8BitFormal(), mode='bmc', depth=100)
        self.assertFormal(RegSet8BitFormal(), mode='prove', depth=100)
