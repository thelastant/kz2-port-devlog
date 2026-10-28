# kz2-port

A native Windows Rust port of Killzone 2, developed against a user-supplied
retail disc dump. The original game is used only as a behavioural and data
reference. No game binaries, assets, or decompiled output are distributed.

## Goal

A 1:1 playable port with no PS3 emulation layer in the runtime: boot, menus,
level load, gameplay, saves, and settings.

Two rules shape the project:

- **Evidence before code.** Every system is derived from the retail executable and
  checked against the original game running in RPCS3 on the same input. RPCS3 is
  an oracle for behaviour and a reference for kernel contracts; none of its
  runtime code is used.
- **Never fake progress.** A subsystem that is not implemented fails loudly with
  the library's own error instead of returning a plausible value. Nothing is
  stubbed with silent success, and no guest data is fabricated to get past a check.

## Status at a glance

| | |
| --- | --- |
| Boot | graphics, file-system and font initialisation reached; frames submitted |
| Executed blocks | **4,644,637** (latest validated build) |
| Submissions | 8 command submissions, 32,768 words, 6 completed flips |
| Static translation | **49,070 functions**, **428,755 basic blocks** |
| Runtime tests | **196** passing, plus recompiler and harness suites |
| Playable? | **No** — the boot stops in the engine's own asset lookup |

---

# Progress checklist

✅ done and verified · ⬜ outstanding · `(in progress)` being worked now ·
`(parked)` tried and reverted, kept on a branch

## 1. Project foundations

- ✅ Rust workspace: core, runtime, assets, render, recompiler, boot harness, 16 generated shards
- ✅ Pinned toolchain and MinGW link paths captured in `tools/build.ps1`
- ✅ Build script validates the produced binary against source timestamps
- ✅ Parallel shard build measured end to end (16 crates over 8 physical cores)
- ✅ Harness-only rebuild path separated from shard rebuilds (~5 s vs ~34 min)
- ✅ Release profile tuned: `panic=abort`, debuginfo stripped, default codegen units
- ✅ Binary size reduced 387 MB → 369 MB by the profile change
- ✅ Jobserver starvation diagnosed when codegen units were raised to 256 (6.0 of 16 cores busy vs 8.4–9.4 with default)
- ✅ Worker-count sweet spot measured rather than assumed (15 workers, 8 physical cores)
- ✅ Private evidence layout (`logs/`, `notes/`) kept separate from the public page
- ✅ Public project page and devlog publishing pipeline, with remote-head verification
- ✅ Commit discipline: one subsystem per commit, contract + measured boot delta in the body
- ⬜ Split generated shards from the runtime ABI so logic edits stop rebuilding 16 crates
- ⬜ Trim the translation closure to the functions a boot actually reaches

## 2. Loading and translation

- ✅ Retail executable parse: ELF headers, segments, entry point
- ✅ Import resolution across the game's libraries (342 imports, 23 libraries)
- ✅ Thread-local storage image copied per thread
- ✅ Guest stack and heap layout
- ✅ System module list answered (the modules the game requests)
- ✅ Disc presented as the read-only `/dev_bdvd` root
- ✅ Static recompiler: decoder, control flow, call/return emission
- ✅ Whole-closure lift: 49,070 functions, 428,755 basic blocks
- ✅ Dispatcher follows real control flow rather than per-function tests
- ✅ Interpreter fallback for blocks the static translation does not contain
- ✅ Fixed: doubleword compares were decoded as word compares, which starved the file layer
- ✅ Verified the lift against the retail disc: function inventory, SPU images, no lifter gaps in the largest image
- ⬜ Executable hot-patching / self-modifying code
- ⬜ Runtime-loaded overlays and additional modules beyond the initial set

## 3. Kernel and threading

- ✅ lv2 syscall table cross-checked against the oracle's (451 entries, name for name)
- ✅ PPU threads: create, start, exit, join, get-id, stack information
- ✅ Cooperative scheduler with a deterministic block clock
- ✅ Per-thread architectural state: general, float, vector, condition, count, status registers
- ✅ Thread switches cannot leak architectural state (regression-tested)
- ✅ Fixed: a run-away memory-clear loop caused by cross-thread register leakage — the thread's condition register was another thread's
- ✅ Mutexes: create, destroy, lock, trylock, unlock
- ✅ Light-weight mutexes: create/destroy/lock/trylock/unlock surface
- ✅ Light-weight condition variables: create/destroy/wait/signal/signal-all, with real blocking and waiter hand-off
- ✅ Semaphores: create, wait, trywait, post, get-value
- ✅ Condition variables: create, destroy, wait, signal, signal-all, signal-to
- ✅ Event queues: create, receive, tryreceive
- ✅ Event ports: create, connect-local, send
- ✅ Event flags
- ✅ Timers: microsecond sleep, timebase, timebase frequency, time zone, current time
- ✅ `sys_process_is_stack` answered per thread
- ✅ `sys_ss_access_control_engine`
- ✅ Return-to-dispatcher marker kept distinct from a real jump to null
- ✅ Regression test: a thread switch preserves per-thread register state
- ✅ Parked: strict light-weight mutex ownership — the first attempt initialised the owner field to the kernel's "free" value and deadlocked, because the guest treats a cleared field as free
- ✅ (parked) Light-weight mutex contention under the guest's own encoding — built and measured; boot behaviour was identical to the baseline (same block count, same stop, no extra file activity), so it is kept on a branch instead of merged
- ⬜ Real-time priority inversion / priority inheritance
- ⬜ Thread renaming, affinity and debug interfaces

## 4. Memory and mappers

- ✅ Guest memory with mapped/unmapped fault reporting
- ✅ `sys_memory_allocate` and user memory size queries
- ✅ Memory container and block allocation used by the engine's allocator
- ✅ Address reservation and shared memory allocation
- ✅ Memory mapper address space and search-and-map
- ✅ Allocation probes confirm zeroed blocks and requested sizes
- ⬜ Shared memory aliasing (the port maps one address instead of aliases)
- ⬜ Memory protection changes and guard pages
- ⬜ Full IO address-space capacity (the engine maps many 1 MB chunks at level load)

## 5. File system

- ✅ `cellFs*` and `sys_fs_*` share one implementation, so both entry points have the same semantics
- ✅ Open, close, read, write, lseek
- ✅ Stat and fstat with the console's exact structure layout (52 bytes, 4-byte packed)
- ✅ Mkdir, rmdir, rename, unlink, access, fsync
- ✅ Opendir, readdir, closedir
- ✅ Device roots: disc (read-only), save root, per-title cache
- ✅ Per-title cache directory created on demand and mounted at `/dev_hdd1`
- ✅ Cache mount reports created vs relayed
- ✅ Path normalisation, including repeated separators and bare device paths
- ✅ Directory-listing contract: `.`/`..`, documented record size, end-of-listing behaviour
- ✅ Fixed: open flags decoded from the library's octal values — create is not the value a hex reading suggests
- ✅ Fixed: host errors mapped by kind (missing, permission, directory, exists) instead of a single collapsed code
- ✅ Fixed: descriptors numbered from the console's first non-stream handle; the engine reads a zero descriptor as "no file"
- ✅ Regression test: every access mode and the create flag
- ✅ Regression test: descriptors start after the standard streams
- ⬜ (in progress) File-cache initialisation completing inside the engine - current blocker
- ⬜ `sys_fs_fcntl` device-query path exercised the way the console exercises it
- ⬜ Blu-ray specific surface beyond plain files

## 6. Assets and data formats

- ✅ PSARC archive reader
- ✅ Serialised object reader
- ✅ Texture reader
- ✅ Mesh reader
- ✅ Skeleton reader
- ✅ Skinning reader
- ⬜ Asset registry / lump resolution through the engine's own cache
- ⬜ Streaming packages and level packages
- ⬜ Animation clip and state-machine data

## 7. Graphics and display

- ✅ Graphics context creation and teardown
- ✅ Display configuration: 720x480 progressive, correct pitch and gamma
- ✅ Frame submission path with completed flips
- ✅ Vblank handling and fence release
- ✅ Nine GCM method classes recorded with argument counts
- ✅ Video-out state and device queries
- ⬜ Rasteriser (nothing is drawn yet)
- ⬜ Shader translation and pipeline state
- ⬜ Texture upload and sampling
- ⬜ Render-target and depth-stencil behaviour
- ⬜ Flip contexts that are not simple rings
- ⬜ IO mapping capacity for level-load chunk mapping
- ⬜ Report/DMA callbacks driven by the title's own frame data

## 8. Audio and video out

- ✅ Audio system initialised; channel and encoder configuration queried
- ✅ Video-out configuration and state reporting
- ⬜ Audio port opened and samples submitted
- ⬜ Encoder and downmix selection honoured
- ⬜ Output device enumeration and format negotiation

## 9. Fonts and text

- ✅ Font library initialisation completes with a real handle in guest memory
- ✅ Caller configuration validated the way the library validates it
- ✅ Cache and revision reporting
- ✅ Font-set requests refused with the library's own "no support function" code instead of returning an unusable object
- ⬜ Font-set opening with real fonts
- ⬜ Glyph rasterisation and text layout
- ⬜ Console system-font data source

## 10. Save data

- ✅ Save API surface answers with real library error codes
- ✅ Save root mapped to the host save directory
- ⬜ Save container format (directory, parameters, icons)
- ⬜ Auto-load and auto-save flows
- ⬜ Listing, deleting and copying saves

## 11. SPU and SPURS

- ✅ SPU image parsing for images embedded in the executable
- ✅ SPU instruction executor with opcode coverage
- ✅ SPU local store, registers and channel handling
- ✅ SPURS API surface: task and group creation, policies, signals
- ✅ Standalone image execution under a development harness
- ⬜ SPU thread groups created and started inside a real boot
- ⬜ DMA transfers and channel semantics exercised by real workloads
- ⬜ SPU threads scheduled alongside PPU threads
- ⬜ Task exit / enabled-bit interleaving verified (known hazard for thread-pool teardown)

## 12. Input

- ⬜ Pad initialisation and capability reporting
- ⬜ Pad state and data delivery
- ⬜ Input mapping and deadzones

## 13. Menus, level load and gameplay

- ⬜ Asset lookup completing (blocked by file-cache initialisation)
- ⬜ Front-end and menu flow
- ⬜ Level loading and streaming
- ⬜ Scripting runtime
- ⬜ Physics runtime
- ⬜ AI runtime
- ⬜ Animation runtime driving skinned meshes
- ⬜ Settings persistence
- ⬜ Save/load integration

## 14. Validation, oracle work and tooling

- ✅ Oracle: retail disc booted headless in RPCS3 with tracing enabled
- ✅ Syscall inventory captured from the oracle (43 lv2 calls, 28 HLE calls)
- ✅ Boot-order file-system contract extracted: paths, order, return codes
- ✅ Descriptor numbering and open-flag evidence taken from the oracle
- ✅ First-boot cache creation captured, including the deterministic cache header
- ✅ Engine fatal path identified: message formatting followed by a deliberate trap, not a wild pointer
- ✅ Fatal message recovered from the guest stack at the trap
- ✅ Asset-lookup chain identified from the message back to the cache initialiser
- ✅ File-cache initialisation loop located and its exit condition identified
- ✅ Request object traced end to end: submit, wait, completion flag, operation-state word
- ✅ Every writer of the completion flag and of the operation-state word enumerated
- ✅ Block-level ordering of completion vs state finalisation captured, including the threads involved
- ✅ Structure layouts cross-checked against the console headers
- ✅ Local tools: decompile-at, references-at, disassembly, store scans, ELF helpers
- ✅ Oracle log miners for paths, HLE calls, inventory and ordering
- ✅ Probes: block entry with link register, interpreter-level, request dereference, object mode
- ✅ Store watch over a memory range, and a block-clock request-state sampler
- ✅ Trace gates for file calls, syscalls, imports, memory and synchronisation
- ⬜ Console-side visibility into engine-internal structures (needed to settle the current ordering question)
- ⬜ Per-subsystem behavioural comparison beyond the boot sequence
- ⬜ Automated regression comparison against oracle traces

## 15. Verified measurements

- ✅ Pre-fix frontier: 4,603,057 blocks, stopped inside a memory-clear loop
- ✅ After the per-thread register fix: 4,614,390 blocks, file layer reached
- ✅ After the open-flag fix: 4,644,637 blocks, cache index created
- ✅ Full rebuild times: 36m33s / 36m41s / 38m11s before tuning, 33–35 min after
- ✅ Harness-only rebuild: ~5 s
- ✅ Runtime test count progression: 193 → 194 → 195 → 196
- ⬜ Profile the runtime once execution advances past the boot

---

## Current blocker, in full

The engine initialises a disk cache through its own I/O layer before it can resolve
asset packages. In this port that initialisation does not complete, so the asset
registry stays empty and the engine aborts by design with "could not locate
application specific assets".

What is established, in order:

- the trap is the engine's own fatal helper: it formats a message and then
  deliberately traps, so the message — not the trap — is the signal;
- the asset lookup resolves names through the engine's cache, so an uninitialised
  cache means an empty registry;
- the cache initialiser opens the cache index, then (by design) the cache data
  file, and only proceeds when its readiness check reports success;
- that readiness check is never reached because the request wait returns a status
  of "1";
- "1" is the operation-state word, whose meaning is "in progress" — the completion
  signal is set while the state word is still 1;
- block-level sampling shows one request object touched by two worker threads: one
  signals completion, another finalises the state 533 blocks later.

Verified against the oracle: the console creates the cache files read-write with
descriptor 3 and 4, writes the header in 512-byte chunks, and produces a
bit-identical cache image on repeated first boots.

Not yet established: whether the console sees the same ordering between completion
and state finalisation. The oracle's syscall trace does not expose engine-internal
structures, so this needs either console-side memory visibility or a runtime hook
that logs worker ownership per request.

## How it is validated

The oracle is the retail disc booted headless in RPCS3 with tracing enabled. Its
traces are the ground truth for call order, arguments, return codes, file paths,
descriptor numbering and file layout. Behaviour is compared against those traces,
not against intuition. Where the oracle cannot answer — engine-internal state
machines, for instance — the port's own instrumentation is used, and anything not
directly observed is recorded as untested rather than assumed.

## Repository layout

```text
rust/            native Rust workspace (runtime, recompiler, harness, graphics)
notes/           private findings, contracts and subsystem notes
tools/           local analysis, oracle mining and validation tools
logs/            private evidence: run logs, probes, experiments
```

Generated code, dumps, and game data stay outside git.

## Building

`tools/build.ps1` pins the exact invocation (toolchain paths, link paths, worker
count) so a build cannot silently run with a different configuration:

```powershell
powershell -File tools/build.ps1            # release build of the boot harness
powershell -File tools/build.ps1 -Test      # runtime test suite
```

Real-disc tests require `KZ2_PSARC` and are opt-in; they are skipped by default.

## Known limitations

- Decode coverage is not behavioural correctness: a compiled block proves the
  instruction was translated, not that the system behaves like the console.
- Shared memory is mapped at one address rather than aliased; RSX driver
  attributes are recorded but not executed.
- The SPU stack exists but has not yet run inside a real boot.
- Anything not reproduced from evidence is called out in the port's notes as
  untested, and failures are surfaced rather than hidden.

## Maintenance

This checklist is the project's status page. It is updated in the same commit as
any change that flips an item (empty square to green tick) — including new items discovered and parked
experiments — so the page never drifts from the repository.

## Legal

No game data or derived binaries are distributed. The port reads only from a
user-selected local disc dump. Killzone 2 and related trademarks belong to their
respective owners.
