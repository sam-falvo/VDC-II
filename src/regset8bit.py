from nmigen import (
    Elaboratable,
    Module,
    Signal,
    Cat,
    Const,
)


from interfaces import create_regset8bit_interface


class RegSet8Bit(Elaboratable):
    """
    This module interfaces a reasonably generic synchronous bus interface
    to a set of 8-bit registers.  Registers are arranged compatibly to
    the CSG8568 VDC chip.

    Host processor signals:

    Inputs:

    - adr_i :: The 6-bit register select input.  Usually this is provided
      from some other I/O port accessible to the host computer (e.g.,
      writing to $D600 in the Commodore 128 I/O space).
    - dat_i :: Data bus input to the VDC-II core.
    - we_i :: Flag indicating whether to replace the addressed register
      contents with the value on dat_i.

    Outputs:

    - dat_o :: The addressed register's current value.

    VDC Control Signals (names chosen to correspond with register definitions
    as documented in the Commodore 128 Programmer's Reference Guide):

    Inputs:

    Outputs:

    """
    def __init__(self, platform=''):
        super().__init__()
        create_regset8bit_interface(self, platform=platform)

    def elaborate(self, platform=''):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Implement the registers we need.
        ht_reg = Signal(8)                      # R00
        hd_reg = Signal(8)                      # R01
        hsp_reg = Signal(8)                     # R02
        vsw_reg = Signal(4)                     # R03[7:4]
        hsw_reg = Signal(4)                     # R03[3:0]
        vt_reg = Signal(8)                      # R04
        vta_reg = Signal(5)                     # R05
        vd_reg = Signal(8)                      # R06
        vsp_reg = Signal(8)                     # R07
        vct_reg = Signal(5)                     # R09
        hct_reg = Signal(4)                     # R22[7:4]
        hcd_reg = Signal(4)                     # R22[3:0]
        hsync_xor_reg = Signal(1, reset=1)      # R37 [7]
        vsync_xor_reg = Signal(1, reset=1)      # R37 [6]

        comb += [
            self.ht.eq(ht_reg),
            self.hd.eq(hd_reg),
            self.hsp.eq(hsp_reg),
            self.vsw.eq(vsw_reg),
            self.hsw.eq(hsw_reg),
            self.vt.eq(vt_reg),
            self.vta.eq(vta_reg),
            self.vd.eq(vd_reg),
            self.vsp.eq(vsp_reg),
            self.vct.eq(vct_reg),
            self.hct.eq(hct_reg),
            self.hcd.eq(hcd_reg),
            self.hsync_xor.eq(hsync_xor_reg),
            self.vsync_xor.eq(vsync_xor_reg),
            self.tallfont.eq(vct_reg[4]),
        ]

        # Handle read data routing
        read_set = {
            1: self.hd,
            2: self.hsp,
            3: Cat(hsw_reg, vsw_reg),
            4: self.vt,
            5: Cat(self.vta, Const(-1, 8-len(self.vta))),
            6: self.vd,
            7: self.vsp,
            9: Cat(self.vct, Const(-1, 8-len(self.vct))),
            12: self.chrbase[8:16],
            13: self.chrbase[0:8],
            18: self.update_location[8:16],
            19: self.update_location[0:8],
            20: self.atrbase[8:16],
            21: self.atrbase[0:8],
            22: Cat(self.hcd, self.hct),
            24: Cat(
                self.vscroll,
                self.blink_rate,
                self.reverse_screen,
                self.block_copy
            ),
            25: Cat(
                self.hscroll,
                self.dotclock_select,
                self.semigraphic_mode,
                self.attr_enable,
                self.bitmap_mode,
            ),
            26: Cat(self.bgpen, self.fgpen),
            28: Cat(Const(-1, 5), self.fontbase),
            30: self.bytecnt,
            31: self.cpudatar,
            32: self.copysrc[8:16],
            33: self.copysrc[0:8],
            37: Cat(Const(-1, 6), self.vsync_xor, self.hsync_xor),
        }

        with m.If(self.adr_i == 0):
            comb += self.dat_o.eq(self.ht)
        for reg, val in read_set.items():
            with m.Elif(self.adr_i == reg):
                comb += self.dat_o.eq(val)
        with m.Else():
            comb += self.dat_o.eq(Const(-1, len(self.dat_o)))

        # Handle Strobe Generation
        incr_updloc = Signal(1)

        comb += [
            self.go_wr_updloc.eq(
                ((self.adr_i == 18) | (self.adr_i == 19)) & self.we_i
            ),
            self.go_rd_cpudatar.eq(
                (self.adr_i == 31) & self.rd_i
            ),
            self.go_wr_cpudataw.eq(
                (self.adr_i == 31) & self.we_i
            ),
            self.go_wr_bytecnt.eq(
                (self.adr_i == 30) & self.we_i
            ),

            incr_updloc.eq(self.go_rd_cpudatar | self.incr_updloc),
        ]

        # Handle write data routing
        with m.If(self.we_i):
            with m.If(self.adr_i == 0):
                sync += ht_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 1):
                sync += hd_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 2):
                sync += hsp_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 3):
                sync += [
                    vsw_reg.eq(self.dat_i[4:8]),
                    hsw_reg.eq(self.dat_i[0:4]),
                ]
            with m.Elif(self.adr_i == 4):
                sync += vt_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 5):
                sync += vta_reg.eq(self.dat_i[0:len(vta_reg)])
            with m.Elif(self.adr_i == 6):
                sync += vd_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 7):
                sync += vsp_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 9):
                sync += vct_reg.eq(self.dat_i[0:len(vct_reg)])
            with m.Elif(self.adr_i == 12):
                sync += self.chrbase[8:16].eq(self.dat_i)
            with m.Elif(self.adr_i == 13):
                sync += self.chrbase[0:8].eq(self.dat_i)
            with m.Elif((self.adr_i == 18) & ~incr_updloc):
                sync += self.update_location[8:16].eq(self.dat_i)
            with m.Elif((self.adr_i == 19) & ~incr_updloc):
                sync += self.update_location[0:8].eq(self.dat_i)
            with m.Elif(self.adr_i == 20):
                sync += self.atrbase[8:16].eq(self.dat_i)
            with m.Elif(self.adr_i == 21):
                sync += self.atrbase[0:8].eq(self.dat_i)
            with m.Elif(self.adr_i == 22):
                sync += [
                    hct_reg.eq(self.dat_i[4:8]),
                    hcd_reg.eq(self.dat_i[0:4]),
                ]
            with m.Elif(self.adr_i == 24):
                sync += [
                    self.vscroll.eq(self.dat_i[0:len(self.vscroll)]),
                    self.blink_rate.eq(self.dat_i[5]),
                    self.reverse_screen.eq(self.dat_i[6]),
                    self.block_copy.eq(self.dat_i[7]),
                ]
            with m.Elif(self.adr_i == 25):
                sync += [
                    self.hscroll.eq(self.dat_i[0:len(self.hscroll)]),
                    self.dotclock_select.eq(self.dat_i[4]),
                    self.semigraphic_mode.eq(self.dat_i[5]),
                    self.attr_enable.eq(self.dat_i[6]),
                    self.bitmap_mode.eq(self.dat_i[7]),
                ]
            with m.Elif(self.adr_i == 26):
                sync += [
                    self.bgpen.eq(self.dat_i[0:4]),
                    self.fgpen.eq(self.dat_i[4:8]),
                ]
            with m.Elif(self.adr_i == 28):
                sync += self.fontbase.eq(self.dat_i[5:8])
            with m.Elif((self.adr_i == 30) & ~self.decr_bytecnt):
                sync += self.bytecnt.eq(self.dat_i)
            with m.Elif(self.adr_i == 31):
                sync += self.cpudataw.eq(self.dat_i)
            with m.Elif((self.adr_i == 32) & ~self.incr_copysrc):
                sync += self.copysrc[8:16].eq(self.dat_i)
            with m.Elif((self.adr_i == 33) & ~self.incr_copysrc):
                sync += self.copysrc[0:8].eq(self.dat_i)
            with m.Elif(self.adr_i == 37):
                sync += [
                    hsync_xor_reg.eq(self.dat_i[7]),
                    vsync_xor_reg.eq(self.dat_i[6]),
                ]

        # Handle updates to pointer registers.
        with m.If(incr_updloc):
            sync += self.update_location.eq(self.update_location + 1)

        with m.If(self.incr_copysrc):
            sync += self.copysrc.eq(self.copysrc + 1)

        with m.If(self.decr_bytecnt):
            sync += self.bytecnt.eq(self.bytecnt - 1)

        return m
