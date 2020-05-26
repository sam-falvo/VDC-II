from nmigen import (
    Elaboratable,
    Module,
    Signal,
)

from interfaces import create_strip_buffer_interface


class StripBuffer(Elaboratable):
    def __init__(self, platform=None):
        super().__init__()
        create_strip_buffer_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # ab selects column registers A or B.
        ab = Signal(1)
        col0a = Signal(16)
        col1a = Signal(16)
        col2a = Signal(16)
        col3a = Signal(16)
        col0b = Signal(16)
        col1b = Signal(16)
        col2b = Signal(16)
        col3b = Signal(16)

        with m.If(self.swap):
            sync += ab.eq(~ab)

        with m.If(~ab):
            with m.If(self.padr == 0):
                comb += self.pair.eq(col0a)
            with m.Elif(self.padr == 1):
                comb += self.pair.eq(col1a)
            with m.Elif(self.padr == 2):
                comb += self.pair.eq(col2a)
            with m.Elif(self.padr == 3):
                comb += self.pair.eq(col3a)
        with m.Else():
            with m.If(self.padr == 0):
                comb += self.pair.eq(col0b)
            with m.Elif(self.padr == 1):
                comb += self.pair.eq(col1b)
            with m.Elif(self.padr == 2):
                comb += self.pair.eq(col2b)
            with m.Elif(self.padr == 3):
                comb += self.pair.eq(col3b)

        with m.If(~ab):
            with m.If(self.sh_padr == 0):
                comb += self.sh_pair.eq(col0b)
            with m.Elif(self.sh_padr == 1):
                comb += self.sh_pair.eq(col1b)
            with m.Elif(self.sh_padr == 2):
                comb += self.sh_pair.eq(col2b)
            with m.Elif(self.sh_padr == 3):
                comb += self.sh_pair.eq(col3b)
        with m.Else():
            with m.If(self.sh_padr == 0):
                comb += self.sh_pair.eq(col0a)
            with m.Elif(self.sh_padr == 1):
                comb += self.sh_pair.eq(col1a)
            with m.Elif(self.sh_padr == 2):
                comb += self.sh_pair.eq(col2a)
            with m.Elif(self.sh_padr == 3):
                comb += self.sh_pair.eq(col3a)

        with m.If(self.cwe):
            with m.If(~ab):
                with m.If(self.wadr == 0):
                    sync += col0a[0:8].eq(self.dat_i)
                with m.Elif(self.wadr == 1):
                    sync += col1a[0:8].eq(self.dat_i)
                with m.Elif(self.wadr == 2):
                    sync += col2a[0:8].eq(self.dat_i)
                with m.Else():
                    sync += col3a[0:8].eq(self.dat_i)
            with m.Else():
                with m.If(self.wadr == 0):
                    sync += col0b[0:8].eq(self.dat_i)
                with m.Elif(self.wadr == 1):
                    sync += col1b[0:8].eq(self.dat_i)
                with m.Elif(self.wadr == 2):
                    sync += col2b[0:8].eq(self.dat_i)
                with m.Else():
                    sync += col3b[0:8].eq(self.dat_i)

        with m.If(self.awe):
            with m.If(~ab):
                with m.If(self.wadr == 0):
                    sync += col0a[8:16].eq(self.dat_i)
                with m.Elif(self.wadr == 1):
                    sync += col1a[8:16].eq(self.dat_i)
                with m.Elif(self.wadr == 2):
                    sync += col2a[8:16].eq(self.dat_i)
                with m.Else():
                    sync += col3a[8:16].eq(self.dat_i)
            with m.Else():
                with m.If(self.wadr == 0):
                    sync += col0b[8:16].eq(self.dat_i)
                with m.Elif(self.wadr == 1):
                    sync += col1b[8:16].eq(self.dat_i)
                with m.Elif(self.wadr == 2):
                    sync += col2b[8:16].eq(self.dat_i)
                with m.Else():
                    sync += col3b[8:16].eq(self.dat_i)

        if platform == 'formal':
            comb += [
                self.fv_col0a.eq(col0a),
                self.fv_col1a.eq(col1a),
                self.fv_col2a.eq(col2a),
                self.fv_col3a.eq(col3a),
                self.fv_col0b.eq(col0b),
                self.fv_col1b.eq(col1b),
                self.fv_col2b.eq(col2b),
                self.fv_col3b.eq(col3b),
                self.fv_ab.eq(ab),
            ]

        return m
