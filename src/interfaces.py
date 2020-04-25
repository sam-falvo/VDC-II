from math import log2

from nmigen import Signal


# Each VDC has a version tag in its register set.
# Convenient!
VDC_VERSION = 2

# Each VDC register is 8-bits wide.
REG_WIDTH=8

# Character tile data can be no wider than 8 pixels.
MAX_PIXELS_PER_CHAR=8


def create_vdc2_interface(self, platform=""):
    # Register Set
    ## Inputs
    self.adr_i = Signal(6)
    self.we_i = Signal(1)
    self.dat_i = Signal(8)

    ## Outputs
    self.dat_o = Signal(8)

    # Video Interface
    ## Outputs
    self.hs = Signal(1)
    self.vs = Signal(1)
    self.r = Signal(1)
    self.g = Signal(1)
    self.b = Signal(1)
    self.i = Signal(1)


def create_syncgen_interface(
    self, platform="",
    char_total_bits=4, total_bits=8, sync_pos_bits=8, sync_width_bits=4,
    disp_bits=8, adj_bits=4
):
    # inputs
    #
    # Inputs come from the following sources in the
    # VDC register set:
    #
    #              X-Axis    Y-Axis
    #              --------  --------
    # xt           R00       R04
    # xta          -         R05
    # xd           R01       R06
    # xsp          R02       R07
    # xsw          R03[0:4]  R03[4:8]
    # xct          R22[0:4]  R09[0:5]

    self.dotclken = Signal(1)
    self.syncen = Signal(1)
    self.xct = Signal(char_total_bits)
    self.xt = Signal(total_bits)
    self.xsp = Signal(sync_pos_bits)
    self.xsw = Signal(sync_width_bits)
    self.xd = Signal(disp_bits)
    self.xta = Signal(adj_bits)

    # outputs
    self.xclken = Signal(1)
    self.xs = Signal(1)
    self.xden = Signal(1)
    self.rastclken = Signal(1)

    # FV outputs
    if platform == 'formal':
        self.fv_xdot = Signal(len(self.xct))
        self.fv_xchr = Signal(len(self.xt))
        self.fv_xtotal = Signal(1)
        self.fv_go_xsync = Signal(1)
        self.fv_xsctr = Signal(len(self.xsw))
        self.fv_xdctr = Signal(len(self.xd))
        self.fv_adj = Signal(1)
        self.fv_adjctr = Signal(len(self.xta))

    self.tp0 = Signal(1)
    self.tp1 = Signal(1)
    self.tp2 = Signal(1)
    self.tp3 = Signal(1)


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
    self.hd = Signal(8)
    self.hsp = Signal(8)
    self.vsw = Signal(4)
    self.hsw = Signal(4)
    self.vt = Signal(8)
    self.vta = Signal(5)
    self.vd = Signal(8)
    self.vsp = Signal(8)
    self.vct = Signal(5)
    self.hcd = Signal(4)
    self.hct = Signal(4)
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
