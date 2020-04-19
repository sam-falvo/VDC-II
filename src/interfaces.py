from math import log2

from nmigen import Signal


# Each VDC has a version tag in its register set.
# Convenient!
VDC_VERSION = 2

# Each VDC register is 8-bits wide.
REG_WIDTH=8

# Character tile data can be no wider than 8 pixels.
MAX_PIXELS_PER_CHAR=8

# Horizontal and vertical totals are given in units of
# characters, not pixels.  Characters, in turn, are
# specified through the character total and character
# displayed fields.  The 8568 VDC allots 8 bits to a 
# horizontal total field, and up to 31 for a vertical
# total.
COUNTER_WIDTH=8
HCOUNTER_WIDTH=COUNTER_WIDTH


def create_syncgen_interface(self, platform="", ctr_width=COUNTER_WIDTH):
    # outputs
    self.counter = Signal(ctr_width)
    self.total_reached = Signal(1)
    self.xsync = Signal(1)
    self.last = Signal(1)

    # inputs
    #
    # Inputs come from the following sources in the
    # VDC register set:
    #
    #              HSYNC     VSYNC
    #              --------  --------
    # total        R00       R04
    # sync_pos     R02       R07
    # sync_width   R03[0:4]  R03[4:8]
    # char_total   R22[0:4]  R22[4:8]
    self.total = Signal(len(self.counter))
    self.sync_pos = Signal(len(self.counter))
    self.sync_width = Signal(4)
    self.char_total = Signal(4)

    # FV outputs
    if platform == 'formal':
        self.fv_sync_width_ctr = Signal(len(self.sync_width))
        self.fv_unit_ctr = Signal(4)


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
    self.hsync_xor = Signal(1)
    self.vsync_xor = Signal(1)


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
