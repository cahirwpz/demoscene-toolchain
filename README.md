# AmigaOS m68k compiler for use with my demoscene project

[![Build Status](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml/badge.svg)](https://github.com/cahirwpz/demoscene-toolchain/actions/workflows/workflow.yml)

**Author:** [Krystian Bacławski](mailto:krystian.baclawski@gmail.com)

## Building

Supported host: Ubuntu 26.04 (x86-64). Install the packages listed by the
`apt-get install` command in [`Dockerfile`](Dockerfile); recommended packages
are not needed.

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
