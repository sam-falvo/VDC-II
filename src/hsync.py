from nmigen import (
    Elaboratable,
    Module,
    ResetSignal,
    Signal,
    Const,
)

from interfaces import create_hsync_interface


class HSync(Elaboratable):
    """
    Implements a horizontal sync generator.

    The module has the following inputs:
    - htotal :: The horizontal total specifies how many pixels
      exist on each raster.  This value is usually provided through
      a programmable register that is CPU-facing.  Note that this
      input has PIXEL-resolution, not character resolution.
    - hsync_pos :: The position of the HSYNC pulse, relative to pixel
      zero.  This also has pixel resolution.
    - hsync_width :: The width of the sync pulse, in pixels.  The VDC
      register set provides 4 bits to specify how many characters the
      sync pulse spans, which is why it is shorter than other position
      counters.

    The following outputs exist:
    - hcounter :: This is the current pixel counter.  On a VGA display,
      at 640x480 resolution, this will span from 0 to 799 or something
      close to that depending on dot clock frequency.  Obviously, set
      htotal = 799 in this case.
    - htotal_reached :: A diagnostic output, it provides a single pulse
      indicating when the horizontal total has been reached for a single
      raster.
    - hsync :: A pulse output whose width is programmable based on
      the hsync_width input.  This output is active high; external
      circuitry will be needed to provide the correct phase.
    """
    def __init__(self, platform=""):
        super().__init__()
        create_hsync_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # The htotal_reached signal asserts when the counter
        # reaches the final count.
        comb += self.htotal_reached.eq(self.hcounter == self.htotal)

        # The counter increments for every pixel displayed,
        # and resets for the next raster.
        with m.If(~self.htotal_reached):
            sync += self.hcounter.eq(self.hcounter + 1)

        with m.If(self.htotal_reached):
            sync += self.hcounter.eq(0)

        # The hsync signal asserts during the configured horizontal
        # sync period, determined by the hsync_pos and hsync_width
        # inputs.
        sync_width_ctr = Signal(len(self.hsync_width))

        if platform == 'formal':
            comb += self.fv_sync_width_ctr.eq(sync_width_ctr)

        # HSYNC asserted as long as the counter is running.
        comb += self.hsync.eq(sync_width_ctr != 0)
        with m.If(self.hsync):
            sync += sync_width_ctr.eq(sync_width_ctr - 1)

        with m.If(~self.hsync & (self.hcounter == self.hsync_pos)):
            sync += sync_width_ctr.eq(self.hsync_width)

        return m
