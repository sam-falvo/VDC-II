from nmigen.test.utils import FHDLTestCase
from nmigen import (
    Elaboratable,
    Module,
)


class HSyncFormal(Elaboratable):
    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        return m


class HSyncTestCase(FHDLTestCase):
    def test_hsync(self):
        self.assertFormal(HSyncFormal(), mode='bmc', depth=100)
        #self.assertFormal(HSyncFormal(), mode='prove', depth=100)
