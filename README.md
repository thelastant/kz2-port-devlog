# kz2-port

A native Windows Rust port of Killzone 2, built from a user-supplied retail disc dump.
The original game is used only as a behavioural and data reference. No game binaries,
assets, or decompiled output are distributed.

**Goal** — a 1:1 playable port with no PS3 emulation in the runtime: boot, menus,
level load, gameplay, saves and settings.

**Rules**

- **Evidence before code.** Systems are derived from the retail executable and checked
  against the original game running in RPCS3 on the same input. RPCS3 is an oracle for
  behaviour and a reference for kernel contracts; none of its runtime code is used.
- **Never fake progress.** Unimplemented behaviour fails loudly with the library's own
  error. Nothing is stubbed with silent success, and no guest data is fabricated.

## At a glance

| | |
| --- | --- |
| Boot | graphics, file system, fonts and the cache file layer initialised (the cache index body is still empty) |
| Executed blocks | **4.7M** to the asset-lookup fault (the cache bootstrap now runs end to end) |
| Submissions | 8 command submissions, 32,768 words, 6 completed flips |
| Static translation | **49,070 functions**, **428,755 basic blocks** (whole-closure decoder lift) |
| Runtime tests | **214** passing, plus recompiler and harness suites |
| Playable? | **No** — the boot stops in the engine's own asset lookup |

## Progress

**143 done · 52 open.** ✅ done and verified · ⬜ outstanding ·
`(in progress)` being worked now · `(parked)` tried and reverted, kept on a branch.

<details>
<summary><b>1. Project foundations</b> — 12 done · 2 open</summary>

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

</details>

<details>
<summary><b>2. Loading and translation</b> — 12 done · 2 open</summary>

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

</details>

<details>
<summary><b>3. Kernel and threading</b> — 21 done · 2 open</summary>

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
- ✅ Preemptive scheduling: a wake makes a higher-priority thread runnable immediately, not at the next slice edge
- ✅ Sleepers become runnable the moment the clock passes their deadline (a thread had been asleep 224,000 blocks past its deadline)
- ✅ Fixed: a lightweight condition wait was refused for ownership — the system's call has no such requirement, and the engine's file layer lost thousands of waits to it
- ✅ Fixed: the system-cache mount no longer creates the file layer's own directory in advance, so the engine takes its real "create the directory" branch
- ✅ Regression test: a thread switch preserves per-thread register state
- ✅ Parked: strict light-weight mutex ownership — the first attempt initialised the owner field to the kernel's "free" value and deadlocked, because the guest treats a cleared field as free
- ✅ (parked) Light-weight mutex contention under the guest's own encoding — built and measured; boot behaviour was identical to the baseline (same block count, same stop, no extra file activity), so it is kept on a branch instead of merged
- ⬜ Real-time priority inversion / priority inheritance
- ⬜ Thread renaming, affinity and debug interfaces

</details>

<details>
<summary><b>4. Memory and mappers</b> — 6 done · 3 open</summary>

- ✅ Guest memory with mapped/unmapped fault reporting
- ✅ `sys_memory_allocate` and user memory size queries
- ✅ Memory container and block allocation used by the engine's allocator
- ✅ Address reservation and shared memory allocation
- ✅ Memory mapper address space and search-and-map
- ✅ Allocation probes confirm zeroed blocks and requested sizes
- ⬜ Shared memory aliasing (the port maps one address instead of aliases)
- ⬜ Memory protection changes and guard pages
- ⬜ Full IO address-space capacity (the engine maps many 1 MB chunks at level load)

</details>

<details>
<summary><b>5. File system</b> — 15 done · 4 open</summary>

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
- ✅ Fixed: the doubleword compare (`cmpdi`/`cmpldi`) was decoded as the word form, so the file layer's free-list bitmap bit test always read a set bit in the upper 32 bits as clear - the same cache-file entry was handed out twice and the index was written to the data file. With it fixed, the cache initialisation routes the writes with the console's exact split (17 writes to the 1 MB index, one 512-byte header to the data file)
- ❌ (in progress) The cache index body is empty: the engine writes a 1 MB zeroed staging buffer instead of file entries, so the index is an empty table. This is the current file-layer blocker.
- ⬜ `sys_fs_fcntl` device-query path exercised the way the console exercises it
- ⬜ Blu-ray specific surface beyond plain files

</details>

<details>
<summary><b>6. Assets and data formats</b> — 7 done · 3 open</summary>

- ✅ PSARC archive reader (retail `data_ps3.psarc` opens: 3 layers, 3,951 hashed entries)
- ✅ Serialised object reader
- ✅ Texture reader
- ✅ Mesh reader
- ✅ Skeleton reader
- ✅ Skinning reader
- ✅ The engine's asset lookup located: a name is resolved to a `cache:lumps/<name>.core` path through the FIOS cache; the "Application" root asset is what the boot asks for first
- ❌ (in progress) Asset registry / lump resolution through the engine's own cache - blocked by the empty cache index body; the lookup returns nothing and the engine fatals by design
- ⬜ Streaming packages and level packages
- ⬜ Animation clip and state-machine data

</details>

<details>
<summary><b>7. Graphics and display</b> — 6 done · 7 open</summary>

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

</details>

<details>
<summary><b>8. Audio and video out</b> — 2 done · 3 open</summary>

- ✅ Audio system initialised; channel and encoder configuration queried
- ✅ Video-out configuration and state reporting
- ⬜ Audio port opened and samples submitted
- ⬜ Encoder and downmix selection honoured
- ⬜ Output device enumeration and format negotiation

</details>

<details>
<summary><b>9. Fonts and text</b> — 4 done · 3 open</summary>

- ✅ Font library initialisation completes with a real handle in guest memory
- ✅ Caller configuration validated the way the library validates it
- ✅ Cache and revision reporting
- ✅ Font-set requests refused with the library's own "no support function" code instead of returning an unusable object
- ⬜ Font-set opening with real fonts
- ⬜ Glyph rasterisation and text layout
- ⬜ Console system-font data source

</details>

<details>
<summary><b>10. Save data</b> — 2 done · 3 open</summary>

- ✅ Save API surface answers with real library error codes
- ✅ Save root mapped to the host save directory
- ⬜ Save container format (directory, parameters, icons)
- ⬜ Auto-load and auto-save flows
- ⬜ Listing, deleting and copying saves

</details>

<details>
<summary><b>11. SPU and SPURS</b> — 5 done · 4 open</summary>

- ✅ SPU image parsing for images embedded in the executable
- ✅ SPU instruction executor with opcode coverage
- ✅ SPU local store, registers and channel handling
- ✅ SPURS API surface: task and group creation, policies, signals
- ✅ Standalone image execution under a development harness
- ⬜ SPU thread groups created and started inside a real boot
- ⬜ DMA transfers and channel semantics exercised by real workloads
- ⬜ SPU threads scheduled alongside PPU threads
- ⬜ Task exit / enabled-bit interleaving verified (known hazard for thread-pool teardown)

</details>

<details>
<summary><b>12. Input</b> — 0 done · 3 open</summary>

- ⬜ Pad initialisation and capability reporting
- ⬜ Pad state and data delivery
- ⬜ Input mapping and deadzones

</details>

<details>
<summary><b>13. Menus, level load and gameplay</b> — 0 done · 9 open</summary>

- ❌ (in progress) Asset lookup completing - the engine asks for the "Application" root asset; it resolves through the cache index, which is currently empty (current blocker)
- ⬜ Front-end and menu flow
- ⬜ Level loading and streaming
- ⬜ Scripting runtime
- ⬜ Physics runtime
- ⬜ AI runtime
- ⬜ Animation runtime driving skinned meshes
- ⬜ Settings persistence
- ⬜ Save/load integration

</details>

<details>
<summary><b>14. Validation, oracle work and tooling</b> — 38 done · 6 open</summary>

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
- ✅ Mode-byte sampler for the byte the worker turns into open flags
- ✅ Operation-state word semantics identified (in progress / done / invalid)
- ✅ Mechanical file-trace comparison against the oracle, aware of encoding and quoting differences
- ✅ Machine-parameter audit: every start-up system parameter, the user-memory figure and the module-load set compared against the oracle
- ✅ All eight start-up system parameters answered (four were refused before the audit)
- ✅ Cross-checked against Project Helghast's Killzone 3 port (same engine family) and adopted its documented contract fixes: the condition-variable block layout and mutex hand-off, the 512-byte stat block size, and distinct stat times
- ✅ Measured: the condition-variable block layout and mutex hand-off, the 512-byte stat block size and the distinct stat times change nothing — the boot is identical, so they are kept as correct console behaviour, not as progress
- ✅ Create-only vs read-write (issue #4) was a real decode bug, not guest state: `cmpwi`/`cmplwi` treated `r0` as literal zero, dropping the read-write access bits. With it fixed the open carries read-write and the cache is written
- ✅ Measured: the user-memory total and the console's reserved slice correct — the guest consumes them (every allocation moves by exactly the reserved amount, +1,052 blocks), but the cache still never gets written
- ✅ Firmware error-code table audited: four wrong values found and fixed, and a test pins the table
- ✅ Host file errors reported as what they are (`EACCES`, `EISDIR`, `ENOTDIR`, `ENOTEMPTY`) instead of always "not found"
- ✅ Cache files: deletion verified, and a recreated file now carries a newer change time
- ✅ Cold-cache oracle boot captured: the console writes a 1 MB index in one pass, bit-identical to the cached copy
- ✅ Retry loop identified as the engine's reopen service, and proved not to inspect the cache contents
- ✅ Lightweight and system mutexes modelled (owner, hand-off, release on condition wait) — measured: the boot does not contend on either
- ✅ Thread ids start at 1, because the guest reads 0 as "no owner"
- ✅ SPURS LF queue object laid out in guest memory (counters, size, depth, buffer, signal address) with the push advancing the guest counter — measured: boot unchanged, because nothing reads it yet
- ✅ Interpreter counter branches (`bdz`/`bdnz`) corrected — they were swapped, which cost the engine its file-object slots; 61 cache opens became 9
- ✅ lv2 mutex numbering corrected (102 = lock, 103 = trylock), condition hand-back wired, timeouts honoured on all four sync waits, console lwmutex layout — measured: 9 → 21 → 31 cache opens
- ✅ The fd swap (the index written to the data file) was a second decode bug: `cmpdi`/`cmpldi` decoded as the word form, so the free-list bitmap bit test in the upper 32 bits always read clear and the same entry was handed out twice. With it fixed the write split matches the console byte-for-byte (17 writes to the index, one header to the data file)
- ✅ Measured: the cache index body is all zeros. The engine writes a 1 MB zeroed staging buffer; the file-entry fill never populates it. A store watch over the buffer shows only the zeroing memset, and the port's cache hash differs from the console's while the size matches
- ✅ Located the engine's asset lookup: the boot asks for a root asset named "Application", which resolves through a `cache:lumps/<name>.core` path; an empty index returns nothing and the engine then takes its own deliberate fatal path
- ⬜ Explain why the module-load set differs between the two boots
- ✅ Trace gates for file calls, syscalls, imports, memory and synchronisation
- ⬜ Console-side visibility into engine-internal structures (needed to settle the current ordering question)
- ⬜ Per-subsystem behavioural comparison beyond the boot sequence
- ⬜ Automated regression suite wired into the build

</details>

<details>
<summary><b>15. Verified measurements</b> — 6 done · 1 open</summary>

- ✅ Pre-fix frontier: 4,603,057 blocks, stopped inside a memory-clear loop
- ✅ After the per-thread register fix: 4,614,390 blocks, file layer reached
- ✅ After the open-flag fix: 4,644,637 blocks, cache index created
- ✅ Full rebuild times: 36m33s / 36m41s / 38m11s before tuning, 33–35 min after
- ✅ Harness-only rebuild: ~5 s
- ✅ Runtime test count progression: 193 → 194 → 195 → 196 → 210 → 213
- ⬜ Profile the runtime once execution advances past the boot

</details>

## Current blocker, in full

**Updated 2026-10-29: the write routing is fixed, but the cache body is still empty.** Two
decode bugs stalled the file-cache bootstrap for weeks, and both are now closed and pinned by
regression tests:

- `cmpwi`/`cmplwi` treated `r0` as literal zero (the `cmp` forms have no such rule), so the
  read-write access bits were dropped and the cache index was opened create-only;
- `cmpdi`/`cmpldi` were decoded as the word forms, so the file layer's free-list bitmap bit
  test compared only the low 32 bits: a set bit in the upper 32 bits always read as "clear",
  the same entry was handed out for both cache files, and every index write went to the data
  file.

With both fixed, the port routes the writes exactly like the console on a cold boot: 17 writes
to the index (1,043,456 bytes, fd 3) and one 512-byte header to the data file (fd 4).

**The content is still wrong.** The index file is 1,043,456 bytes but only 19 bytes are
non-zero — the `fioscach` header. The entire 1 MB index body is zeros. The engine allocates and
zeroes a staging buffer and writes it out, but the step that would fill it with file entries
never populates it. So the cache index is an empty table.

The boot therefore advances past the cache and stops at the next step: the engine's own "could
not locate application specific assets" report. That lookup resolves an asset named
"Application" through a `cache:lumps/<name>.core` path; with an empty index the lookup returns
nothing and the engine fatals by design. Fixing the empty index body is the current frontier.

The two earlier divergences are now explained and closed: the create-only open was the `cmpwi`
bug (issue #4), and the "retry loop" was the reopen service walking a table whose entries were
never marked open because the same entry was being handed out twice.

## How it is validated

The oracle is the retail disc booted headless in RPCS3 with tracing enabled. Its
traces are the ground truth for call order, arguments, return codes, file paths,
descriptor numbering and file layout. Behaviour is compared against those traces,
not against intuition. Where the oracle cannot answer — engine-internal state
machines, for instance — the port's own instrumentation is used, and anything not
directly observed is recorded as untested rather than assumed.

## Source and credits

The source tree, tools and documentation live in the **private** repository
[thelastant/kz2-port](https://github.com/thelastant/kz2-port); this page and the devlog are
public. That repository ships no game data, and its analysis notes and run logs stay out of it.

It is MIT licensed. Credits and third-party notices are in `NOTICE.md` there, and
[`docs/ACKNOWLEDGEMENTS.md`](https://github.com/thelastant/kz2-port/blob/main/docs/ACKNOWLEDGEMENTS.md)
lists every tool, specification and reference the work relies on.

- **[undecuple](https://github.com/undecuple)** - Project Helghast (MIT), the Killzone 3 port
  on the same engine family, whose documented findings shaped several fixes here; now also a
  contributor with write access to the source repository;
- **[sp00nznet](https://github.com/sp00nznet)** - ps3recomp (MIT), reference for PS3 runtime
  and library semantics;
- **[thelastant](https://github.com/thelastant)** - author and maintainer;
- **[RPCS3](https://github.com/RPCS3)** team (GPL-2.0) - a behavioural oracle only; no code is
  used or linked.

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
