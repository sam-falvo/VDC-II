from math import log2

from nmigen import Signal


# Each VDC register is 8-bits wide.
REG_WIDTH=8

# Character tile data can be no wider than 8 pixels.
MAX_PIXELS_PER_CHAR=8

HCOUNTER_WIDTH=int(REG_WIDTH+log2(MAX_PIXELS_PER_CHAR))


def create_hsync_interface(self, platform=""):
    # outputs
    self.hcounter = Signal(HCOUNTER_WIDTH)
    self.htotal_reached = Signal(1)
    self.hsync = Signal(1)

    # inputs
    self.htotal = Signal(HCOUNTER_WIDTH)
    self.hsync_pos = Signal(HCOUNTER_WIDTH)
    self.hsync_width = Signal(7)

    # FV outputs
    if platform == 'formal':
        self.fv_sync_width_ctr = Signal(len(self.hsync_width))
