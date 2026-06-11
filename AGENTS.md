# demoscene-toolchain

AmigaOS m68k cross-toolchain builder. Builds binutils-gdb, gcc-2.95.3 and the
amiberry / fs-uae emulators (used as debugger backends) from `submodules/`.

Build: `./toolchain-m68k.py build --prefix=$HOME/amiga`
Rebuild one emulator: `./rebuild-amiberry.sh` / `./rebuild-fs-uae.sh`

Submodules are modified only via quilt patches (`quilt push -a` at build,
`pop -a` at clean). Their working trees carry the applied patches; the gitlink
SHA stays pristine and is NOT committed. The deliverables are the patch files
under `patches/` — see `patches/AGENTS.md`.
