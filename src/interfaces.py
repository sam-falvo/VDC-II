from math import log2

from nmigen import Signal


# Each VDC has a version tag in its register set.
# Convenient!
VDC_VERSION = 2

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


def create_regset8bit_interface(self, platform=''):
    # Host CPU Interface
    ## Inputs
    self.adr_i = Signal(6)
    self.we_i = Signal(1)
    self.dat_i = Signal(8)

    ## Outputs
    self.dat_o = Signal(8)

    # Register Settings and Status/Flags
    ## Inputs
    ## Outputs
    self.ht = Signal(8)
    self.hp = Signal(8)
    self.hw = Signal(4)
    self.vw = Signal(4)
    self.cdh = Signal(4)
    self.cth = Signal(4)


def create_hostbus_interface(self, platform=""):
    self.a = Signal(1)
    self.rd = Signal(1)
    self.d = Signal(REG_WIDTH)
    self.cs = Signal(1)

    self.q = Signal(len(self.d))
    self.qoe = Signal(1)

    self.ready_i = Signal(1)
    self.vblank_i = Signal(1)
    self.lp_i = Signal(1)
    self.dat_i = Signal(len(self.d))
    self.dat_o = Signal(len(self.d))
    self.adr_o = Signal(6)
    self.we_o = Signal(1)

    if platform == 'formal':
        self.fv_old_cssync = Signal(1)
        self.fv_cssync = Signal(1)
        self.fv_rdsync = Signal(1)
        self.fv_we_ports = Signal(1)
        self.fv_async = Signal(1)
        self.fv_dsync = Signal(len(self.d))
