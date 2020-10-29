#!/bin/bash

set -ue

block_for_change() {
	inotifywait --event modify $1.py
	return 0
}

build() {
	python -m unittest $1
}

TARGET="$1"
build $TARGET
while block_for_change $TARGET; do
	clear
	echo "Performing tests..."
	echo
	build $TARGET
done
