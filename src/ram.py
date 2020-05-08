from nmigen import (
    Elaboratable,
    Module,
    Signal,
    Memory,
)


class RAM(Elaboratable):
    """
    This core should map to one or more block RAM resources.
    """

    def __init__(self, platform="", abus_width=14):
        super().__init__()
        self.adr_i = Signal(abus_width)
        self.dat_i = Signal(8)
        self.we_i = Signal(1)
        self.dat_o = Signal(8)

        self.mem = Memory(width=8, depth=(1<<abus_width))

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb

        m.submodules.rdport = rdport = self.mem.read_port()
        m.submodules.wrport = wrport = self.mem.write_port()
        comb += [
            rdport.addr.eq(self.adr_i),
            self.dat_o.eq(rdport.data),

            wrport.addr.eq(self.adr_i),
            wrport.data.eq(self.dat_i),
            wrport.en.eq(self.we_i),
        ]

        return m
