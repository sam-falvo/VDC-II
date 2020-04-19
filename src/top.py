import os

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
from sync_generator import SyncGenerator


class VDC_II_Chip(TinyFPGABXPlatform):
    resources = TinyFPGABXPlatform.resources + [
        Resource("host_bus", 0,
            Subsignal("rd", PinsN("A2", dir="i")),
            Subsignal("ad",  Pins("A1", dir="i")),
            Subsignal("cs", PinsN("B1", dir="i")),
            Subsignal("dboe", Pins("C2", dir="o")),
            Subsignal("db", Pins("C1 D2 D1 E2 E1 G2 H1 J1", dir="io")),
            Attrs(IO_STANDARD="LVCMOS"),
        ),
        Resource("video", 0,
            Subsignal("hsync", Pins("H9", dir="o")),
            Subsignal("vsync", Pins("D9", dir="o")),
        ),
    ]

    # This code comes from
    # https://github.com/GlasgowEmbedded/glasgow/blob/master/software/glasgow/platform/ice40.py#L28-L118
    # provided to me by Whitequark as an example of how to instantiate a PLL
    # resource for the iCE40 family of FPGAs.  Many thanks!
    def get_pll(self, pll, simple_feedback=True):
        if not 10e6 <= pll.f_in <= 133e6:
            pll.logger.error("PLL: f_in (%.3f MHz) must be between 10 and 133 MHz",
                             pll.f_in / 1e6)
            raise GatewareBuildError("PLL f_in out of range")


        if not 16e6 <= pll.f_out <= 275e6:
            pll.logger.error("PLL: f_out (%.3f MHz) must be between 16 and 275 MHz",
                             pll.f_out / 1e6)
            raise GatewareBuildError("PLL f_out out of range")


        # The documentation in the iCE40 PLL Usage Guide incorrectly lists the
        # maximum value of DIVF as 63, when it is only limited to 63 when using
        # feedback modes other that SIMPLE.
        if simple_feedback:
            divf_max = 128
        else:
            divf_max = 64


        variants = []
        for divr in range(0, 16):
            f_pfd = pll.f_in / (divr + 1)
            if not 10e6 <= f_pfd <= 133e6:
                continue


            for divf in range(0, divf_max):
                if simple_feedback:
                    f_vco = f_pfd * (divf + 1)
                    if not 533e6 <= f_vco <= 1066e6:
                        continue


                    for divq in range(1, 7):
                        f_out = f_vco * (2 ** -divq)
                        variants.append((divr, divf, divq, f_pfd, f_out))


                else:
                    for divq in range(1, 7):
                        f_vco = f_pfd * (divf + 1) * (2 ** divq)
                        if not 533e6 <= f_vco <= 1066e6:
                            continue


                        f_out = f_vco * (2 ** -divq)
                        variants.append((divr, divf, divq, f_pfd, f_out))


        if not variants:
            pll.logger.error("PLL: f_in (%.3f MHz) to f_out (%.3f) constraints not satisfiable",
                             pll.f_in / 1e6, pll.f_out / 1e6)
            raise GatewareBuildError("PLL f_in/f_out out of range")


        def f_out_diff(variant):
            *_, f_out = variant
            return abs(f_out - pll.f_out)
        divr, divf, divq, f_pfd, f_out = min(variants, key=f_out_diff)


        if f_pfd < 17:
            filter_range = 1
        elif f_pfd < 26:
            filter_range = 2
        elif f_pfd < 44:
            filter_range = 3
        elif f_pfd < 66:
            filter_range = 4
        elif f_pfd < 101:
            filter_range = 5
        else:
            filter_range = 6


        if simple_feedback:
            feedback_path = "SIMPLE"
        else:
            feedback_path = "NON_SIMPLE"


        ppm = abs(pll.f_out - f_out) / pll.f_out * 1e6


        pll.logger.debug("PLL: f_in=%.3f f_out(req)=%.3f f_out(act)=%.3f [MHz] ppm=%d",
                         pll.f_in / 1e6, pll.f_out / 1e6, f_out / 1e6, ppm)
        pll.logger.info("iCE40 PLL: feedback_path=%s divr=%d divf=%d divq=%d filter_range=%d",
                         feedback_path, divr, divf, divq, filter_range)


        return Instance("SB_PLL40_CORE",
            p_FEEDBACK_PATH=feedback_path,
            p_PLLOUT_SELECT="GENCLK",
            p_DIVR=divr,
            p_DIVF=divf,
            p_DIVQ=divq,
            p_FILTER_RANGE=filter_range,
            i_REFERENCECLK=ClockSignal(pll.idomain),
            o_PLLOUTCORE=ClockSignal(pll.odomain),
            i_RESETB=~ResetSignal(pll.idomain),
            i_BYPASS=Const(0),
        )


class Top(Elaboratable):
    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        vga = ClockDomain()
        m.domains.vga = vga

        pll = PLL(
            f_in=16e6,
            f_out=25.145e6,
            odomain="vga",
        )
        m.submodules.pll = pll

        bus = platform.request("host_bus", 0)
        hostbus = m.submodules.hostbus = DomainRenamer("vga")(HostBus())
        comb += [
            # Inputs
            hostbus.a.eq(bus.ad.i),
            hostbus.rd.eq(bus.rd.i),
            hostbus.d.eq(bus.db.i),
            hostbus.cs.eq(bus.cs.i),

            hostbus.ready_i.eq(1),
            hostbus.vblank_i.eq(0),
            hostbus.lp_i.eq(0),

            # Outputs
            bus.db.o.eq(hostbus.q),
            bus.db.oe.eq(hostbus.qoe),
            bus.dboe.o.eq(hostbus.qoe),
        ]

        regset = m.submodules.regset = DomainRenamer("vga")(RegSet8Bit())
        comb += [
            # Inputs
            regset.adr_i.eq(hostbus.adr_o),
            regset.we_i.eq(hostbus.we_o),
            regset.dat_i.eq(hostbus.dat_o),

            # Outputs
            hostbus.dat_i.eq(regset.dat_o),
        ]

        hsync = m.submodules.hsync = DomainRenamer("vga")(SyncGenerator())
        video = platform.request("video", 0)
        comb += [
            # Inputs
            hsync.total.eq(regset.ht),
            hsync.sync_pos.eq(regset.hp),
            hsync.sync_width.eq(regset.hw),
            hsync.char_total.eq(regset.cth),

            # Outputs
            video.hsync.o.eq(hsync.xsync ^ regset.hsync_xor),
            video.vsync.o.eq(hsync.xsync), # DEBUG
        ]

        return m


if __name__ == '__main__':
    do_program = not(not(os.getenv("DO_PROGRAM", None)))
    VDC_II_Chip().build(Top(), do_program=do_program)
