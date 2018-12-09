AmigaOS m68k compiler for use with my demoscene project
===

[![Build Status](https://circleci.com/gh/cahirwpz/demoscene-toolchain.svg?&style=shield)](https://circleci.com/gh/cahirwpz/demoscene-toolchain)

**Author:** [Krystian Bacławski](mailto:krystian.baclawski@gmail.com)

**Short description:** Cross toolchain build script for AmigaOS m68k targets. Supported host platforms are Linux and MacOSX.

### Overview

**demoscene-toolchain** project provides an easy way to build AmigaOS 3.x (m68k) target toolchain in a Unix-like environment.

Build process should produce following set of tools for **m68k-amigaos** target:

 * gcc 2.95.3
 * g++ 2.95.3
 * libstdc++ 2.10
 * binutils 2.14 (assembler, linker, etc.)
 * libnix 2.2 (standard ANSI/C library replacement for AmigaOS)
 * libm 5.4 (provides math library implementation for non-FPU Amigas)
 * AmigaOS headers & libraries & autodocs (for AmigaOS 3.9)
 * vbcc toolchain (most recent release) including vasm, vlink and C standard library
 * IRA: portable M68000/010/020/030/040 reassembler for AmigaOS hunk-format
   executables, libraries, devices and raw binary files
 * vda68k: portable M68k disassembler for 68000-68060, 68851, 68881, 68882
 * [amitools](https://github.com/cnvogelg/amitools/blob/master/README.md#contents) with [vamos](https://github.com/cnvogelg/amitools/blob/master/doc/vamos.md) AmigaOS emulator which is proven to run SAS/C

### Downloads

There are no binary downloads provided for the time being. I do as much as possible to make the toolchain portable among Unix-like environments. Following platforms were tested and the toolchain is known to work for them:

 * Debian 9.6.0 64-bit *Requires gcc-multilib package, and i386 libraries!*
 * MacOS X 10.12.4 (MacPorts - Apple's clang-900.0.39.2)
 
### Documentation

Documentation from Free Software Fundation:

 * [gcc 2.95.3](http://gcc.gnu.org/onlinedocs/gcc-2.95.3/gcc.html)
 * [binutils](http://sourceware.org/binutils/docs/)

Texinfo documents from GeekGadgets converted into HTML:

 * [libnix - a static library for GCC on the amiga](http://cahirwpz.users.sourceforge.net/libnix/index.html)
 * [AmigaOS-only features of GCC](http://cahirwpz.users.sourceforge.net/gcc-amigaos/index.html)

AmigaOS specific documents:

 * [Amiga Developer Docs](http://amigadev.elowar.com)

### Compiling

*Firstly… you should have basic understanding of Unix console environment, really* ;-)

#### Prerequisites

You have to have following packages installed in your system:

 * GNU gcc 6.x **32-bit version!** or Clang
 * Python 2.7.x
 * libncurses-dev
 * python-dev 2.7
 * GNU make 4.x
 * perl 5.22
 * git
 * GNU patch
 * GNU gperf
 * GNU bison

*For MacOSX users*: you'll likely need to have [MacPorts](http://www.macports.org) or [Homebrew](http://brew.sh) installed in order to build the toolchain.

#### How to build?

**Warning:** *Building with `sudo` is not recommended. I'm not responsible for any damage to your system.*

Follow steps listed below:

1. Fetch *demoscene-toolchain* project to your local drive:  

```
    # git clone git://github.com/cahirwpz/demoscene-toolchain.git
    # cd demoscene-toolchain
```

2. Run `toolchain-m68k` script (with `--prefix` option to specify where to install the toolchain). Note, that the destination directory must be writable by the user. 

```
    # ./toolchain-m68k --prefix=/opt/m68k-amigaos build
```
