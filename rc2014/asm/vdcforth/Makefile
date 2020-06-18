CPMFS=asdf.d71
FORTH_DRIVERS=drivers/evtloop/cpm2.asm drivers/osal/cpm2.asm drivers/vdc/c128.asm drivers/data.asm
FORTH_SRCS=usecase/startup/vdcforth.asm

help:
	@echo "make d71   -- builds a D71 file named ${CPMFS} for a C128 emulator"
	@echo "make run   -- As above, but also launches the C128 emulator"
	@echo "make clean -- Delete all build artifacts"
	@echo "make help  -- shows this message."


.phony: clean
clean:
	rm -f *.o *.err *.com *.bin ${CPMFS}
	rm -f tvdc.asm

.phony: run
run: d71
	x128 -8 cpmf3-1.d64 -10 ${CPMFS}


.phony: d71
d71: ${CPMFS} vdcforth.com tvdc.com
	yes | ctools ${CPMFS} p vdcforth.com
	yes | ctools ${CPMFS} p tvdc.com


.phony: ${CPMFS}
${CPMFS}:
	cformat -2 ${CPMFS}


vdcforth.com: ${FORTH_DRIVERS} ${FORTH_SRCS}
	z80asm -b vdcforth.asm
	mv vdcforth.bin vdcforth.com


tvdc.com: tvdc.asm.m4 testdefs.asm.m4 drivers/osal/cpm2.asm drivers/vdc/c128.asm drivers/data.asm utils.asm tester.asm
	m4 tvdc.asm.m4 >tvdc.asm
	z80asm -b tvdc.asm
	mv tvdc.bin tvdc.com
