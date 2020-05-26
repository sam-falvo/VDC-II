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

from interfaces import create_strip_buffer_interface

from strip_buffer import StripBuffer


class StripBufferFormal(Elaboratable):
    def __init__(self):
        super().__init__()
        create_strip_buffer_interface(self, platform="formal")

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

        dut = StripBuffer(platform=platform)
        m.submodules.dut = dut
        rst = ResetSignal()

        past_valid = Signal()
        comb += past_valid.eq(z_past_valid & Stable(rst) & ~rst)

        # Connect DUT outputs
        comb += [
            self.fv_col0a.eq(dut.fv_col0a),
            self.fv_col1a.eq(dut.fv_col1a),
            self.fv_col2a.eq(dut.fv_col2a),
            self.fv_col3a.eq(dut.fv_col3a),
            self.fv_col0b.eq(dut.fv_col0b),
            self.fv_col1b.eq(dut.fv_col1b),
            self.fv_col2b.eq(dut.fv_col2b),
            self.fv_col3b.eq(dut.fv_col3b),
            self.fv_ab.eq(dut.fv_ab),

            self.pair.eq(dut.pair),
            self.sh_pair.eq(dut.sh_pair),
        ]

        # Connect DUT inputs.  These will be driven by the formal verifier
        # for us, based on assertions and assumptions.
        comb += [
            dut.padr.eq(self.padr),
            dut.swap.eq(self.swap),
            dut.cwe.eq(self.cwe),
            dut.awe.eq(self.awe),
            dut.wadr.eq(self.wadr),
            dut.dat_i.eq(self.dat_i),

            dut.sh_padr.eq(self.sh_padr),
        ]

        # Pair output is selected asynchronously.
        with m.If(~self.fv_ab):
            with m.If(self.padr == 0):
                comb += Assert(self.pair == self.fv_col0a)
            with m.If(self.padr == 1):
                comb += Assert(self.pair == self.fv_col1a)
            with m.If(self.padr == 2):
                comb += Assert(self.pair == self.fv_col2a)
            with m.If(self.padr == 3):
                comb += Assert(self.pair == self.fv_col3a)
        with m.If(self.fv_ab):
            with m.If(self.padr == 0):
                comb += Assert(self.pair == self.fv_col0b)
            with m.If(self.padr == 1):
                comb += Assert(self.pair == self.fv_col1b)
            with m.If(self.padr == 2):
                comb += Assert(self.pair == self.fv_col2b)
            with m.If(self.padr == 3):
                comb += Assert(self.pair == self.fv_col3b)

        # Shifter pair output is selected asynchronously as well,
        # but always draws from the opposite set of registers.
        with m.If(~self.fv_ab):
            with m.If(self.sh_padr == 0):
                comb += Assert(self.sh_pair == self.fv_col0b)
            with m.If(self.sh_padr == 1):
                comb += Assert(self.sh_pair == self.fv_col1b)
            with m.If(self.sh_padr == 2):
                comb += Assert(self.sh_pair == self.fv_col2b)
            with m.If(self.sh_padr == 3):
                comb += Assert(self.sh_pair == self.fv_col3b)
        with m.If(self.fv_ab):
            with m.If(self.sh_padr == 0):
                comb += Assert(self.sh_pair == self.fv_col0a)
            with m.If(self.sh_padr == 1):
                comb += Assert(self.sh_pair == self.fv_col1a)
            with m.If(self.sh_padr == 2):
                comb += Assert(self.sh_pair == self.fv_col2a)
            with m.If(self.sh_padr == 3):
                comb += Assert(self.sh_pair == self.fv_col3a)

        # We must swap strips when instructed to by the shifter.
        with m.If(past_valid & Past(self.swap)):
            sync += Assert(self.fv_ab == ~Past(self.fv_ab))

        # Character data is recorded in the low 8 bits of a pair.
        with m.If(past_valid & Past(self.cwe) & ~Past(self.awe)):
            with m.If(~Past(self.fv_ab)):
                with m.If(Past(self.wadr) == 0):
                    sync += [
                        Assert(Past(self.fv_col0a)[8:16] == self.fv_col0a[8:16]),
                        Assert(self.fv_col0a[0:8] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 1):
                    sync += [
                        Assert(Past(self.fv_col1a)[8:16] == self.fv_col1a[8:16]),
                        Assert(self.fv_col1a[0:8] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 2):
                    sync += [
                        Assert(Past(self.fv_col2a)[8:16] == self.fv_col2a[8:16]),
                        Assert(self.fv_col2a[0:8] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 3):
                    sync += [
                        Assert(Past(self.fv_col3a)[8:16] == self.fv_col3a[8:16]),
                        Assert(self.fv_col3a[0:8] == Past(self.dat_i)),
                    ]
            with m.Else():
                with m.If(Past(self.wadr) == 0):
                    sync += [
                        Assert(Past(self.fv_col0b)[8:16] == self.fv_col0b[8:16]),
                        Assert(self.fv_col0b[0:8] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 1):
                    sync += [
                        Assert(Past(self.fv_col1b)[8:16] == self.fv_col1b[8:16]),
                        Assert(self.fv_col1b[0:8] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 2):
                    sync += [
                        Assert(Past(self.fv_col2b)[8:16] == self.fv_col2b[8:16]),
                        Assert(self.fv_col2b[0:8] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 3):
                    sync += [
                        Assert(Past(self.fv_col3b)[8:16] == self.fv_col3b[8:16]),
                        Assert(self.fv_col3b[0:8] == Past(self.dat_i)),
                    ]
                
        # Character data is recorded in the upper 8 bits of a pair.
        with m.If(past_valid & ~Past(self.cwe) & Past(self.awe)):
            with m.If(~Past(self.fv_ab)):
                with m.If(Past(self.wadr) == 0):
                    sync += [
                        Assert(Past(self.fv_col0a)[0:8] == self.fv_col0a[0:8]),
                        Assert(self.fv_col0a[8:16] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 1):
                    sync += [
                        Assert(Past(self.fv_col1a)[0:8] == self.fv_col1a[0:8]),
                        Assert(self.fv_col1a[8:16] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 2):
                    sync += [
                        Assert(Past(self.fv_col2a)[0:8] == self.fv_col2a[0:8]),
                        Assert(self.fv_col2a[8:16] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 3):
                    sync += [
                        Assert(Past(self.fv_col3a)[0:8] == self.fv_col3a[0:8]),
                        Assert(self.fv_col3a[8:16] == Past(self.dat_i)),
                    ]
            with m.Else():
                with m.If(Past(self.wadr) == 0):
                    sync += [
                        Assert(Past(self.fv_col0b)[0:8] == self.fv_col0b[0:8]),
                        Assert(self.fv_col0b[8:16] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 1):
                    sync += [
                        Assert(Past(self.fv_col1b)[0:8] == self.fv_col1b[0:8]),
                        Assert(self.fv_col1b[8:16] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 2):
                    sync += [
                        Assert(Past(self.fv_col2b)[0:8] == self.fv_col2b[0:8]),
                        Assert(self.fv_col2b[8:16] == Past(self.dat_i)),
                    ]
                with m.If(Past(self.wadr) == 3):
                    sync += [
                        Assert(Past(self.fv_col3b)[0:8] == self.fv_col3b[0:8]),
                        Assert(self.fv_col3b[8:16] == Past(self.dat_i)),
                    ]
                
        return m


class StripBufferTestCase(FHDLTestCase):
    def test_strip_buffer(self):
        self.assertFormal(StripBufferFormal(), mode='bmc', depth=100)
        self.assertFormal(StripBufferFormal(), mode='prove', depth=100)
