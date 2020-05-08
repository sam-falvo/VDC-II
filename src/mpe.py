from nmigen.test.utils import FHDLTestCase
from nmigen import (
    Elaboratable,
    Module,
    Signal,
)


from interfaces import create_mpe_interface


class MPE(Elaboratable):
    def __init__(self, platform='', abus_width=14):
        super().__init__()
        create_mpe_interface(self, platform=platform, abus_width=abus_width)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        comb += [
            self.mem_cyc_o.eq(0),
            self.mem_stb_o.eq(0),
            self.mem_adr_o.eq(0),
            self.mem_we_o.eq(0),
            self.incr_updloc.eq(0),
            self.incr_copysrc.eq(0),
            self.decr_bytecnt.eq(0),
        ]

        with m.FSM() as fsm:
            comb += self.ready.eq(fsm.ongoing("IDLE"))
            with m.State("IDLE"):
                with m.If(self.go_wr_updloc):
                    m.next = "PREFETCH_0"
                with m.If(self.go_rd_cpudatar):
                    m.next = "PREFETCH_0"
                with m.If(self.go_wr_cpudataw):
                    m.next = "STORE_0"
                with m.If(self.go_wr_bytecnt):
                    m.next = "BLOCK_0"

            with m.State("PREFETCH_0"):
                comb += [
                    self.mem_cyc_o.eq(1),
                    self.mem_stb_o.eq(1),
                    self.mem_adr_o.eq(self.update_location),
                ]
                with m.If(~self.mem_stall_i):
                    m.next = "PREFETCH_1"

            with m.State("PREFETCH_1"):
                comb += [
                    self.mem_cyc_o.eq(1),
                ]
                with m.If(self.mem_ack_i):
                    m.next = "IDLE"
                    sync += self.cpudatar.eq(self.mem_dat_i)

            with m.State("STORE_0"):
                comb += [
                    self.mem_cyc_o.eq(1),
                    self.mem_stb_o.eq(1),
                    self.mem_adr_o.eq(self.update_location),
                    self.mem_we_o.eq(1),
                    self.mem_dat_o.eq(self.cpudataw),
                ]
                with m.If(~self.mem_stall_i):
                    m.next = "STORE_1"

            with m.State("STORE_1"):
                comb += [
                    self.mem_cyc_o.eq(1),
                ]
                with m.If(self.mem_ack_i):
                    comb += self.incr_updloc.eq(1)
                    m.next = "PREFETCH_0"

            with m.State("BLOCK_0"):
                with m.If(self.bytecnt != 0):
                    with m.If(self.block_copy):
                        comb += [
                            self.mem_cyc_o.eq(1),
                            self.mem_stb_o.eq(1),
                            self.mem_adr_o.eq(self.copysrc),
                        ]
                        with m.If(~self.mem_stall_i):
                            m.next = "BLOCK_1"
                    with m.Else():
                        sync += self.cpudatar.eq(self.cpudataw)
                        m.next = "BLOCK_2"
                with m.Else():
                    m.next = "PREFETCH_0"

            with m.State("BLOCK_1"):
                comb += [
                    self.mem_cyc_o.eq(1),
                ]
                with m.If(self.mem_ack_i):
                    sync += self.cpudatar.eq(self.mem_dat_i)
                    m.next = "BLOCK_2"

            with m.State("BLOCK_2"):
                comb += [
                    self.mem_cyc_o.eq(1),
                    self.mem_stb_o.eq(1),
                    self.mem_adr_o.eq(self.update_location),
                    self.mem_we_o.eq(1),
                    self.mem_dat_o.eq(self.cpudatar),
                ]

                with m.If(~self.mem_stall_i):
                    m.next = "BLOCK_3"

            with m.State("BLOCK_3"):
                comb += self.mem_cyc_o.eq(1)

                with m.If(self.mem_ack_i):
                    comb += [
                        self.incr_updloc.eq(1),
                        self.decr_bytecnt.eq(1),
                    ]
                    with m.If(self.block_copy):
                        comb += self.incr_copysrc.eq(1)
                    m.next = "BLOCK_0"

            if platform == 'formal':
                comb += [
                    self.fv_prefetch_0.eq(fsm.ongoing("PREFETCH_0")),
                    self.fv_prefetch_1.eq(fsm.ongoing("PREFETCH_1")),
                    self.fv_store_0.eq(fsm.ongoing("STORE_0")),
                    self.fv_store_1.eq(fsm.ongoing("STORE_1")),
                    self.fv_block_0.eq(fsm.ongoing("BLOCK_0")),
                    self.fv_block_1.eq(fsm.ongoing("BLOCK_1")),
                    self.fv_block_2.eq(fsm.ongoing("BLOCK_2")),
                    self.fv_block_3.eq(fsm.ongoing("BLOCK_3")),
                ]

        return m
