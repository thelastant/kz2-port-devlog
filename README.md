# kz2-port

A native Windows Rust port of Killzone 2, built from a user-supplied retail disc dump.
The original game is used only as a behavioural and data reference. No game binaries,
assets, or decompiled output are distributed.

**Goal** â€” a 1:1 playable port with no PS3 emulation in the runtime: boot, menus,
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
| Playable? | **No** â€” the boot stops in the engine's own asset lookup |

## Progress

**143 done Â· 52 open.** âœ… done and verified Â· â¬œ outstanding Â·
`(in progress)` being worked now Â· `(parked)` tried and reverted, kept on a branch.

<details>
<summary><b>1. Project foundations</b> â€” 12 done Â· 2 open</summary>

- âœ… Rust workspace: core, runtime, assets, render, recompiler, boot harness, 16 generated shards
- âœ… Pinned toolchain and MinGW link paths captured in `tools/build.ps1`
- âœ… Build script validates the produced binary against source timestamps
- âœ… Parallel shard build measured end to end (16 crates over 8 physical cores)
- âœ… Harness-only rebuild path separated from shard rebuilds (~5 s vs ~34 min)
- âœ… Release profile tuned: `panic=abort`, debuginfo stripped, default codegen units
- âœ… Binary size reduced 387 MB â†’ 369 MB by the profile change
- âœ… Jobserver starvation diagnosed when codegen units were raised to 256 (6.0 of 16 cores busy vs 8.4â€“9.4 with default)
- âœ… Worker-count sweet spot measured rather than assumed (15 workers, 8 physical cores)
- âœ… Private evidence layout (`logs/`, `notes/`) kept separate from the public page
- âœ… Public project page and devlog publishing pipeline, with remote-head verification
- âœ… Commit discipline: one subsystem per commit, contract + measured boot delta in the body
- â¬œ Split generated shards from the runtime ABI so logic edits stop rebuilding 16 crates
- â¬œ Trim the translation closure to the functions a boot actually reaches

</details>

<details>
<summary><b>2. Loading and translation</b> â€” 12 done Â· 2 open</summary>

- âœ… Retail executable parse: ELF headers, segments, entry point
- âœ… Import resolution across the game's libraries (342 imports, 23 libraries)
- âœ… Thread-local storage image copied per thread
- âœ… Guest stack and heap layout
- âœ… System module list answered (the modules the game requests)
- âœ… Disc presented as the read-only `/dev_bdvd` root
- âœ… Static recompiler: decoder, control flow, call/return emission
- âœ… Whole-closure lift: 49,070 functions, 428,755 basic blocks
- âœ… Dispatcher follows real control flow rather than per-function tests
- âœ… Interpreter fallback for blocks the static translation does not contain
- âœ… Fixed: doubleword compares were decoded as word compares, which starved the file layer
- âœ… Verified the lift against the retail disc: function inventory, SPU images, no lifter gaps in the largest image
- â¬œ Executable hot-patching / self-modifying code
- â¬œ Runtime-loaded overlays and additional modules beyond the initial set

</details>

<details>
<summary><b>3. Kernel and threading</b> â€” 21 done Â· 2 open</summary>

- âœ… lv2 syscall table cross-checked against the oracle's (451 entries, name for name)
- âœ… PPU threads: create, start, exit, join, get-id, stack information
- âœ… Cooperative scheduler with a deterministic block clock
- âœ… Per-thread architectural state: general, float, vector, condition, count, status registers
- âœ… Thread switches cannot leak architectural state (regression-tested)
- âœ… Fixed: a run-away memory-clear loop caused by cross-thread register leakage â€” the thread's condition register was another thread's
- âœ… Mutexes: create, destroy, lock, trylock, unlock
- âœ… Light-weight mutexes: create/destroy/lock/trylock/unlock surface
- âœ… Light-weight condition variables: create/destroy/wait/signal/signal-all, with real blocking and waiter hand-off
- âœ… Semaphores: create, wait, trywait, post, get-value
- âœ… Condition variables: create, destroy, wait, signal, signal-all, signal-to
- âœ… Event queues: create, receive, tryreceive
- âœ… Event ports: create, connect-local, send
- âœ… Event flags
- âœ… Timers: microsecond sleep, timebase, timebase frequency, time zone, current time
- âœ… `sys_process_is_stack` answered per thread
- âœ… `sys_ss_access_control_engine`
- âœ… Return-to-dispatcher marker kept distinct from a real jump to null
- âœ… Preemptive scheduling: a wake makes a higher-priority thread runnable immediately, not at the next slice edge
- âœ… Sleepers become runnable the moment the clock passes their deadline (a thread had been asleep 224,000 blocks past its deadline)
- âœ… Fixed: a lightweight condition wait was refused for ownership â€” the system's call has no such requirement, and the engine's file layer lost thousands of waits to it
- âœ… Fixed: the system-cache mount no longer creates the file layer's own directory in advance, so the engine takes its real "create the directory" branch
- âœ… Regression test: a thread switch preserves per-thread register state
- âœ… Parked: strict light-weight mutex ownership â€” the first attempt initialised the owner field to the kernel's "free" value and deadlocked, because the guest treats a cleared field as free
- âœ… (parked) Light-weight mutex contention under the guest's own encoding â€” built and measured; boot behaviour was identical to the baseline (same block count, same stop, no extra file activity), so it is kept on a branch instead of merged
- â¬œ Real-time priority inversion / priority inheritance
- â¬œ Thread renaming, affinity and debug interfaces

</details>

<details>
<summary><b>4. Memory and mappers</b> â€” 6 done Â· 3 open</summary>

- âœ… Guest memory with mapped/unmapped fault reporting
- âœ… `sys_memory_allocate` and user memory size queries
- âœ… Memory container and block allocation used by the engine's allocator
- âœ… Address reservation and shared memory allocation
- âœ… Memory mapper address space and search-and-map
- âœ… Allocation probes confirm zeroed blocks and requested sizes
- â¬œ Shared memory aliasing (the port maps one address instead of aliases)
- â¬œ Memory protection changes and guard pages
- â¬œ Full IO address-space capacity (the engine maps many 1 MB chunks at level load)

</details>

<details>
<summary><b>5. File system</b> â€” 15 done Â· 4 open</summary>

- âœ… `cellFs*` and `sys_fs_*` share one implementation, so both entry points have the same semantics
- âœ… Open, close, read, write, lseek
- âœ… Stat and fstat with the console's exact structure layout (52 bytes, 4-byte packed)
- âœ… Mkdir, rmdir, rename, unlink, access, fsync
- âœ… Opendir, readdir, closedir
- âœ… Device roots: disc (read-only), save root, per-title cache
- âœ… Per-title cache directory created on demand and mounted at `/dev_hdd1`
- âœ… Cache mount reports created vs relayed
- âœ… Path normalisation, including repeated separators and bare device paths
- âœ… Directory-listing contract: `.`/`..`, documented record size, end-of-listing behaviour
- âœ… Fixed: open flags decoded from the library's octal values â€” create is not the value a hex reading suggests
- âœ… Fixed: host errors mapped by kind (missing, permission, directory, exists) instead of a single collapsed code
- âœ… Fixed: descriptors numbered from the console's first non-stream handle; the engine reads a zero descriptor as "no file"
- âœ… Regression test: every access mode and the create flag
- âœ… Regression test: descriptors start after the standard streams
- âœ… Fixed: the doubleword compare (`cmpdi`/`cmpldi`) was decoded as the word form, so the file layer's free-list bitmap bit test always read a set bit in the upper 32 bits as clear - the same cache-file entry was handed out twice and the index was written to the data file. With it fixed, the cache initialisation routes the writes with the console's exact split (17 writes to the 1 MB index, one 512-byte header to the data file)
- âŒ (in progress) The cache index body is empty: the engine writes a 1 MB zeroed staging buffer instead of file entries, so the index is an empty table. This is the current file-layer blocker.
- â¬œ `sys_fs_fcntl` device-query path exercised the way the console exercises it
- â¬œ Blu-ray specific surface beyond plain files

</details>

<details>
<summary><b>6. Assets and data formats</b> â€” 7 done Â· 3 open</summary>

- âœ… PSARC archive reader (retail `data_ps3.psarc` opens: 3 layers, 3,951 hashed entries)
- âœ… Serialised object reader
- âœ… Texture reader
- âœ… Mesh reader
- âœ… Skeleton reader
- âœ… Skinning reader
- âœ… The engine's asset lookup located: a name is resolved to a `cache:lumps/<name>.core` path through the FIOS cache; the "Application" root asset is what the boot asks for first
- âŒ (in progress) Asset registry / lump resolution through the engine's own cache - blocked by the empty cache index body; the lookup returns nothing and the engine fatals by design
- â¬œ Streaming packages and level packages
- â¬œ Animation clip and state-machine data

</details>

<details>
<summary><b>7. Graphics and display</b> â€” 6 done Â· 7 open</summary>

- âœ… Graphics context creation and teardown
- âœ… Display configuration: 720x480 progressive, correct pitch and gamma
- âœ… Frame submission path with completed flips
- âœ… Vblank handling and fence release
- âœ… Nine GCM method classes recorded with argument counts
- âœ… Video-out state and device queries
- â¬œ Rasteriser (nothing is drawn yet)
- â¬œ Shader translation and pipeline state
- â¬œ Texture upload and sampling
- â¬œ Render-target and depth-stencil behaviour
- â¬œ Flip contexts that are not simple rings
- â¬œ IO mapping capacity for level-load chunk mapping
- â¬œ Report/DMA callbacks driven by the title's own frame data

</details>

<details>
<summary><b>8. Audio and video out</b> â€” 2 done Â· 3 open</summary>

- âœ… Audio system initialised; channel and encoder configuration queried
- âœ… Video-out configuration and state reporting
- â¬œ Audio port opened and samples submitted
- â¬œ Encoder and downmix selection honoured
- â¬œ Output device enumeration and format negotiation

</details>

<details>
<summary><b>9. Fonts and text</b> â€” 4 done Â· 3 open</summary>

- âœ… Font library initialisation completes with a real handle in guest memory
- âœ… Caller configuration validated the way the library validates it
- âœ… Cache and revision reporting
- âœ… Font-set requests refused with the library's own "no support function" code instead of returning an unusable object
- â¬œ Font-set opening with real fonts
- â¬œ Glyph rasterisation and text layout
- â¬œ Console system-font data source

</details>

<details>
<summary><b>10. Save data</b> â€” 2 done Â· 3 open</summary>

- âœ… Save API surface answers with real library error codes
- âœ… Save root mapped to the host save directory
- â¬œ Save container format (directory, parameters, icons)
- â¬œ Auto-load and auto-save flows
- â¬œ Listing, deleting and copying saves

</details>

<details>
<summary><b>11. SPU and SPURS</b> â€” 5 done Â· 4 open</summary>

- âœ… SPU image parsing for images embedded in the executable
- âœ… SPU instruction executor with opcode coverage
- âœ… SPU local store, registers and channel handling
- âœ… SPURS API surface: task and group creation, policies, signals
- âœ… Standalone image execution under a development harness
- â¬œ SPU thread groups created and started inside a real boot
- â¬œ DMA transfers and channel semantics exercised by real workloads
- â¬œ SPU threads scheduled alongside PPU threads
- â¬œ Task exit / enabled-bit interleaving verified (known hazard for thread-pool teardown)

</details>

<details>
<summary><b>12. Input</b> â€” 0 done Â· 3 open</summary>

- â¬œ Pad initialisation and capability reporting
- â¬œ Pad state and data delivery
- â¬œ Input mapping and deadzones

</details>

<details>
<summary><b>13. Menus, level load and gameplay</b> â€” 0 done Â· 9 open</summary>

- âŒ (in progress) Asset lookup completing - the engine asks for the "Application" root asset; it resolves through the cache index, which is currently empty (current blocker)
- â¬œ Front-end and menu flow
- â¬œ Level loading and streaming
- â¬œ Scripting runtime
- â¬œ Physics runtime
- â¬œ AI runtime
- â¬œ Animation runtime driving skinned meshes
- â¬œ Settings persistence
- â¬œ Save/load integration

</details>

<details>
<summary><b>14. Validation, oracle work and tooling</b> â€” 38 done Â· 6 open</summary>

- âœ… Oracle: retail disc booted headless in RPCS3 with tracing enabled
- âœ… Syscall inventory captured from the oracle (43 lv2 calls, 28 HLE calls)
- âœ… Boot-order file-system contract extracted: paths, order, return codes
- âœ… Descriptor numbering and open-flag evidence taken from the oracle
- âœ… First-boot cache creation captured, including the deterministic cache header
- âœ… Engine fatal path identified: message formatting followed by a deliberate trap, not a wild pointer
- âœ… Fatal message recovered from the guest stack at the trap
- âœ… Asset-lookup chain identified from the message back to the cache initialiser
- âœ… File-cache initialisation loop located and its exit condition identified
- âœ… Request object traced end to end: submit, wait, completion flag, operation-state word
- âœ… Every writer of the completion flag and of the operation-state word enumerated
- âœ… Block-level ordering of completion vs state finalisation captured, including the threads involved
- âœ… Structure layouts cross-checked against the console headers
- âœ… Local tools: decompile-at, references-at, disassembly, store scans, ELF helpers
- âœ… Oracle log miners for paths, HLE calls, inventory and ordering
- âœ… Probes: block entry with link register, interpreter-level, request dereference, object mode
- âœ… Store watch over a memory range, and a block-clock request-state sampler
- âœ… Mode-byte sampler for the byte the worker turns into open flags
- âœ… Operation-state word semantics identified (in progress / done / invalid)
- âœ… Mechanical file-trace comparison against the oracle, aware of encoding and quoting differences
- âœ… Machine-parameter audit: every start-up system parameter, the user-memory figure and the module-load set compared against the oracle
- âœ… All eight start-up system parameters answered (four were refused before the audit)
- âœ… Cross-checked against Project Helghast's Killzone 3 port (same engine family) and adopted its documented contract fixes: the condition-variable block layout and mutex hand-off, the 512-byte stat block size, and distinct stat times
- âœ… Measured: the condition-variable block layout and mutex hand-off, the 512-byte stat block size and the distinct stat times change nothing â€” the boot is identical, so they are kept as correct console behaviour, not as progress
- âœ… Create-only vs read-write (issue #4) was a real decode bug, not guest state: `cmpwi`/`cmplwi` treated `r0` as literal zero, dropping the read-write access bits. With it fixed the open carries read-write and the cache is written
- âœ… Measured: the user-memory total and the console's reserved slice correct â€” the guest consumes them (every allocation moves by exactly the reserved amount, +1,052 blocks), but the cache still never gets written
- âœ… Firmware error-code table audited: four wrong values found and fixed, and a test pins the table
- âœ… Host file errors reported as what they are (`EACCES`, `EISDIR`, `ENOTDIR`, `ENOTEMPTY`) instead of always "not found"
- âœ… Cache files: deletion verified, and a recreated file now carries a newer change time
- âœ… Cold-cache oracle boot captured: the console writes a 1 MB index in one pass, bit-identical to the cached copy
- âœ… Retry loop identified as the engine's reopen service, and proved not to inspect the cache contents
- âœ… Lightweight and system mutexes modelled (owner, hand-off, release on condition wait) â€” measured: the boot does not contend on either
- âœ… Thread ids start at 1, because the guest reads 0 as "no owner"
- âœ… SPURS LF queue object laid out in guest memory (counters, size, depth, buffer, signal address) with the push advancing the guest counter â€” measured: boot unchanged, because nothing reads it yet
- âœ… Interpreter counter branches (`bdz`/`bdnz`) corrected â€” they were swapped, which cost the engine its file-object slots; 61 cache opens became 9
- âœ… lv2 mutex numbering corrected (102 = lock, 103 = trylock), condition hand-back wired, timeouts honoured on all four sync waits, console lwmutex layout â€” measured: 9 â†’ 21 â†’ 31 cache opens
- âœ… The fd swap (the index written to the data file) was a second decode bug: `cmpdi`/`cmpldi` decoded as the word form, so the free-list bitmap bit test in the upper 32 bits always read clear and the same entry was handed out twice. With it fixed the write split matches the console byte-for-byte (17 writes to the index, one header to the data file)
- âœ… Measured: the cache index body is all zeros. The engine writes a 1 MB zeroed staging buffer; the file-entry fill never populates it. A store watch over the buffer shows only the zeroing memset, and the port's cache hash differs from the console's while the size matches
- âœ… Located the engine's asset lookup: the boot asks for a root asset named "Application", which resolves through a `cache:lumps/<name>.core` path; an empty index returns nothing and the engine then takes its own deliberate fatal path
- â¬œ Explain why the module-load set differs between the two boots
- âœ… Trace gates for file calls, syscalls, imports, memory and synchronisation
- â¬œ Console-side visibility into engine-internal structures (needed to settle the current ordering question)
- â¬œ Per-subsystem behavioural comparison beyond the boot sequence
- â¬œ Automated regression suite wired into the build

</details>

<details>
<summary><b>15. Verified measurements</b> â€” 6 done Â· 1 open</summary>

- âœ… Pre-fix frontier: 4,603,057 blocks, stopped inside a memory-clear loop
- âœ… After the per-thread register fix: 4,614,390 blocks, file layer reached
- âœ… After the open-flag fix: 4,644,637 blocks, cache index created
- âœ… Full rebuild times: 36m33s / 36m41s / 38m11s before tuning, 33â€“35 min after
- âœ… Harness-only rebuild: ~5 s
- âœ… Runtime test count progression: 193 â†’ 194 â†’ 195 â†’ 196 â†’ 210 â†’ 213
- â¬œ Profile the runtime once execution advances past the boot

</details>

## Current blocker, in full

**Updated 2026-10-29 (evening): the cache is not the blocker. The asset lookup is.**

The previous update said the cache index body was empty and that fixing it was the frontier. This
one corrects that: the cache index was never the problem, and the port was chasing the wrong
subsystem for most of the day.

What the investigation established, in order:

- The empty 64 KB block the engine writes is not a missing index serialisation. It is a
  completion record; the routine that writes it is the request's own write-completion path,
  and the zeroed payload it carries is what the engine prepared.
- The record geometry is 40 bytes per entry, not the 512-byte stride assumed earlier.
- The engine's asset request is well formed. Its lookup key is built correctly and the disc
  contains the matching entry, so the failure is not a naming, case or separator problem.
- The asset subsystem's own registry is populated at the point of failure, with several
  entries including the one being asked for. The table lookup is not starting from empty.
- The lookup's record scan behaves correctly when observed at the right point.
- Startup order matches the console up to the point where the asset subsystem's mutex is
  created.

**So what fails?** The port reaches the asset lookup and reports "not found", while the console
log shows the main thread polling a work-queue condition repeatedly after the archive is mounted.
The port's main thread does not appear to wait there. Why the two diverge is the current
frontier, and it is now a question about ordering and synchronisation rather than about parsing
or decoding.

**Methodological cost, recorded honestly:** several claims made during the day had to be
retracted â€” a misidentified writer, a "registry is never populated" conclusion, a missing
instruction in the recompiler, and a "the program entry never runs" conclusion. Each was
corrected by measurement rather than argument. The private notes now open with a current-state
block that separates verified facts from retracted claims, so the next pass does not rebuild work
that was already disproved.

Two measurement rules matter more than any single finding here: probes in this harness observe
only translated block entries, not arbitrary addresses; and the link-register value seen at an
import call is the trampoline's own return address, not the caller's.

The two decode bugs from the earlier update remain fixed and pinned by regression tests, and the
port still routes cache writes exactly like the console on a cold boot.

## How it is validated

The oracle is the retail disc booted headless in RPCS3 with tracing enabled. Its
traces are the ground truth for call order, arguments, return codes, file paths,
descriptor numbering and file layout. Behaviour is compared against those traces,
not against intuition. Where the oracle cannot answer â€” engine-internal state
machines, for instance â€” the port's own instrumentation is used, and anything not
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
any change that flips an item (empty square to green tick) â€” including new items discovered and parked
experiments â€” so the page never drifts from the repository.

## Legal

No game data or derived binaries are distributed. The port reads only from a
user-selected local disc dump. Killzone 2 and related trademarks belong to their
respective owners.
