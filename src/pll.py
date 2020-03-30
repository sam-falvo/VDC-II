# This module is taken from the following source and used with permission:
# https://github.com/GlasgowEmbedded/glasgow/blob/master/software/glasgow/gateware/pll.py


import logging
from nmigen import *


__all__ = ["PLL"]


class PLL(Elaboratable):
    def __init__(self, f_in, f_out, odomain, idomain="sync", logger=None):
        self.logger  = logger or logging.getLogger(__name__)
        self.f_in    = float(f_in)
        self.f_out   = float(f_out)
        self.odomain = odomain
        self.idomain = idomain

    def elaborate(self, platform):
        if hasattr(platform, "get_pll"):
            return platform.get_pll(self)

        raise NotImplementedError("No PLL support for platform")
