# patches/

Quilt stack. `series` = apply order; quilt runs from repo root, `-p1` strips the
leading `demoscene-toolchain/`. `.pc/` tracks applied state.

Patch file = prose header (what & why) then a `quilt refresh`-style diff:

```diff
Index: demoscene-toolchain/submodules/<sub>/<path>
--- demoscene-toolchain.orig/submodules/<sub>/<path>
+++ demoscene-toolchain/submodules/<sub>/<path>
```

No `.quiltrc`; this exact format is quilt's default here.

Add or edit a patch (let quilt make the diff — don't hand-write):

- `quilt pop <patch>` # to the insertion point
- `quilt new <dir>/<name>.diff` # inserts into series after current top
- `quilt add submodules/<sub>/<file>`
- `<edit file>; quilt refresh` # correct format + line numbers
- `<prepend the prose header to the .diff>` Verify the stack:
  `quilt pop -a && quilt push -a` (FAILED/fuzz = bad; context "offset N lines" =
  fine).

Commit only `*.diff` + `series`. Never the submodule gitlinks.
