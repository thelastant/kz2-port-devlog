# Development log

## 2026-10-30 - the map pipeline is decoded end to end; placement was the last missing piece

- The asset side of the map work is finished. Every single-player level now loads, and levels can
  be assembled into placed scenes rather than piles of resources.
- Eleven levels, 237 lumps, zero load failures. The archive reader, catalog, RTTI object reader and
  cross-file reference resolution all work for every level.
- Mesh geometry resolves as well: sampling across levels produced no degenerate and no failed
  meshes, with vertex counts in the millions per level.
- The last missing piece was placement. World nodes were being walked past during parsing and
  never decoded, so nothing carried a transform. An opt-in capture now records them without
  changing the default parse path.
- The transform format is confirmed from data: a 4x4 row-major affine matrix, orthonormal basis,
  translation in the last row. A pure rotation node decodes to a clean cosine/sine pair, and the
  identity node appears exactly as an unplaced instance should.
- Assembled scenes look like levels. Corinth River yields over ten thousand placed nodes across a
  2.4 x 2.7 x 3.9 kilometre extent; the small epilogue area is a few hundred units across; the
  long linear missions stretch several kilometres along one axis. Placement scales with level size
  the way a real scene would.
- One correction worth recording: a first pass filtered level lumps on a single filename suffix and
  found nothing for three levels. Lumps are named by content descriptor rather than a consistent
  suffix, so that filter missed most geometry. Searching on the common asset prefix instead
  multiplied the node counts by an order of magnitude. The zero result was a filter bug, not
  empty levels.
- The boot thread remains parked. Its engine still stops during asset lookup, and the reason is
  not in the cache, the device registry, the string handling, the record scan, the startup order,
  the synchronisation layer or the file-operation ordering - all of those were checked and
  excluded by measurement. That investigation is documented with a current-state summary so it can
  be resumed without re-walking the dead ends.
- Next: render an assembled scene. The decoding problem is closed; what remains is drawing the
  nodes.

## 2026-10-29 - the cache was a red herring; the frontier is asset-lookup ordering

## 2026-10-29 - the cache was a red herring; the frontier is asset-lookup ordering

- Spent the day following the empty cache index to its source and found that it is not a
  serialisation failure. The block the engine writes is a request-completion record, and the
  zeroed payload it carries is what the engine prepared. Fixing the index would not have
  changed the boot.
- Along the way the asset lookup itself was mapped: the key the engine builds is correct, the
  disc contains the matching entry, and the asset subsystem's registry is populated at the
  point of failure rather than empty. The record scan behaves correctly when observed at the
  right boundary.
- Startup order also matches the console up to the point where the asset subsystem's mutex is
  created, so the divergence is later than expected.
- The console trace shows the main thread polling a work-queue condition repeatedly after the
  archive is mounted. The port's main thread does not appear to wait there. Why the two differ
  is the current frontier, and it is a question about ordering and synchronisation, not about
  parsing or decoding.
- Four conclusions were retracted during the day after measurement contradicted them: a
  misidentified writer routine, a "registry is never populated" reading, an alleged missing
  instruction in the recompiler, and a "program entry never runs" reading. The private notes
  now open with a current-state block that separates verified facts from retracted claims.
- Two measurement rules are worth publishing because they cost the most time: the harness's
  probes observe only translated block entries rather than arbitrary addresses, and the
  link-register value visible at an import call is the trampoline's own return address rather
  than the caller's.
- Next: instrument the import boundary so guest call sites can be attributed, then compare the
  port's main-thread ordering against the console's after the archive mount.

## 2026-10-29 - the empty cache body is a completion record, not missing entries

- Followed the write routine from its first instruction instead of from its call site. It takes
  the fios request object as its first argument and reads its own fields: an enable flag, a slot
  count, a per-request offset and an element size. That makes it the request's write completion,
  not a free-standing index serialiser.
- It formats the cache data file name, waits on the block fetch, and then stores a clock value at
  the request's offset. The helper it calls is the system clock syscall, scaled from seconds to
  nanoseconds.
- So the 64 KB index body write carries a timestamp at offset 0 and zeros after it. Nothing
  failed to serialise: the engine wrote exactly what it prepared.
- The record geometry is 40 bytes per entry, which also corrects an earlier guess of 512-byte
  records.
- Next: trace who sets the request's slot count and per-entry offset before the write, since
  they are the fields that decide whether any real entry is ever placed in the block.

## 2026-10-29 - the cache write routing is correct, but the index is still empty

## 2026-10-29 - the cache write routing is correct, but the index is still empty

- The previous entry fixed where the cache writes go; this entry reports what they contain. The
  index file is 1,043,456 bytes with only 19 non-zero bytes (the `fioscach` header): the whole
  1 MB index body is zeros.
- Instrumented the write path to print the buffer and size the engine hands the file layer. The
  two header writes carry a stack buffer holding `fioscach`; the sixteen body writes all carry
  the same heap staging buffer and the first words are zero on every one.
- A store watch over that buffer shows only the zeroing memset ever touches it. The engine
  allocates and clears the staging buffer and writes it out, but the step that would fill it
  with file entries never runs. So the index is an empty table.
- That is why the boot then stops at the engine's "could not locate application specific
  assets called 'Application'": the lookup resolves the name through a `cache:lumps/<name>.core`
  path, and an empty index returns nothing. The engine then hits its own deliberate trap.
- Next: find what populates the cache index (or why the file list it copies from is empty) so
  the index has entries and the asset lookup can succeed.

## 2026-10-29 - the cache bootstrap completes: the index is written correctly

- The cache build was blocked by a second interpreter/recompiler bug: the doubleword
  compare (`cmpdi`/`cmpldi`) was decoded as the word form. The engine's entry allocator uses a
  256-bit free-list bitmap and tests a bit with a doubleword compare, so a set bit in the upper
  32 bits was always read as clear, the same entry was handed out for both cache files, and
  every index write went to the data file.
- With the decode fixed, the port now builds the cache exactly like the console: 17 writes to
  the index (1,043,456 bytes) and one 512-byte header to the data file. The acceptance bar - a
  write in the trace and a cache index above zero - is met.
- The boot then advances past the cache to the next step and stops at the engine's own
  "could not locate application specific assets" report, which is the asset lookup that
  follows cache initialisation - the next frontier.

## 2026-10-29 - the create-only open is fixed; the engine now writes its cache

- The cache index was opened create-only (0x40) here but read-write (0x42) on the console. The
  cause was not the engine's request - the mode byte was always read-write - but a bug in the
  port's interpreter: its word-compare treated register 0 as a literal zero, which the compare
  instructions do not, so the equality test that selects read-write never passed and the
  read-write bit was dropped. The recompiler did not share the bug, so only interpreted code
  was affected.
- With the interpreter fixed, the port opens both cache files read-write, writes eighteen
  times, and produces a 1,043,456-byte cache file - the console's own index size. A regression
  test pins the instruction.
- This is the acceptance milestone: a write in the trace and a cache above zero. The boot still
  stops before the front-end, but the file-cache bootstrap that had been blocking everything
  now completes its writes.

## 2026-10-29 - the cache loop is now counted exactly, and the stall has a concrete shape

- A full trace with the file layer's report enabled settles the earlier uncertainty over the
  open flags: across 61,884 opens of the cache index - every one create-only, every one
  successful, none read-write - there is not a single write, read, or close. The handle number
  climbs monotonically from 3 to past 61,000, so the engine opens the same file and never
  releases it.
- The loop is not a busy retry: every open and every stat succeeds. The two worker threads
  run a healthy work-queue cycle - they wait for work, process an open, and wait again - until
  the main thread stops handing them work and moves onto a cache-hash loop, leaving the
  workers idle on the work-queue condition and two more threads idle on event queues. That is
  why the port reaches its step limit with the cache index still empty.
- This sharpens the earlier "request wait reports in-progress" finding: the workers are
  genuinely waiting on their work queue, and the open question is whether the main thread's
  hash loop is finite-but-slow or stuck.
- Also recorded this session: the engine's SPU architecture, from a public GDC 2009 talk, as
  the target shape for the port's scheduler and graphics - six SPUs, roughly 44 job types and
  a thousand jobs a frame, a deferred renderer with a quarter-resolution SPU post-processing
  chain composited by the GPU.
- Tests: 214. The level viewer still runs on retail data; the game itself is still not
  playable, and the acceptance test is unchanged - a write in the trace and the cache index
  above zero.

## 2026-10-29 - the cache directory is created, and the missing write has a name

- The engine's start-up for its disk cache is a short chain: check the working directory,
  create it if it is missing, then open the two cache files. The port now runs that chain
  itself - the engine issues its own "create directory" request, the directory appears, and the
  cache file is opened and registered in the engine's own table, at the same relative path the
  console uses.
- Getting there needed one behavioural decision, kept behind a switch while it is verified:
  when the engine asks whether a missing path exists, it expects the answer that means "not
  found" rather than a hard error, because that is the branch that creates the directory. With
  that switch on, the request types the engine dispatches went from one to four - including the
  directory-creation request it had never sent before.
- The cache file is still never written, and the reason is now specific rather than mysterious.
  The engine registers its record for the cache file with **no access mode**, opens it
  create-only, and then reopens it forever: the access mode never reaches the platform, so no
  write can happen.
- The read-write open is not mis-encoded: it is **abandoned**. A per-request flag tested by the
  engine's dispatcher drops roughly half of the open requests before they are executed, and the
  ones dropped are exactly the read-write ones. The create-only opens that survive are the
  retry loop's.
- A first attempt to fix access handling in the file layer was reverted after a test showed the
  premise was wrong: the engine converts its file-layer mode into access flags itself, so the
  platform never sees the ambiguous value. It is recorded as a rejected change rather than kept
  as speculative code.
- Measurement added for the next step: the dispatcher now reports which thread abandons a
  request and the whole field the abandon test reads, which distinguishes "a flag somebody
  sets" from "a field I have misread". No behaviour change is in that build.
- Tests: 214. The level viewer still runs on retail data; the game itself is still not playable,
  and the acceptance test is unchanged - a write in the trace and the cache index above zero.

## 2026-10-29 - the missing directory is now named down to one error code

- The engine's cache start-up is a short chain: initialise, create the directories the file
  layer needs, then open the two cache files. Probes show the first two steps run in this port
  and the third is never reached.
- The reason is now specific. The directory walk asks the file layer about each path fragment.
  On the console a missing fragment answers "not found", the walk creates it, and start-up
  continues. In this port that same query comes back with an **internal rejection code from the
  engine's own request layer**, not a file-system answer, and the walk treats any error as fatal
  and gives up before creating anything.
- So the create-the-directory call is never even submitted, which matches the earlier finding
  that this boot only ever submits one kind of file request out of the seventeen the worker
  knows how to dispatch.
- Also identified: the engine's file worker dispatches on a numeric request type, and the type
  that creates a directory is a specific one that this boot never sends.
- No new build was needed for any of this - it is probe and table work on the existing binary.
- Tests: 214. The level viewer is unaffected and still runs on the retail archive.

## 2026-10-29 - the reopen loop was a symptom: the cache directory is never created

- The system-cache mount used to create the file layer's working directory in advance. That one
  line was steering the engine: with the directory present it registered a cache entry and its
  reopen service opened the index 62,405 times, every open create-only, and never wrote a byte.
- With the directory absent - which is what a console cold boot sees - the engine's check answers
  "no such file", and the port now takes the same branch the console takes. Measured: six checks
  from the media threads, **no opens, no writes**, and the boot runs to the engine's own asset
  abort instead of spinning in a reopen loop.
- The missing call is the directory creation the console performs between those two states, from
  the same media thread, before it opens the index read-write. The engine has that code path and
  does not reach it here; two probes on it record zero hits. So the last few days' loop was not a
  deadlock in the file layer - it was a branch the port made unreachable.
- Why this is progress rather than a regression: the previous state produced 62,405 opens and no
  writes because the engine was on a path the console never takes. The port now follows the
  console's sequence up to the missing call, which is a smaller and better-defined gap.
- Also fixed and measured in this build: a sleeping thread is runnable as soon as its deadline
  passes (one had been asleep 224,000 blocks past it), and the file layer's own condition wait is
  no longer refused with a permission error it never returns on the console.
- Tests: 213. Still not playable; the acceptance test is unchanged - a write in the trace and the
  cache index larger than zero.

## 2026-10-29 - the loop had a cause: a condition wait that always failed

- Preemption from the previous entry was implemented and immediately broke the boot in a way that
  was my bug, not the game's: the scheduler switched threads but forgot to hand the resume address
  back to the boot loop, so two threads ran each other's code and the program counter ended at
  zero. Fixed and pinned with a test.
- With that correct, the boot went further than ever - and then stopped on a null condition handle.
  Tracing the wait that produced it showed the real problem: **every condition wait from the file
  layer's media threads was being refused**. The port required the caller to own the paired
  lightweight mutex; the system's actual call has no such requirement, it releases the mutex if
  held and sleeps either way. The console trace confirms it: 254 condition waits during a cold
  boot, zero errors. The invented check is gone.
- Two more defects were visible in the same dump. A sleeping thread whose deadline was 224,000
  blocks in the past was still asleep, because sleepers only woke once every other thread blocked;
  the scheduler now makes an expired deadline runnable first. And the system-cache mount was
  creating the file layer's own working directory in advance, which removed the engine's
  "directory missing, create it" branch entirely.
- Measured, one run: the null fault is gone, the boot no longer stops early (it reached the
  harness's 60,000,000-block step limit), and the cache descriptor is reopened **62,405** times
  where the previous build managed 169. That is not progress toward the goal by itself - writes
  are still zero - but the loop is now understood and driven by a real state machine rather than a
  refusal.
- Console evidence gathered for the next step: read live out of the emulated machine, the engine
  keeps one fixed-size record per managed file, holding its own file descriptor, the access mode
  and the path. On the console the cache records carry **read-write** access and stay open. In the
  port they carry create-only, which is exactly why the reopen service keeps rejecting them.
- Tests: 213. The port is still not playable; the acceptance test is unchanged - a file write in
  the trace and the cache index growing past zero.

## 2026-10-28 - the game played to the first level, and what a level load costs

- The retail disc was driven from the language screen through the main menu and difficulty into **Corinth River**, the first campaign level, with the virtual pad. That needed two things that were not obvious: RPCS3's keyboard pad handler has to be selected in its configuration, and key presses must go through Win32 events - the usual automation route only reaches the game list, never the render surface.
- With a run in a level, the file layer could be profiled for the first time at a point past start-up. From the log tail, counted mechanically: **96 opens, every one of them a `.pspatch` file** - 18 hashes, each requested from both the disc and the installed game directory - **30.4 MB written** to the two cache descriptors and **394 MB read**.
- The consequence for the port is sharper than the start-up numbers suggested: the disk cache is **not** a start-up artefact. The console writes 1 MB while initialising and another **30 MB during a level load**, into the same descriptor pair. A port that never performs the first write cannot reach the second, and the level's asset path never runs.
- Patch files are part of every load: the engine looks for a per-asset `.pspatch` on the disc and in the install directory. A port that serves only the disc tree takes a different branch for all 96 of those opens.
- Also recorded: the two cache descriptors are 3 and 4 in the load as well as at start-up, which independently confirms that the cache pair is the first two files the process opens.
- New tools: `rpcs3_press.py` (Win32 key events at the emulator window), `rpcs3_screenshot.py`, `oracle_level_load.py` (streams a multi-gigabyte log tail and counts opens, writes and reads), and `rpcs3_mem.py`, which reads guest memory over RPCS3's debug stub because `gdb` cannot talk to it.
- Tests: 210. The port itself is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the stall is scheduling, not a missing system call

- After a day of fixing kernel contracts with measurable but insufficient effect, the question changed from "which call is wrong" to "which *interleaving* is wrong". The answer came from one experiment: make the thread-switch interval configurable and see what the boot does with it.
- It does everything.

  ```
  quantum   1   129,555 blocks   15 file opens   crashes early
  quantum  16   152,357 blocks   35 file opens   crashes early
  quantum  64 60,000,000 blocks    0 file opens   spins to the block limit
  quantum 256 4,636,309 blocks   31 file opens   reaches the asset abort
  ```

  The console runs these threads on separate hardware threads with priorities and preemption. This port runs one at a time and switches every 256 blocks - close enough to get through start-up, and wrong at every other setting. That is not a missing kernel call; it is a scheduling-fidelity problem.
- The deadlock itself is three lines of trace: the scheduler wakes both file-layer threads, runs for about 1,400 blocks before it blocks, and by then the threads have signalled into an empty queue and gone back to sleep. On the console the same handshake happens in six microseconds, in the opposite order.
- Everything learned is now in one place rather than scattered across the day's notes: the blocker, the console's cold-boot sequence, every suspect closed with the measurement that closed it, what each fix did to the boot in order, and what finishing it needs.
- Finishing it means modelling lv2 priorities and making a woken thread eligible immediately, rather than a fixed round-robin. The acceptance test is unchanged and blunt: a `cellFsWrite` in the trace and `cache.idx` growing past zero.
- Tests: 210. The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the SPURS queue object, and a null result reported as one

- The last of the three contributor issues was about a SPURS queue whose state lived only on our side while the consumer reads the object in guest memory. The trace answered the ordering question first: the queue **is** initialised and attached, and the push is **never called** anywhere in the boot.
- So the initialiser was fixed and the producer was split out. The object now exists where the console puts it - counters, size, depth, buffer with its valid bit, direction, initialised flag, signal address and event-queue id - and a push advances the guest's own counter and writes into the slot it selects, instead of bumping a host index that never went down.
- **Measured: byte-identical. 4,636,309 blocks, 31 cache opens, no writes.** Exactly what was predicted before the build: nothing in this boot reads the object yet. It is recorded as a null result, not as progress.
- The half that cannot be exercised - the consumer registering itself, the push waking it through the attached event queue, the 16-bit sub-counters and the blocking flag - is now its own issue, with the trace as its evidence and an acceptance test that needs a run reaching the first push.
- Two tests drive the queue object directly, so the layout and the counter arithmetic are pinned even though the boot cannot reach them.
- Tests: 210. The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - three contributor issues, and a boot that keeps moving

- undecuple read the new mutex code and filed three issues. Two were defects in what had just been written, one was a gap further out; all three are answered here.
- **The syscall numbering was swapped** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 102 is `lock`, 103 is `trylock`, and the arm had them the other way round. A contended lock returned "busy" at once, so a caller that did not check the result entered its critical section without the mutex; a contended trylock blocked instead. The unit test repeated the same wrong number, which is exactly how such a thing survives review.
- **A woken condition waiter could return without its mutex**: the hand-back function existed and had no callers. Signals now hand it over, or queue the waiter until it holds it. The four waits (`lwcond`, `lwmutex`, `mutex`, `cond`) also had **no timeouts at all** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the timeout argument was ignored and "timed out" was unreachable; all four now honour it.
- The lightweight mutex layout was wrong in a way that only matters when the game reads the object itself: the recursive depth sat on the word that is the waiting-locker count on the console. It is at the console's offset now.
- **Measured, one build and one run each: 9 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 21 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 31 cache opens, 4,609,672 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 4,619,414 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 4,636,309 blocks, and still no cache write.** Every sync correction moves the boot, and none of them reaches the write, so the remaining gap between a working mutex hand-off and a written cache is somewhere else.
- On the SPURS issue: the import trace shows the LF queue **initialised and attached, and never pushed to** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no `PushBody`, no event-flag wait anywhere in the boot. So the initialiser writing nothing into the guest object is a real defect on the path, while the push cannot be exercised until the run gets further. Said so in the issue rather than closing it on code review.
- Tests: 208. Two issues closed with the commit, one kept open with the trace.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - auditing the emulator instead of the game

- The bdz/bdnz bug was found by accident, which suggested the same class of defect could be hiding elsewhere. So the interpreter was checked against the architecture, not against the game.
- Three more silent disagreements, all fixed: **word shifts by 32 or more** returned the operand unchanged instead of zero (Rust re-masks shift counts, which hid the rule); **`rldicr` kept the low bits instead of the high ones**, and `rldic`/`rldimi` missed the low bits the instruction clears; and a **wrapped word mask** (`mb > me`) was computed as an intersection, so every wrapped bit-field extraction read as zero.
- Each has a test now, and the boot is **byte-identical** afterwards ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â these paths are not exercised in this boot, so they are recorded as correctness with a null result rather than as progress.
- Worth saying what the audit has produced overall: four emulator bugs, one of which (the counter branches) was costing the engine its file-object slots. The emulator was a larger source of wrong behaviour than any of the console-contract differences chased earlier today.
- Tests: 205 runtime, 31 harness.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - a bug in our own interpreter, found by watching a bitmap

- The investigation had narrowed to a single thing: the engine gives up on a cache it opened successfully because it cannot obtain a **file-object slot** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the allocator returns zero on every call, so nothing records the descriptor and the poll repeats.
- That allocator is one of the blocks our **interpreter** covers rather than a lifted one, and the reason it failed was ours: the interpreter tested the counter-branch polarity backwards. `bdz` and `bdnz` were swapped, so every loop driven by the hardware counter that ran in the interpreter ran the wrong number of times. The allocator's 256-bit scan looked at one bit, declared the table full and returned zero, with a bitmap that was almost entirely clear.
- Corrected, with three tests pinning the semantics: a counter loop with CTR = n runs its body n times, `bdz` branches only at zero, and a plain conditional branch leaves the counter alone.
- **Measured: 61 cache opens became 9, and the run reaches the same asset abort 36,000 blocks earlier.** So this was real and its effect is larger than any of the console-contract fixes made today ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â and still not enough: the end state is unchanged, nine threads asleep with the two file-layer threads waiting on one condition.
- Worth stating plainly: this bug was in *our* emulation, not in the game. It was found by watching a bitmap the guest was scanning, not by reading more of the guest.
- Tests: 205 runtime, 24 harness. The harness suite is not part of the standard test run because linking it takes far longer than everything else; the command is recorded where the build is pinned.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the boot ends as a deadlock, not a fault

- The harness now prints every thread's state at the end of a run, and the picture is much clearer than "the engine aborts": at block 4,645,689 **nine threads are asleep and nothing can wake them**.
- Two wait on event queues **with no deadline** (the schedulers), seven wait on condition variables ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â including both fios media threads, which wait on the *same* condition object. The main thread is the only one running, and it reaches the asset abort without ever reading the disc.
- Neither of the two threads that finish exits early: they finish in the last 100,000 blocks. So the poll that gives up at block 155,821 is not ended by a worker dying ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the media threads are alive and waiting.
- The condition the media threads wait on sits 0x20 bytes above the request object the poll was writing. Nothing in the whole trace signals that object after the poll ends; the signals that do happen are for its neighbour.
- So the whole boot hinges on one missing completion: the media threads sleep, the schedulers wait for the events those media threads would have posted, and the main thread proceeds without asset I/O until it fails.
- Tests: 205. The port is not yet playable.

## 2026-10-28 - the cache poll has an end, and nothing reads the disc after it

- Put the 61 cache opens on the block timeline for the first time. They run from block **113,605** to **155,821** - roughly every 700 blocks - and then stop.
- That kills the working assumption. The completion write happens at block **115,663** and the state word clears at 116,196, *inside* that window, so the poll outlives the completion it was supposed to be waiting for. It is a bounded wait that gives up after about 42,000 blocks (ÃƒÂ¢Ã¢â‚¬Â°Ã‹â€ 42 ms of the port's virtual clock), not a spin.
- The more useful part is what comes after: from block 155,821 to the abort at 4.6 million, the file trace records **no file call at all**. The engine never opens `data_ps3.psarc` or any other asset file. So the asset failure is not caused by a file that could not be read - nothing is read.
- The console, for comparison, does three things in order: writes the cache index (12.94 s), opens the 6.5 GB `data_ps3.psarc` immediately (12.95 s), and half a second later creates an **SPU thread group of five**. This port creates no SPU thread group at all - `sys_spu_initialize` runs once and nothing follows - which is the next concrete divergence once the engine gets that far, since the game's asset path decompresses on SPUs.
- Two questions now, in order: why the engine gives up on a cache it successfully opened, and what it needs before it will read the disc at all.
- Tests: 205. The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - another port's notes, two real contracts, and a boot that ignores both

- Read **Project Pyrrhus** - undecuple's own Killzone 2 port, same engine family, MIT - and took its documented console behaviour rather than its code. Its notes describe the exact failure shape here: the file layer signals **two media threads**, and a counting wake-up lets one wake twice while the other sleeps on with its request.
- That exposed two genuine defects in this port. The lightweight mutex calls answered success and **never touched the guest word** - and the word *is* the lock, so a thread could never see itself as the owner. And the system mutex, which is what the file layer actually uses, was documented as "no ownership tracking is needed yet": six lock/unlock pairs and three mutexes, all no-ops.
- Both are now real: owner and recursive depth tracked, waiters queued, the mutex **handed** to the first waiter at unlock, `EBUSY` for a trylock on a held mutex, `EPERM` for a foreign unlock, and a condition wait that **releases** its bound mutex before blocking and takes it back on wake. Thread ids also start at 1 now - they started at 0, which the guest reads as "no owner", and came from the same counter as queue ids.
- **The boot did not move: 4,645,689 blocks, 61 opens, no writes, same trap, twice.** The first null result explained itself: the boot's syscall list contains no lightweight-mutex call at all - the file layer uses the *system* mutex. The second says the six lock/unlock pairs were already uncontended, so mutual exclusion is not the stall.
- What is left is narrower than before: the engine polls - open, fstat, retry about every 80 blocks - while an operation it submitted never reports completion. Every contract around that poll has now been corrected and measured. The missing piece is inside the engine's own request path.
- Method note: the old unit test that asserted a foreign unlock *succeeds* was itself encoding the bug, and was corrected rather than deleted.
- Tests: 205. Credits for Project Pyrrhus added to the notices, with what was taken.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the cache loop ignores the cache, and the instrument was lying

- Planted the console's own cold-boot cache ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the 1,043,456-byte index and its data file, byte-identical to what the console rebuilds ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â into the port's cache directory. Result: **nothing changed**. Same 61 create-only opens, no reads at all, no writes, identical block count, files untouched afterwards. The retry loop is not checking the cache; it never looks at it.
- Decompiling the worker explains the shape: it is a **reopen service**. It walks a table of managed files and reopens any entry the engine has left closed, using flags recorded when the entry was registered. The 61 opens are 61 reopens of an entry that never stays open.
- That moves the question to something much more specific: the handle is written into a **stack descriptor**, the table entry's handle is written once and never again, and the guest never calls close at all. So on this side the entry stays "closed" forever and the service loops; on the console the same loop exits on its first pass.
- Two of our own instruments turned out to be weaker than assumed, and both are now fixed rather than trusted: the store watch silently stops after 64 records, and the file trace printed the open flags from a register **after** the call, which the guest may clobber. The build in flight captures arguments before the call and prints the descriptor pointer and the stored handle.
- Method note, again: the analysis-database experiment ran on a copy; the live database keeps its function bodies.
- Tests: 202. The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the cache worker, read at last, and two answers eliminated

- The function behind the file-cache retry had never been decompiled ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the analysis tool had only fragments of it, so every reading of its behaviour was inference. It is now a proper function in the analysis database: 9,608 bytes, identified by its own error strings ("Error re-opening file", "Error calling fstat in reopen of"). It opens the cache with a descriptor's flags field.
- That killed both easy explanations in one pass. The code that decodes the request's mode byte and would produce **read-write|create** exists, is correct, and **never executes** on this path. And the descriptor the call receives does not hold the flags either ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â it reads 0 or 3 where the register carries `0x40`.
- So the value that keeps the cache read-only is assigned somewhere not yet instrumented. That is a smaller question than "why does the cache not initialise", and it is now the only question on this path.
- Also established: the static table of file descriptors gets its path written three times during the boot, but its flags field is **never written at all**.
- Method note: the destructive part (removing an overlapping function, creating the worker) ran on a **copy** of the analysis database. The live one keeps its function bodies, and the single body widened mid-pass was narrowed back to its analysed range.
- Tests: 202. Source and the shared repository updated; the issue stays open until the assignment is found.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - a contributor's first day: three issues, two defects, one experiment

- **undecuple** got access and opened three issues the same day. All three were checked against primary evidence rather than taken on trust, and all three are now closed with the evidence linked.
- **Error codes (their first finding).** Three constants did not match the firmware's table: a timed-out wait reached the game as a *deadlock*, out-of-memory as an *abort*, and a bad file handle as *not permitted*. An audit of every kernel error literal in the runtime found a fourth they had not mentioned ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â a port-binding call answering "not connected" where the meaning is "already connected". A test now pins the whole table. Boot measurement: exactly unchanged, which is what an error-path fix should do.
- **Deletion and file times (their third).** Their Killzone 3 experience was that deletes were no-ops on Windows and the game looped reopening a cache it could not remove. Here deletes really happen ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â but the test found something just as bad: after delete and recreate, the **change time did not move**, because Windows keeps the original creation time for a same-named file recreated within seconds. A file layer that validates its cache against that time would accept the file it just rejected. It now reports the later of creation and modification, so a rebuilt cache always looks newer.
- **The same report exposed a habit.** Every host failure on the file calls came back as "not found" ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no permission, is-a-directory, directory-not-empty, all reported as the same thing. They now say what happened, and a device path the port does not serve is refused instead of quietly resolving inside the game folder.
- **Cold against warm (their second).** They pointed out that a cold and a warm boot are different experiments, and ours was warm. Reproduced: with no cache at all, the console creates both files read-write and writes **1,043,456 bytes** to the index in about six milliseconds, then goes to the disc. The file it builds is bit-identical to the cached one.
- That narrows the real question to one bit of intent: the game under this runtime asks for **create-only**, where the console's game asks **read-write**, cold and warm alike. That is now issue #4 rather than a guess, with the static work on the flags builder as the next step.
- Tooling: a cold-boot harness that restores the warm cache afterwards, a collaboration status command, an issue triage view, and an export that refuses to publish over a contributor's push. Every issue closed here says what was fixed and links the commit.
- Tests: 202. Builds: one full (32m23s) and one harness relink.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the console's memory figures, and a probe that had gone quiet

- The port was telling the engine it had a **192 MiB** user-memory region, all of it free.
  The console answers the same query with **223,346,688 bytes total and 203,554,816 available**
  at the game's first ask - so the region is now the console's size, and the same 18.875 MiB is
  declared held back. It has to be declared: the port has no firmware allocations to account
  for, and inventing a smaller total would be worse than saying what the machine says.
- The guest **does** consume the figures. Every allocation in the memory dump moved by exactly
  the reserved amount, the boot runs **1,052 blocks longer** (4,644,637 to 4,645,689) and the
  fatal path returns through a different frame. The outcome is unchanged: same trap, same 61
  create-only opens of the cache index, no write, cache still empty.
- All 132 request-state transitions are identical, **including their block numbers**, and the
  syscall summary line is byte-for-byte the same. So the file-layer stall is not driven by
  memory pressure either.
- A trap worth recording: those transitions briefly dropped to **one line**. The watched
  request object lives in memory the guest allocated, so growing the region moved it - and the
  probe kept sampling the old address, quietly reporting nothing. The harness now follows the
  pointer the wait is actually handed, and says so in the log when it moves. A probe that goes
  silent now announces it instead of looking like a result.
- With the corrected probe, the byte the engine turns into open flags reads **0** at the moment
  the cache index is opened - which is exactly why the port asks to create rather than to
  read-write. Whether the console's own byte is 0 there cannot be seen from its syscall trace.
- Tests: 199. Builds: one full (32m55s), plus a six-second harness relink.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the three borrowed contracts are right, and change nothing

- Built the batch that carried every fix borrowed from Project Helghast at once, then ran it
  once so the result could be attributed: the condition-variable block layout, the hand-off of
  the paired mutex to a woken waiter, the 512-byte stat block size and three distinct file
  times.
- **Result: identical.** Same failure, same block count to the digit, same sequence of file
  calls, no write to the disk cache. The fixes are kept - they are console behaviour and they
  have tests - but they are not credited with progress, and the page now says so instead of
  leaving a "pending" box.
- The sync trace also shows the new hand-off path really runs: the same producers write the
  "in progress" and "done" words in the same order at the same block counts as before. Nothing
  in the scheduling moved.
- The one real difference left on this path, measured mechanically against the oracle: the
  console opens the cache index **read-write** and reads it before writing, while the game in
  the port opens it **create-only**, never writes, and re-opens a fresh descriptor on every
  retry. Whether that is the cause or a consequence of the stuck state is not known yet; the
  oracle run that produced the trace started with a cache left by an earlier boot, so a fresh
  console boot has not been compared.
- Tests: 198 passing. Build: one, 33m43s at 15 jobs.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - the toolchain written down, and a second pair of hands

- Wrote down **everything** the work rests on, in one place: the reverse-engineering
  toolchain (Ghidra and its headless scripts, the REA analysis server, the JDK, the
  disassembly library, Python), the oracle setup (RPCS3, plus the small automation that drives
  its memory-dump dialog so captures run with nobody at the keyboard), the architecture
  references consulted for the processor and the console, the two open projects whose findings
  shaped fixes here, and the build toolchain. It is one document, not a scattered list.
- The source repository was rebuilt as a **clean, shareable tree**: only the Rust workspace,
  the tools, the licence, the credits, the contributing guide and a README written for that
  repository. Fifty function-name tables, ninety-one analysis scripts and the private
  workspace's own documentation are gone from it, along with every path that only means
  something on this machine.
- **undecuple** - author of Project Helghast, the Killzone 3 port on the same engine family -
  now has write access to the source repository, and is credited as a contributor with a link
  to their page wherever credits appear.
- The build carrying the condition-variable, block-size and stat-time fixes is still
  compiling; the boot measurement that decides whether they help is still pending.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-28 - inputs audited instead of internals, and a cross-check with the Killzone 3 port

- Six rebuilds of engine-internal probing had not moved the boot, so the work changed shape:
  instead of asking what one more internal field does, the port's *inputs* were compared
  against the console's. A single audit found more than the probing had.
- Four start-up system parameters were being refused with an error where the console answers
  them: date format, time format, parental level and the "has an NP account" flag. All eight
  the game asks for are answered now, with the console's defaults.
- The console reports 213 MiB of user memory; the port reported 192 MiB, a 10% shortfall the
  engine sizes its heap-backed structures from. Queued for its own change so the effect can be
  attributed.
- With evidence rather than reasoning, three suspects were closed: descriptor numbering was a
  real deviation but not the cause, both mutex-ownership variants were measured (one regressed,
  one was a null result), and free space is not involved because the game never queries it.
- Cross-checked with **Project Helghast**, the Killzone 3 port on the same engine family. Its
  notes supplied three concrete contracts the port had wrong: the condition-variable block
  carries the paired mutex address at its first word (the engine reads it and stalls when it is
  not a usable mutex), the stat block size is 512 bytes rather than 4096, and stat reports three
  distinct file times which the engine's file cache validates against. All three are
  implemented with tests; the boot measurement is pending.
- Test suite: 198 passing.
- The port is not yet playable; it still stops in the engine's asset lookup.

## 2026-10-27 - threads keep their own state, and the caches begin to open

- A short memory-clear loop in the file-system worker never terminated. It was not a
  translation problem: switching threads saved only the general-purpose registers, so the
  condition flags, count register and floating-point/vector register files of one thread
  were visible to the next, and the loop kept testing another thread's flags. Each thread
  now owns its full register state, which removed the last of the long stalls and let the
  boot leave the file-system initialisation it had been stuck in.
- The file layer then reached its first real open, and was refused. The port honoured only
  one of the console's file-open modes, so "create this file" arrived as "open this
  existing file". The complete flag set is now decoded, including create, truncate and
  append, with the console's own error codes returned instead of a single blanket answer.
- The result: the file system's cache index is created at the expected location and opened
  successfully. It is still empty, so the file layer retries while the game moves on - the
  next stop is elsewhere, in the save/asset path.
- Build work: a full rebuild is now **34m57s** against 36m33s before. Measurement showed
  the shard crates were already built with the optimiser off, so the remaining cost was
  codegen bookkeeping and a jobserver stall between parallel crates, not optimisation. The
  exact toolchain invocation is now pinned in a script so a build cannot silently run with
  a different configuration.
- Runtime tests: 195 passing.
- The port is not yet playable, but it now gets through file-system initialisation, font
  initialisation, and several completed frames.

## 2026-10-27 - fonts: initialise honestly, and refuse what we cannot draw

- With threads, graphics and frames working, the boot reached font initialisation. The port
  now answers the font library's setup properly: the caller's configuration is validated
  the way the library validates it, and the library object handed back is real memory with
  the documented fields, because the game stores that pointer and passes it to every later
  font call.
- The next call asks for an actual font. On hardware that comes from the console's own
  system fonts; this port has neither those files nor a font rasteriser. It therefore
  refuses with the library's own "no support function" code and prints the requested font
  type once, instead of handing back a font object that could never produce a glyph.
- The refusal is tolerated by the game - it warns and continues - which took the boot
  another **40,940** blocks and a fifth completed frame.
- The next stop is save-data initialisation, which is the first subsystem where the port's
  storage mapping (`/dev_hdd0` to the save directory) becomes user-visible.
- Tests: harness 17.
- The port is not yet playable.

## 2026-10-27 - the missing TLS image, and the first frames

- A stubborn assertion about a full "allocation map" turned out to have nothing to do with
  memory pressure. The game asks a thread-local configuration question, and the port had
  been giving every thread a blank copy of that state, so the answer was always the same
  and always wrong.
- The real state exists in the executable: a small initialised block that a loader is
  supposed to copy into each thread's local storage before the first instruction runs. The
  port now does exactly that.
- The same investigation found a second, quieter bug next to it: one of the graphics
  structures had been placed inside that thread-local page, so reading a thread-local flag
  could observe a graphics counter instead. The structures moved; the flag is now a flag.
- With the real values in place the assertion disappears, and the game does something it
  has never done in this port: it submits **frames**. Six submissions, four completed
  flips, 4.45 million executed blocks.
- The boot now stops on font initialisation, which is where menus begin. That is the next
  subsystem, not another mystery.
- Tests: graphics layer 9, harness 13.
- The port is not yet playable, but it is now rendering its own frames.

## 2026-10-26 - the guest stopped waiting

- The boot had reached the game's main loop and sat in it: four thousand sleeps, twenty
  million blocks, no progress. Not a missing translation - the game was waiting for
  evidence that the GPU had consumed its commands, and the port was never producing it.
- The evidence is a counter. The command ring's control block has a reference value the
  guest polls; the port initialised it and then left it frozen forever. Consuming a
  submission now advances it, exactly as the hardware does, along with the read pointer.
- The effect was immediate: the loop exits on the first iteration and the game proceeds
  into code the port had never executed.
- It then stops on its **own assertion** - a deliberate marker write into a null address,
  the failure path of its internal assert handler. That is a good sign: the guest is
  running real code and telling us it detected a bad state.
- So the next question is narrow and answerable: which assertion fired. The handler has
  hundreds of callers, but the return address at the trap identifies the site.
- Tests: graphics layer 9 (control-register progress), recompiler 60, harness 13.
- The port is not yet playable.

## 2026-10-26 - the boot stops stopping

- With the runtime fallback in place, the interpreter grew by iteration rather than by
  rebuild: floating point, condition-register logic, vector compares and conversions,
  and one missing vector decode case that the retail binary exposed.
- The result is a different kind of state. The boot no longer stops on a missing
  translation anywhere on its path; it now reaches the game's own polling loop and runs
  until the safety cap - **20,000,000 blocks**, over four times what it managed before.
- The loop calls a sleep 4,032 times and polls an event queue 14 times. That is the shape
  of code waiting for something the port does not yet deliver, not code that is missing.
- So the next question is behavioural, and a much better one: what is the game waiting
  for? Candidates are a display flip completion, a vblank, or a message on an event
  queue. All three are things the port has records for but no producer of yet.
- 38 blocks were interpreted on the way, which is the fallback doing its job: those are
  addresses the static translation had never seen.
- Tests: recompiler 60 (including a decode case taken from the retail binary), harness
  13, graphics 8.
- The port is not yet playable.

## 2026-10-26 - the treadmill is gone: run the code you have not compiled

- The port had a bad feedback loop. Each address the boot reached through an indirect
  call or a computed jump had no compiled code, and adding it meant regenerating and
  rebuilding for roughly half an hour. Progress was real but the cost per step was
  absurd.
- The fix is the obvious one, and it should have come earlier: when there is no compiled
  code for an address, interpret that block and carry on. The interpreter shares the
  recompiler's decoder, delegates system calls to the runtime that already owns them, and
  records every address it runs so hot code can still be compiled later.
- Anything it does not understand stops the run and says which instruction and where.
  That matters more than coverage: a guess would corrupt the game's state quietly, and a
  quiet corruption is far more expensive than a stop.
- Effect: the boot immediately ran **10,002** more blocks and the next stop is a
  *decoder* gap rather than a missing block. Iterating on those now takes seconds, not
  half an hour.
- This is the first structural change in a while that changes the *rate* of progress
  rather than the position.
- Current state: **4,435,979** executed blocks, two command submissions, and a fallback
  that covers the common integer, memory, branch and floating-point surface plus a first
  slice of vector code.
- Tests: harness 13, recompiler 59, graphics 8.
- The port is not yet playable.

## 2026-10-26 - address translation was the missing piece

- The port had been handing the game two address-translation tables and leaving them
  completely blank. Blank, in this API, does not mean "nothing mapped yet" - it means
  *every* address fails to translate. The game translates addresses itself, read the
  failure, and its allocator returned null; the caller then wrote through the null.
- The fix was not a guess: the initialisation call describes an input/output memory
  window, the system is supposed to map it as part of initialisation, and the game's own
  translation code shows exactly how it reads the tables. Publishing those entries was
  enough.
- Effect: the boot ran **4,240 more blocks** and the null-pointer fault disappeared.
- A second, smaller correctness point came out of it: the game writes slightly past the
  end of its own command ring (a jump command at the boundary). Those bytes are now
  counted and shown in the report instead of being dropped, and the boundary submission
  reports that its last packet is truncated rather than pretending the stream ended
  cleanly.
- Current state: **4,061,815** executed blocks, **two** command submissions totalling
  16,384 words with nine distinct methods, and the next stop is again a translation gap -
  which the toolkit now handles in batches rather than one address at a time.
- Tests: graphics layer 8 passing.
- The port is not yet playable.

## 2026-10-26 - a conditional return, and the first behaviour fault

- A stubborn class of "no translated code here" stops traced back to one wrong
  assumption in the translator: a *conditional* return was treated as the end of a
  function's reachable code. It only returns when its condition holds; when it does not,
  execution simply continues, and that continuation had never been translated.
- Fixing it was not a local patch: it added **2,471** previously invisible blocks
  across the whole program, and the boot immediately ran further than before.
- With the holes closed, the failure changed character. The port is no longer stopping
  because code is missing; it is stopping because the game called one of its own
  routines with a null buffer and then wrote through it.
- That is the useful kind of failure. The chain is fully laid out in the registers and
  the code: the buffer came from the game's own allocator, which returned null for a
  128-byte request. So the question is now "why is the game's heap unusable", not "what
  instruction is missing".
- Two candidate answers, in order: the heap was sized from a memory-size answer the
  port gives incorrectly, or an earlier allocation failed and the game did not check it.
  Both can be settled by reading the values the port actually returned, so neither has
  to be guessed.
- Boot: **4,057,575** executed blocks; the first command submission is unchanged at
  15,376 words with nine methods, which is the correct behaviour for a port that has
  not yet drawn anything.
- Tests: recompiler 59 (a conditional return now falls through to a real block, an
  unconditional one does not).
- The port is not yet playable.

## 2026-10-26 - the graphics context, and the first real submission

- The boot had been stopping on a null callback deep inside the game's own code. The
  cause was not the game and not the renderer: the graphics initialisation call takes a
  *variable* that receives a pointer to a structure the system owns, and the port had
  been writing the structure directly into that variable. The game then read the first
  word of a structure that was not there.
- Two independent clues settled it. The game's own command-writing code loads that
  variable and dereferences it before use, which only makes sense if the system stores
  a pointer there. The reference implementation says the same thing twice - in how it
  logs the argument and in what it writes at the end.
- The structure is now real and owned by the port, and the command buffer is the game's
  own memory rather than one the port invents. The first four kilobytes stay reserved,
  a fragment is 32 KiB with one word held back, and the fill callback is expressed the
  way PPU code expects to call it: as a descriptor with a code and a table-of-contents
  word, not a bare address.
- With that fixed, the boot walks through display configuration - it probes the modes
  it cares about and configures one - and produces its **first real command
  submission: 16,384 words.** The decode shows a single large no-operation packet,
  which is exactly what a command ring looks like before the first draw is built.
- That is the milestone that changes the shape of the work: submissions are now
  measured rather than predicted, and the next steps are decode coverage and the
  renderer, not speculation.
- Also new: a tool that seeds a whole function's control flow at once - branch targets
  and switch-table cases - instead of chasing one address per rebuild. For the display
  function that is 25 entry points in one pass, replacing about ten cycles.
- Tests: graphics crate 5 passing, rewritten for the corrected ownership contract.
- The port is not yet playable.

## 2026-10-26 - reaching the graphics system, and answering it honestly

- The boot now passes the graphics system's initialisation call and continues into the
  display configuration path. That is the boundary where the work stops being about
  reachability and starts being about pixels.
- One finding changed the design: the game never calls a draw function. It writes its
  own command stream into a buffer and submits it by updating a register the graphics
  system consumes. The port therefore provides a real buffer and a real register, and
  records every submission, decoding it into a list of operations. That recorded list -
  not recollection, and not documentation - will drive the renderer.
- It also caught a bug by reading rather than by crashing: the command buffer was
  originally sized so that its last page fell outside the mapped region. Nothing would
  have failed until a frame had nearly filled the buffer, at which point it would have
  looked like a mystery fault in unrelated code. It is now sized to fit, with the end
  of the buffer inside the mapped region.
- The display answer turned out to matter more than expected. The game asks for the
  output state and then branches on the aspect and the scan mode it is told. Answering
  zeroes would have sent it down a path no console takes, so the port answers with what
  it will actually present: 1080p, widescreen, progressive.
- Audio output advertises **stereo only**, deliberately. Surround support does not exist
  in the port yet, and advertising it would have produced a configuration that silently
  produces nothing much later. The game now selects stereo, which is what the port can
  play.
- Everything unimplemented is refused with the system's own error code rather than
  accepted and ignored - stereoscopic display modes, secondary outputs, and non-PCM
  audio formats among them. A refusal is visible; a silent success is not.
- Iteration cost dropped from about half an hour to a few seconds for this workstream,
  because the new state lives outside the generated game code. That matters more than it
  sounds: it is the difference between trying an idea and not bothering.
- Coverage: **4,053,634** guest blocks executed. The next stop is a translation gap
  rather than a missing system call, which is a different kind of problem and a
  reasonable place to be.
- Harness tests: 13 passing (display state layout, device errors, resolution table,
  configuration validation, audio device information, error paths, and slot resolution
  by name rather than by number).
- The port is not yet playable.

## 2026-10-26 - one wrong choice, and twice the code

- The port had been sitting in a loop for millions of executed blocks. The culprit was
  a decision I had made earlier and defended: making a condition-variable wait return
  immediately, on the grounds that a spurious wake-up is permitted.
- It is permitted. It was also wrong here. The game's pattern is "wait while the
  condition is false"; returning immediately turns that into a spin, and because the
  port runs threads cooperatively, the thread that would satisfy the condition never
  got to run. The loop consumed three million blocks before hitting the safety cap.
- The fix makes waits real: a waiter is recorded and blocked, a signal releases one,
  a signal-all releases all, destroying the condition releases anyone still waiting,
  and if nothing can ever signal, the port reports a deadlock rather than spinning.
- The effect was immediate and much larger than expected: executed coverage doubled, from
  about a hundred and ten thousand blocks to **223,049**. The spin had been hiding how
  much of the game the port can already reach.
- A test covers both halves of the contract - the wait must block, and the signal must
  wake exactly that waiter - driven through the same import trampolines a real call uses.
- Runtime tests: 182 passing
- The port is not yet playable.
## 2026-10-26 - two harness rules, learned the hard way

- Coverage had collapsed from around a hundred and fourteen thousand executed blocks to
  twenty-one. The cause was not the game and not the port: the walker had been pruning
  its list of entry points after a run that was aborted mid-way, and the aborted run had
  never reached most of them, so they looked unused.
- The rule is now explicit: prune only when a run actually walks its path. A spin or a
  fault tells us nothing about which entry points are needed, so nothing is removed.
- The second rule is about not fooling ourselves: after three cycles with no improvement,
  the walker stops and reports the best figure instead of looping. A stall is a signal
  that the frontier needs a subsystem, not more entry points, and it should be visible
  rather than buried in logs.
- Coverage has recovered from twenty-one to **95,530** executed blocks and is still
  climbing, so these rules cost a little wall-clock time and save a lot of confusion.
- Runtime tests: 177 passing
- The port is not yet playable.
## 2026-10-26 - measuring before optimising, and a spin that cost an hour

- The complaint was that the harness only used one core. That was worth checking rather
  than assuming, so each stage was timed separately: the recompiler decodes three
  thousand functions in well under a second, the emulated program itself runs for tens
  of milliseconds, and the build that follows takes about fifty seconds.
- So the single-core complaint was pointing at the right place but the wrong culprit.
  The stage that eats the time is the Rust compiler turning generated straight-line
  code into a binary - and that stage does not care how fast the emulated code runs.
- Three changes followed. Generated shards are built without optimisation, because
  optimising code that executes for thirty milliseconds is pure compile-time cost.
  They are also split into sixteen crates instead of eight, since the compiler
  parallelises across crates rather than inside one. And a shard file is only rewritten
  when its contents actually changed, which means most cycles rebuild one or two crates
  instead of all of them.
- The result is a thirty-second cycle instead of fifty, on eight cores rather than
  sixteen - a deliberate cap, since the point is to leave the machine usable while it
  works.
- One more thing surfaced, and it was worse than the slowness: a single cycle sat in a
  loop inside the emulated program for **fifty-seven minutes** of CPU time. There is now
  a hard instruction cap, so a spin costs seconds and is reported as a spin - which is
  itself useful, because it means the game is waiting for something the port never
  delivers.
- Boot position: coverage was rebuilt after that abort pruned some seed points and is
  climbing again (65,922 blocks at the time of writing, from 21 after the abort).
- Runtime tests: 177 passing
- The port is not yet playable.
## 2026-10-26 - not copying a stub

- The next piece was the queue that task submissions travel through. The obvious move -
  copy the reference implementation - was not available, because the reference
  implementation is a placeholder that reports success and does nothing.
- That distinction matters. Copying it would have produced an import that "works"
  while silently discarding the game's work: no crash, no error, just a game that
  quietly stops making progress somewhere later. The port has already been burned once
  by a wrong unit turning into a null-pointer crash three layers away; a silent
  no-op is worse, because nothing points at it.
- So the contract came from the game instead: the call sites show 32-byte elements, a
  caller-chosen depth, a direction, and a 32-byte body pushed with a flags word. The
  queue is implemented as a bounded FIFO in the guest's own buffer, refusing
  submissions that would not fit rather than dropping them, and refusing a
  configuration whose buffer is not real memory - because a push that "succeeds" into
  nowhere is the same lie in a different place.
- Boot position: **111,605** executed blocks, up from 110,336.
- Runtime tests: 177 passing
- The port is not yet playable.
## 2026-10-26 - flags that actually wait

- Synchronisation inside the job system now works the way it does on the console: the
  event bits live in the shared structure, so code that polls them sees real values,
  and a wait blocks until the bits appear instead of returning a comfortable lie.
- That last part matters for diagnosis. If a wait's condition can never be satisfied -
  because the task that would satisfy it does not run yet - the port reports a
  deadlock and stops. The alternative, pretending the wait succeeded, would let the
  game run on with wrong assumptions and fail much later somewhere unrelated.
- Both wait variants are handled: any-of and all-of, matching the two modes the API
  defines.
- The boot is at **110,336** executed blocks. The next call is the lock-free queue that
  tasks are submitted through - the queue between the game and the SPU work, and the
  last structural piece before task execution can mean something.
- Runtime tests: 177 passing
- The port is not yet playable.
## 2026-10-26 - deciding where a PC game keeps its data

- The game asked for a writable cache. That forced a decision that is as much product
  as engineering: on a console the platform owns save data and cache; on a PC the port
  has to choose, and that choice is hard to change once players have saves.
- The decision, now implemented: three locations with different lifetimes. The disc is
  read-only game data and stays wherever the game is installed. Saves and settings live
  in the user's application data, so updating or moving the install cannot take them
  away. The cache is a separate, disposable directory, so "clear the cache" is safe by
  construction rather than by asking every subsystem to be careful.
- The default is the standard per-user application data folder, overridable with an
  environment variable, and the port prints both paths at startup so there is nothing
  hidden about where a player's data went.
- The effect was immediate: the boot went from 104,007 to **110,251** executed blocks,
  because the calls behind the cache mount stopped failing.
- Runtime tests: 177 passing (three new ones cover device mapping, save-directory
  creation and file metadata)
- The port is not yet playable.
## 2026-10-26 - the game starts looking at the disk

- Two more pieces of the platform are real now, and one of them is the first that
  reaches outside the process.
- Condition variables: creating one works, and waiting on one returns immediately. That
  is not a shortcut dressed up as an implementation - a condition variable is allowed
  to wake spuriously, so the caller re-checks its condition and waits again. The
  alternative, blocking forever with nothing able to signal, would hang the port.
- File metadata: asking for a file's details now goes to the host filesystem and comes
  back with real sizes and modification times, in the structure the platform expects.
  That matters because the game uses file checks to decide what data exists.
- Boot position: **104,007 executed blocks**, up from 102,567.
- The next call asks for a writable cache area rather than a read of the disc. That is
  a different kind of requirement: the port has to decide where a PC game's cache and
  save data live on the host, which is a product decision as much as a technical one.
- Runtime tests: 175 passing
- The port is not yet playable.
## 2026-10-26 - past a hundred thousand, inside the job system's setup

- The boot has now executed more than **100,000 blocks** of the game's own code: from
  the platform's C runtime, through threads and memory, the job system, the game's
  own metadata, its frame loop, and now its workload configuration.
- This stretch was more of the same useful work: the job system's workload
  description is a documented structure, so the port builds it exactly - including
  the checks the firmware makes, such as alignment, a non-zero minimum contention and
  priorities that cannot exceed a nibble.
- The port also now accepts workload add/shutdown/wait/remove, idle-SPU requests and
  exception handlers. Two of those are honest placeholders in a specific sense: a
  workload has nothing to wait for yet because no job chain executes, and a handler
  is stored but cannot fire until a task reports an error. Both are written down as
  such rather than presented as working.
- Nothing here is guessing at the API. Each call was implemented from its structure
  or its reference behaviour, and the frontier moves one call at a time.
- Boot position: **100,384 executed blocks**
- Runtime tests: 175 passing
- The port is not yet playable.
## 2026-10-26 - the game reaches its frame loop, and what multithreading means here

- Two things were asked for and both are now answered with evidence.
- First, multithreading. The dispatch table the harness builds at startup is now
  merged in parallel across workers, and the port reports startup and run time
  separately. Measured: four milliseconds of startup against twenty-four to seven
  hundred milliseconds of guest run. The guest loop itself stays single-threaded, and
  that is deliberate: switch points, the simulated clock and data transfers must not
  depend on host timing, or nothing measured in this project stays reproducible.
- Second, the crash from the previous entry is gone, and the reason was worth the
  hunt. Creating an event queue takes a number of entries, not a number of bytes. The
  port required a multiple of thirty-two, so every queue creation failed, callers
  never stored an id, and a dispatcher thread later waited on queue zero and called
  through a null handler. One wrong unit, three layers of confusing symptoms.
- With that fixed the game no longer crashes. It reached its main loop: three million
  blocks showed two thousand iterations of polling input, trying an event queue and
  sleeping between frames. Sleeping returned immediately in the port, so the loop was
  spinning; sleeping now advances the simulated clock and actually waits.
- The boot now sits at 95,781 executed blocks, working through the job system's
  workload attributes - the last stretch before the graphics calls.
- Also fixed: an instrumentation list that grew without bound and took a spinning run
  to two gigabytes, and a run cap so an unattended run stops instead of hanging.
- Runtime tests: 175 passing
- The port is not yet playable.
## 2026-10-26 - narrowing a crash instead of guessing at it

- The boot stops on a null pointer after a thread waits on an event queue. This entry
  is about turning that symptom into a fact.
- Instead of reading code and forming a theory, the harness now reports the machine
  state at the moment of the fault - every register that is not zero, the condition
  registers, and the call chain - and can dump a chosen object or narrow a store
  watch to a chosen region of memory.
- What that produced: the pointer being dereferenced lives in a structure that is
  only half filled in. The event queue id at its start is zero, and the handler slot
  further in is zero, while other fields around them hold real values. A watch over
  the structure shows every write that ever reached it, and none of them ever touched
  the queue id. The caller also ignores the result of the wait, so it walks straight
  into a null handler.
- One theory was tested and eliminated rather than believed: that a worker thread ran
  before its creator finished setting the structure up. Thread priorities were not
  honoured, so that was plausible. They are now honoured - lower numbers run first,
  ties take turns - and the fault is unchanged. So it is not a race; something that
  should have written that field never ran.
- That is a much better position than "it crashes": the next question is precise and
  local - which routine owns that field, and did one of the calls the port
  implements fail to hand back the value it should have.
- Boot position: 95,749 executed blocks, unchanged this entry
- Runtime tests: 175 passing
- The port is not yet playable.
## 2026-10-26 - the job system starts accepting work, and a new kind of wall

- SPURS can now be told about the game's event queues, and it can accept tasks: the
  task binary is read out of the game's own memory, checked, loaded into an SPU
  workspace and started on the port's scheduler.
- Loading is deliberately strict. A task whose image cannot be read, or that is not
  an SPU program at all, is reported as a failure. The tempting alternative - saying
  "created" and letting the guest wait forever - is the worst outcome, because from
  the outside it looks like a hang with no explanation.
- The boot moved again: from 95,518 to **95,749** executed blocks. That is the
  furthest it has been.
- And it then stopped on something new. Not a missing instruction, not an
  unimplemented call: a null pointer dereference, immediately after a thread waited
  on an event queue. That is a different class of problem - the kind a real program
  has - and it points at either what we deliver in an event or at code that does not
  check a wait result. Both are findable, and the next step is to read the faulting
  routine rather than guess.
- Runtime tests: 175 passing
- The port is not yet playable.
## 2026-10-26 - the job system's own state, implemented natively

- The port now creates the game's SPURS instances and tasksets - the containers its
  SPU work lives in - rather than stopping at the call that would create them.
- The approach is worth stating: the job system's scheduler is implemented in the
  port's own code, and the *tasks* it will dispatch are the game's own SPU programs
  running on the SPU threads built earlier. That keeps the port native: no firmware
  kernel is interpreted, no emulated hardware sits in the path.
- The rules that matter are enforced rather than assumed: a second instance at the
  same address is rejected, a taskset must belong to a live instance, its size must
  fit an SPU's workspace and align to the descriptor size, and tearing an instance
  down takes its tasksets with it.
- One honest limitation is written down in the notes: joining a taskset currently
  succeeds immediately, because no task has ever been submitted. That is true for an
  empty taskset, and it will have to block once tasks exist.
- Boot position: **95,518 executed blocks**, up from 95,507. The next stop is
  attaching an event queue to SPURS - which the port can do for real, since it
  already has working event queues.
- Runtime tests: 175 passing
- The port is not yet playable.
## 2026-10-26 - SPU programs become schedulable threads

- The pieces so far ran SPU programs one at a time, as a test harness. Now they are
  threads: a group with a priority and a lifecycle, members with their own 256 KiB
  workspace, and turns taken in a fixed rotation so one SPU cannot starve another.
- Loading a program is checked, not assumed: the image arrives as segments, and if a
  segment that should contain code cannot be fetched, the thread refuses to start
  rather than beginning with zeros where its instructions should be. That class of
  bug - a program that runs but computes nonsense - is the expensive one.
- A group cannot gain threads after it starts, group size is bounded to the six
  usable SPUs, and destroying a group takes its threads with it. These are the
  firmware's own rules, and following them means the game's expectations are met
  instead of argued with.
- The boot itself has not moved: it still stops at the call that would create the job
  system. That is the next piece - the scheduler that sits on top of these threads -
  and it is a real subsystem rather than wiring.
- Boot position: 95,507 executed blocks
- Runtime tests: 171 passing
- The port is not yet playable.
## 2026-10-26 - up to the SPURS gate

- The boot now gets through the job system's setup and stops at the call that would
  actually create it. That is progress, and it is also the honest boundary.
- What was done: the attribute block SPURS is configured with is a documented
  structure, so the port writes it exactly - the version, the number of SPUs, the
  priorities, the exit flag - and the setter for thread-group type touches only the
  one flag it owns, refusing combinations the firmware refuses.
- What was deliberately not done: creating a SPURS instance. That call allocates an
  SPU thread group, installs the scheduler into the SPUs' local stores and starts
  them running. The port can execute SPU programs and move their data, but it has no
  SPU *threads* inside its scheduler yet, so reporting success would be a claim that
  would only fall over much later, in a place that would be far harder to diagnose.
- So the next piece is concrete: SPU thread groups - images, local stores, and SPU
  contexts scheduled alongside the processor threads. After that the job system can
  be created for real, and the boot can reach the graphics calls.
- Boot position: 95,507 executed blocks
- Runtime tests: 164 passing
- The port is not yet playable.
## 2026-10-26 - the graphics boundary, and a decision about backends

- Two questions got answered in code and in writing this round: where graphics work
  attaches, and which GPU APIs the port will target.
- First, the address layer the game itself manipulates: the renderer's own memory
  window, the page tables that map system memory into it, and translation in both
  directions. An address that was never mapped now fails instead of returning
  something plausible, which is the difference between a bug that shows up and one
  that corrupts a picture in a way nobody can explain.
- Second, the seam the renderer will sit behind, plus a backend that records what
  the game submits without drawing anything. That matters because it lets the
  translation be checked against the game's real submissions before any GPU code
  exists. A draw with no program bound is rejected rather than counted, so the
  recorder cannot flatter the port.
- Backend decision, recorded with its reasoning: Vulkan first, because translated
  shaders land naturally in SPIR-V and because it covers Windows and Linux/Steam
  Deck; Direct3D 12 afterwards behind the same seam, which is a port of the state
  and submission layer rather than a second renderer. If only one ships in v1,
  Vulkan is the better single choice.
- The honest risk, written down rather than discovered later: shader translation is
  the largest piece, and the renderer's quirks are the kind that look almost right
  when they are wrong.
- Runtime tests: 160 passing
- The port is not yet playable.
## 2026-10-26 - memory for the SPU programs, and a place for framerate and aspect options

- The SPU programs can now move data: main memory is attached, and the two transfer
  commands the game uses copy between that memory and an SPU's 256 KiB workspace.
  Tags are marked complete the way a waiting program expects to see them.
- Not every transfer form is implemented. Lists, atomics and the barrier variants
  report themselves with their parameters rather than silently doing nothing, which
  is the same rule applied throughout. Transfers also complete immediately, because
  there is no asynchronous DMA engine yet - stated, not implied.
- One encoding detail was wrong at first and a test caught it: the flag that marks a
  list transfer is not one of the low bits I had stripped, so list loads had been
  quietly folded into ordinary loads.
- Separately, a small but structural piece for the question of whether this port can
  add framerate, aspect and similar options: the split between *guest ticks* and
  *host frames* is now explicit. The game simulates at its own fixed rate; the host
  decides how those steps become frames, with a window size, a vsync and frame-cap
  setting, and an aspect policy that can letterbox to the native shape or record an
  ultrawide intent.
- That split is what makes such features configuration instead of binary patches. It
  does not change what the game computes - only when. Features that change the
  simulation itself are a different, larger job.
- Runtime tests: 149 passing
- Missing SPU instructions across the corpus: none
- The port is not yet playable.
## 2026-10-26 - the SPU programs run end to end, and the gaps are gone

- Every one of the game's twenty-three SPU programs now runs without hitting an
  instruction the port cannot execute. That was the goal of this stage.
- The measurement went from seven hundred instructions executed across the corpus to
  almost twenty-five thousand, not because of one big change, but because each
  missing instruction turned out to be small and exact once its behaviour was taken
  from a reference rather than guessed.
- The boundary that remains is not decoding. It is *memory*: four of the programs
  ask to move data between their own 256 KiB workspace and the console's main
  memory, and the port has no main memory attached to an SPU yet. That request is
  now reported with its parameters instead of being ignored or faked.
- The other remaining boundary is time: one program sits in a loop polling for a
  signal that never arrives, because standalone there is nothing to signal it. A real
  run gives that thread a scheduler to block in, which is the next piece of work.
- Channels - the instruction-level mechanism SPUs use to talk to the rest of the
  machine - are now modelled with real state: event masks, signal registers,
  mailboxes, tags and the decrementer. A read with nothing to deliver says so
  precisely, per channel, rather than inventing a value.
- Also cleaned up: the earlier instruction table was silently missing six entries
  (instructions with no operands, and two branch-hint fields). It now carries the
  complete set.
- Runtime tests: 140 passing
- Missing instructions across all 23 programs: none
- The port is not yet playable.
## 2026-10-26 - the port starts running SPU code

- The port now executes the game's SPU instructions. Not simulated hardware: the
  actual programs from the disc, one instruction at a time.
- All twenty-three embedded programs start and run. Sixteen of them follow their
  initialisation path all the way to a clean halt. The rest stop with a precise
  report of the instruction that is not implemented yet - four of them, named and
  ranked, instead of a vague failure.
- Two mistakes were caught by running the code rather than by reading it. The
  first: 32-bit values and addresses on an SPU live in the "preferred slot", which
  is the most significant word of the register. Reading the low word instead made
  an address computed by the program point at zero, so the interpreter executed
  the program image as if it were data. The second: SPU arithmetic works on four
  independent 32-bit lanes with no carry between them, while the reference
  definition the table came from models a whole-register add. Following the
  reference there would have been wrong.
- Also fixed: the table generator had been silently dropping instructions that take
  no operands, and was missing two branch-hint fields. The table now carries all
  204 encodings from the source, not 198.
- Next: the remaining instructions, of which one needs the SPU's channel interface
  (data transfer) that does not exist yet. After that, translating these programs to
  native code with this interpreter as the reference.
- Runtime tests: 137 passing (one steps every encoding and requires each to run or
  name itself)
- PPU boot unchanged: 95,497 blocks
- The port is not yet playable.
## 2026-10-26 - the executable contains 23 SPU programs, and they all read

- Scanning the game's executable for SPU programs turned up twenty-three of them,
  roughly 290,000 instructions together. That is the workload the port has to run,
  now measured instead of estimated.
- More useful than the count: every one of those programs decodes at between 85 and
  96 percent with the generated instruction table, most in the mid nineties. That
  consistency matters. A table fitted to one image could look good on that image
  and fail elsewhere; twenty-three independent programs agreeing at the same rate
  is evidence that the decoder covers the instruction set as the game actually
  uses it.
- The remaining words are dominated by a repeated padding value, not by unknown
  instructions.
- This is the preparation for execution: the next step is giving those instructions
  meaning and running a real task, then compiling them to native code.
- Runtime tests: 129 passing
- Recompiler tests: 58 passing
- The port is not yet playable.
## 2026-10-26 - teaching the port to read SPU programs

- The port can now decode the game's SPU instructions, and the table it uses was
  generated from a published instruction-set definition rather than written from
  memory.
- That mattered. The first attempt at the table got the bit order wrong, which
  showed up immediately in two ways: only half the words in a real program
  resolved, and the program's *first* instruction did not decode at all. Both were
  fixed by reading the data instead of trusting the assumption.
- Decoding the animation task image the game embeds now resolves **93%** of its
  words, and the entry instruction reads as "load immediate address", which is
  exactly what a task entry looks like. The remainder is dominated by a repeated
  padding word, not by undecoded code.
- Two instructions share an encoding with a general form (`lr` is "or with zero",
  `iret` is "compare with zero in the destination"). The generator records those
  overlaps explicitly and a test requires them to stay documented, so a decoder
  can never silently pick a name for the wrong reason.
- Runtime tests: 129 passing
- Recompiler tests: 58 passing
- The port is not yet playable.
## 2026-10-26 - deciding how the game's SPU code will run

- The port reached the point where the game starts its SPU job system. That is the
  real fork in this project: most of the game's gameplay code lives on the SPUs,
  and the animation decoder is one such program.
- The question was put plainly - interpreter, defer, or compile - and the honest
  answer for a native PC game is that you do not ship an interpreter. The play path
  should run compiled code, exactly as the main processor code already does.
- So the plan is two stages. First write an interpreter, once, as the written-down
  specification of what the instructions mean and as a reference to test against.
  Then translate the SPU programs to native code and check every translated block
  against that reference. The interpreter is scaffolding, not the product.
- The first piece is in: the port can read an SPU program image out of the game and
  build the 256 KiB working memory an SPU sees. Verified against the real program
  the game embeds, not a synthetic one.
- Nothing executes yet, and the port does not pretend otherwise: the first call
  that would run SPU code still fails loudly.
- Boot position: **95,497 executed blocks** (unchanged this entry; the work was
  foundation and a decision).
- Runtime tests: 127 passing
- Recompiler tests: 58 passing
- The port is not yet playable.
## 2026-10-26 - threads that actually wait, and the game reading its own metadata

- The port's scheduler used to be polite but dumb: guest threads took turns whether
  or not they could do anything, so a thread waiting for a message just spun. This
  entry is about fixing that properly, because the game's next steps depend on it.
- Event queues, event ports and event flags are now real objects with real state -
  messages queued, senders mapped to receivers, bit patterns held. A thread that
  waits on them is marked blocked and the scheduler moves on.
- Two details made this work. A syscall can now stop a thread in the middle of a
  block, so it resumes at the instruction after the call. And when every thread is
  waiting, the port does not hang: it skips the idle time forward to the earliest
  timeout, or reports a deadlock if there is none. That keeps runs deterministic
  and makes a stuck game a diagnostic instead of a freeze.
- The wait-mode constants for event flags were checked against the platform
  definitions after a guess turned out backwards (AND versus OR). Worth noting
  because the wrong way round would have looked like a game logic bug later.
- Controller support landed with the real structures: one connected standard pad,
  sticks centred, no buttons pressed. There is no host input source yet, so the
  port does not pretend buttons are being pressed - only that a pad is present.
- The game now reads its own metadata, and the port answers from the actual disc:
  the game's PARAM.SFO is parsed and served, so the title id, title and version are
  the shipped values. First attempt read only a third of the file because the
  string encoding assumption was wrong; the real file says otherwise, which is why
  it is worth parsing the real thing.
- Also added: a tool that lists every imported function the game actually calls,
  with call sites. 311 of 342 imports are used across 1,424 sites, and that map is
  now the work queue for the rest of the port.
- Boot position: **95,497 executed blocks**, up from 58,011.
- Runtime tests: 123 passing
- Recompiler tests: 58 passing
- The port is not yet playable.
## 2026-10-27 - the wall was a compare bug, not a missing subsystem

- This is a correction. The previous entry classified the boot's frontier as a
  subsystem the emulator would have to grow. That was wrong, and the way it was
  disproved matters more than the fix.
- A single-function call test - run one recompiled guest function against data
  known to be static and correct - returned a garbage fault before the fix and a
  valid pointer after it. The data had been fine all along.
- The actual bug: the word-compare instructions compared the full 64-bit register
  instead of the low 32 bits. A list terminator of minus one, loaded by a word
  load into a register whose upper half stays zero, therefore never compared
  equal, so every list walk ran past its end and dereferenced whatever followed.
  Two instructions, one class of symptom, and it looked exactly like the game
  expecting memory that was never allocated.
- Effect: the boot went from 6,090 to 39,193 executed blocks immediately, and to
  **58,011** after the next few requirements. It now runs deep into subsystem
  initialisation - mutexes, memory mapping, synchronisation primitives - rather
  than stopping in the C runtime.
- Lesson recorded for next time: when a fault looks like "the game expects data
  we never built", test the hypothesis by calling the suspect function directly
  on known-good inputs before concluding anything about missing subsystems.
- Also added: a host-backed virtual filesystem for the game's device paths, with
  traversal rejection, plus two runtime tests.
- Runtime tests: 105 passing
- Recompiler tests: 58 passing
- Decoding: 47,916 of 47,929 functions, zero real instruction gaps.
- The port is not yet playable.
## 2026-10-27 - zero real gaps again, and where the boot actually stands

- Decoding is complete again and better than before: **47,916 of 47,929 functions**
  (99.97%), with **zero real instruction gaps** - the thirteen remaining failures
  are data outside the analyser's instruction ranges. Basic blocks: 407,953.
- The improvement came from a decoder fix made for the boot: functions that
  return early and continue further on are now decoded along every branch, not
  just up to their first return.
- The last two real gaps were a single vector instruction, chosen deliberately
  from the failure list rather than guessed at.
- The boot walk reached **6,090 executed basic blocks** from the retail entry
  point (it started at 22 when this work began) and now stops walking a list
  whose nodes are built at runtime. That was established by measurement: no code
  computes the address, no static node holds it, and an instrumented store watch
  on both store widths recorded no writer. So the next requirement is a
  data-producing subsystem - resource or module registration - not a decoding bug.
- Decision recorded: pause the boot crawl there. It is project-sized work, and
  graphics and file I/O remain before anything is playable, so speculative
  crawling would spend time off the critical path.
- Runtime tests: 103 passing
- Recompiler tests: 57 passing
- The port is not yet playable.
## 2026-10-27 - eight-way parallel compilation

- The compiler for the recompiled guest code now uses the whole machine. A single
  rustc invocation is serial no matter how its codegen units are configured, so
  the translated code is emitted as eight independent crates that cargo builds
  concurrently, with the boot harness merging their tables once at startup.
- Measured on the same closure: a 1200-function build went from 86 s to 18 s, and
  the automated walk's cycle dropped from 6-9 s to 4 s.
- The gain grows with closure size, which is the direction this needs: the set of
  translated code only ever gets larger.
- Also fixed a coupling bug the walk exposed: the function budget must stay above
  the number of seeded entry points, otherwise the entry's own call graph is
  truncated and the run stops after a single block.
- Current state of the walk: 4,260 executed blocks from the retail entry point,
  up from 22 at the start of this stretch, frontier moving through the game's own
  code with no invented behaviour.
- Runtime tests: 103 passing
- Recompiler tests: 56 passing
- The port is not yet playable.
## 2026-10-27 - threads, syscalls, and a self-driving boot walk

- The port now runs guest threads. A game does not start its main function on
  the loader thread; the C runtime creates one, so without a thread model the
  boot could only ever stop. Threads are switched cooperatively at block
  boundaries, which keeps execution deterministic and is enough for code that
  waits on shared flags.
- The boot walk became automatic: it regenerates a small module, seeds the
  address it stopped on, rebuilds and repeats, and it now remembers those
  addresses so each run continues instead of repeating. It stops itself when the
  blocker needs real code rather than more emitted code.
- System calls implemented from stops rather than guesses: stack information,
  address reservation and backing memory, timebase frequency, current time, and
  thread identity. One of them was a bug in our own call handling, found because
  the fault report includes the address.
- Measured progress on the same entry point: 22 executed blocks at the start of
  this stretch, 3,069 now, with the frontier moving from the C runtime into the
  game's own subsystems.
- Runtime tests: 103 passing
- Recompiler tests: 56 passing
- The port is not yet playable.
## 2026-10-27 - a stack-frame bug that broke every function, and a 10x faster loop

- Found the reason the boot kept unwinding almost immediately: doubleword load
  and store instructions were decoded without their opcode extension. The net
  effect was that the stack-store-with-update never updated the stack pointer,
  so **no function in the game allocated a stack frame**, and every frame
  displacement was also short by the low two bits of the encoding.
- After fixing it the same boot path went from 22 executed blocks ending in a
  jump to null to 370+ blocks with a balanced stack, and it now stops on real
  library and system calls instead of collapsing.
- That fix was only findable because the harness now reports blocks executed and
  traces the stack pointer per block. A clean "returned successfully" had been
  hiding a null branch; those are now distinct outcomes.
- Iteration speed was the other limiter. Measured: a 150-function closure builds
  in 5 s, 1200 functions in 86 s, and the large build executed 383 of its 16,326
  blocks - so compiling more was both slower and less reliable. The loop now
  compiles a small closure and seeds the exact address the boot stopped on.
- An automated walker repeats that cycle unattended and stops when the blocker
  needs real code rather than more emitted code. It advanced nine functions and
  then surfaced a system call, which is the correct kind of stop.
- Runtime tests: 103 passing
- Recompiler tests: 56 passing (DS-form regression added)
- The port is not yet playable.
## 2026-10-27 - second firmware call, and a compiler-scaling fix

- The boot now gets past the C runtime's TLS setup and reaches its second
  firmware call: creating a lightweight mutex. For a guest that runs one thread
  that is modelled faithfully rather than stubbed - no lock can be contended,
  so creation zeroes the object and the lock operations succeed.
- Registering a library is now recorded instead of discarded. Returning success
  while throwing the descriptor away would be exactly the kind of silent lie
  that surfaces much later as inexplicable behaviour.
- The generated dispatcher was a match with one arm per translated block -
  about 12,800 arms for a 900-function closure, which dominated compile time
  (three minutes for a nine-megabyte file). It now uses a sorted table and a
  binary search. That matters for what comes next: larger closures were limited
  by the compiler, not by the amount of code.
- Runtime tests: 103 passing
- Recompiler tests: 55 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - the decoder was silently truncating functions

- Found a decoding bug by chasing a boot failure: the recompiler stopped reading
  a function at the first return instruction. Compilers routinely emit an early
  return and then more code reached only by a forward branch, so whole regions
  of already-"emitted" functions had no blocks.
- The decoder now walks a worklist: fall-through plus every branch target inside
  the function window, each path stopping at its own return.
- Two mistakes of mine, caught immediately by the boot and by the closure size:
  treating a call as the end of a path cut the boot closure from 600 functions
  to 3, and treating an indirect call as one lost a thunk's epilogue. Calls
  return, so decoding continues through them; only unconditional branches and
  returns end a path.
- Both cases now have regression tests. The closure also shrank from 600 to 116
  functions for the same instruction budget, because the old decoder was also
  reading code after unconditional branches that can never execute.
- Runtime tests: 103 passing
- Recompiler tests: 55 passing (two added)
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - every import is now named

- Cracked the identifier scheme: the per-function numbers in the executable are
  standard PS3 NIDs - the first four bytes of SHA-1 of the function name plus a
  fixed 16-byte suffix, read little-endian.
- Verified two ways: all 30 identifiers of the system library resolve to real
  API names, and a public NID list resolves the rest. All 342 imports across 23
  libraries now have names, and the boot cross-checks the generated table
  against the executable's own descriptor counts so it cannot go stale quietly.
- The first import the startup code reaches is sys_initialize_tls, called with
  no arguments - exactly the kind of call a C runtime makes first. It is now
  implemented as a documented decision: the thread gets a zeroed TLS block and
  the thread pointer register is set; the real TLS image is not modelled yet.
- Two loader responsibilities were found by running the code rather than
  guessing: the entry takes argc/argv/envp in registers, and startup walks the
  stack pointer above its initial value, so it needs headroom. Supplying both
  moved the boot from address 4 past the end of the C runtime into the game's
  own code.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - complete import map recovered

- Found the per-library import descriptors in the executable. Each one names a
  library, carries a 32-bit identifier per function, and points at that
  library's block of the dispatch table.
- All 23 libraries are now named and accounted for - sysPrxForUser, cellGcmSys,
  cellSpurs, sys_fs, cellAudio, cellSysutil and the rest - and their blocks add
  up exactly to the 342 thunk slots in the binary. Nothing is unaccounted for.
- The boot therefore no longer says "slot 263"; it says the truth:
  the first required import is sysPrxForUser[14], called from startup with no
  arguments.
- Remaining gap, stated plainly: the per-function identifiers are sorted 32-bit
  values, but they are not SHA-1, SHA-256 or MD5 of the obvious export names in
  any form tried. Until that hash is identified, individual functions are known
  by library and index only, and will be implemented against observed behaviour
  rather than guessed names.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - full import table bound; first import identified by slot

- Corrected the import table: it lives at a different address and is four times
  larger than first bound - 342 slots, one per thunk, matching the 342 thunks in
  the stub section exactly.
- The boot now reports the true slot number of the first import it needs.
- Found and recorded an important limitation: this executable carries no import
  name metadata at all - no stub-name section, and no pointer anywhere in the
  file references a library or function name. So the slots cannot be named from
  the binary yet; that is now an explicit open question rather than a guess.
- Deliberate policy restated: an unbound import is a hard error. Returning a
  fabricated zero would let the game continue in a state that can never match
  the original, which is worse than stopping.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - import binding; the boot now stops on a real library call

- The startup code reaches the game's import thunks, which read a resolved
  function descriptor out of a table and branch through it. The port now binds
  every populated slot (94) to synthetic descriptors that the recompiled
  dispatcher recognises as imports.
- Result: the native boot runs module startup, goes through the thunk, and
  stops at the first genuine library call - import slot 15.
- Unbound imports raise a hard error carrying the slot and the calling address,
  rather than returning an invented value. That is deliberate: a wrong return
  here would silently corrupt everything downstream.
- Calls into the import-thunk section are now followed even though it sits
  outside the function inventory.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - the retail entry point runs natively

- New boot binary: it maps the retail executable, reads the entry descriptor
  from the ELF header, and jumps straight into recompiled native code. No
  emulator is involved anywhere in this path.
- First run executes real module startup code and stops at the first branch
  target that has not been translated yet. That address turns out to be an
  import thunk: it loads a function descriptor from a table and branches
  through it.
- So the next piece of work is binding that import table to native
  implementations, not writing more decoder code.
- The prior session's debugging detour is closed out: the reference emulator's
  breakpoints are silently disabled under its default CPU decoder, which is why
  that protocol never worked. The emulator is back to its normal settings and
  is not part of the build or the runtime.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - why the oracle was blocked (it was not set-pc)

- Spent this session reading the emulator's debugger source and testing against
  a live process instead of guessing.
- The real cause: with the default LLVM CPU decoder, the debugger's breakpoint
  request is answered "OK" but the breakpoint is never installed. Every
  "redirect, resume, stop at a sentinel" attempt was therefore guaranteed to
  fail, no matter how correct the register writes were.
- Second cause: closing a debugger connection terminates the debugger thread
  inside the emulator. A previous session had been talking to a dead stub that
  reported one thread and a frozen PC, which is where the misleading
  "PC never changes" observations came from. A fresh process reports 19 threads.
- Third finding: under the LLVM decoder the reported program counter is not the
  live one, so writes to it do not redirect a running thread. Registers are
  live; the PC is not.
- The only non-LLVM CPU decoder is the static interpreter, which does install
  breakpoints. Moving the oracle to that decoder is the next step; the rest of
  the protocol (host-side memory reads, argument setup, record comparison)
  carries over unchanged.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- Coverage unchanged: 47,823 of 47,929 functions decoded, zero real gaps.
- The port is not yet playable.
## 2026-10-27 - the decoder is complete

- The last nine instruction forms are in: string store, doubleword conditional
  store, an unsigned halfword compare, unsigned halfword add/subtract (both
  modulo and saturating), the shift-left control vector, FPSCR read, and a word
  pack.
- The full scan now decodes **47,823 of 47,929 functions** and the remaining
  106 failures all classify as data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â bytes outside the disassembler's defined
  instruction ranges. Real instruction gaps: **zero**.
- To be precise about what that means: every word the analysis presents as a
  real instruction now decodes and emits a native block. It does not mean any
  of those blocks has been proven to behave like the original. No function has
  been compared against the emulator yet.
- Known modelling gaps are unchanged and still documented: vector saturation
  flags are not modelled, FPSCR is recorded but not consumed, prefetch and trap
  forms are no-ops, and the cache-block zero assumes Cell's 128-byte line.
- Runtime tests: 103 passing
- Recompiler tests: 53 passing
- The port is not yet playable.
## 2026-10-27 - cache, string and vector-element tail

- Closed 17 more instruction forms, covering string loads, cache-block zero,
  vector element stores, byte-reversed stores, extended subtract, doubleword
  arithmetic shifts, FPSCR field moves and a scratch special-purpose register.
- One of them exposed a real branch bug rather than just a decoder gap: the
  "branch if set" encodings carry two prediction bits, and the port had only
  ever accepted the one canonical spelling, so those aliases were rejected
  instead of being mis-executed. The decoder now normalises the hint bits.
- Two behaviours are documented as port decisions rather than architecture:
  saturation flags are not modelled (no vector status register yet), and FPSCR
  is recorded state that no floating-point helper consumes yet.
- Runtime tests: 103 passing
- Recompiler tests: 52 passing
- Coverage: 47,808 of 47,929 functions (99.7%); 377,492 native blocks.
  Real remaining gaps: 15.
- The port is not yet playable.
## 2026-10-27 - vector word forms and a split-field shift

- Added four vector forms (halfword splat, arithmetic word shift, two word
  merges) and the arithmetic doubleword shift-right-immediate.
- That last one carried the two largest remaining decoder gaps on its own: its
  sixth shift bit lives in the instruction's extension field, so it appears as
  two different encodings depending on the shift amount. Both retail sites
  confirmed the split before it shipped.
- Runtime tests: 103 passing
- Recompiler tests: 51 passing
- Coverage: 47,757 of 47,929 functions (99.6%); 376,353 native blocks.
  Real remaining gaps: 46.
- The port is not yet playable.
## 2026-10-27 - word shifts, unsigned multiply-high, CR move

- Added six more instructions, including a register-controlled word rotate and
  a condition-register field copy; one was registered in the wrong decode table
  and an existing test caught it immediately.
- Runtime tests: 103 passing
- Recompiler tests: 50 passing
- Coverage: 47,682 of 47,929 functions (99.5%); 374,939 native blocks.
  Real remaining gaps: 115.
- The port is not yet playable.
## 2026-10-27 - word compares, 64-bit divide, updating stores

- Added eight more instructions: an integer vector compare with condition
  aggregation, signed and unsigned 64-bit division, two updating stores, a
  doubleword multiply-high, a prefetch no-op and a sign-extending word load.
- A unit test caught two of them registered in the wrong decode table before
  they could ship.
- Runtime tests: 103 passing
- Recompiler tests: 49 passing
- Coverage: 47,652 of 47,929 functions (99.4%); 374,413 native blocks.
  Real remaining gaps: 142.
- The port is not yet playable.

## 2026-10-27 - tail instructions and three caught defects

- Added eight tail instructions covering vector halfword merge, doubleword
  store-with-update, unsigned multiply-high, double-precision multiply,
  byte-reversed load, doubleword shifts and multiply-low.
- Three defects were caught by tests before commit: an A-form operand error in
  the double multiply, a negative-shift bug in the halfword merge, and a wrong
  expected value in its test.
- One instruction is deliberately a no-op (trap word) because the port has no
  trap handler; that is recorded as a limitation.
- Runtime tests: 103 passing
- Recompiler tests: 48 passing
- Coverage: 47,584 of 47,929 functions (99.3%); 373,532 native blocks.
  Real remaining gaps: 222.
- The port is not yet playable.

## 2026-10-27 - vector maximum, permute, shifts and estimates

- Added five more primitives: vector maximum with the architecture's
  signed-zero rule, a per-byte shift, a byte permute, a reciprocal estimate and
  an updating single-precision load.
- A unit test caught an undefined shift in the permute implementation, and a
  compile-time overflow check caught the first attempt at it.
- Runtime tests: 103 passing
- Recompiler tests: 47 passing
- Coverage: 47,406 of 47,929 functions (98.9%); 370,144 native blocks.
  Real remaining gaps: 396.
- The port is not yet playable.

## 2026-10-27 - five more vector and integer forms

- Added a vector minimum (with the architecture's signed-zero rule), a halfword
  splat, a reciprocal square-root estimate, a rotate-mask-insert doubleword and
  an element-word store.
- A unit test caught an incorrect signed-zero rule in the first version of the
  minimum before it shipped.
- Runtime tests: 103 passing
- Recompiler tests: 46 passing
- Coverage: 47,240 of 47,929 functions (98.6%); 367,165 native blocks.
  Real remaining gaps: 522.
- The port is not yet playable.

## 2026-10-27 - vector select and float-as-integer store

- Added a vector bit-select primitive and a store that writes floating-point
  register bits as an integer word without conversion (the two differ, and the
  second had to be implemented explicitly rather than reused from the first).
- Runtime tests: 103 passing
- Recompiler tests: 45 passing
- Coverage: 46,963 of 47,929 functions (98.0%); 359,941 native blocks.
  Real remaining gaps: 592; the rest are embedded data.
- The port is not yet playable.

## 2026-10-27 - five more instruction families

- Closed five decode classes in one pass: a logical-with-complement form, an
  immediate XOR, a byte load with address update, an instruction barrier, and
  the recording forms of the rotate-mask doubleword family (which was the real
  cause of a 48-site class, not a missing instruction).
- Runtime tests: 103 passing
- Recompiler tests: 44 passing
- Coverage: 46,904 of 47,929 functions (97.9%); 358,405 native blocks.
  Real remaining gaps: 648; the rest are embedded data.
- The port is not yet playable.

## 2026-10-27 - double-to-integer conversion and barriers

- Added a double-to-signed-integer conversion with documented invalid-result
  behaviour, and treated memory barriers as no-ops for the single-threaded
  port.
- Runtime tests: 103 passing
- Recompiler tests: 43 passing
- Coverage: 46,726 of 47,929 functions (97.5%); 355,227 native blocks.
  Real remaining gaps: 827; the other 376 are embedded data.
- The port is not yet playable.

## 2026-10-27 - automatic import of untranslated targets

- The execution driver now discovers untranslated targets by itself: it runs,
  reads the reported target, imports it and retries, then re-runs the whole
  property matrix. It finds the one indirect callee on the first round.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks
- This is still a pre-run import step, not runtime translation of arbitrary
  indirect calls, and it is still not a reference-emulator comparison.
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â end-to-end check turned into a property

- The execution check no longer compares against one fixed record: it asserts
  that the recovered constructor echoes whatever type and flags it is given,
  marks the record active and returns cleanly. Three input pairs pass.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks
- Still not a reference-emulator comparison.
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â recovered function now runs to completion

- The end-to-end check now executes a recovered retail function through to its
  return, including one indirect callee imported as an extra root, and asserts
  the resulting record fields.
- Two harness defects were found and fixed: the stack pointer sat at the top of
  the region (one access past the mapping), and the transaction could not be
  started from more than one root.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks
- Still not a reference-emulator comparison; arbitrary indirect calls also need
  runtime resolution rather than manual roots.
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â first end-to-end execution check

- A recovered retail function now runs through the native recompiled path in an
  automated harness: emit, compile, execute, and assert its observable output.
- The check reproduces the function's previously recorded behaviour and fails
  if any of it regresses.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks
- Not yet a comparison against the reference emulator; that is the next step.
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â doubleword rotate and hinted branches

- Added a doubleword rotate-mask primitive and accepted the hinted conditional
  branch forms, deriving the condition test from the branch's option field
  instead of a fixed list.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks.
  Remaining real gaps: 912; the other 369 "gaps" are embedded data.
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â decode audit and integer arithmetic

- Coverage accounting now separates real code from embedded data using the
  analyser's own instruction map; a sixth of the previous "gaps" were data.
- Added integer divide, multiply-high and condition-register-move primitives,
  with undefined-case behaviour documented rather than assumed.
- Runtime tests: 103 passing
- Recompiler tests: 41 passing
- Coverage: 46,585 of 47,929 functions (97.2%); 352,335 native blocks.
  Real remaining gaps: 1,026 (the rest are data).
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â system-call boundary

- Added a system-call boundary with a small, explicitly limited set of
  behaviours: mutex create/destroy/lock/unlock and elided sleeps. Anything
  else fails loudly with its call number instead of returning a guessed value.
- 522 of the 794 statically identified call sites now have defined behaviour.
- Runtime tests: 103 passing
- Recompiler tests: 40 passing
- Coverage: 46,122 of 47,929 functions (96.2%); 340,226 native blocks.
  Decode coverage is not capability: unimplemented calls fail at runtime.
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â reservation-based atomic pair

- Added the load-reserve / store-conditional pair with a single-threaded
  reservation model and condition-register success reporting.
- Runtime tests: 102 passing
- Recompiler tests: 39 passing
- Coverage: 45,899 of 47,929 functions (95.8%); 336,396 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â deterministic timebase

- Added the timebase read (both encodings) backed by a deterministic counter
  advanced once per dispatched native block, so runs stay reproducible.
- Runtime tests: 102 passing
- Recompiler tests: 38 passing
- Coverage: 45,827 of 47,929 functions (95.6%); 334,786 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â subtract-from-immediate and shift fix

- Added a subtract-from-immediate primitive with carry recording, and fixed
  one shift form that previously ignored its recording bit.
- Runtime tests: 102 passing
- Recompiler tests: 37 passing
- Coverage: 45,685 of 47,929 functions (95.3%); 332,387 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â word shift primitives

- Added three 32-bit word shift primitives with masked shift counts,
  zero/sign extension and condition-register updates, unit-tested at the
  31/32-bit boundary.
- Runtime tests: 102 passing
- Recompiler tests: 36 passing
- Coverage: 45,566 of 47,929 functions (95.1%); 329,859 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â coverage rebased, reciprocal square root added

- Coverage measurement was corrected to cover the full analysed function
  inventory instead of a long-standing subset. Reported coverage therefore
  rises because the denominator was wrong, not because the port jumped.
- Added a reciprocal square-root estimate primitive; its exact result bits are
  implementation-defined and are not claimed.
- Runtime tests: 102 passing
- Recompiler tests: 35 passing
- Coverage: 45,435 of 47,929 functions (94.8%); 327,315 native blocks
- The port is not yet playable. Decode coverage is not behavioural correctness.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â indexed float access and single-precision square root

- Added the indexed floating-point load/store family and a single-precision
  square root primitive; a prior label in the audit was corrected against the
  live analysis database.
- Runtime tests: 102 passing
- Recompiler tests: 34 passing
- Coverage: 12,963 of 14,732 functions; 148,296 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â bounded function-body manifests and vector subtract

- Coverage measurement is now bounded to analysed function bodies, so embedded
  data is no longer misread as code. This corrected the baseline: 208 reported
  gaps were data, not code.
- Added a vector single-precision subtract primitive with signed-zero and
  overflow coverage.
- Runtime tests: 102 passing
- Recompiler tests: 32 passing
- Coverage: 12,637 of 14,732 functions; 140,242 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â vector floating-point compares

- Added the three vector floating-point compare primitives, including their
  recording forms, with the architecture-defined condition-register summary
  and NaN handling.
- Runtime tests: 102 passing
- Recompiler tests: 31 passing
- Coverage: 12,407 of 14,732 functions; 141,034 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â vector single-precision add

- Added a vector single-precision add primitive with round-to-nearest
  semantics, including signed-zero and overflow coverage in tests.
- Runtime tests: 102 passing
- Recompiler tests: 30 passing
- Coverage: 12,384 of 14,732 functions; 140,349 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â vector integer and fused arithmetic primitives

- Added three more vector primitives: unsigned word add and subtract (modulo
  32-bit lanes, no flag changes) and a fused negative multiply-subtract with
  architecture-specified rounding and signed-zero behaviour.
- Runtime tests: 102 passing
- Recompiler tests: 28 passing
- Coverage: 12,325 of 14,732 functions; 139,990 native blocks
- The port is not yet playable.

## 2026-10-27 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â vector conversion primitives

- Added two vector floating-point to fixed-point conversion primitives, both
  with round-toward-zero and saturation, checked against the architecture
  specification and an independent emulator implementation.
- Runtime tests: 102 passing
- Recompiler tests: 25 passing
- Coverage: 12,325 of 14,732 functions; 139,990 native blocks
- The port is not yet playable.

## 2026-10-27

Continued private native-porting work. Public updates are intentionally limited
to high-level progress and test status; implementation details remain in the
private workspace.

- Runtime tests: 102 passing
- Recompiler tests: 23 passing
- The port is not yet playable.

## 2026-10-30 - level geometry renders for the first time

- A level now renders as actual geometry rather than scattered fragments. Corinth River produces
  342,484 triangles across 1,723 placed meshes, and the image shows walls, ground planes and
  structures laid out along the map.
- Two decoding defects were doing all the damage, and both were invisible from a distance.
- First: a section shares one large vertex buffer between many meshes, and each mesh addresses a
  small slice of it. The reader was returning the whole buffer for every mesh, so every mesh drew
  the same low geometry. The fix keeps only the vertices each mesh actually uses.
- Second: each mesh records its world position near the start of its own data, while an earlier pass
  scanned backwards from the end. That works only while a mesh has a short list of parts; meshes with
  longer lists produced nonsense positions that threw off the camera. Two meshes in nearly three
  thousand were affected.
- With both fixed, 87 unit tests pass and the software renderer shows recognisable level structure.
- Still to do: about 1,200 meshes are skipped on a plausibility check, and some surfaces present as
  spikes. Both look like per-part details rather than placement, which is now measured and working.

## 2026-10-30 - placement solved: the geometry was already in the right place

- Levels now render as coherent scenes: buildings with facades, a cylindrical structure with spiral
  detail, clean slabs and beams. Corinth River draws 533,472 triangles across 2,831 meshes inside a
  tightly level-scale volume.
- The fix was to remove code, not add it. Every mesh was being shifted by a value read from its own
  data, and that value was never a position.
- Each section builds one shared vertex buffer that already sits in level space, and each mesh selects
  its own slice of it. Adding a per-mesh offset displaced everything that had been correctly placed.
- Four conventions were tried before the answer: a direct offset, a relaxed validity check, an axis
  permutation, and finally no offset at all. Only the last one produced a scene.
- Worth recording honestly: two of the earlier attempts reported more meshes "placed" than the working
  version. Those counts measured how many meshes passed a check, not how many rendered correctly. A
  higher number was hiding a worse picture.
- The remaining work is small in scope: around 90 meshes still lack a usable record, and a few
  surfaces present as spikes.
