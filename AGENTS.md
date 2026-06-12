# demoscene-toolchain

AmigaOS m68k cross-toolchain builder. Builds binutils-gdb, gcc-2.95.3 and the
amiberry / fs-uae emulators (used as debugger backends) from `submodules/`.

- Build: `./toolchain-m68k.py build --prefix=$HOME/amiga`
- Build one component: `./toolchain-m68k.py build <component>` (names listed in
  `BUILD_PHASES`, e.g. `amiberry`, `fs-uae`, `binutils`, `gcc`); assumes the
  component's dependencies were already built.
- Rebuild one component (force make+install, skip configure/cmake):
  `./toolchain-m68k.py rebuild <component> --prefix=$HOME/amiga`

Build steps are gated by stamp files under `.build-m68k/stamps/`, keyed on the
target name only — they do NOT invalidate when a patch, configure flag, or
version changes. To force a step to re-run, delete its stamp;
`rebuild <component>` does this for the `make`/`make install` stamps before
re-running `build <component>`.

Submodules are modified only via quilt patches (`quilt push -a` at build,
`pop -a` at clean). Their working trees carry the applied patches; the gitlink
SHA stays pristine and is NOT committed. The deliverables are the patch files
under `patches/` — see `patches/AGENTS.md`.
