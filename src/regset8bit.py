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

    - ht :: Horizontal Total
    - hp :: Horizontal sync position
    - hw :: Horizontal Sync Width
    - vw :: Vertical Sync Width (currently unused)
    - cth :: Horizontal character cell total
    - cdh :: Horizontal character cell displayed
    """
    def __init__(self, platform=''):
        super().__init__()
        create_regset8bit_interface(self, platform=platform)

    def elaborate(self, platform=''):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Implement the registers we need.
        ht_reg = Signal(8)  # R00
        hp_reg = Signal(8)  # R02
        vw_reg = Signal(4)  # R03[7:4]
        hw_reg = Signal(4)  # R03[3:0]
        cth_reg = Signal(4) # R22[7:4]
        cdh_reg = Signal(4) # R22[3:0]

        comb += [
            self.ht.eq(ht_reg),
            self.hp.eq(hp_reg),
            self.vw.eq(vw_reg),
            self.hw.eq(hw_reg),
            self.cth.eq(cth_reg),
            self.cdh.eq(cdh_reg),
        ]

        # Handle read data routing
        with m.If(self.adr_i == 0):
            comb += self.dat_o.eq(self.ht)
        with m.Elif(self.adr_i == 2):
            comb += self.dat_o.eq(self.hp)
        with m.Elif(self.adr_i == 3):
            comb += self.dat_o.eq(Cat(self.hw, self.vw))
        with m.Elif(self.adr_i == 22):
            comb += self.dat_o.eq(Cat(self.cdh, self.cth))
        with m.Else():
            comb += self.dat_o.eq(Const(-1, len(self.dat_o)))

        # Handle write data routing
        with m.If(self.we_i):
            with m.If(self.adr_i == 0):
                sync += ht_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 2):
                sync += hp_reg.eq(self.dat_i)
            with m.Elif(self.adr_i == 3):
                sync += [
                    vw_reg.eq(self.dat_i[4:8]),
                    hw_reg.eq(self.dat_i[0:4]),
                ]
            with m.Elif(self.adr_i == 22):
                sync += [
                    cth_reg.eq(self.dat_i[4:8]),
                    cdh_reg.eq(self.dat_i[0:4]),
                ]
                
        return m
