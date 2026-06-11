#!/bin/bash

rm -f .build-m68k/stamps/fs-uae-make*
# shellcheck disable=SC1091
source activate
python3 toolchain-m68k.py build --prefix="${HOME}/amiga" fs-uae
