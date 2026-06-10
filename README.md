# AmigaOS m68k compiler for use with my demoscene project

[![Build Status](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml/badge.svg)](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml)

**Author:** [Krystian Bacławski](mailto:krystian.baclawski@gmail.com)

## Building

Supported host: Ubuntu 26.04 (x86-64). Install the build dependencies:

```sh
sudo apt install --no-install-recommends \
     autoconf automake bison ca-certificates cmake flex g++ gcc gettext git \
     gperf libasound2-dev libc6-dev libcurl4-openssl-dev libdbus-1-dev \
     libdecor-0-dev libdrm-dev libegl1-mesa-dev libflac-dev libgbm-dev \
     libgl1-mesa-dev libgles2-mesa-dev libglib2.0-dev libjpeg-dev libmpg123-dev \
     libncurses-dev libopenal-dev libpng-dev libpulse-dev libsdl2-dev \
     libsdl2-ttf-dev libtool libudev-dev libwayland-dev libx11-dev \
     libxcursor-dev libxext-dev libxfixes-dev libxi-dev libxkbcommon-dev \
     libxrandr-dev libxrender-dev libxss-dev make nlohmann-json3-dev patch perl \
     pkg-config python3 python3-dev python3-venv quilt texinfo \
     wayland-protocols zip zlib1g-dev
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
