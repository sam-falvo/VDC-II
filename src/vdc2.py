from nmigen import (
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

from hostbus import HostBus
from regset8bit import RegSet8Bit
from syncgen import SyncGen

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

        comb += [
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
            self.r.eq(hsyncgen.rastclken),
            self.g.eq(vsyncgen.xclken),
            self.b.eq(0),
            self.i.eq(hsyncgen.xden & vsyncgen.xden),
        ]

        return m
