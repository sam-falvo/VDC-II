from nmigen import (
    Elaboratable,
    Module,
    Signal,
)

from interfaces import create_blockram_arbiter_interface


class BlockRamArbiter(Elaboratable):
    def __init__(self, platform=None):
        create_blockram_arbiter_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        grant_mpe = Signal(1)
        grant_vfe = Signal(1)

        comb += [
            grant_vfe.eq(self.vfe_cyc_i),
            grant_mpe.eq(self.mpe_cyc_i & ~grant_vfe),
        ]

        with m.If(grant_vfe):
            comb += [
                self.adr_o.eq(self.vfe_adr_i),
                self.we_o.eq(self.vfe_we_i),
                self.dat_o.eq(self.vfe_dat_i),

                self.mpe_stall_o.eq(1),
            ]
        with m.Elif(grant_mpe):
            comb += [
                self.adr_o.eq(self.mpe_adr_i),
                self.we_o.eq(self.mpe_we_i),
                self.dat_o.eq(self.mpe_dat_i),

                self.vfe_stall_o.eq(1),
            ]

        sync += [
            self.vfe_ack_o.eq(grant_vfe & self.vfe_stb_i),
            self.mpe_ack_o.eq(grant_mpe & self.mpe_stb_i),
        ]

        with m.If(self.vfe_ack_o):
            comb += self.vfe_dat_o.eq(self.dat_i)
        with m.Elif(self.mpe_ack_o):
            comb += self.mpe_dat_o.eq(self.dat_i)

        return m


