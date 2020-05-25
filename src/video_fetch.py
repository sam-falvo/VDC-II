from nmigen import (
    Cat,
    Elaboratable,
    Module,
    Signal,
)

from interfaces import create_video_fetch_interface


class VideoFetch(Elaboratable):
    """
    The VideoFetch module is responsible for referencing video memory
    in the correct order and with the correct timing needed to ensure
    that the next strip buffer contents is available for display before
    it's actually needed.

    This module doesn't actually implement the strip buffers.

    Signals:

    # Video Timing Interface
    - atrptr.  The current attribute pointer.  Note that this IS NOT the same
      as the contents of the attribute base address in the register set.
    - chrptr.  The current character pointer.  Note that this IS NOT the same
      as the contents of the character base address in the register set.
    - go_i.  When asserted, it kicks off the next batch of read cycles.
    - ldptr.  When asserted in conjunction with go_i, it causes the character
      and attribute pointer registers to be reloaded.  Otherwise, these
      registers will retain their current values.
    - ra.  Row Address.  This input indicates which row of pixels is currently
      being refreshed within the character row.
    
    # Register Set Interface
    - attr_enable.  If asserted, attribute fetches will occur.  Otherwise,
      they will be skipped.
    - bitmap_mode.  If asserted, character codes fetched will be treated
      as bitmapped pixels, and font memory will not be referenced.  Otherwise,
      character codes (in conjunction with the `ra` signal above) are used
      to reference font memory in order to provide bitmap data for
      serialization.
    - fontbase.  Sets the upper 3 bits (2 bits) of the font base address if
      the font height is 16 (resp., 32) pixels tall.
    - tallfont.  If asserted, fonts are taken to have up to 32 rows.
      Otherwise, they're taken to have 16 rows.

    # Video Memory Interface
    - ack_i.  Asserted by the video memory system when referenced data is valid
      on the data bus.  Note that the VideoFetch module doesn't use this data,
      which is why it lacks a corresponding dat_i signal.  The video memory data
      must be routed to the stripe buffers instead.
    - adr_o.  The video fetch address.
    - cyc_o.  Remains asserted by the VideoFetch unit for as long as it is
      waiting for new data.  It will be negated when this video fetch burst
      has concluded.  cyc_o is used by arbiters and crossbar switches to
      know when access to video memory is being requested.
    - stall_i.  Asserted by the video memory system when it cannot accept a
      new address at the moment.
    - stb_o.  Asserted by VideoFetch when a valid video meory address appears
      on the adr_o signal.

    # Strip Buffer Interface
    - awe.  Asserted by VideoFetch when the video memory data bus is known to
      have valid attribute data.
    - charcode.  This signal is driven by the strip buffer, providing an
      asynchronous view of the currently selected character code.  Note that
      this signal is 9-bits in length, not 8.  The 9th bit is usually driven
      by the top attribute bit for the character cell.
    - cwe.  Asserted by VideoFetch when the video memory data bus is known to
      have valid character data.
    - padr.  Pair Address.  This output is routed to the stripe buffer, where
      the stripe buffer will then drive the charcode input with the selected
      character code.  (Pair Address is named because one address selects a
      pair of bytes: the attribute and the corresponding character code.)
    - wadr.  Write Address.  This output is routed to the stripe buffer,
      where it determines which character (cwe) or attribute (awe) register
      receives the data currently on the video memory data bus.
    """

    def __init__(self, platform=None):
        super().__init__()
        create_video_fetch_interface(self, platform=platform)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Address Generation Logic.

        ag_go_font = Signal(1)

        atrptr = Signal(len(self.adr_o))
        chrptr = Signal(len(self.adr_o))
        fontptr = Signal(len(self.adr_o))
        safe_to_go = Signal(1)
        ag_idle = Signal(1)
        dr_idle = Signal(1)
        r_bitmap_mode = Signal(1)

        atrptr_inc = Signal(len(atrptr))
        chrptr_inc = Signal(len(chrptr))

        comb += [
            atrptr_inc.eq(atrptr + 1),
            chrptr_inc.eq(chrptr + 1),
            safe_to_go.eq(ag_idle & dr_idle),
        ]
        with m.If(self.tallfont):
            comb += fontptr.eq(Cat(self.ra[0:5], self.charcode, self.fontbase[1:3]))
        with m.Else():
            comb += fontptr.eq(Cat(self.ra[0:4], self.charcode, self.fontbase[0:3]))

        with m.FSM() as ag:
            comb += ag_idle.eq(ag.ongoing("idle"))
            with m.State("idle"):
                with m.If(self.go_i & safe_to_go):
                    sync += r_bitmap_mode.eq(self.bitmap_mode)
                    with m.If(self.ldptr):
                        sync += [
                            atrptr.eq(self.atrptr),
                            chrptr.eq(self.chrptr),
                        ]
                    with m.If(self.attr_enable):
                        m.next = "a1"
                    with m.Else():
                        m.next = "c1"

            with m.State("a1"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "a2"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("a2"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "a3"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("a3"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "a4"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("a4"):
                comb += [
                    self.adr_o.eq(atrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c1"
                    sync += atrptr.eq(atrptr_inc)

            with m.State("c1"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c2"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("c2"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c3"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("c3"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    m.next = "c4"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("c4"):
                comb += [
                    self.adr_o.eq(chrptr),
                    self.stb_o.eq(1),
                ]
                with m.If(~self.stall_i):
                    with m.If(~r_bitmap_mode):
                        m.next = "f1"
                    with m.Else():
                        m.next = "idle"
                    sync += chrptr.eq(chrptr_inc)

            with m.State("f1"):
                comb += [
                    self.padr.eq(0),
                    self.stb_o.eq(ag_go_font),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(ag_go_font):
                    with m.If(~self.stall_i):
                        m.next = "f2"

            with m.State("f2"):
                comb += [
                    self.padr.eq(1),
                    self.stb_o.eq(1),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(~self.stall_i):
                    m.next = "f3"

            with m.State("f3"):
                comb += [
                    self.padr.eq(2),
                    self.stb_o.eq(1),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(~self.stall_i):
                    m.next = "f4"

            with m.State("f4"):
                comb += [
                    self.padr.eq(3),
                    self.stb_o.eq(1),
                    self.adr_o.eq(fontptr),
                ]
                with m.If(~self.stall_i):
                    m.next = "idle"

            # The set of valid states takes four bits to represent internally.
            # The remaining 'states' are here to enforce a valid state.
            # In a way, we're leaking the abstraction in order to satisfy
            # formal verification and testing.

            with m.State("stateD"):
                m.next = 'idle'

            with m.State("stateE"):
                m.next = 'idle'

            with m.State("stateF"):
                m.next = 'idle'

            if platform == 'formal':
                comb += [
                    self.fv_ag_idle.eq(ag_idle),
                    self.fv_ag_a1.eq(ag.ongoing("a1")),
                    self.fv_ag_a2.eq(ag.ongoing("a2")),
                    self.fv_ag_a3.eq(ag.ongoing("a3")),
                    self.fv_ag_a4.eq(ag.ongoing("a4")),
                    self.fv_ag_c1.eq(ag.ongoing("c1")),
                    self.fv_ag_c2.eq(ag.ongoing("c2")),
                    self.fv_ag_c3.eq(ag.ongoing("c3")),
                    self.fv_ag_c4.eq(ag.ongoing("c4")),
                    self.fv_ag_f1.eq(ag.ongoing("f1")),
                    self.fv_ag_f2.eq(ag.ongoing("f2")),
                    self.fv_ag_f3.eq(ag.ongoing("f3")),
                    self.fv_ag_f4.eq(ag.ongoing("f4")),
                    self.fv_ag_go_font.eq(ag_go_font),
                ]

        #
        # Data Receiver Logic
        #
        # Because the data we expect back on the Wishbone bus is structured by
        # what the address generator uses, we must structure this FSM identically
        # to match that of the address generator FSM.
        #

        with m.FSM() as dr:
            comb += [
                self.cyc_o.eq(~dr.ongoing("idle")),
                dr_idle.eq(~self.cyc_o),
            ]
            with m.State("idle"):
                with m.If(self.go_i & safe_to_go):
                    with m.If(self.attr_enable):
                        m.next = "a1"
                    with m.Else():
                        m.next = "c1"

            with m.State("a1"):
                comb += [
                    self.wadr.eq(0),
                    self.awe.eq(self.ack_i),
                    self.cwe.eq(0),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "a2"

            with m.State("a2"):
                comb += [
                    self.wadr.eq(1),
                    self.awe.eq(self.ack_i),
                    self.cwe.eq(0),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "a3"

            with m.State("a3"):
                comb += [
                    self.wadr.eq(2),
                    self.awe.eq(self.ack_i),
                    self.cwe.eq(0),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "a4"

            with m.State("a4"):
                comb += [
                    self.wadr.eq(3),
                    self.awe.eq(self.ack_i),
                    self.cwe.eq(0),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "c1"

            with m.State("c1"):
                comb += [
                    self.wadr.eq(0),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "c2"

            with m.State("c2"):
                comb += [
                    self.wadr.eq(1),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "c3"

            with m.State("c3"):
                comb += [
                    self.wadr.eq(2),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "c4"

            with m.State("c4"):
                comb += [
                    self.wadr.eq(3),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    with m.If(r_bitmap_mode):
                        m.next = "idle"
                    with m.Else():
                        m.next = "f1"

            with m.State("f1"):
                comb += [
                    self.wadr.eq(0),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(1),
                ]
                with m.If(self.ack_i):
                    m.next = "f2"

            with m.State("f2"):
                comb += [
                    self.wadr.eq(1),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "f3"

            with m.State("f3"):
                comb += [
                    self.wadr.eq(2),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "f4"

            with m.State("f4"):
                comb += [
                    self.wadr.eq(3),
                    self.awe.eq(0),
                    self.cwe.eq(self.ack_i),
                    ag_go_font.eq(0),
                ]
                with m.If(self.ack_i):
                    m.next = "idle"

            # The set of valid states takes four bits to represent internally.
            # The remaining 'states' are here to enforce a valid state.
            # In a way, we're leaking the abstraction in order to satisfy
            # formal verification and testing.

            with m.State("stateD"):
                m.next = 'idle'

            with m.State("stateE"):
                m.next = 'idle'

            with m.State("stateF"):
                m.next = 'idle'

            if platform == 'formal':
                comb += [
                    self.fv_dr_idle.eq(dr_idle),
                    self.fv_dr_a1.eq(dr.ongoing('a1')),
                    self.fv_dr_a2.eq(dr.ongoing('a2')),
                    self.fv_dr_a3.eq(dr.ongoing('a3')),
                    self.fv_dr_a4.eq(dr.ongoing('a4')),
                    self.fv_dr_c1.eq(dr.ongoing('c1')),
                    self.fv_dr_c2.eq(dr.ongoing('c2')),
                    self.fv_dr_c3.eq(dr.ongoing('c3')),
                    self.fv_dr_c4.eq(dr.ongoing('c4')),
                    self.fv_dr_f1.eq(dr.ongoing('f1')),
                    self.fv_dr_f2.eq(dr.ongoing('f2')),
                    self.fv_dr_f3.eq(dr.ongoing('f3')),
                    self.fv_dr_f4.eq(dr.ongoing('f4')),
                ]

        if platform == 'formal':
            comb += [
                self.fv_atrptr.eq(atrptr),
                self.fv_chrptr.eq(chrptr),
                self.fv_bitmap_mode.eq(r_bitmap_mode),
            ]

        return m
