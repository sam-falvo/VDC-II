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
from shifter import Shifter
from video_fetch import VideoFetch
from blockram_arbiter import BlockRamArbiter
from strip_buffer import StripBuffer

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

        regset = m.submodules.regset = RegSet8Bit()
        hsyncgen = m.submodules.hsyncgen = SyncGen()
        vsyncgen = m.submodules.vsyncgen = SyncGen(
            char_total_bits=5,
            adj_bits=5,
        )
        shifter = m.submodules.shifter = Shifter()
        vfe = m.submodules.vfe = VideoFetch()
        mpe = m.submodules.mpe = MPE(abus_width=14)
        vram = m.submodules.vram = RAM(abus_width=14)
        arb = m.submodules.arb = BlockRamArbiter()
        stripbuf = m.submodules.stripbuf = StripBuffer()

        # Register Set (R0-R..)

        comb += [
            # Inputs
            regset.adr_i.eq(self.adr_i),
            regset.we_i.eq(self.we_i),
            regset.dat_i.eq(self.dat_i),

            # Outputs
            self.dat_o.eq(regset.dat_o),
        ]

        # Sync Generators

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

        ## VFE

        comb += [
            vfe.atrptr.eq(shifter.atrptr),
            vfe.chrptr.eq(shifter.chrptr),
            vfe.go_i.eq(shifter.go_prefetch),
            vfe.ldptr.eq(shifter.go_ldptr),
            vfe.ra.eq(shifter.ra),

            vfe.attr_enable.eq(regset.attr_enable),
            vfe.bitmap_mode.eq(regset.bitmap_mode),
            vfe.fontbase.eq(regset.fontbase),
            vfe.tallfont.eq(regset.tallfont),

            vfe.ack_i.eq(arb.vfe_ack_o),
            vfe.stall_i.eq(arb.vfe_stall_o),
            arb.vfe_adr_i.eq(vfe.adr_o),
            arb.vfe_cyc_i.eq(vfe.cyc_o),
            arb.vfe_dat_i.eq(0),
            arb.vfe_stb_i.eq(vfe.stb_o),
            arb.vfe_we_i.eq(0),

            vfe.charcode.eq(Cat(stripbuf.pair[0:8], stripbuf.pair[15])),
            stripbuf.awe.eq(vfe.awe),
            stripbuf.cwe.eq(vfe.cwe),
            stripbuf.padr.eq(vfe.padr),
            stripbuf.wadr.eq(vfe.wadr),
            stripbuf.dat_i.eq(arb.vfe_dat_o),
        ]

        ## MPE

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

            arb.mpe_cyc_i.eq(mpe.mem_cyc_o),
            arb.mpe_stb_i.eq(mpe.mem_stb_o),
            arb.mpe_adr_i.eq(mpe.mem_adr_o),
            arb.mpe_we_i.eq(mpe.mem_we_o),
            arb.mpe_dat_i.eq(mpe.mem_dat_o),
            mpe.mem_stall_i.eq(arb.mpe_stall_o),
            mpe.mem_ack_i.eq(arb.mpe_ack_o),
            mpe.mem_dat_i.eq(arb.mpe_dat_o),
        ]

        # Block RAM and arbiter

        comb += [
            vram.adr_i.eq(arb.adr_o),
            vram.we_i.eq(arb.we_o),
            vram.dat_i.eq(arb.dat_o),
            arb.dat_i.eq(vram.dat_o),
        ]

        # Shifter

        comb += [
            shifter.hclken.eq(hsyncgen.xclken),
            shifter.den.eq(den),
            shifter.hs.eq(hsyncgen.xs),
            shifter.vs.eq(vsyncgen.xs),
            shifter.vden.eq(vsyncgen.xden),

            shifter.hscroll.eq(regset.hscroll),
            shifter.vscroll.eq(regset.vscroll),
            shifter.hcd.eq(regset.hcd),
            shifter.hct.eq(regset.hct),
            shifter.vct.eq(regset.vct),
            shifter.fgpen.eq(regset.fgpen),
            shifter.bgpen.eq(regset.bgpen),
            shifter.attr_enable.eq(regset.attr_enable),
            shifter.blink_rate.eq(regset.blink_rate),
            shifter.reverse_screen.eq(regset.reverse_screen),
            shifter.bitmap_mode.eq(regset.bitmap_mode),
            shifter.atrbase.eq(regset.atrbase),
            shifter.chrbase.eq(regset.chrbase),

            shifter.attr_pen.eq(stripbuf.sh_pair[8:12]),
            shifter.attr_blink.eq(stripbuf.sh_pair[12]),
            #shifter.attr_underline.eq(stripbuf.sh_pair[13]),
            shifter.attr_rvs.eq(stripbuf.sh_pair[14]),
            shifter.char_bm.eq(stripbuf.sh_pair[0:8]),
            stripbuf.sh_padr.eq(shifter.padr),
            stripbuf.swap.eq(shifter.swap_strip),

            shifter.done_prefetch.eq(vfe.done_o),

            #self.r.eq(stripbuf.sh_pair[3]),
            #self.g.eq(stripbuf.sh_pair[2]),
            #self.b.eq(stripbuf.sh_padr[1]),
            #self.i.eq(stripbuf.sh_padr[0]),

            self.r.eq(shifter.outpen[3]),
            self.g.eq(shifter.outpen[2]),
            self.b.eq(shifter.outpen[1]),
            self.i.eq(shifter.outpen[0]),
        ]

        return m
