#!/bin/bash

set -ue

MAIN=$1
CPMFS=asdf.d71

z80asm -b ${MAIN}.asm && mv ${MAIN}.bin ${MAIN}.com && ctools ${CPMFS} p ${MAIN}.com

