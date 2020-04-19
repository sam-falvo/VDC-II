from nmigen import (
    Elaboratable,
    Module,
    ResetSignal,
    Signal,
    Const,
)

from interfaces import create_syncgen_interface


class SyncGenerator(Elaboratable):
    """
    Implements a generic sync generator.  A careful study of the VDC
    register map defined by Commodore strongly suggests that they used
    the same circuit for both horizontal and vertical sync pulse
    generation.  This module attempts to replicate what I think that
    circuit is capable of.

    - total :: The total specifies how many pixels (horizontal)
      or lines (vertical) exist between the leading edges of the
      sync pulses.  This value is has *character* resolution.
    - sync_pos :: The position of the xSYNC pulse, relative to pixel
      or line zero.  This also has character resolution.
    - sync_width :: The width of the sync pulse, in characters or lines.
      The VDC register set provides 4 bits to specify how many units
      the sync pulse spans, which is why it is shorter than other
      position counters.
    - char_total :: The total number of pixels in a character column, or
      how many lines a character cell contains.

    The following outputs exist:
    - counter :: This is the current value of the unit counter.  On a VGA
      display, at 640x480 resolution, this will span from 0 to 799
      (horizontal) or from 0 to 524 (vertical).
    - total_reached :: A diagnostic output, it provides a single pulse
      indicating when the counter total has been reached.
    - xsync :: A pulse output whose width is programmable based on
      the sync_width input.  This output is active high; external
      circuitry will be needed to provide the correct phase.  The name
      is chosen to minimize confusion with nmigen's m.d.sync reference.
    - last :: A pulse that is asserted when displaying the right-most
      column of pixels in a character column, or the bottom-most line
      in a character row.
    """

    def __init__(self, platform=""):
        super().__init__()
        create_syncgen_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # The display is measured in units of characters; however,
        # characters occupy a finite number of pixels on the screen.
        # The last signal is asserted when the character column
        # is displaying its very last pixel.
        unit_ctr = Signal(4)
        comb += self.last.eq(unit_ctr == 0)

        with m.If(unit_ctr == 0):
            sync += unit_ctr.eq(self.char_total)
        with m.Else():
            sync += unit_ctr.eq(unit_ctr - 1)

        # The total_reached signal asserts when the counter
        # reaches the final count.
        comb += self.total_reached.eq(self.counter == 0)

        # The counter decrements for every character displayed,
        # and resets for the next unit.
        with m.If(~self.total_reached & self.last):
            sync += self.counter.eq(self.counter - 1)

        with m.If(self.total_reached & self.last):
            sync += self.counter.eq(self.total)

        # The sync signal asserts during the configured sync period,
        # determined by the sync_pos and sync_width inputs.
        sync_width_ctr = Signal(len(self.sync_width))

        # xSYNC asserted as long as the counter is running.
        comb += self.xsync.eq(sync_width_ctr != 0)
        with m.If(self.xsync & self.last):
            sync += sync_width_ctr.eq(sync_width_ctr - 1)

        with m.If(~self.xsync & (self.counter == self.sync_pos) & self.last):
            sync += sync_width_ctr.eq(self.sync_width)

        # Debugging ports for formal verification
        if platform == 'formal':
            comb += [
                self.fv_sync_width_ctr.eq(sync_width_ctr),
                self.fv_unit_ctr.eq(unit_ctr),
            ]


        return m
