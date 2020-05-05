# Description

The syncgen module is designed to provide horizontal and vertical sync pulse trains to a VGA-compatible video device.
A single syncgen module provides either horizontal or vertical sync pulses.
However, two syncgen module instances may be cascaded to provide both horizontal and vertical pulse trains.


# Features

- Compatible with Commodore/MOS 6545 CRTC and 8563 VDC sync generators.
- Configurable sync width and position.
- Support for characters up to 32 pixels wide and 32 pixels tall.
- Progressive scan.


# Interface Signal Description


         clk >----------------.
       reset >------------.   |
                          |   |
                       +---------+
                       |         |
    dotclken >---------|         |---------> xclken
                       |         |
      syncen >---------|         |---------> xs
                       |         |
         xct >--/------|         |---------> xden
               4-5     |         |
          xt >------/--|         |---------> rastclken
                    8  | SyncGen |
         xsp >--/------|         |
                8      |         |
         xsw >------/--|         |
                    4  |         |
          xd >--/------|         |
                8      |         |
         xta >------/--|         |
                   4-5 |         |
                       +---------+


## Implied Signals

### clk

All syncgen instances are intended to be clocked from the master dot-clock.
Ideally, for precise VGA compatibility, this would be a 25.175MHz or 25.2MHz clock.

### reset

If asserted, internal syncgen state is reset upon the next clock edge.
`dotclken` and `syncen` are ignored.

## Register File Interface

These signals are intended to be routed to a register file accessible to the host processor.
The `RegSet8Bit` module implements a MOS/CSG 8563 compatible register set.

### xct

Character Dot Total.
This sets the number of pixels per character
by identifying the largest value that a character dot counter may reach
before it resets back to zero.
For example,
if you want a 5-pixel wide font with a one pixel gap between characters,
you'd set this input to 5.
If you want an 8-pixel wide font with no gaps between characters,
you'd set this input to 7.

### xt
Axis Total.
This sets the maximum number of characters along the axis of the display
by setting the largest value the total counter may reach
before it resets back to zero.

For example,
if you're using a typical VGA display configuration of 25.1MHz dot-clock,
an 8-pixel wide font with no gaps,
and a horizontal sync frequency of 31.5kHz,
you would set this input to 98:

                  25.1e6 pix/sec
    floor(----------------------------)-1 = 98
          (8 pix/chr)(31500 lines/sec)

If your dot-clock is instead runs at 16MHz,
and you're using a 4-pixel wide font with 1-pixel gap,
you would set this input to 100:

                  16.0e6 pix/sec
    floor(----------------------------)-1 = 100
          (5 pix/chr)(31500 lines/sec)

### xsp
Sync Position.
This input determines where the sync signal appears relative to an edge of the playfield.
For a horizontal syncgen instance,
this determines how far to the right of the left-edge of the visible playfield the sync pulse appears.
For a vertical syncgen interface,
this determines how far below the top of the visible playfield the sync pulse appears.
This field is measured in character units.

### xsw
Sync Width.
This input determines how wide the sync pulse is.
The unit of measurement is determined by how the `syncen` input is connected.

### xd
Display Width.
This input determines the number of characters comprising the visible playfield.
For example, a horizontal syncgen instance might be set to 80 for an 80-column display.
This field is measured in character units.

### xta
Total Adjust.
Sometimes, the number of character units is not sufficient to completely determine timing parameters.
For example, a vertical syncgen instance might be configured to render a 25-line display on a VGA display.
To fit the 480 pixel vertical resolution as best as possible, you'll want a floor(480/25)=19 pixel tall font.
You'd therefore configure `xct` to be (floor(480/25)-1)=18,
`xd` to 25,
and `xt` to floor(525/19)-1 = 26.
However, this still leaves 12 scanlines unaccounted for.
The `xta` input would be set to 12 to provide proper sync timing adjustment.

**Note:** The MOS 6545 and CSG 8563 lack a horizontal total adjust setting.
For compatibility with these devices, you'll want to strap `xta` to 0 for horizontal sync generators.

## Video Interface

### dotclken

Dot Clock Enable.
This input serves as a more convenient way to
emulate multiple clock domains in programmable logic
without actually creating multiple clock domains.
If negated, the module's clock has negligible or no effect.
Only when this input is asserted are the internal counters altered.

For horizontal sync generators, this signal is typically strapped to 1.
For vertical sync generators,
this signal is typically connected
to the `rastclken` output of the horizontal sync generator.

### syncen

Sync Clock Enable.
This input is used to configure the unit of measurement
for the sync width input, `xsw`.

To measure the sync width in characters,
such as you'd find in a typical 6545-compatible horizontal sync generator,
you'd route the `xclken` output to `syncen`.

To measure the sync width in pixels,
such as you'd find in a typical 6545-compatible vertical sync generator,
you'd fix the `syncen` input to 1.

If `syncen` is ever held low for extended time periods,
sync generation never completes.

### xclken

Character Clock Enable.
This output is used to indicate when the last dot of the character occurs.
This can help external dot-shifter circuits to reload the next byte of bitmap data at the appropriate time,
can help determine sync width unit of measurement,
etc.

### xs

Sync.
This active-high output is used to synchronize the display device.
External inversion is required for displays expecting an active-low signal.

### xden
Display Enable.
This active-high output is used to identify the visible playfield.
For example, if you route the logical-AND of the horizontal and vertical display enable signals
to the red gun output of a display, you will see a red square which covers where the playfield will appear.

### rastclken
Raster Clock Enable.
This output is asserted when the total counter has reached its limit and is about to reset to zero.
This output is used to cascade syncgen instances together to create compound timing chains.
On a horizontal sync generator, it delineates raster lines.
On a vertical sync generator, it delineates fields.
Since the syncgen module does not support interlaced displays at this time,
a field corresponds to a frame.


# Instantiation

You can instantiate the SyncGen module as you would any other in nMigen.
The constructor takes several optional arguments which determines the bit-width of the character total and total adjust fields.

| Keyword       | Default | Meaning                              |
|:--------------|:-------:|:-------------------------------------|
|char_total_bits|4        |The number of bits in the `xct` field.|
|adj_bits       |4        |The number of bits in the `xta` field.|


# Example Application

The following application more or less replicates the MOS 6545 CRTC timing chain.


    clk25MHz >----------------.
       reset >------------.   |
                          |   |
                    .-----|---|-----------------.
                    |  +---------------------+  |
                    |  |                     |  |
              "1" -----|dotclken      xclken |--*-----------.
                    |  |                     |              |
                    `--|syncen            xs |-------------------------------> HSYNC
                       |                     |              |   +---+
         hct >--/------|xct             xden |------------------|   |
                4      |                     |       .----------| & |--------> DEN
          ht >------/--|xt         rastclken |-------|----. |   +---+
                    8  |                     |       |    | |
         hsp >--/------|xsp                  |       |    | |
                8      |                     |       |    | |
         hsw >------/--|xsw                  |       |    | |
                    4  |                     |       |    | |
          hd >--/------|xd             H     |       |    | |
                8      |            SyncGen  |       |    | |
              "0" --/--|xta                  |       |   +---+
                    4  |                     |       |   | & |
                       +---------------------+       |   +---+
                          |   |                      |     |
                    .-----|---|----------------------|-----*
                    |     |   |                      |     |
                    |  +---------------------+       |     |
                    |  |                     |       |     |
                    *--|dotclken      xclken |----------*--------------------> BADLINE
                    |  |                     |       |  |  |
                    `--|syncen            xs |-------------------------------> VSYNC
                       |                     |       |  |  |    +---+
         vct >--/------|xct             xden |-------'  |  `----|   |
                5      |                     |          `-------| & |--------> VSYNC_IRQ
          vt >------/--|xt         rastclken |------------------|   |
                    8  |                     |                  +---+
         vsp >--/------|xsp                  |
                8      |                     |
         vsw >------/--|xsw                  |
                    4  |                     |
          vd >--/------|xd             V     |
                8      |            SyncGen  |
         vta >------/--|xta                  |
                    5  |                     |
                       +---------------------+


HSYNC and VSYNC would drive the monitor directly, perhaps through inverters as needed.
BADLINE would assert when the last raster-line currently displayed is the last for that character row.
This would trigger a memory fetch for the next row of character and attribute codes, for example.
