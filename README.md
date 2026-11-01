AmigaOS m68k compiler for use with my demoscene project
===

[![Build Status](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml/badge.svg)](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml)

**Author:** [Krystian Bacławski](mailto:krystian.baclawski@gmail.com)

Building
---

Supported host: Ubuntu 26.04 (x86-64). Install the build dependencies:

```
sudo apt install --no-install-recommends \
     automake autoconf bison ca-certificates flex gcc g++ gettext git gperf \
     libc6-dev libglib2.0-dev libncurses-dev libopenal-dev libpng-dev \
     libsdl2-dev libsdl2-ttf-dev libtool make patch perl pkg-config python3 \
     python3-dev python3-venv quilt texinfo zip
```

Only the listed packages are required; recommended packages are not needed.

Clone with submodules and build (default prefix is `./m68k-amigaos`):

```
git clone --recurse-submodules https://github.com/cahirwpz/demoscene-toolchain
cd demoscene-toolchain
./toolchain-m68k build [--prefix=/opt/amiga]
```

To build a Debian package (needs `debhelper` and `fakeroot`):

```
env PREFIX=/opt/amiga ./build-deb
```
