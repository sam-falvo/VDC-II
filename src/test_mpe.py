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


from interfaces import create_mpe_interface

from mpe import MPE


class MPEFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_mpe_interface(self, platform="formal")

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

        dut = MPE(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.ready.eq(dut.ready),
            self.cpudatar.eq(dut.cpudatar),
            self.incr_updloc.eq(dut.incr_updloc),
            self.incr_copysrc.eq(dut.incr_copysrc),
            self.decr_bytecnt.eq(dut.decr_bytecnt),

            self.mem_cyc_o.eq(dut.mem_cyc_o),
            self.mem_stb_o.eq(dut.mem_stb_o),
            self.mem_adr_o.eq(dut.mem_adr_o),
            self.mem_we_o.eq(dut.mem_we_o),
            self.mem_dat_o.eq(dut.mem_dat_o),

            self.fv_prefetch_0.eq(dut.fv_prefetch_0),
            self.fv_prefetch_1.eq(dut.fv_prefetch_1),
            self.fv_store_0.eq(dut.fv_store_0),
            self.fv_store_1.eq(dut.fv_store_1),
            self.fv_block_0.eq(dut.fv_block_0),
            self.fv_block_1.eq(dut.fv_block_1),
            self.fv_block_2.eq(dut.fv_block_2),
            self.fv_block_3.eq(dut.fv_block_3),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.mem_stall_i.eq(self.mem_stall_i),
            dut.mem_ack_i.eq(self.mem_ack_i),
            dut.mem_dat_i.eq(self.mem_dat_i),

            dut.go_wr_updloc.eq(self.go_wr_updloc),
            dut.go_rd_cpudatar.eq(self.go_rd_cpudatar),
            dut.go_wr_cpudataw.eq(self.go_wr_cpudataw),
            dut.go_wr_bytecnt.eq(self.go_wr_bytecnt),
            dut.update_location.eq(self.update_location),
            dut.cpudataw.eq(self.cpudataw),
            dut.block_copy.eq(self.block_copy),
            dut.copysrc.eq(self.copysrc),
            dut.bytecnt.eq(self.bytecnt),
        ]

        # Establish some interface assumptions.
        #
        # The "go_*" signals are triggered by accesses to the register
        # set, by some means.  Correspondingly, only one will fire at any
        # given time.

        with m.If(self.go_wr_updloc):
            comb += [
                Assume(~self.go_rd_cpudatar),
                Assume(~self.go_wr_cpudataw),
                Assume(~self.go_wr_bytecnt),
            ]

        with m.If(self.go_rd_cpudatar):
            comb += [
                Assume(~self.go_wr_updloc),
                Assume(~self.go_wr_cpudataw),
                Assume(~self.go_wr_bytecnt),
            ]

        with m.If(self.go_wr_cpudataw):
            comb += [
                Assume(~self.go_wr_updloc),
                Assume(~self.go_rd_cpudatar),
                Assume(~self.go_wr_bytecnt),
            ]

        with m.If(self.go_wr_bytecnt):
            comb += [
                Assume(~self.go_wr_updloc),
                Assume(~self.go_rd_cpudatar),
                Assume(~self.go_wr_cpudataw),
            ]

        # When the host processor writes to the Update Location registers
        # (either R18 or R19), we want to commence a prefetch operation
        # that lands data into the CpuReadR register, which the host CPU
        # can later read.
        #
        # The bus interface in this module uses Wishbone B4 pipelined
        # procedures, as it is designed to couple with synchronous memories.
        # This implies that the ACK for the cycle's STB must come on a
        # subsequent clock cycle.  Single-cycle STB/ACK handshakes are not
        # supported, and will lock up the bus.

        ## Any write to R18 or R19 will trigger a prefetch operation.
        ## The register file is responsible for asserting go_wr_updloc
        ## when a write to these registers happens.
        with m.If(past_valid & Past(self.ready) & Past(self.go_wr_updloc)):
            sync += [
                Assert(~self.ready),
                Assert(self.fv_prefetch_0),
                Assert(~self.fv_prefetch_1),

                Assert(self.mem_cyc_o),
                Assert(self.mem_stb_o),
                Assert(self.mem_adr_o == self.update_location[0:len(self.mem_adr_o)]),
                Assert(~self.mem_we_o),
            ]

        with m.If(past_valid & ~Past(self.ready) & Past(self.fv_prefetch_0)):
            ## If the Wishbone interconnect is not ready for the access cycle
            ## (for example, if video refresh is currently in progress), then
            ## we must wait for when it is ready.
            with m.If(Past(self.mem_stall_i)):
                sync += [
                    Assert(~self.ready),
                    Assert(self.fv_prefetch_0),
                    Assert(~self.fv_prefetch_1),

                    Assert(self.mem_cyc_o),
                    Assert(self.mem_stb_o),
                    Assert(self.mem_adr_o == self.update_location[0:len(self.mem_adr_o)]),
                    Assert(~self.mem_we_o),
                ]

            ## Otherwise, once we confirm cycle hand-off has occurred, we must
            ## then wait for acknowledgement from the interconnect (which will
            ## also deliver the requested data).
            with m.Else():
                sync += [
                    Assert(~self.ready),
                    Assert(~self.fv_prefetch_0),
                    Assert(self.fv_prefetch_1),

                    Assert(self.mem_cyc_o),
                    Assert(~self.mem_stb_o),
                ]

        ## After receiving acknowledgement and data, update the CpuDataR register
        ## and return to being idle.
        with m.If(past_valid & ~Past(self.ready) & Past(self.fv_prefetch_1)):
            with m.If(~Past(self.mem_ack_i)):
                sync += [
                    Assert(~self.ready),
                    Assert(~self.fv_prefetch_0),
                    Assert(self.fv_prefetch_1),

                    Assert(self.mem_cyc_o),
                    Assert(~self.mem_stb_o),
                ]
            with m.Else():
                sync += [
                    Assert(self.ready),
                    Assert(~self.fv_prefetch_0),
                    Assert(~self.fv_prefetch_1),

                    Assert(~self.mem_cyc_o),
                    Assert(~self.mem_stb_o),

                    Assert(self.cpudatar == Past(self.mem_dat_i)),
                ]

        # Any read from R31 ("CPU Data") will auto-increment the update
        # location pointer, thus requiring another prefetch operation.
        with m.If(past_valid & Past(self.ready) & Past(self.go_rd_cpudatar)):
            sync += [
                Assert(~self.ready),
                Assert(self.fv_prefetch_0),
            ]

        # Any write to R31 will *not* auto-increment the update location
        # pointer, allowing the MPE the opportunity to use its current value
        # for writing data to video memory.  However, the MPE is responsible
        # for incrementing the pointer and commencing another prefetch
        # operation.
        with m.If(past_valid & Past(self.ready) & Past(self.go_wr_cpudataw)):
            sync += [
                Assert(~self.ready),
                Assert(self.fv_store_0),
            ]

        ## When writing a value to R31, the MPE must commence a write cycle
        ## to video RAM.  We must wait for any stalls.
        with m.If(self.fv_store_0):
            comb += [
                Assert(self.mem_cyc_o),
                Assert(self.mem_stb_o),
                Assert(self.mem_adr_o == self.update_location[0:len(self.mem_adr_o)]),
                Assert(self.mem_we_o),
                Assert(self.mem_dat_o == self.cpudataw),
            ]

        with m.If(past_valid & Past(self.fv_store_0)):
            with m.If(Past(self.mem_stall_i)):
                sync += Assert(self.fv_store_0)
            with m.Else():
                sync += Assert(self.fv_store_1)

        ## When receiving a store acknowledgement, we must remember to increment
        ## the update location, so that we prefetch from the next address.
        with m.If(self.fv_store_1):
            comb += [
                Assert(self.mem_cyc_o),
                Assert(~self.mem_stb_o),
            ]

        with m.If(past_valid & Past(self.fv_store_1)):
            with m.If(~Past(self.mem_ack_i)):
                sync += [
                    Assert(self.fv_store_1),
                    Assert(~Past(self.incr_updloc)),
                ]
            with m.Else():
                sync += [
                    Assert(self.fv_prefetch_0),
                    Assert(Past(self.incr_updloc)),
                ]

        # When the CPU writes a value into the Byte Count register (R30),
        # we must commence a block copy or block write operation, depending
        # upon the state of the Block Copy flag bit (R24, bit 7).
        #
        # In this version of the MPE, both block write and block copy use
        # the same basic algorithm.  Block copy mode takes four cycles to
        # copy one byte of data.  Block write takes three.
        #
        # The following table illustrates what happens each iteration of the
        # write-loop.
        #
        # Cycle  Copy Task                          Write Task
        #   0    Drive source address               Copy cpudataw to cpudatar
        #   1    Wait for data                      (skipped)
        #   2    Drive destination address, data    Drive destination address, data
        #   3    Wait for ack.  Decrement bytecnt.  Wait for ack.  Decrement bytecnt.
        #
        # This loop iterates for as long as Byte Count register is non-zero.
        with m.If(past_valid & Past(self.ready) & Past(self.go_wr_bytecnt)):
            sync += [
                Assert(self.fv_block_0),
                Assert(~self.ready),
            ]

        ## If we're performing a block copy...
        with m.If(self.fv_block_0 & self.block_copy):
            ### and we haven't reached the end of the loop yet,
            ### the first cycle must drive the source address onto the memory bus.
            with m.If(self.bytecnt != 0):
                comb += [
                    Assert(self.mem_cyc_o),
                    Assert(self.mem_stb_o),
                    Assert(self.mem_adr_o == self.copysrc[0:len(self.mem_adr_o)]),
                    Assert(~self.mem_we_o),
                ]
            with m.Else():
                comb += Assert(~self.mem_cyc_o)

        with m.If(past_valid & Past(self.fv_block_0)):
            ### For Block Copy operations...
            with m.If(Past(self.block_copy)):
                ### Wait for bus stalls when driving the source address.
                with m.If(Past(self.bytecnt) != 0):
                    with m.If(Past(self.mem_stall_i)):
                        sync += Assert(self.fv_block_0)
                    with m.Else():
                        sync += Assert(self.fv_block_1)

                ### When we reach the end of the copy loop, which could have
                ### altered the update location pointer, we drop into the prefetch
                ### state so that we reset the CPU Data register with an up-to-date
                ### view of video memory.
                with m.Else():
                    sync += Assert(self.fv_prefetch_0)

            ### For Block Write operations, we just use a constant byte value
            ### set by the programmer by storing a byte to R31.  As usual, if/when
            ### we reach the end, begin a prefetch operation.
            with m.Else():
                with m.If(Past(self.bytecnt) != 0):
                    sync += [
                        Assert(self.cpudatar == Past(self.cpudataw)),
                        Assert(self.fv_block_2),
                    ]
                with m.Else():
                    sync += Assert(self.fv_prefetch_0)

        ### State 1 is reachable only if we're doing a block copy.
        ### Here, we wait for acknowledgement and source data.
        with m.If(self.fv_block_1):
            comb += [
                Assert(self.mem_cyc_o),
                Assert(~self.mem_stb_o),
            ]

        with m.If(past_valid & Past(self.fv_block_1)):
            with m.If(Past(self.mem_ack_i)):
                sync += [
                    Assert(self.fv_block_2),
                    Assert(self.cpudatar == Past(self.mem_dat_i)),
                ]

        ### State 2 always appears; it is what stores the byte into video memory.
        with m.If(self.fv_block_2):
            comb += [
                Assert(self.mem_cyc_o),
                Assert(self.mem_stb_o),
                Assert(self.mem_adr_o == self.update_location[0:len(self.mem_adr_o)]),
                Assert(self.mem_we_o),
                Assert(self.mem_dat_o == self.cpudatar),
            ]

        with m.If(past_valid & Past(self.fv_block_2)):
            with m.If(Past(self.mem_stall_i)):
                sync += Assert(self.fv_block_2)
            with m.Else():
                sync += Assert(self.fv_block_3)

        ### State3 always appears; this concludes the write access.  It is also
        ### responsible for incrementing the pointer registers as well.
        with m.If(self.fv_block_3):
            comb += [
                Assert(self.mem_cyc_o),
                Assert(~self.mem_stb_o),
            ]

            with m.If(self.mem_ack_i):
                comb += [
                    Assert(self.incr_updloc),
                    Assert(self.decr_bytecnt),
                ]
                with m.If(self.block_copy):
                    comb += Assert(self.incr_copysrc)
                with m.Else():
                    comb += Assert(~self.incr_copysrc)
            with m.Else():
                comb += [
                    Assert(~self.incr_updloc),
                    Assert(~self.incr_copysrc),
                    Assert(~self.decr_bytecnt),
                ]

        with m.If(past_valid & Past(self.fv_block_3)):
            with m.If(Past(self.mem_ack_i)):
                sync += Assert(self.fv_block_0)

        return m


class MPETestCase(FHDLTestCase):
    def test_mpe(self):
        self.assertFormal(MPEFormal(), mode='bmc', depth=100)
        self.assertFormal(MPEFormal(), mode='prove', depth=100)
