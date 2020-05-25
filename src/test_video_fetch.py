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

from interfaces import create_video_fetch_interface

from video_fetch import VideoFetch


class VideoFetchFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_video_fetch_interface(self, platform="formal")

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

        dut = VideoFetch(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.adr_o.eq(dut.adr_o),
            self.cyc_o.eq(dut.cyc_o),
            self.stb_o.eq(dut.stb_o),

            self.padr.eq(dut.padr),
            self.wadr.eq(dut.wadr),
            self.awe.eq(dut.awe),
            self.cwe.eq(dut.cwe),

            self.fv_ag_idle.eq(dut.fv_ag_idle),
            self.fv_ag_a1.eq(dut.fv_ag_a1),
            self.fv_ag_a2.eq(dut.fv_ag_a2),
            self.fv_ag_a3.eq(dut.fv_ag_a3),
            self.fv_ag_a4.eq(dut.fv_ag_a4),
            self.fv_ag_c1.eq(dut.fv_ag_c1),
            self.fv_ag_c2.eq(dut.fv_ag_c2),
            self.fv_ag_c3.eq(dut.fv_ag_c3),
            self.fv_ag_c4.eq(dut.fv_ag_c4),
            self.fv_ag_f1.eq(dut.fv_ag_f1),
            self.fv_ag_f2.eq(dut.fv_ag_f2),
            self.fv_ag_f3.eq(dut.fv_ag_f3),
            self.fv_ag_f4.eq(dut.fv_ag_f4),
            self.fv_ag_go_font.eq(dut.fv_ag_go_font),
            self.fv_atrptr.eq(dut.fv_atrptr),
            self.fv_chrptr.eq(dut.fv_chrptr),
            self.fv_dr_idle.eq(dut.fv_dr_idle),
            self.fv_dr_a1.eq(dut.fv_dr_a1),
            self.fv_dr_a2.eq(dut.fv_dr_a2),
            self.fv_dr_a3.eq(dut.fv_dr_a3),
            self.fv_dr_a4.eq(dut.fv_dr_a4),
            self.fv_dr_c1.eq(dut.fv_dr_c1),
            self.fv_dr_c2.eq(dut.fv_dr_c2),
            self.fv_dr_c3.eq(dut.fv_dr_c3),
            self.fv_dr_c4.eq(dut.fv_dr_c4),
            self.fv_dr_f1.eq(dut.fv_dr_f1),
            self.fv_dr_f2.eq(dut.fv_dr_f2),
            self.fv_dr_f3.eq(dut.fv_dr_f3),
            self.fv_dr_f4.eq(dut.fv_dr_f4),
            self.fv_bitmap_mode.eq(dut.fv_bitmap_mode),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.go_i.eq(self.go_i),
            dut.attr_enable.eq(self.attr_enable),
            dut.bitmap_mode.eq(self.bitmap_mode),
            dut.tallfont.eq(self.tallfont),
            dut.fontbase.eq(self.fontbase),
            dut.ra.eq(self.ra),
            dut.charcode.eq(self.charcode),
            dut.tallfont.eq(self.tallfont),
            dut.fontbase.eq(self.fontbase),
            dut.ldptr.eq(self.ldptr),
            dut.atrptr.eq(self.atrptr),
            dut.chrptr.eq(self.chrptr),

            dut.stall_i.eq(self.stall_i),
            dut.ack_i.eq(self.ack_i),
        ]

        # There is a known bug with the implementation of my Wishbone master:
        # you can use stall_i to slow down the address generator while stuffing
        # data down the data receiver's throat at maximum speed.  Since more
        # acknowledgements arrive than address strobes generated, the data
        # receiver will go idle before the address generator, resulting in a
        # protocol violation that has undefined behavior (this case is simply
        # not covered in the Wishbone B4 specifications).
        #
        # The only work-around for this situation is to Don't Do That.

        with m.If(~self.fv_ag_idle):
            comb += Assume(~self.fv_dr_idle)

        with m.If(~self.cyc_o):
            comb += [
                Assert(self.fv_ag_idle),
                Assert(self.fv_dr_idle),
            ]

        # Video Fetch Unit sits idle until told to do something.  go_i triggers a
        # video fetch sequence.  attr_enable and bitmap_mode parameterize the
        # sequence taken.
        #
        # Although the address generator (ag_xxx) and data receiver (dr_xxx) logic
        # runs asynchronously to each other, they both *start* at the same time.

        with m.If(past_valid & Past(self.fv_ag_idle) & Past(self.fv_dr_idle)):
            sync += [
                Assert(~Past(self.stb_o)),
                Assert(~Past(self.cyc_o)),
            ]

            with m.If(~Past(self.go_i)):
                sync += [
                    Assert(self.fv_ag_idle),
                    Assert(self.fv_dr_idle),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
            with m.If(Past(self.go_i)):
                sync += Assert(self.fv_bitmap_mode == Past(self.bitmap_mode))
                with m.If(~Past(self.attr_enable)):
                    sync += [
                        Assert(self.fv_ag_c1),
                        Assert(self.fv_dr_c1),
                    ]
                with m.Else():
                    sync += [
                        Assert(self.fv_ag_a1),
                        Assert(self.fv_dr_a1),
                    ]

                with m.If(Past(self.ldptr)):
                    sync += [
                        Assert(self.fv_atrptr == Past(self.atrptr)),
                        Assert(self.fv_chrptr == Past(self.chrptr)),
                    ]
                with m.Else():
                    sync += [
                        Assert(Stable(self.fv_atrptr)),
                        Assert(Stable(self.fv_chrptr)),
                    ]

        ## Ignore go_i unless both FSMs are idle.  That way we don't interrupt a
        ## memory fetch cycle in progress.
        with m.If(past_valid & Past(self.fv_ag_idle) & ~Past(self.fv_dr_idle) & Past(self.go_i)):
            sync += Assert(self.fv_ag_idle)

        with m.If(past_valid & ~Past(self.fv_ag_idle) & Past(self.fv_dr_idle) & Past(self.go_i)):
            sync += Assert(self.fv_dr_idle)

        # If we're fetching attribute and character code bytes, then we need to
        # sequence through them as quickly as the Wishbone interface will let
        # us.

        with m.If(past_valid):
            with m.If(Past(self.fv_ag_a1)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_atrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_a2),
                        Assert(self.fv_atrptr == (Past(self.fv_atrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_chrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_a1)

            with m.If(Past(self.fv_ag_a2)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_atrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_a3),
                        Assert(self.fv_atrptr == (Past(self.fv_atrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_chrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_a2)

            with m.If(Past(self.fv_ag_a3)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_atrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_a4),
                        Assert(self.fv_atrptr == (Past(self.fv_atrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_chrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_a3)

            with m.If(Past(self.fv_ag_a4)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_atrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_c1),
                        Assert(self.fv_atrptr == (Past(self.fv_atrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_chrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_a4)

            with m.If(Past(self.fv_ag_c1)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_c2),
                        Assert(self.fv_chrptr == (Past(self.fv_chrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_atrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_c1)

            with m.If(Past(self.fv_ag_c2)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_c3),
                        Assert(self.fv_chrptr == (Past(self.fv_chrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_atrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_c2)

            with m.If(Past(self.fv_ag_c3)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_ag_c4),
                        Assert(self.fv_chrptr == (Past(self.fv_chrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_atrptr)),
                    ]
                with m.Else():
                    sync += Assert(self.fv_ag_c3)

            with m.If(Past(self.fv_ag_c4)):
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.cyc_o)),
                    Assert(Past(self.adr_o) == Past(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += [
                        Assert(self.fv_chrptr == (Past(self.fv_chrptr) + 1)[0:16]),
                        Assert(Stable(self.fv_atrptr)),
                    ]
                    with m.If(~Past(self.fv_bitmap_mode)):
                        sync += Assert(self.fv_ag_f1)
                    with m.Else():
                        sync += Assert(self.fv_ag_idle)
                with m.Else():
                    sync += Assert(self.fv_ag_c4)

            old_ra = Signal(len(self.ra))
            old_fontbase = Signal(len(self.fontbase))

            sync += [
                old_ra.eq(self.ra),
                old_fontbase.eq(self.fontbase),
            ]

            with m.If(Past(self.fv_ag_f1)):
                with m.If(~Past(self.tallfont)):
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:4], Past(self.charcode), old_fontbase[0:3])
                    )
                with m.Else():
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:5], Past(self.charcode), old_fontbase[1:3])
                    )
                sync += [
                    Assert(Past(self.padr) == 0),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
                # We don't want to issue an address to fetch until we know that all attributes and
                # characters have been fetched.  For this reason, we wait until ag_go_font is asserted
                # by the data receiver before commencing memory operations.
                with m.If(~Past(self.fv_ag_go_font)):
                    sync += [
                        Assert(~Past(self.stb_o)),
                        Assert(self.fv_ag_f1),
                    ]
                with m.Else():
                    sync += Assert(Past(self.stb_o))
                    with m.If(~Past(self.stall_i)):
                        sync += Assert(self.fv_ag_f2)
                    with m.Else():
                        sync += Assert(self.fv_ag_f1)

            with m.If(Past(self.fv_ag_f2)):
                with m.If(~Past(self.tallfont)):
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:4], Past(self.charcode), old_fontbase[0:3])
                    )
                with m.Else():
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:5], Past(self.charcode), old_fontbase[1:3])
                    )
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.padr) == 1),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += Assert(self.fv_ag_f3)
                with m.Else():
                    sync += Assert(self.fv_ag_f2)

            with m.If(Past(self.fv_ag_f3)):
                with m.If(~Past(self.tallfont)):
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:4], Past(self.charcode), old_fontbase[0:3])
                    )
                with m.Else():
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:5], Past(self.charcode), old_fontbase[1:3])
                    )
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.padr) == 2),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += Assert(self.fv_ag_f4)
                with m.Else():
                    sync += Assert(self.fv_ag_f3)

            with m.If(Past(self.fv_ag_f4)):
                with m.If(~Past(self.tallfont)):
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:4], Past(self.charcode), old_fontbase[0:3])
                    )
                with m.Else():
                    sync += Assert(
                        Past(self.adr_o) == Cat(old_ra[0:5], Past(self.charcode), old_fontbase[1:3])
                    )
                sync += [
                    Assert(Past(self.stb_o)),
                    Assert(Past(self.padr) == 3),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
                with m.If(~Past(self.stall_i)):
                    sync += Assert(self.fv_ag_idle)
                with m.Else():
                    sync += Assert(self.fv_ag_f4)

        # Data Receiver is responsible for routing the data which is addressed by the address
        # generator to the appropriate bytes in the current strip buffer.

        with m.If(past_valid & Past(self.fv_dr_a1)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 0),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a1),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 0),
                    Assert(Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a2),
                ]

        with m.If(past_valid & Past(self.fv_dr_a2)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 1),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a2),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 1),
                    Assert(Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a3),
                ]

        with m.If(past_valid & Past(self.fv_dr_a3)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 2),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a3),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 2),
                    Assert(Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a4),
                ]

        with m.If(past_valid & Past(self.fv_dr_a4)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 3),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_a4),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 3),
                    Assert(Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c1),
                ]

        with m.If(past_valid & Past(self.fv_dr_c1)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 0),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c1),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 0),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c2),
                ]

        with m.If(past_valid & Past(self.fv_dr_c2)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 1),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c2),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 1),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c3),
                ]

        with m.If(past_valid & Past(self.fv_dr_c3)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 2),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c3),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 2),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c4),
                ]

        with m.If(past_valid & Past(self.fv_dr_c4)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 3),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_c4),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 3),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                ]
                with m.If(~Past(self.fv_bitmap_mode)):
                    sync += Assert(self.fv_dr_f1)
                with m.Else():
                    sync += Assert(self.fv_dr_idle)

        with m.If(past_valid & Past(self.fv_dr_f1)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 0),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f1),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 0),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f2),
                ]

        with m.If(past_valid & Past(self.fv_dr_f2)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 1),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f2),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 1),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f3),
                ]

        with m.If(past_valid & Past(self.fv_dr_f3)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 2),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f3),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 2),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f4),
                ]

        with m.If(past_valid & Past(self.fv_dr_f4)):
            with m.If(~Past(self.ack_i)):
                sync += [
                    Assert(Past(self.wadr) == 3),
                    Assert(~Past(self.awe)),
                    Assert(~Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_f4),
                ]
            with m.Else():
                sync += [
                    Assert(Past(self.wadr) == 3),
                    Assert(~Past(self.awe)),
                    Assert(Past(self.cwe)),
                    Assert(~Past(self.fv_ag_go_font)),
                    Assert(self.fv_dr_idle),
                ]

        return m


class VideoFetchTestCase(FHDLTestCase):
    def test_video_fetch(self):
        self.assertFormal(VideoFetchFormal(), mode='bmc', depth=100)
        self.assertFormal(VideoFetchFormal(), mode='prove', depth=100)
