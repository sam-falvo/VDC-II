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


def create_video_fetch_interface(self, platform=None):
    # Video Timing Interface
    ## Inputs
    self.go_i = Signal(1)
    self.ra = Signal(5)

    # Register Set Interface
    ## Inputs
    self.fetch_enable = Signal(1)
    self.attr_enable = Signal(1)
    self.bitmap_mode = Signal(1)
    self.tallfont = Signal(1)
    self.fontbase = Signal(3)

    ## Outputs

    # Video Memory Interface
    ## Inputs
    self.stall_i = Signal(1)

    ## Outputs
    self.adr_o = Signal(16)
    self.cyc_o = Signal(1)
    self.stb_o = Signal(1)

    # Strip Buffer Interface
    ## Inputs
    self.charcode = Signal(9)

    ## Outputs
    self.padr = Signal(2)

    if platform == 'formal':
        self.fv_ag_idle = Signal(1)
        self.fv_ag_a1 = Signal(1)
        self.fv_ag_a2 = Signal(1)
        self.fv_ag_a3 = Signal(1)
        self.fv_ag_a4 = Signal(1)
        self.fv_ag_c1 = Signal(1)
        self.fv_ag_c2 = Signal(1)
        self.fv_ag_c3 = Signal(1)
        self.fv_ag_c4 = Signal(1)
        self.fv_ag_f1 = Signal(1)
        self.fv_ag_f2 = Signal(1)
        self.fv_ag_f3 = Signal(1)
        self.fv_ag_f4 = Signal(1)
        self.fv_atrptr = Signal(len(self.adr_o))
        self.fv_chrptr = Signal(len(self.adr_o))
        self.fv_ag_go_font = Signal(1)


class VideoFetch(Elaboratable):
    def __init__(self, platform=None):
        super().__init__()
        create_video_fetch_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Address Generation Logic.

        ag_go_font = Signal(1)

        atrptr = Signal(len(self.adr_o))
        chrptr = Signal(len(self.adr_o))
        fontptr = Signal(len(self.adr_o))

        atrptr_inc = Signal(len(atrptr))
        chrptr_inc = Signal(len(chrptr))

        comb += [
            atrptr_inc.eq(atrptr + 1),
            chrptr_inc.eq(chrptr + 1),
        ]
        with m.If(self.tallfont):
            comb += fontptr.eq(Cat(self.ra[0:5], self.charcode, self.fontbase[1:3]))
        with m.Else():
            comb += fontptr.eq(Cat(self.ra[0:4], self.charcode, self.fontbase[0:3]))

        with m.FSM() as ag:
            with m.State("idle"):
                with m.If(self.go_i):
                    with m.If(self.attr_enable):
                        m.next = "a1"
                    with m.Else():
                        m.next = "c1"

            with m.State("a1"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "a2"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("a2"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "a3"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("a3"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "a4"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("a4"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c1"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("c1"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c2"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("c2"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c3"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("c3"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c4"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("c4"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    with m.If(~self.bitmap_mode):
                        m.next = "f1"
                    with m.Else():
                        m.next = "idle"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("f1"):
                comb += [
                    self.padr.eq(0),
                    self.stb_o.eq(ag_go_font),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(ag_go_font):
                    with m.If(~self.stall_i):
                        m.next = "f2"

            with m.State("f2"):
                comb += [
                    self.padr.eq(1),
                    self.stb_o.eq(1),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(~self.stall_i):
                    m.next = "f3"

            with m.State("f3"):
                comb += [
                    self.padr.eq(2),
                    self.stb_o.eq(1),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(~self.stall_i):
                    m.next = "f4"

            with m.State("f4"):
                comb += [
                    self.padr.eq(3),
                    self.stb_o.eq(1),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(~self.stall_i):
                    m.next = "idle"

            if platform == 'formal':
                comb += [
                    self.fv_ag_idle.eq(ag.ongoing("idle")),
                    self.fv_ag_a1.eq(ag.ongoing("a1")),
                    self.fv_ag_a2.eq(ag.ongoing("a2")),
                    self.fv_ag_a3.eq(ag.ongoing("a3")),
                    self.fv_ag_a4.eq(ag.ongoing("a4")),
                    self.fv_ag_c1.eq(ag.ongoing("c1")),
                    self.fv_ag_c2.eq(ag.ongoing("c2")),
                    self.fv_ag_c3.eq(ag.ongoing("c3")),
                    self.fv_ag_c4.eq(ag.ongoing("c4")),
                    self.fv_ag_f1.eq(ag.ongoing("f1")),
                    self.fv_ag_f2.eq(ag.ongoing("f2")),
                    self.fv_ag_f3.eq(ag.ongoing("f3")),
                    self.fv_ag_f4.eq(ag.ongoing("f4")),
                    self.fv_ag_go_font.eq(ag_go_font),
                ]

        #
        # Data Receiver Logic
        #
        # Because the data we expect back on the Wishbone bus is structured by
        # what the address generator uses, we must structure this FSM identically
        # to match that of the address generator FSM.
        #

        with m.FSM() as dr:
            comb += self.cyc_o.eq(~dr.ongoing("idle"))
            with m.State("idle"):
                with m.If(self.go_i):
                    with m.If(self.attr_enable):
                        m.next = "a1"
                    with m.Else():
                        m.next = "c1"

            with m.State("a1"):
                pass

            with m.State("c1"):
                pass

        if platform == 'formal':
            comb += [
                self.fv_atrptr.eq(atrptr),
                self.fv_chrptr.eq(chrptr),
            ]

        return m


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
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.go_i.eq(self.go_i),
            dut.fetch_enable.eq(self.fetch_enable),
            dut.attr_enable.eq(self.attr_enable),
            dut.bitmap_mode.eq(self.bitmap_mode),
            dut.tallfont.eq(self.tallfont),
            dut.fontbase.eq(self.fontbase),
            dut.ra.eq(self.ra),
            dut.charcode.eq(self.charcode),
            dut.tallfont.eq(self.tallfont),
            dut.fontbase.eq(self.fontbase),

            dut.stall_i.eq(self.stall_i),
        ]

        # Video Fetch Unit sits idle until told to do something.  go_i triggers a
        # video fetch sequence.  attr_enable and bitmap_mode parameterize the
        # sequence taken.

        with m.If(past_valid & Past(self.fv_ag_idle)):
            sync += Assert(~Past(self.stb_o))

            with m.If(~Past(self.go_i)):
                sync += [
                    Assert(self.fv_ag_idle),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
            with m.If(Past(self.go_i) & ~Past(self.attr_enable)):
                sync += [
                    Assert(self.fv_ag_c1),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]
            with m.If(Past(self.go_i) & Past(self.attr_enable)):
                sync += [
                    Assert(self.fv_ag_a1),
                    Assert(Stable(self.fv_atrptr)),
                    Assert(Stable(self.fv_chrptr)),
                ]


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
                    with m.If(~Past(self.bitmap_mode)):
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

        return m


class VideoFetchTestCase(FHDLTestCase):
    def test_video_fetch(self):
        self.assertFormal(VideoFetchFormal(), mode='bmc', depth=100)
        self.assertFormal(VideoFetchFormal(), mode='prove', depth=100)
