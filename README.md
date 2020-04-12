# VDC-II
The VDC-II core is an open source Video Display Controller following in the footsteps, but not a pure clone, of the Commodore 8568 VDC chip.

Link to project on [Hackaday.io](https://hackaday.io/project/170581-vdc-ii).

## Why?
I'm working on a homebrew computer of my own design, called the Kestrel-3.
The Kestrel-3 project, however, is very slow-going, as I'm basically building everything from the ground up.
I was asked if I could instead implement the salient bits of the Kestrel-3's video core, the Configurable Graphics Interface Adapter, or CGIA, for the RC2014 backplane.
That would both speed up development of the Kestrel-3 project, as I'm more focused on individual components, but also can benefit the RC2014 community as well.
I said, "that sounds like a great idea!"

Problem is, I've never built an RC2014 or an expansion board for it before.
And, there are many unknowns along the way:
for example, I've never worked with level shifting logic before,
and interfacing a 25MHz dot-clock circuit to the 7MHz bus of the RC2014 will involve multiple clock domains and its respective complexities.
To get my feet wet, I decided to target a design for the 39-pin RC2014 expansion bus using a small FPGA part, specifically the TinyFPGA BX.

The problem with the TinyFPGA BX is that I'm severely I/O limited!
But, with careful interface design, and a constriction on the number of I/O ports accessible to the host CPU, I was able to fit everything into the pins available.
Also, the TinyFPGA BX provides 16KB of block RAM resources, and that sparked a memory: didn't the C128's VDC chip only have 16KB available to it?

Turns out, yes.  And, it also has a constrained host CPU interface as well.
And looking through the C128's Programmers Reference Manual on how to code for the VDC chip,
I saw that much of the CGIA's feature set was already present in the VDC.  Not everything, but most things for sure!
So, I got to thinking, instead of using the CGIA as the basis,
maybe I can create a version of the VDC chip which can drive a VGA monitor, flexibly.
After all,
the [RomWBW HBIOS](https://github.com/wwarthen/RomWBW/blob/master/Source/HBIOS/cvdu.asm)
software already has a VDC driver available for it, so porting software should be much easier.
(Though, strangely, it goes by the name CVDU or Color VDU in the source tree.)
That's the operating theory, at least.

The VDC-II project was born.

## Description
The VDC-II core aims to be a worthy successor to the original Commodore VDC design.
Unlike the original VDC chip, which runs at NTSC frequencies, the VDC-II core is intended to drive a VGA monitor.

While 100% backward compatibility is not my primary goal, I would continue to strive for it where I can afford to.
There will be some features which will simply work differently between the VDC and VDC-II,
such as how horizontal smooth scrolling works.
Some of these incompatibilities will stem naturally from the fact that we're driving a VGA display instead of a CGA display.
**Disclaimer: I do not have a real Commodore 128 to test behavior with.**
I'm limited to comparing behavior against what the Vice `x128` emulator supports.

## Goals
Most importantly, I want to make a VDC-II core that achieves *basic* feature parity with the original VDC.
This should include supporting all 37 of the original register set.
**Note:** Not all bits of all registers will be supported, or will work *exactly* the same way.
For example, the complex interaction between inter-character gaps and horizontal smooth scrolling might compel me to just leave inter-character gaps out of the design.
(Kind of how `x128` does now.)

Going into future day-dreaming mode,
I'd next implement color palette registers,
giving the VDC-II core more color options.
I'd also support an alternative attribute format which allows for both 16 foreground *and* background colors.

The VDC-II core could conceivably be expanded to support sprites as well, perhaps using an interface not unlike the TMS9918A VDP.
This will be very nice for, e.g., supporting mouse pointers and text cursors while in bitmapped mode (e.g., GEOS/128).

## Resources
These are some handy references and resources I've found to help guide my development.
These might be of interest to you as well.

- https://www.retrobrewcomputers.org/lib/exe/fetch.php?media=boards:ecb:cvdu:8563notes.txt
- [Commodore 128 Programmer's Reference Guide](https://www.pagetable.com/?p=620)

