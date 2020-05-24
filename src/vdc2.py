from nmigen import (
    Cat,
    ClockDomain,
    ClockSignal,
    Const,
    DomainRenamer,
    Elaboratable,
    Instance,
    Module,
    ResetSignal,
    Signal,
)
from nmigen.build import (
    Attrs,
    Pins,
    PinsN,
    Resource,
    Subsignal,
)

from nmigen_boards.tinyfpga_bx import TinyFPGABXPlatform

from pll import PLL

from regset8bit import RegSet8Bit
from syncgen import SyncGen
from ram import RAM
from mpe import MPE
from test_shifter import Shifter

from interfaces import create_vdc2_interface


class VDC2(Elaboratable):
    """
    This core implements the "top" level module of the VDC-II.
    """

    def __init__(self, platform=""):
        super().__init__()
        create_vdc2_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Register Set (R0-R..)
        regset = m.submodules.regset = RegSet8Bit()

        comb += [
            # Inputs
            regset.adr_i.eq(self.adr_i),
            regset.we_i.eq(self.we_i),
            regset.dat_i.eq(self.dat_i),

            # Outputs
            self.dat_o.eq(regset.dat_o),
        ]

        # Sync Generators

        hsyncgen = m.submodules.hsyncgen = SyncGen()
        vsyncgen = m.submodules.vsyncgen = SyncGen(
            char_total_bits=5,
            adj_bits=5,
        )
        den = Signal(1)

        comb += [
            den.eq(hsyncgen.xden & vsyncgen.xden),

            # Inputs
            hsyncgen.dotclken.eq(1),
            hsyncgen.syncen.eq(hsyncgen.xclken),
            hsyncgen.xct.eq(regset.hct),
            hsyncgen.xt.eq(regset.ht),
            hsyncgen.xsp.eq(regset.hsp),
            hsyncgen.xsw.eq(regset.hsw),
            hsyncgen.xd.eq(regset.hd),
            hsyncgen.xta.eq(0),

            vsyncgen.dotclken.eq(hsyncgen.rastclken & hsyncgen.xclken),
            vsyncgen.syncen.eq(hsyncgen.rastclken & hsyncgen.xclken),
            vsyncgen.xct.eq(regset.vct),
            vsyncgen.xt.eq(regset.vt),
            vsyncgen.xsp.eq(regset.vsp),
            vsyncgen.xsw.eq(regset.vsw),
            vsyncgen.xd.eq(regset.vd),
            vsyncgen.xta.eq(regset.vta),

            # Outputs
            self.hs.eq(hsyncgen.xs ^ regset.hsync_xor),
            self.vs.eq(vsyncgen.xs ^ regset.vsync_xor),
            self.raw_vs.eq(vsyncgen.xs),
        ]

        # Video Block RAM and MPE

        vram = m.submodules.vram = RAM(abus_width=14)
        mpe = m.submodules.mpe = MPE(abus_width=14)
        comb += [
            self.ready_o.eq(mpe.ready),

            regset.cpudatar.eq(mpe.cpudatar),
            regset.incr_updloc.eq(mpe.incr_updloc),
            regset.incr_copysrc.eq(mpe.incr_copysrc),
            regset.decr_bytecnt.eq(mpe.decr_bytecnt),

            mpe.go_wr_updloc.eq(regset.go_wr_updloc),
            mpe.go_rd_cpudatar.eq(regset.go_rd_cpudatar),
            mpe.go_wr_cpudataw.eq(regset.go_wr_cpudataw),
            mpe.go_wr_bytecnt.eq(regset.go_wr_bytecnt),
            mpe.update_location.eq(regset.update_location),
            mpe.cpudataw.eq(regset.cpudataw),
            mpe.block_copy.eq(regset.block_copy),
            mpe.copysrc.eq(regset.copysrc),
            mpe.bytecnt.eq(regset.bytecnt),

            # TODO(sfalvo):
            # Just for now; we need to route this connection to a
            # proper arbiter to support video fetch, etc.
            vram.adr_i.eq(mpe.mem_adr_o),
            vram.we_i.eq(mpe.mem_we_o),
            vram.dat_i.eq(mpe.mem_dat_o),
            mpe.mem_dat_i.eq(vram.dat_o),
            mpe.mem_stall_i.eq(0),
            mpe.mem_ack_i.eq(1),
        ]

        # Shifter
        char_byte = Signal(8)
        attr_byte = Signal(8)
        
        adr = Signal(3)
        swap_state = Signal(1)

        shifter = m.submodules.shifter = Shifter()
        comb += [
            shifter.hclken.eq(hsyncgen.xclken),
            shifter.den.eq(den),
            shifter.hs.eq(hsyncgen.xs),
            shifter.vs.eq(vsyncgen.xs),
            shifter.vden.eq(vsyncgen.xden),

            shifter.hscroll.eq(regset.hscroll),
            shifter.hcd.eq(regset.hcd),
            shifter.hct.eq(regset.hct),
            shifter.fgpen.eq(regset.fgpen),
            shifter.bgpen.eq(regset.bgpen),
            shifter.attr_enable.eq(regset.attr_enable),
            shifter.blink_rate.eq(regset.blink_rate),
            shifter.reverse_screen.eq(regset.reverse_screen),

            # TODO(sfalvo): DEBUG.  Connect to strip buffer later.
            shifter.attr_pen.eq(attr_byte[0:4]),
            shifter.attr_blink.eq(attr_byte[4]),
            shifter.attr_rvs.eq(attr_byte[6]),
            shifter.char_bm.eq(char_byte),

            shifter.done_prefetch.eq(1),

            self.r.eq(shifter.outpen[3]),
            self.g.eq(shifter.outpen[2]),
            self.b.eq(shifter.outpen[1]),
            self.i.eq(shifter.outpen[0]),

            #self.r.eq(shifter.swap_strip),
            #self.g.eq(0),
            #self.b.eq(0),
            #self.i.eq(swap_state),
        ]

        comb += adr.eq(Cat(shifter.padr, swap_state))

        with m.If(shifter.swap_strip):
            sync += swap_state.eq(swap_state ^ 1)

        with m.If(adr == 0):
            comb += [
                char_byte.eq(0xC0),
                attr_byte.eq(0x02),
            ]
        with m.Elif(adr == 1):
            comb += [
                char_byte.eq(0xF0),
                attr_byte.eq(0x04),
            ]
        with m.Elif(adr == 2):
            comb += [
                char_byte.eq(0xFC),
                attr_byte.eq(0x06),
            ]
        with m.Elif(adr == 3):
            comb += [
                char_byte.eq(0xCC),
                attr_byte.eq(0x08),
            ]
        with m.Elif(adr == 4):
            comb += [
                char_byte.eq(0x3F),
                attr_byte.eq(0x0A),
            ]
        with m.Elif(adr == 5):
            comb += [
                char_byte.eq(0x0F),
                attr_byte.eq(0x0C),
            ]
        with m.Elif(adr == 6):
            comb += [
                char_byte.eq(0x03),
                attr_byte.eq(0x0E),
            ]
        with m.Else():
            comb += [
                char_byte.eq(0x33),
                attr_byte.eq(0x01),
            ]

        return m
