# demoscene-toolchain

- **binutils-gdb stays on AmigaPorts `amiga` (gdb 13).** gdb >= 17 dropped
  stabs, the only debug format gcc-2.95.3 emits. Fix host breakage (e.g. new
  Python) with quilt patches, not by moving to a newer branch.
- **Submodules change only via quilt patches; the gitlink is not committed** —
  except for a deliberate submodule bump: `quilt pop -a`, move the submodule,
  commit the gitlink (the build runs `git submodule update`), `quilt push -a`.
- **Stamps in `.build-m68k/stamps/` never invalidate.** `CC`/`CFLAGS` are fixed
  at configure time, so after changing a component's flags delete its
  `.build-m68k/build/<component>` dir and its `<component>-configure` stamp.
- **Build one component:** `./toolchain-m68k.py build <component>` (names in
  `BUILD_PHASES`); assumes its dependencies are already built.
- **Rebuild one component:** `./toolchain-m68k.py rebuild <component>` deletes
  its `<component>-make*` stamps and reruns `build <component>`; configure is
  kept.
