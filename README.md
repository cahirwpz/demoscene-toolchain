# AmigaOS m68k compiler for use with my demoscene project

[![Build Status](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml/badge.svg)](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml)

**Author:** [Krystian Bacławski](mailto:krystian.baclawski@gmail.com)

## Building

Supported host: Ubuntu 26.04 (x86-64). Install the build dependencies:

```sh
sudo apt install --no-install-recommends \
     autoconf automake bison ca-certificates cmake flex g++ gcc gettext git \
     gperf libc6-dev libcurl4-openssl-dev libdbus-1-dev libflac-dev libgl-dev \
     libglib2.0-dev libmpg123-dev libncurses-dev libopenal-dev libpng-dev \
     libsdl2-dev libsdl2-ttf-dev libsdl3-dev libsdl3-image-dev libtool make \
     nlohmann-json3-dev patch perl pkg-config python3 python3-dev python3-venv \
     quilt texinfo zip zlib1g-dev
```

Only the listed packages are required; recommended packages are not needed.

Clone with submodules and build (default prefix is `./m68k-amigaos`).
`source activate` sets up the Python venv in `.venv`; the script requires it:

```sh
git clone --recurse-submodules https://github.com/cahirwpz/demoscene-toolchain
cd demoscene-toolchain
source activate
./toolchain-m68k.py build [--prefix=/opt/amiga]
```

To build a Debian package (needs `debhelper` and `fakeroot`):

```sh
env PREFIX=/opt/amiga ./build-deb
```

## Releasing

Run the CI workflow on `master`: _Actions → Demoscene Toolchain → Run workflow_,
or `gh workflow run workflow.yml --ref master`. It builds the `.deb` (version
`YYYY.MM.DD+N`) and creates a draft release with generated notes. Review and
publish it.
