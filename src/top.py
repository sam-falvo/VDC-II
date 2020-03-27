from nmigen import (
    Elaboratable,
    Module,
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

from hostbus import HostBus
from regset8bit import RegSet8Bit
from hsync import HSync


class VDC_II_Chip(TinyFPGABXPlatform):
    resources = TinyFPGABXPlatform.resources + [
        Resource("host_bus", 0,
            Subsignal("db", Pins("A2 A1 B1 C2 C1 D2 D1 E2", dir="io")),
            Subsignal("ad",  Pins("E1", dir="i")),
            Subsignal("rd", PinsN("G2", dir="i")),
            Subsignal("cs", PinsN("H1", dir="i")),
            Attrs(IO_STANDARD="LVCMOS"),
        ),
        Resource("video", 0,
            Subsignal("hsync", Pins("H9", dir="o")),
            Subsignal("vsync", Pins("D9", dir="o")),
        ),
    ]


class Top(Elaboratable):
    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        bus = platform.request("host_bus", 0)
        hostbus = m.submodules.hostbus = HostBus()
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
        ]

        regset = m.submodules.regset = RegSet8Bit()
        comb += [
            # Inputs
            regset.adr_i.eq(hostbus.adr_o),
            regset.we_i.eq(hostbus.we_o),
            regset.dat_i.eq(hostbus.dat_o),

            # Outputs
            hostbus.dat_i.eq(regset.dat_o),
        ]

        hsync = m.submodules.hsync = HSync()
        video = platform.request("video", 0)
        comb += [
            # Inputs
            hsync.htotal.eq(regset.ht),
            hsync.hsync_pos.eq(regset.hp),
            hsync.hsync_width.eq(regset.hw),
            hsync.char_total.eq(regset.cth),

            # Outputs
            video.hsync.o.eq(hsync.hsync ^ regset.hsync_xor),
            video.vsync.o.eq(hsync.hsync), # DEBUG
        ]


        return m


if __name__ == '__main__':
    VDC_II_Chip().build(Top(), do_program=False)
