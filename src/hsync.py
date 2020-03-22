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
    - char_total :: The total number of pixels in a character column.
      This should never exceed 8 or there'll be undefined behavior.

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
    - charpix0 :: A pulse that is asserted when displaying the right-most
      column of pixels in a character column.  Put another way, there
      are 0 more pixels to display in this character, and the next dot
      clock will start the next character column.
    """
    def __init__(self, platform=""):
        super().__init__()
        create_hsync_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # The display is measured in units of characters; however,
        # characters occupy a finite number of pixels on the screen.
        # The charpix0 signal is asserted when the character column
        # is displaying its very last pixel.
        charpix_ctr = Signal(4)
        comb += self.charpix0.eq(charpix_ctr == 0)

        with m.If(charpix_ctr == 0):
            sync += charpix_ctr.eq(self.char_total)
        with m.Else():
            sync += charpix_ctr.eq(charpix_ctr - 1)

        # The htotal_reached signal asserts when the counter
        # reaches the final count.
        comb += self.htotal_reached.eq(self.hcounter == self.htotal)

        # The counter increments for every pixel displayed,
        # and resets for the next raster.
        with m.If(~self.htotal_reached & self.charpix0):
            sync += self.hcounter.eq(self.hcounter + 1)

        with m.If(self.htotal_reached & self.charpix0):
            sync += self.hcounter.eq(0)

        # The hsync signal asserts during the configured horizontal
        # sync period, determined by the hsync_pos and hsync_width
        # inputs.
        sync_width_ctr = Signal(len(self.hsync_width))

        # HSYNC asserted as long as the counter is running.
        comb += self.hsync.eq(sync_width_ctr != 0)
        with m.If(self.hsync):
            sync += sync_width_ctr.eq(sync_width_ctr - 1)

        with m.If(~self.hsync & (self.hcounter == self.hsync_pos)):
            sync += sync_width_ctr.eq(self.hsync_width)

        # Debugging ports for formal verification
        if platform == 'formal':
            comb += [
                self.fv_sync_width_ctr.eq(sync_width_ctr),
                self.fv_charpix_ctr.eq(charpix_ctr),
            ]


        return m
