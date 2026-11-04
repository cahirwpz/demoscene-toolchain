# patches/amiberry/

Patches that make submodules/amiberry work as a debugger backend. Build must
define DEBUGGER. To add/modify a patch see ../AGENTS.md.

## The contract amiberry must satisfy

The `uaedbg` GDB bridge popen-runs the emulator, talks to its console debugger,
and serves GDB RSP on :8888.

1. I/O streams (keep separate):
   - stdin <- debugger commands, one per line
   - stderr <- debugger protocol; every response ends with a '>' prompt
   - stdout <- emulator log ONLY
2. Required behaviours:
   - console output on stderr, off stdout/SDL_Log [debugger-on-stderr]
   - SIGINT halts the guest into the debugger [break-on-sigint]
   - boot already halted when use_debugger is set [break-at-start]
   - guest ILLEGAL $4AFC outside ROM breaks (asserts) [break-on-illegal]
3. Exact output strings uaedbg parses:
   - `Breakpoint at <hexPC>` [debug-msg-fix]
   - `Exception <n>, PC=<hex>` [exceptions-on-stderr]
   - `Memwatch <n>: break at AAAAAAAA.{B|W|L} <RWI> VVVVVVVV PC=<hex> ...`
   - `Memprotect: break at ...` [uaelib-memprotect]
   - `Memwatch <n> added`, `Breakpoint added`/`removed` [print-memwatch]
4. Console commands are WinUAE's (`f`, `w`, `fi`, `fo`, `fR`, `fl`, `i`, `t`,
   `m`, `dma` ...) — keep their output shapes stable.

## uaelib trap ABI (guest header include/uae.h pins the numbers)

1. src/uaelib.cpp uaelib_demux must dispatch these (guest enters via an ILLEGAL
   planted at a magic linker address):
   - 3 HardReset (stock)
   - 4 Reset (stock)
   - 13 ExitEmu (stock)
   - 40 Log(printf fmt+varargs) [uaelib-log]
   - 41 WarpMode(on) [uaelib-warpmode]
   - 42 DebugDMA(on) [uaelib-debugdma]
   - 43-47 Trace Begin/End/Counter/Instant/Metadata; args are key-value pairs,
     key's 1st char = type (P ptr, S str, I i32, U u32), NULL-terminated;
     records go out the parallel-port side-channel (CTEF) [uaelib-trace]
   - 48-50 MemProtect Allow/Deny/Activate; 32-bit UAE*MP*\* component masks
     (CPU_I=1, CPU_D_R=2, CPU_D_W=4, BLT/COP/DSK/AUD/BPL/SPR..,
     NONE=0x80000000), per-16-bit-word; Activate one-way; then any ungranted RAM
     access breaks [uaelib-memprotect]
1. `launch.py` externals: warp on; serial TCP:8000; parallel TCP:8001 (CTEF
   sink); gdb :8888; models A500/A1200.

## Where each concern lives in amiberry

- console/log : src/osdep/writelog.cpp (out: console_out\*->writeconsole_2,
  flushconsole; in: console_isch/getch/get; Linux out=stderr/SDL_Log, in=stdin)
- serial : src/osdep/amiberry_serial.cpp (TCP server; canreceive()/
  serial_rethink() guard RX; TCP_NODELAY set)
- brk/debug : setup_brkhandler/sigbrkhandler/debuggable are DECLARED in
  src/include/xwin.h, DEFINED in src/main.cpp; startup activation is in
  real_main2() (off by default). osdep/amiberry.cpp signal handlers are
  `#if CPU_arm` only. cfgfile maps use_debugger-> start_debugger.
- cpu/exc : src/newcpu.cpp op_illg(), exception_debug(); the exception
  breakpoint message is in src/debug.cpp debug_exception().
- uaelib : src/uaelib.cpp (uaelib_demux + uaelib_log.cpp).
