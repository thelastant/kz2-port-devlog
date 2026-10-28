# kz2-port

A native Windows Rust port of Killzone 2, developed against a user-supplied
retail disc dump. The original game is used only as a behavioural and data
reference. No game binaries, assets, or decompiled output are distributed.

## Goal

A 1:1 playable port with no PS3 emulation layer in the runtime: boot, menus,
level load, gameplay, saves, and settings.

Two rules shape the whole project:

- **Evidence before code.** Every system is derived from the retail executable
  and checked against the original game running in RPCS3 on the same input.
  RPCS3 is an oracle for behaviour and a reference for kernel contracts; none of
  its runtime code is used.
- **Never fake progress.** A subsystem that is not implemented fails loudly with
  the library's own error instead of returning a plausible value. Nothing is
  stubbed with silent success, and no guest data is fabricated to get past a
  check.

## Status at a glance

| | |
| --- | --- |
| Boot | reaches graphics, file-system and font initialisation, then submits frames |
| Executed blocks | **4,644,637** (latest validated build) |
| Submissions | 8 command submissions, 32,768 words, 6 completed flips |
| Static translation | **49,070 functions**, **428,755 basic blocks** of the retail executable |
| Runtime tests | **196** passing, plus recompiler and harness suites |
| Playable? | **No.** The boot stops in the engine's own asset lookup |

## What works

**Loading and translation**

- Native lift of the retail executable: parsing, import resolution, thread-local
  image setup, module list, and stack/heap layout for the guest.
- Static recompiler producing native basic blocks for the whole analysed
  closure, driven by a dispatcher that follows real control flow.
- An interpreter fallback covers blocks the static translation does not contain,
  so newly discovered control-flow targets can be explored without regenerating
  the translated binary.

**Kernel and threading**

- The lv2 syscall surface the game actually uses: PPU threads and joins, mutexes,
  light-weight mutexes and condition variables, semaphores, event queues, event
  ports, event flags, timers, memory allocation, and user-memory queries.
- Cooperative multi-threading with a deterministic block clock, plus per-thread
  register state (general purpose, floating point, vector, condition, count, and
  status registers) so a thread switch cannot leak architectural state.
- Memory mapper address reservation and shared allocations, and the RSX driver
  syscalls the guest issues at start-up.

**File system**

- `cellFs*` and `sys_fs_*` share one implementation, so both entry points have
  the same semantics.
- Device roots: the disc is the read-only `/dev_bdvd` mount, `/dev_hdd0` is the
  save root, and `/dev_hdd1` is a per-title cache directory created on demand.
- Directory listing follows the console contract (`.`/`..` entries, the
  documented record size, end-of-listing behaviour), and open flags are decoded
  from the library's octal values, including create, truncate and append.
- Errors are mapped from the host by kind — missing file, permission, directory,
  already-exists — instead of collapsing to a single code.
- Descriptors are numbered from the console's first non-stream handle.

**Video, audio and fonts**

- Graphics context and display configuration (720x480 progressive, correct pitch
  and gamma), with command submissions and completed flips.
- Video/audio output queries answered from the configured state.
- Font library initialisation completes, with the returned handle being real
  guest memory the game stores and reuses.

**Deliberately refused, not faked**

- Requesting an actual system font is refused with the library's own
  "no support function" code: the port has neither the console's system fonts
  nor a rasteriser, so a font object that could never draw a glyph is not handed
  back. The game warns and continues.
- Save auto-load and save are refused with real library error codes until the
  save container is implemented.

## What remains

1. **File-cache / asset initialisation — the current blocker.** The engine's own
   I/O layer initialises a disk cache before it can resolve asset packages. In
   this port that initialisation does not complete, the asset registry stays
   empty, and the engine aborts by design with "could not locate application
   specific assets". Verified against the oracle: the cache files are created
   read-write and the header is written in 512-byte chunks. Restoring that
   sequence is the next milestone.
2. **Rendering.** GCM initialisation is real, but command execution is recorded
   rather than executed — nine method classes are captured and no rasteriser
   exists yet. This includes the display-list, shader and IO-mapping behaviour a
   retail title depends on.
3. **SPU execution in a boot.** A full SPU instruction executor and the SPURS API
   surface exist, and images embedded in the executable parse and run under a
   development harness, but no boot has yet created and started an SPU thread
   group.
4. **Animation, physics and AI runtime** — the systems that consume the ported
   mesh and skeleton readers.
5. **Audio output**, **input**, **save data**, **menus and level load**,
   **settings**.
6. **Performance**: the static translation runs through a dispatcher with an
   interpreter fallback; both need profiling once the game runs further than a
   boot.

## How it is validated

The oracle is the retail disc booted headless in RPCS3 with tracing enabled. Its
traces provide the ground truth for call order, arguments, return codes, file
paths, descriptor numbering and file layout. Behaviour is compared against those
traces, not against intuition. Where the oracle cannot answer — game-internal
state machines, for instance — the port's own instrumentation is used, and
anything not directly observed is recorded as untested rather than assumed.

## Repository layout

```text
rust/            native Rust workspace (runtime, recompiler, harness, graphics)
notes/           private findings, contracts and subsystem notes
tools/           local analysis, oracle mining and validation tools
logs/            private evidence: run logs, probes, experiments
```

Generated code, dumps, and game data stay outside git.

## Building

The workspace builds with the pinned Rust and MinGW toolchain; `tools/build.ps1`
pins the exact invocation (toolchain paths, link paths, worker count) so a build
cannot silently run with a different configuration:

```powershell
powershell -File tools/build.ps1            # release build of the boot harness
powershell -File tools/build.ps1 -Test      # runtime test suite
```

Real-disc tests require `KZ2_PSARC` and are opt-in; they are skipped by default.

## Known limitations

- Decode coverage is not behavioural correctness: compiled blocks only prove the
  instruction was translated, not that the system behaves like the console.
- Shared memory is mapped at one address rather than aliased, and RSX driver
  attributes are recorded but not executed.
- The SPU stack is present but untested inside a real boot.
- Anything not reproduced from evidence is called out in the port's notes as
  untested, and failures are surfaced rather than hidden.

## Legal

No game data or derived binaries are distributed. The port reads only from a
user-selected local disc dump. Killzone 2 and related trademarks belong to their
respective owners.
