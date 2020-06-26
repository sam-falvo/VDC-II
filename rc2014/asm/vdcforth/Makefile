CPMFS=asdf.d71
FORTH_DRIVERS=drivers/evtloop/cpm2.asm drivers/osal/cpm2.asm drivers/vdc/c128.asm drivers/data.asm
FORTH_SRCS=consts.asm usecase/startup/vdcforth.asm usecase/cmdline/tib.asm usecase/cmdline/control.asm usecase/cmdline/view.asm
TVDC_DRIVERS=drivers/osal/cpm2.asm drivers/vdc/c128.asm drivers/data.asm
TVDC_SRCS=drivers/vdc/tests/tvdc.asm.m4 testdefs.asm.m4 utils.asm tester.asm
TCMDLINE_DRIVERS=drivers/osal/cpm2.asm
TCMDLINE_SRCS=usecase/cmdline/tcmdline.asm.m4 testdefs.asm.m4 utils.asm tester.asm usecase/cmdline/tib.asm
TSTREQ_DRIVERS=drivers/osal/cpm2.asm
TSTREQ_SRCS=usecase/cmdline/tstreq.asm.m4 usecase/cmdline/strings.asm testdefs.asm.m4 utils.asm tester.asm

help:
	@echo "make d71   -- builds a D71 file named ${CPMFS} for a C128 emulator"
	@echo "make run   -- As above, but also launches the C128 emulator"
	@echo "make clean -- Delete all build artifacts"
	@echo "make help  -- shows this message."


.phony: clean
clean:
	rm -f *.o *.err *.com *.bin ${CPMFS}
	rm -f tvdc.asm tcmdline.asm

.phony: run
run: d71
	x128 -8 cpmf3-1.d64 -10 ${CPMFS}


.phony: d71
d71: ${CPMFS} vdcforth.com tvdc.com tcmdline.com tstreq.com
	yes | ctools ${CPMFS} p vdcforth.com >/dev/null
	yes | ctools ${CPMFS} p tvdc.com >/dev/null
	yes | ctools ${CPMFS} p tcmdline.com >/dev/null
	yes | ctools ${CPMFS} p tstreq.com >/dev/null


.phony: ${CPMFS}
${CPMFS}:
	cformat -2 ${CPMFS}


vdcforth.com: ${FORTH_DRIVERS} ${FORTH_SRCS}
	z80asm -b vdcforth.asm
	mv vdcforth.bin vdcforth.com


tvdc.com: ${TVDC_DRIVERS} ${TVDC_SRCS}
	m4 drivers/vdc/tests/tvdc.asm.m4 >tvdc.asm
	z80asm -b tvdc.asm
	mv tvdc.bin tvdc.com


tcmdline.com: ${TCMDLINE_DRIVERS} ${TCMDLINE_SRCS}
	m4 usecase/cmdline/tcmdline.asm.m4 >tcmdline.asm
	z80asm -b tcmdline.asm
	mv tcmdline.bin tcmdline.com

tstreq.com: ${TSTREQ_DRIVERS} ${TSTREQ_SRCS}
	m4 usecase/cmdline/tstreq.asm.m4 >tstreq.asm
	z80asm -b tstreq.asm
	mv tstreq.bin tstreq.com
