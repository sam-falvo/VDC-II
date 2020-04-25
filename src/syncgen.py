from nmigen.test.utils import FHDLTestCase
from nmigen import (
    Elaboratable,
    Module,
    Signal,
)

from interfaces import create_syncgen_interface


class SyncGen(Elaboratable):
    """
    Implements the core logic that would define a typical MC6845 or
    MOS 6545 sync generator.  Note that this does NOT define the bus
    interface for the core logic; register settings are taken as
    explicit inputs, and the external logic is free to use the outputs
    as it sees fit.

    Inputs:
    - dotclken -- Dot Clock Enable.  If negated, the module's clock has
      neglible or no effect.  Only when this signal is asserted are the
      SyncGen counters altered.  For horizontal sync generators, this
      would probably be tied to 1.  For vertical sync generators, this
      would be tied to the rastclken output of a horizontal sync generator.

    - syncen -- Sync Clock Enable.  If negated, sync generation will never
      complete.  Typically, for horizontal sync generators, this is tied
      to the xclk output, to give sync generation character resolution.
      For vertical sync generators, this is typically tied to 1 to give
      sync generation line resolution.

    - xct -- Character Total; this sets the number of pixels
      per character along the X-axis, or the number of raster lines in the
      Y-axis.  For example, a font with 5 pixels and no inter-character gaps
      would set this to 4.  A font 8-pixels wide with a one pixel inter-
      character gap would set this to 8.

    - xt -- Total; this sets the maximum number of characters
      in a single scanline or playfield.

    - xsp -- Sync Position; relative to the left-edge of the visible
      playfield, sets how far to the right the horizontal sync pulse sits.
      Relative to the top of the playfield, it sets how far below the
      vertical sync pulse sits.

    - xsw -- Sync Width, in characters (horizontal) or lines (vertical).

    - xd -- Horizontal Displayed; determines how wide the visible playfield
      is in characters.

    Outputs:
    - xclken -- Asserted while the display is painting the right-most (resp.,
      bottom-most) dot (line) of a character.  The falling edge of this signal
      demarcates the end of one character and the start of the next.

    - xs -- Sync.

    - xden -- Display Enable.  Asserted during the portion of
      the playfield which will show the frame buffer contents.

    - rastclken -- Raster Clock Enable.  When asserted it grants the next
      sync generator permission to count.
    """

    def __init__(self, **kw_args):
        super().__init__()
        create_syncgen_interface(self, **kw_args)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        #
        # Horizontal Total Adjust support.
        #
        # Note: adjctr is reloaded later on in the source.
        #

        adjctr = Signal(len(self.xta))
        adj = Signal(1)

        comb += adj.eq(adjctr != 0)

        with m.If(self.dotclken):
            with m.If(adj):
                sync += adjctr.eq(adjctr - 1)

        #
        # Horizontal Character Clocking
        #

        xdot = Signal(len(self.xct))
        xclken = Signal(1)

        comb += [
            xclken.eq(xdot == self.xct),
            self.xclken.eq(xclken),
        ]

        with m.If(self.dotclken):
            with m.If(xclken):
                sync += xdot.eq(0)

            with m.If(~xclken & ~adj):
                sync += xdot.eq(xdot + 1)

        #
        # Horizontal Line Clocking
        #

        xchr = Signal(len(self.xt))
        xtotal = Signal(1)

        comb += [
            xtotal.eq(xchr == self.xt),
        ]

        with m.If(self.dotclken):
            with m.If(~adj):
                with m.If(xclken & ~xtotal):
                    sync += xchr.eq(xchr + 1)
                with m.If(xclken & xtotal):
                    with m.If(self.xta == 0):
                        sync += xchr.eq(0)
                    with m.If(self.xta != 0):
                        sync += adjctr.eq(self.xta)

            with m.If(adjctr == 1):
                sync += xchr.eq(0)

        #
        # Horizontal Sync Generator
        #

        xsctr = Signal(len(self.xsw))
        go_xsync = Signal(1)

        comb += [
            self.xs.eq(xsctr != 0),
            self.rastclken.eq(xsctr == 1),
            go_xsync.eq(xchr == self.xsp),
        ]

        with m.If(self.dotclken):
            with m.If(self.syncen & self.xclken & go_xsync):
                sync += xsctr.eq(self.xsw)
            with m.If(self.syncen & ~go_xsync & self.xs):
                sync += xsctr.eq(xsctr - 1)

        #
        # Horizontal Display Enable Generator
        #

        xdctr = Signal(len(self.xd))

        comb += [
            self.xden.eq(xdctr != 0),
        ]

        with m.If(self.dotclken):
            with m.If(xclken & xtotal):
                sync += xdctr.eq(self.xd)
            with m.If(xclken & ~xtotal & self.xden):
                sync += xdctr.eq(xdctr - 1)

        if platform == 'formal':
            comb += [
                self.fv_xdot.eq(xdot),
                self.fv_xchr.eq(xchr),
                self.fv_xtotal.eq(xtotal),
                self.fv_go_xsync.eq(go_xsync),
                self.fv_xsctr.eq(xsctr),
                self.fv_xdctr.eq(xdctr),
                self.fv_adj.eq(adj),
                self.fv_adjctr.eq(adjctr),
            ]

        return m
