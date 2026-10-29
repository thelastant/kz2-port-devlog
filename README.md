# kz2-port

A native Windows Rust port of Killzone 2, built from a user-supplied retail disc dump.
The original game is used only as a behavioural and data reference. No game binaries,
assets, or decompiled output are distributed.

**Goal** Ã¢â‚¬â€ a 1:1 playable port with no PS3 emulation in the runtime: boot, menus,
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
| Playable? | **No** Ã¢â‚¬â€ the boot stops in the engine's own asset lookup |

## Progress

**143 done Ã‚Â· 52 open.** Ã¢Å“â€¦ done and verified Ã‚Â· Ã¢Â¬Å“ outstanding Ã‚Â·
`(in progress)` being worked now Ã‚Â· `(parked)` tried and reverted, kept on a branch.

<details>
<summary><b>1. Project foundations</b> Ã¢â‚¬â€ 12 done Ã‚Â· 2 open</summary>

- Ã¢Å“â€¦ Rust workspace: core, runtime, assets, render, recompiler, boot harness, 16 generated shards
- Ã¢Å“â€¦ Pinned toolchain and MinGW link paths captured in `tools/build.ps1`
- Ã¢Å“â€¦ Build script validates the produced binary against source timestamps
- Ã¢Å“â€¦ Parallel shard build measured end to end (16 crates over 8 physical cores)
- Ã¢Å“â€¦ Harness-only rebuild path separated from shard rebuilds (~5 s vs ~34 min)
- Ã¢Å“â€¦ Release profile tuned: `panic=abort`, debuginfo stripped, default codegen units
- Ã¢Å“â€¦ Binary size reduced 387 MB Ã¢â€ â€™ 369 MB by the profile change
- Ã¢Å“â€¦ Jobserver starvation diagnosed when codegen units were raised to 256 (6.0 of 16 cores busy vs 8.4Ã¢â‚¬â€œ9.4 with default)
- Ã¢Å“â€¦ Worker-count sweet spot measured rather than assumed (15 workers, 8 physical cores)
- Ã¢Å“â€¦ Private evidence layout (`logs/`, `notes/`) kept separate from the public page
- Ã¢Å“â€¦ Public project page and devlog publishing pipeline, with remote-head verification
- Ã¢Å“â€¦ Commit discipline: one subsystem per commit, contract + measured boot delta in the body
- Ã¢Â¬Å“ Split generated shards from the runtime ABI so logic edits stop rebuilding 16 crates
- Ã¢Â¬Å“ Trim the translation closure to the functions a boot actually reaches

</details>

<details>
<summary><b>2. Loading and translation</b> Ã¢â‚¬â€ 12 done Ã‚Â· 2 open</summary>

- Ã¢Å“â€¦ Retail executable parse: ELF headers, segments, entry point
- Ã¢Å“â€¦ Import resolution across the game's libraries (342 imports, 23 libraries)
- Ã¢Å“â€¦ Thread-local storage image copied per thread
- Ã¢Å“â€¦ Guest stack and heap layout
- Ã¢Å“â€¦ System module list answered (the modules the game requests)
- Ã¢Å“â€¦ Disc presented as the read-only `/dev_bdvd` root
- Ã¢Å“â€¦ Static recompiler: decoder, control flow, call/return emission
- Ã¢Å“â€¦ Whole-closure lift: 49,070 functions, 428,755 basic blocks
- Ã¢Å“â€¦ Dispatcher follows real control flow rather than per-function tests
- Ã¢Å“â€¦ Interpreter fallback for blocks the static translation does not contain
- Ã¢Å“â€¦ Fixed: doubleword compares were decoded as word compares, which starved the file layer
- Ã¢Å“â€¦ Verified the lift against the retail disc: function inventory, SPU images, no lifter gaps in the largest image
- Ã¢Â¬Å“ Executable hot-patching / self-modifying code
- Ã¢Â¬Å“ Runtime-loaded overlays and additional modules beyond the initial set

</details>

<details>
<summary><b>3. Kernel and threading</b> Ã¢â‚¬â€ 21 done Ã‚Â· 2 open</summary>

- Ã¢Å“â€¦ lv2 syscall table cross-checked against the oracle's (451 entries, name for name)
- Ã¢Å“â€¦ PPU threads: create, start, exit, join, get-id, stack information
- Ã¢Å“â€¦ Cooperative scheduler with a deterministic block clock
- Ã¢Å“â€¦ Per-thread architectural state: general, float, vector, condition, count, status registers
- Ã¢Å“â€¦ Thread switches cannot leak architectural state (regression-tested)
- Ã¢Å“â€¦ Fixed: a run-away memory-clear loop caused by cross-thread register leakage Ã¢â‚¬â€ the thread's condition register was another thread's
- Ã¢Å“â€¦ Mutexes: create, destroy, lock, trylock, unlock
- Ã¢Å“â€¦ Light-weight mutexes: create/destroy/lock/trylock/unlock surface
- Ã¢Å“â€¦ Light-weight condition variables: create/destroy/wait/signal/signal-all, with real blocking and waiter hand-off
- Ã¢Å“â€¦ Semaphores: create, wait, trywait, post, get-value
- Ã¢Å“â€¦ Condition variables: create, destroy, wait, signal, signal-all, signal-to
- Ã¢Å“â€¦ Event queues: create, receive, tryreceive
- Ã¢Å“â€¦ Event ports: create, connect-local, send
- Ã¢Å“â€¦ Event flags
- Ã¢Å“â€¦ Timers: microsecond sleep, timebase, timebase frequency, time zone, current time
- Ã¢Å“â€¦ `sys_process_is_stack` answered per thread
- Ã¢Å“â€¦ `sys_ss_access_control_engine`
- Ã¢Å“â€¦ Return-to-dispatcher marker kept distinct from a real jump to null
- Ã¢Å“â€¦ Preemptive scheduling: a wake makes a higher-priority thread runnable immediately, not at the next slice edge
- Ã¢Å“â€¦ Sleepers become runnable the moment the clock passes their deadline (a thread had been asleep 224,000 blocks past its deadline)
- Ã¢Å“â€¦ Fixed: a lightweight condition wait was refused for ownership Ã¢â‚¬â€ the system's call has no such requirement, and the engine's file layer lost thousands of waits to it
- Ã¢Å“â€¦ Fixed: the system-cache mount no longer creates the file layer's own directory in advance, so the engine takes its real "create the directory" branch
- Ã¢Å“â€¦ Regression test: a thread switch preserves per-thread register state
- Ã¢Å“â€¦ Parked: strict light-weight mutex ownership Ã¢â‚¬â€ the first attempt initialised the owner field to the kernel's "free" value and deadlocked, because the guest treats a cleared field as free
- Ã¢Å“â€¦ (parked) Light-weight mutex contention under the guest's own encoding Ã¢â‚¬â€ built and measured; boot behaviour was identical to the baseline (same block count, same stop, no extra file activity), so it is kept on a branch instead of merged
- Ã¢Â¬Å“ Real-time priority inversion / priority inheritance
- Ã¢Â¬Å“ Thread renaming, affinity and debug interfaces

</details>

<details>
<summary><b>4. Memory and mappers</b> Ã¢â‚¬â€ 6 done Ã‚Â· 3 open</summary>

- Ã¢Å“â€¦ Guest memory with mapped/unmapped fault reporting
- Ã¢Å“â€¦ `sys_memory_allocate` and user memory size queries
- Ã¢Å“â€¦ Memory container and block allocation used by the engine's allocator
- Ã¢Å“â€¦ Address reservation and shared memory allocation
- Ã¢Å“â€¦ Memory mapper address space and search-and-map
- Ã¢Å“â€¦ Allocation probes confirm zeroed blocks and requested sizes
- Ã¢Â¬Å“ Shared memory aliasing (the port maps one address instead of aliases)
- Ã¢Â¬Å“ Memory protection changes and guard pages
- Ã¢Â¬Å“ Full IO address-space capacity (the engine maps many 1 MB chunks at level load)

</details>

<details>
<summary><b>5. File system</b> Ã¢â‚¬â€ 15 done Ã‚Â· 4 open</summary>

- Ã¢Å“â€¦ `cellFs*` and `sys_fs_*` share one implementation, so both entry points have the same semantics
- Ã¢Å“â€¦ Open, close, read, write, lseek
- Ã¢Å“â€¦ Stat and fstat with the console's exact structure layout (52 bytes, 4-byte packed)
- Ã¢Å“â€¦ Mkdir, rmdir, rename, unlink, access, fsync
- Ã¢Å“â€¦ Opendir, readdir, closedir
- Ã¢Å“â€¦ Device roots: disc (read-only), save root, per-title cache
- Ã¢Å“â€¦ Per-title cache directory created on demand and mounted at `/dev_hdd1`
- Ã¢Å“â€¦ Cache mount reports created vs relayed
- Ã¢Å“â€¦ Path normalisation, including repeated separators and bare device paths
- Ã¢Å“â€¦ Directory-listing contract: `.`/`..`, documented record size, end-of-listing behaviour
- Ã¢Å“â€¦ Fixed: open flags decoded from the library's octal values Ã¢â‚¬â€ create is not the value a hex reading suggests
- Ã¢Å“â€¦ Fixed: host errors mapped by kind (missing, permission, directory, exists) instead of a single collapsed code
- Ã¢Å“â€¦ Fixed: descriptors numbered from the console's first non-stream handle; the engine reads a zero descriptor as "no file"
- Ã¢Å“â€¦ Regression test: every access mode and the create flag
- Ã¢Å“â€¦ Regression test: descriptors start after the standard streams
- Ã¢Å“â€¦ Fixed: the doubleword compare (`cmpdi`/`cmpldi`) was decoded as the word form, so the file layer's free-list bitmap bit test always read a set bit in the upper 32 bits as clear - the same cache-file entry was handed out twice and the index was written to the data file. With it fixed, the cache initialisation routes the writes with the console's exact split (17 writes to the 1 MB index, one 512-byte header to the data file)
- Ã¢ÂÅ’ (in progress) The cache index body is empty: the engine writes a 1 MB zeroed staging buffer instead of file entries, so the index is an empty table. This is the current file-layer blocker.
- Ã¢Â¬Å“ `sys_fs_fcntl` device-query path exercised the way the console exercises it
- Ã¢Â¬Å“ Blu-ray specific surface beyond plain files

</details>

<details>
<summary><b>6. Assets and data formats</b> Ã¢â‚¬â€ 7 done Ã‚Â· 3 open</summary>

- Ã¢Å“â€¦ PSARC archive reader (retail `data_ps3.psarc` opens: 3 layers, 3,951 hashed entries)
- Ã¢Å“â€¦ Serialised object reader
- Ã¢Å“â€¦ Texture reader
- Ã¢Å“â€¦ Mesh reader
- Ã¢Å“â€¦ Skeleton reader
- Ã¢Å“â€¦ Skinning reader
- Ã¢Å“â€¦ The engine's asset lookup located: a name is resolved to a `cache:lumps/<name>.core` path through the FIOS cache; the "Application" root asset is what the boot asks for first
- Ã¢ÂÅ’ (in progress) Asset registry / lump resolution through the engine's own cache - blocked by the empty cache index body; the lookup returns nothing and the engine fatals by design
- Ã¢Â¬Å“ Streaming packages and level packages
- Ã¢Â¬Å“ Animation clip and state-machine data

</details>

<details>
<summary><b>7. Graphics and display</b> Ã¢â‚¬â€ 6 done Ã‚Â· 7 open</summary>

- Ã¢Å“â€¦ Graphics context creation and teardown
- Ã¢Å“â€¦ Display configuration: 720x480 progressive, correct pitch and gamma
- Ã¢Å“â€¦ Frame submission path with completed flips
- Ã¢Å“â€¦ Vblank handling and fence release
- Ã¢Å“â€¦ Nine GCM method classes recorded with argument counts
- Ã¢Å“â€¦ Video-out state and device queries
- Ã¢Â¬Å“ Rasteriser (nothing is drawn yet)
- Ã¢Â¬Å“ Shader translation and pipeline state
- Ã¢Â¬Å“ Texture upload and sampling
- Ã¢Â¬Å“ Render-target and depth-stencil behaviour
- Ã¢Â¬Å“ Flip contexts that are not simple rings
- Ã¢Â¬Å“ IO mapping capacity for level-load chunk mapping
- Ã¢Â¬Å“ Report/DMA callbacks driven by the title's own frame data

</details>

<details>
<summary><b>8. Audio and video out</b> Ã¢â‚¬â€ 2 done Ã‚Â· 3 open</summary>

- Ã¢Å“â€¦ Audio system initialised; channel and encoder configuration queried
- Ã¢Å“â€¦ Video-out configuration and state reporting
- Ã¢Â¬Å“ Audio port opened and samples submitted
- Ã¢Â¬Å“ Encoder and downmix selection honoured
- Ã¢Â¬Å“ Output device enumeration and format negotiation

</details>

<details>
<summary><b>9. Fonts and text</b> Ã¢â‚¬â€ 4 done Ã‚Â· 3 open</summary>

- Ã¢Å“â€¦ Font library initialisation completes with a real handle in guest memory
- Ã¢Å“â€¦ Caller configuration validated the way the library validates it
- Ã¢Å“â€¦ Cache and revision reporting
- Ã¢Å“â€¦ Font-set requests refused with the library's own "no support function" code instead of returning an unusable object
- Ã¢Â¬Å“ Font-set opening with real fonts
- Ã¢Â¬Å“ Glyph rasterisation and text layout
- Ã¢Â¬Å“ Console system-font data source

</details>

<details>
<summary><b>10. Save data</b> Ã¢â‚¬â€ 2 done Ã‚Â· 3 open</summary>

- Ã¢Å“â€¦ Save API surface answers with real library error codes
- Ã¢Å“â€¦ Save root mapped to the host save directory
- Ã¢Â¬Å“ Save container format (directory, parameters, icons)
- Ã¢Â¬Å“ Auto-load and auto-save flows
- Ã¢Â¬Å“ Listing, deleting and copying saves

</details>

<details>
<summary><b>11. SPU and SPURS</b> Ã¢â‚¬â€ 5 done Ã‚Â· 4 open</summary>

- Ã¢Å“â€¦ SPU image parsing for images embedded in the executable
- Ã¢Å“â€¦ SPU instruction executor with opcode coverage
- Ã¢Å“â€¦ SPU local store, registers and channel handling
- Ã¢Å“â€¦ SPURS API surface: task and group creation, policies, signals
- Ã¢Å“â€¦ Standalone image execution under a development harness
- Ã¢Â¬Å“ SPU thread groups created and started inside a real boot
- Ã¢Â¬Å“ DMA transfers and channel semantics exercised by real workloads
- Ã¢Â¬Å“ SPU threads scheduled alongside PPU threads
- Ã¢Â¬Å“ Task exit / enabled-bit interleaving verified (known hazard for thread-pool teardown)

</details>

<details>
<summary><b>12. Input</b> Ã¢â‚¬â€ 0 done Ã‚Â· 3 open</summary>

- Ã¢Â¬Å“ Pad initialisation and capability reporting
- Ã¢Â¬Å“ Pad state and data delivery
- Ã¢Â¬Å“ Input mapping and deadzones

</details>

<details>
<summary><b>13. Menus, level load and gameplay</b> Ã¢â‚¬â€ 0 done Ã‚Â· 9 open</summary>

- Ã¢ÂÅ’ (in progress) Asset lookup completing - the engine asks for the "Application" root asset; it resolves through the cache index, which is currently empty (current blocker)
- Ã¢Â¬Å“ Front-end and menu flow
- Ã¢Â¬Å“ Level loading and streaming
- Ã¢Â¬Å“ Scripting runtime
- Ã¢Â¬Å“ Physics runtime
- Ã¢Â¬Å“ AI runtime
- Ã¢Â¬Å“ Animation runtime driving skinned meshes
- Ã¢Â¬Å“ Settings persistence
- Ã¢Â¬Å“ Save/load integration

</details>

<details>
<summary><b>14. Validation, oracle work and tooling</b> Ã¢â‚¬â€ 38 done Ã‚Â· 6 open</summary>

- Ã¢Å“â€¦ Oracle: retail disc booted headless in RPCS3 with tracing enabled
- Ã¢Å“â€¦ Syscall inventory captured from the oracle (43 lv2 calls, 28 HLE calls)
- Ã¢Å“â€¦ Boot-order file-system contract extracted: paths, order, return codes
- Ã¢Å“â€¦ Descriptor numbering and open-flag evidence taken from the oracle
- Ã¢Å“â€¦ First-boot cache creation captured, including the deterministic cache header
- Ã¢Å“â€¦ Engine fatal path identified: message formatting followed by a deliberate trap, not a wild pointer
- Ã¢Å“â€¦ Fatal message recovered from the guest stack at the trap
- Ã¢Å“â€¦ Asset-lookup chain identified from the message back to the cache initialiser
- Ã¢Å“â€¦ File-cache initialisation loop located and its exit condition identified
- Ã¢Å“â€¦ Request object traced end to end: submit, wait, completion flag, operation-state word
- Ã¢Å“â€¦ Every writer of the completion flag and of the operation-state word enumerated
- Ã¢Å“â€¦ Block-level ordering of completion vs state finalisation captured, including the threads involved
- Ã¢Å“â€¦ Structure layouts cross-checked against the console headers
- Ã¢Å“â€¦ Local tools: decompile-at, references-at, disassembly, store scans, ELF helpers
- Ã¢Å“â€¦ Oracle log miners for paths, HLE calls, inventory and ordering
- Ã¢Å“â€¦ Probes: block entry with link register, interpreter-level, request dereference, object mode
- Ã¢Å“â€¦ Store watch over a memory range, and a block-clock request-state sampler
- Ã¢Å“â€¦ Mode-byte sampler for the byte the worker turns into open flags
- Ã¢Å“â€¦ Operation-state word semantics identified (in progress / done / invalid)
- Ã¢Å“â€¦ Mechanical file-trace comparison against the oracle, aware of encoding and quoting differences
- Ã¢Å“â€¦ Machine-parameter audit: every start-up system parameter, the user-memory figure and the module-load set compared against the oracle
- Ã¢Å“â€¦ All eight start-up system parameters answered (four were refused before the audit)
- Ã¢Å“â€¦ Cross-checked against Project Helghast's Killzone 3 port (same engine family) and adopted its documented contract fixes: the condition-variable block layout and mutex hand-off, the 512-byte stat block size, and distinct stat times
- Ã¢Å“â€¦ Measured: the condition-variable block layout and mutex hand-off, the 512-byte stat block size and the distinct stat times change nothing Ã¢â‚¬â€ the boot is identical, so they are kept as correct console behaviour, not as progress
- Ã¢Å“â€¦ Create-only vs read-write (issue #4) was a real decode bug, not guest state: `cmpwi`/`cmplwi` treated `r0` as literal zero, dropping the read-write access bits. With it fixed the open carries read-write and the cache is written
- Ã¢Å“â€¦ Measured: the user-memory total and the console's reserved slice correct Ã¢â‚¬â€ the guest consumes them (every allocation moves by exactly the reserved amount, +1,052 blocks), but the cache still never gets written
- Ã¢Å“â€¦ Firmware error-code table audited: four wrong values found and fixed, and a test pins the table
- Ã¢Å“â€¦ Host file errors reported as what they are (`EACCES`, `EISDIR`, `ENOTDIR`, `ENOTEMPTY`) instead of always "not found"
- Ã¢Å“â€¦ Cache files: deletion verified, and a recreated file now carries a newer change time
- Ã¢Å“â€¦ Cold-cache oracle boot captured: the console writes a 1 MB index in one pass, bit-identical to the cached copy
- Ã¢Å“â€¦ Retry loop identified as the engine's reopen service, and proved not to inspect the cache contents
- Ã¢Å“â€¦ Lightweight and system mutexes modelled (owner, hand-off, release on condition wait) Ã¢â‚¬â€ measured: the boot does not contend on either
- Ã¢Å“â€¦ Thread ids start at 1, because the guest reads 0 as "no owner"
- Ã¢Å“â€¦ SPURS LF queue object laid out in guest memory (counters, size, depth, buffer, signal address) with the push advancing the guest counter Ã¢â‚¬â€ measured: boot unchanged, because nothing reads it yet
- Ã¢Å“â€¦ Interpreter counter branches (`bdz`/`bdnz`) corrected Ã¢â‚¬â€ they were swapped, which cost the engine its file-object slots; 61 cache opens became 9
- Ã¢Å“â€¦ lv2 mutex numbering corrected (102 = lock, 103 = trylock), condition hand-back wired, timeouts honoured on all four sync waits, console lwmutex layout Ã¢â‚¬â€ measured: 9 Ã¢â€ â€™ 21 Ã¢â€ â€™ 31 cache opens
- Ã¢Å“â€¦ The fd swap (the index written to the data file) was a second decode bug: `cmpdi`/`cmpldi` decoded as the word form, so the free-list bitmap bit test in the upper 32 bits always read clear and the same entry was handed out twice. With it fixed the write split matches the console byte-for-byte (17 writes to the index, one header to the data file)
- Ã¢Å“â€¦ Measured: the cache index body is all zeros. The engine writes a 1 MB zeroed staging buffer; the file-entry fill never populates it. A store watch over the buffer shows only the zeroing memset, and the port's cache hash differs from the console's while the size matches
- Ã¢Å“â€¦ Located the engine's asset lookup: the boot asks for a root asset named "Application", which resolves through a `cache:lumps/<name>.core` path; an empty index returns nothing and the engine then takes its own deliberate fatal path
- Ã¢Â¬Å“ Explain why the module-load set differs between the two boots
- Ã¢Å“â€¦ Trace gates for file calls, syscalls, imports, memory and synchronisation
- Ã¢Â¬Å“ Console-side visibility into engine-internal structures (needed to settle the current ordering question)
- Ã¢Â¬Å“ Per-subsystem behavioural comparison beyond the boot sequence
- Ã¢Â¬Å“ Automated regression suite wired into the build

</details>

<details>
<summary><b>15. Verified measurements</b> Ã¢â‚¬â€ 6 done Ã‚Â· 1 open</summary>

- Ã¢Å“â€¦ Pre-fix frontier: 4,603,057 blocks, stopped inside a memory-clear loop
- Ã¢Å“â€¦ After the per-thread register fix: 4,614,390 blocks, file layer reached
- Ã¢Å“â€¦ After the open-flag fix: 4,644,637 blocks, cache index created
- Ã¢Å“â€¦ Full rebuild times: 36m33s / 36m41s / 38m11s before tuning, 33Ã¢â‚¬â€œ35 min after
- Ã¢Å“â€¦ Harness-only rebuild: ~5 s
- Ã¢Å“â€¦ Runtime test count progression: 193 Ã¢â€ â€™ 194 Ã¢â€ â€™ 195 Ã¢â€ â€™ 196 Ã¢â€ â€™ 210 Ã¢â€ â€™ 213
- Ã¢Â¬Å“ Profile the runtime once execution advances past the boot

</details>

## Current blocker, in full

**Updated 2026-10-30: the map pipeline is decoded; rendering is next. The engine boot remains
parked.**

Two separate threads are in play, and it is worth keeping them apart.

**Maps â€” decoding is finished.** Every single-player level loads through the asset pipeline: the
archive reader, the catalog, the object reader and cross-file reference resolution all work across
eleven levels and more than two hundred level lumps, with no load failures. Mesh geometry resolves
as well, with no degenerate or failed meshes in sampling across levels.

The last missing piece was placement. World nodes were walked past during parsing and never
reduced to transforms, so a level was a pile of resources rather than a scene. An opt-in capture
now records them, leaving the default parse path unchanged. The format is confirmed from data â€” a
4x4 row-major affine matrix with an orthonormal basis and translation in the last row; a pure
rotation decodes to an exact cosine/sine pair and identity nodes appear where an unplaced instance
should be.

Assembled scenes behave like levels: a large mission produces over ten thousand placed nodes
across a multi-kilometre extent, a small epilogue area a few hundred units, and long linear
missions stretch several kilometres along one axis. What remains for maps is drawing that set,
which is a renderer task rather than a decoding one.

**Boot â€” parked, with the question stated.** The engine still stops during asset lookup. The
reason is not in the cache content, the device registry, string handling, record scanning, startup
ordering, the synchronisation layer or file-operation ordering; each was checked and excluded by
measurement, and several early conclusions were retracted when measurement contradicted them. In
the console trace the main thread is polling a work queue after mounting the archive, while the
port proceeds into the lookup. Why the two diverge is unresolved and documented in a
current-state summary in the private notes so it can be resumed without repeating the dead ends.

**A note on method**, because it shaped the day: the map thread succeeded where the boot thread
stalled, and the difference was not effort. Map progress was measured by counts â€” how many lumps
loaded, how many meshes resolved, how many nodes were placed â€” while the boot investigation asked
why something failed, where every answer had to be checked against a harness whose probes only
observe block boundaries. Countable questions were kind to this port today; causal ones were not.

## How it is validated

The oracle is the retail disc booted headless in RPCS3 with tracing enabled. Its
traces are the ground truth for call order, arguments, return codes, file paths,
descriptor numbering and file layout. Behaviour is compared against those traces,
not against intuition. Where the oracle cannot answer Ã¢â‚¬â€ engine-internal state
machines, for instance Ã¢â‚¬â€ the port's own instrumentation is used, and anything not
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
any change that flips an item (empty square to green tick) Ã¢â‚¬â€ including new items discovered and parked
experiments Ã¢â‚¬â€ so the page never drifts from the repository.

## Legal

No game data or derived binaries are distributed. The port reads only from a
user-selected local disc dump. Killzone 2 and related trademarks belong to their
respective owners.
