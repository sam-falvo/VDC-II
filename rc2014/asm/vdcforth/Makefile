PLATFORM=c128
OS=cpm2
CPMFS=asdf.d71

OSAL=drivers/osal/${OS}.asm
EVTLOOP=drivers/evtloop/${OS}.asm drivers/data.asm
VDC=drivers/vdc/${PLATFORM}.asm drivers/data.asm

TEST_SRCS=testdefs.asm.m4 utils.asm tester.asm

FORTH_DRIVERS=${EVTLOOP} ${OSAL} ${VDC} drivers/math.asm
FORTH_SRCS=consts.asm \
	   usecase/startup/vdcforth.asm \
	   usecase/cmdline/tib.asm \
	   usecase/cmdline/control.asm \
	   usecase/cmdline/view.asm \
	   usecase/cmdline/strings.asm \
	   usecase/cmdline/interp.asm \
	   usecase/cmdline/dict.asm \
	   usecase/cmdline/stack.asm
TVDC_DRIVERS=${OSAL} ${VDC}
TVDC_SRCS=drivers/vdc/tests/tvdc.asm.m4 ${TEST_SRCS}
TCMDLINE_DRIVERS=${OSAL}
TCMDLINE_SRCS=usecase/cmdline/tcmdline.asm.m4 usecase/cmdline/tib.asm ${TEST_SRCS}
TSTREQ_DRIVERS=${OSAL}
TSTREQ_SRCS=usecase/cmdline/tstreq.asm.m4 usecase/cmdline/strings.asm ${TEST_SRCS}
TINTERP_DRIVERS=${OSAL}
TINTERP_SRCS=usecase/cmdline/tinterp.asm.m4 usecase/cmdline/interp.asm usecase/cmdline/tib.asm ${TEST_SRCS}
TMATH_DRIVERS=${OSAL} drivers/math.asm
TMATH_SRCS=drivers/tmath.asm.m4 ${TEST_SRCS}
TSTACK_DRIVERS=${OSAL}
TSTACK_SRCS=usecase/cmdline/tstack.asm.m4 usecase/cmdline/stack.asm ${TEST_SRCS}
TNUM_DRIVERS=${OSAL}
TNUM_SRCS=usecase/cmdline/tnum.asm.m4 usecase/cmdline/interp.asm usecase/cmdline/strings.asm usecase/cmdline/tib.asm ${TEST_SRCS}
TEST_ASMS=tvdc.asm tcmdline.asm tstreq.asm tinterp.asm tmath.asm tstack.asm tnum.asm
COMS=vdcforth.com ${TEST_ASMS:%.asm=%.com}

help:
	@echo "make d71   -- builds a D71 file named ${CPMFS} for a C128 emulator"
	@echo "make run   -- As above, but also launches the C128 emulator"
	@echo "make clean -- Delete all build artifacts"
	@echo "make help  -- shows this message."


.phony: clean
clean:
	rm -f *.o *.err *.com *.bin ${CPMFS}
	rm -f ${TEST_ASMS}

.phony: run
run: d71
	x128 -8 cpmf3-1.d64 -10 ${CPMFS}


.phony: d71
d71: ${CPMFS} ${COMS}
	yes | ctools ${CPMFS} p vdcforth.com >/dev/null
	yes | ctools ${CPMFS} p tvdc.com >/dev/null
	yes | ctools ${CPMFS} p tcmdline.com >/dev/null
	yes | ctools ${CPMFS} p tstreq.com >/dev/null
	yes | ctools ${CPMFS} p tinterp.com >/dev/null
	yes | ctools ${CPMFS} p tmath.com >/dev/null
	yes | ctools ${CPMFS} p tstack.com >/dev/null
	yes | ctools ${CPMFS} p tnum.com >/dev/null


.phony: ${CPMFS}
${CPMFS}:
	cformat -2 ${CPMFS}


vdcforth.com: ${FORTH_DRIVERS} ${FORTH_SRCS}
	z80asm -l -b vdcforth.asm
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

tinterp.com: ${TINTERP_DRIVERS} ${TINTERP_SRCS}
	m4 usecase/cmdline/tinterp.asm.m4 >tinterp.asm
	z80asm -b tinterp.asm
	mv tinterp.bin tinterp.com

tmath.com: ${TMATH_DRIVERS} ${TMATH_SRCS}
	m4 drivers/tmath.asm.m4 >tmath.asm
	z80asm -b tmath.asm
	mv tmath.bin tmath.com

tstack.com: ${TSTACK_DRIVERS} ${TSTACK_SRCS}
	m4 usecase/cmdline/tstack.asm.m4 >tstack.asm
	z80asm -b tstack.asm
	mv tstack.bin tstack.com

tnum.com: ${TNUM_DRIVERS} ${TNUM_SRCS}
	m4 usecase/cmdline/tnum.asm.m4 >tnum.asm
	z80asm -b tnum.asm
	mv tnum.bin tnum.com

