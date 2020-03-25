from nmigen import (
    Elaboratable,
    Module,
    ResetSignal,
    Signal,
    Cat,
    Const,
)

from interfaces import VDC_VERSION, create_hostbus_interface


class HostBus(Elaboratable):
    """
    This module implements a Z80 CPU-compatible bus interface that should
    work up to about 8MHz, assuming the FPGA is clocked at least at 24MHz.

    This module is designed to connect to a RegSet8Bit module.

    Z80 CPU Signals.  NOTE: ALL ARE ACTIVE HIGH.  It is up to the top-level
    module to perform signal inversion on this module's behalf when binding
    signals to I/O pins.

    Inputs:
    - a :: Address selection.  If 0, the host processor is either going
      to read from the status port, or write to the register select port.
    - rd :: Read command.  When asserted, this enables the FPGA's data
      bus output drivers.
    - d :: Data bus input.  If rd is low and cs is high, this indicates
      a write operation.  Data on d are vald during write transactions.
    - cs :: Chip Select.  ALL other signals are meaningless as long as cs
      is negated.

    Outputs:
    - q :: Data bus outputs.  If rd is high and cs is high, this indicates
      a read transaction.  The value on q0-q7 will be presented to the host
      CPU data bus combinatorially.  q is always driven, even if the output
      enable (qoe) is negated.
    - qoe :: Data bus output enable.

    Register Set signals.  These are designed to interface with a VDC register
    set module.

    Inputs:
    - ready_i :: A flag indicating when the video memory read/write engine
      is ready for another host CPU-activated operation.
    - vblank_i :: Vertical blank in progress flag.
    - lp_i :: Light pen values are valid flag.

    Outputs:
    - dat_o :: 8-bit data path going *to* the register set module.
    - adr_o :: 6-bit register select address.
    - we_o :: A write-enable strobe for writing a value to the register set.
      Lasts for a single clock cycle, and indicates when dat_o is valid.
      Only asserts if the host processor is writing to the data port.
    """
    def __init__(self, platform=""):
        super().__init__()
        create_hostbus_interface(self, platform=platform)

    def elaborate(self, platform=''):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # qoe is driven only during valid read transactions.
        comb += self.qoe.eq(self.cs & self.rd)

        # Synchronize the chip inputs to control metastability.
        a1 = Signal(1)
        a2 = Signal(1)
        a3 = Signal(1)

        cs1 = Signal(1)
        cs2 = Signal(1)
        cs3 = Signal(1)

        rd1 = Signal(1)
        rd2 = Signal(1)
        rd3 = Signal(1)

        d1 = Signal(len(self.d))
        d2 = Signal(len(self.d))
        d3 = Signal(len(self.d))

        sync += [
            a1.eq(self.a),
            a2.eq(a1),
            a3.eq(a2),

            cs1.eq(self.cs),
            cs2.eq(cs1),
            cs3.eq(cs2),

            rd1.eq(self.rd),
            rd2.eq(rd1),
            rd3.eq(rd2),

            d1.eq(self.d),
            d2.eq(d1),
            d3.eq(d2),
        ]

        comb += [
            self.dat_o.eq(d3),
        ]

        # Derive write enable pulse for the I/O ports and
        # register set.

        we_ports = Signal(1)
        comb += [
            we_ports.eq(~cs2 & cs3 & ~rd3),
            self.we_o.eq(we_ports & a3),
        ]

        # Write to the register select port if addressed.
        with m.If(we_ports & ~a3):
            sync += self.adr_o.eq(d3[0:6])

        # Read from the status port or addressed register.
        status = Cat(
            Const(VDC_VERSION, 3),
            Const(0b11, 2),
            self.vblank_i, self.lp_i, self.ready_i
        )
        with m.If(~a3):
            comb += self.q.eq(status)
        with m.Else():
            comb += self.q.eq(self.dat_i)

        if platform == 'formal':
            comb += [
                self.fv_old_cssync.eq(cs2),
                self.fv_cssync.eq(cs3),
                self.fv_rdsync.eq(rd3),
                self.fv_we_ports.eq(we_ports),
                self.fv_async.eq(a3),
                self.fv_dsync.eq(d3),
            ]
        return m
