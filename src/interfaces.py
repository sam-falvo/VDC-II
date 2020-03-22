from math import log2

from nmigen import Signal


# Each VDC register is 8-bits wide.
REG_WIDTH=8

# Character tile data can be no wider than 8 pixels.
MAX_PIXELS_PER_CHAR=8

# Horizontal total is given in units of characters, not
# pixels.  Characters, in turn, are specified through
# the character total and character displayed fields.
# The 8568 VDC allots 8 bits to a horizontal total field.
HCOUNTER_WIDTH=8


def create_hsync_interface(self, platform=""):
    # outputs
    self.hcounter = Signal(HCOUNTER_WIDTH)
    self.htotal_reached = Signal(1)
    self.hsync = Signal(1)
    self.charpix0 = Signal()

    # inputs                                    VDC Reg/Field
    self.htotal = Signal(HCOUNTER_WIDTH)        # R00
    self.hsync_pos = Signal(HCOUNTER_WIDTH)     # R02
    self.hsync_width = Signal(4)                # R03 [0:4]
    self.char_total = Signal(4)                 # R22 [0:4]

    # FV outputs
    if platform == 'formal':
        self.fv_sync_width_ctr = Signal(len(self.hsync_width))
        self.fv_charpix_ctr = Signal(4)
