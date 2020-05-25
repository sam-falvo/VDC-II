from math import log2

from nmigen import Signal


# Each VDC has a version tag in its register set.
# Convenient!
VDC_VERSION = 2

# Each VDC register is 8-bits wide.
REG_WIDTH=8

# Character tile data can be no wider than 8 pixels.
MAX_PIXELS_PER_CHAR=8


def create_strip_buffer_interface(self, platform=None):
    # Video Fetch Engine Interface
    ## Inputs
    self.padr = Signal(2)
    self.cwe = Signal(1)
    self.awe = Signal(1)
    self.wadr = Signal(2)
    self.dat_i = Signal(8)

    ## Outputs
    self.pair = Signal(16)

    # Shifter Interface
    ## Inputs
    self.sh_padr = Signal(2)
    self.swap = Signal(1)

    ## Outputs
    self.sh_pair = Signal(16)

    if platform == 'formal':
        self.fv_col0a = Signal(16)
        self.fv_col1a = Signal(16)
        self.fv_col2a = Signal(16)
        self.fv_col3a = Signal(16)
        self.fv_col0b = Signal(16)
        self.fv_col1b = Signal(16)
        self.fv_col2b = Signal(16)
        self.fv_col3b = Signal(16)
        self.fv_ab = Signal(1)


def create_video_fetch_interface(self, platform=None):
    # Video Timing Interface
    ## Inputs
    self.atrptr = Signal(16)
    self.chrptr = Signal(len(self.atrptr))
    self.go_i = Signal(1)
    self.ldptr = Signal(1)
    self.ra = Signal(5)

    ## Outputs
    self.done_o = Signal(1)

    # Register Set Interface
    ## Inputs
    self.attr_enable = Signal(1)
    self.bitmap_mode = Signal(1)
    self.fontbase = Signal(3)
    self.tallfont = Signal(1)

    ## Outputs

    # Video Memory Interface
    ## Inputs
    self.ack_i = Signal(1)
    self.stall_i = Signal(1)

    ## Outputs
    self.adr_o = Signal(len(self.atrptr))
    self.cyc_o = Signal(1)
    self.stb_o = Signal(1)

    # Strip Buffer Interface
    ## Inputs
    self.charcode = Signal(9)

    ## Outputs
    self.awe = Signal(1)
    self.cwe = Signal(1)
    self.padr = Signal(2)
    self.wadr = Signal(2)

    if platform == 'formal':
        self.fv_ag_a1 = Signal(1)
        self.fv_ag_a2 = Signal(1)
        self.fv_ag_a3 = Signal(1)
        self.fv_ag_a4 = Signal(1)
        self.fv_ag_c1 = Signal(1)
        self.fv_ag_c2 = Signal(1)
        self.fv_ag_c3 = Signal(1)
        self.fv_ag_c4 = Signal(1)
        self.fv_ag_f1 = Signal(1)
        self.fv_ag_f2 = Signal(1)
        self.fv_ag_f3 = Signal(1)
        self.fv_ag_f4 = Signal(1)
        self.fv_ag_go_font = Signal(1)
        self.fv_ag_idle = Signal(1)
        self.fv_atrptr = Signal(len(self.adr_o))
        self.fv_chrptr = Signal(len(self.adr_o))
        self.fv_dr_idle = Signal(1)
        self.fv_dr_a1 = Signal(1)
        self.fv_dr_a2 = Signal(1)
        self.fv_dr_a3 = Signal(1)
        self.fv_dr_a4 = Signal(1)
        self.fv_dr_c1 = Signal(1)
        self.fv_dr_c2 = Signal(1)
        self.fv_dr_c3 = Signal(1)
        self.fv_dr_c4 = Signal(1)
        self.fv_dr_f1 = Signal(1)
        self.fv_dr_f2 = Signal(1)
        self.fv_dr_f3 = Signal(1)
        self.fv_dr_f4 = Signal(1)
        self.fv_bitmap_mode = Signal(1)


def create_shifter_interface(self, platform=None):
    # CRTC Interface
    ## Inputs
    self.hclken = Signal(1)
    self.den = Signal(1)
    self.hs = Signal(1)
    self.vs = Signal(1)
    self.vden = Signal(1)

    # Register Set Interface
    ## Inputs
    self.hscroll = Signal(4)
    self.hcd = Signal(4)
    self.hct = Signal(4)
    self.vct = Signal(5)
    self.fgpen = Signal(4)
    self.bgpen = Signal(4)
    self.attr_enable = Signal(1)
    self.blink_rate = Signal(1)
    self.reverse_screen = Signal(1)
    self.atrbase = Signal(16)
    self.chrbase = Signal(16)
    self.vscroll = Signal(5)
    self.bitmap_mode = Signal(1)

    # Video Interface
    ## Outputs
    self.outpen = Signal(4)

    # Video Fetch Engine Interface
    self.atrptr = Signal(16)
    self.chrptr = Signal(16)
    self.ra = Signal(5)
    self.go_ldptr = Signal(1)

    # Strip Buffer Interface
    ## Inputs
    self.attr_pen = Signal(4)
    self.attr_rvs = Signal(1)
    #self.attr_underline = Signal(1)
    self.attr_blink = Signal(1)
    self.char_bm = Signal(8)
    self.done_prefetch = Signal(1)

    ## Outputs
    self.go_prefetch = Signal(1)
    self.swap_strip = Signal(1)
    self.padr = Signal(2)

    if platform == 'formal':
        self.fv_reveal_ctr = Signal(4)
        self.fv_conceal_ctr = Signal(4)
        self.fv_chrgate = Signal(1)
        self.fv_dot = Signal(1)
        self.fv_sbsm_wait_hs = Signal(1)
        self.fv_sbsm_wait_hs_not = Signal(1)
        self.fv_sbsm_wait_vden = Signal(1)
        self.fv_sbsm_prefetch = Signal(1)
        self.fv_sbsm_wait_den = Signal(1)
        self.fv_lpic = Signal(1)
        self.fv_sbsm_column0 = Signal(1)
        self.fv_sbsm_column1 = Signal(1)
        self.fv_sbsm_column2 = Signal(1)
        self.fv_sbsm_column3 = Signal(1)
        self.fv_pixctr = Signal(3)
        self.fv_lastrow = Signal(1)
        self.fv_bump_atrptr = Signal(1)
        self.fv_bump_chrptr = Signal(1)


def create_blockram_arbiter_interface(self, platform=None, asize=14):
    # VFE Memory Interface
    ## Inputs
    self.vfe_adr_i = Signal(asize)
    self.vfe_cyc_i = Signal(1)
    self.vfe_dat_i = Signal(8)
    self.vfe_stb_i = Signal(1)
    self.vfe_we_i = Signal(1)

    ## Outputs
    self.vfe_ack_o = Signal(1)
    self.vfe_dat_o = Signal(8)
    self.vfe_stall_o = Signal(1)

    # MPE Memory Interface
    ## Inputs
    self.mpe_adr_i = Signal(asize)
    self.mpe_cyc_i = Signal(1)
    self.mpe_dat_i = Signal(8)
    self.mpe_stb_i = Signal(1)
    self.mpe_we_i = Signal(1)

    ## Outputs
    self.mpe_ack_o = Signal(1)
    self.mpe_dat_o = Signal(8)
    self.mpe_stall_o = Signal(1)

    # Block RAM Interface
    ## Inputs
    self.dat_i = Signal(8)

    ## Outputs
    self.adr_o = Signal(asize)
    self.dat_o = Signal(8)
    self.we_o = Signal(1)

    if platform == 'formal':
        pass


def create_mpe_interface(self, platform='', abus_width=14):
    # Register-File Interface
    ## Outputs
    self.ready = Signal(1)
    self.cpudatar = Signal(8)
    self.incr_updloc = Signal(1)
    self.incr_copysrc = Signal(1)
    self.decr_bytecnt = Signal(1)

    ## Inputs
    self.go_wr_updloc = Signal(1)
    self.go_rd_cpudatar = Signal(1)
    self.go_wr_cpudataw = Signal(1)
    self.go_wr_bytecnt = Signal(1)
    self.update_location = Signal(16)
    self.cpudataw = Signal(8)
    self.block_copy = Signal(1)
    self.copysrc = Signal(16)
    self.bytecnt = Signal(8)

    # Memory Interface
    ## Outputs
    self.mem_cyc_o = Signal(1)
    self.mem_stb_o = Signal(1)
    self.mem_adr_o = Signal(abus_width)
    self.mem_we_o = Signal(1)
    self.mem_dat_o = Signal(8)

    ## Inputs
    self.mem_stall_i = Signal(1)
    self.mem_ack_i = Signal(1)
    self.mem_dat_i = Signal(8)

    if platform == 'formal':
        self.fv_prefetch_0 = Signal(1)
        self.fv_prefetch_1 = Signal(1)
        self.fv_store_0 = Signal(1)
        self.fv_store_1 = Signal(1)
        self.fv_block_0 = Signal(1)
        self.fv_block_1 = Signal(1)
        self.fv_block_2 = Signal(1)
        self.fv_block_3 = Signal(1)


def create_vdc2_interface(self, platform=""):
    # Register Set
    ## Inputs
    self.adr_i = Signal(6)
    self.we_i = Signal(1)
    self.dat_i = Signal(8)

    ## Outputs
    self.dat_o = Signal(8)
    self.ready_o = Signal(1)

    # Video Interface
    ## Outputs
    self.hs = Signal(1)
    self.vs = Signal(1)
    self.raw_vs = Signal(1)
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
    self.rd_i = Signal(1)

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
    self.vscroll = Signal(5)
    self.blink_rate = Signal(1)
    self.reverse_screen = Signal(1)
    self.block_copy = Signal(1)
    self.bitmap_mode = Signal(1)
    self.attr_enable = Signal(1)
    self.semigraphic_mode = Signal(1)
    self.dotclock_select = Signal(1)
    self.hscroll = Signal(4)
    self.fgpen = Signal(4)
    self.bgpen = Signal(4)
    self.atrbase = Signal(16)
    self.chrbase = Signal(16)
    self.tallfont = Signal(1)
    self.fontbase = Signal(3)

    # Memory Port Engine/DMA Engine Interface
    ## Inputs
    self.cpudatar = Signal(8)
    self.incr_updloc = Signal(1)
    self.incr_copysrc = Signal(1)
    self.decr_bytecnt = Signal(1)

    ## Outputs
    self.update_location = Signal(16)
    self.copysrc = Signal(16)
    self.cpudataw = Signal(8)
    self.bytecnt = Signal(8)
    self.go_wr_updloc = Signal(1)
    self.go_rd_cpudatar = Signal(1)
    self.go_wr_cpudataw = Signal(1)
    self.go_wr_bytecnt = Signal(1)


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
    self.rd_o = Signal(1)

    if platform == 'formal':
        self.fv_old_cssync = Signal(1)
        self.fv_cssync = Signal(1)
        self.fv_rdsync = Signal(1)
        self.fv_we_ports = Signal(1)
        self.fv_rd_ports = Signal(1)
        self.fv_async = Signal(1)
        self.fv_dsync = Signal(len(self.d))
