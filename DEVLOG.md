# Development log

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
  106 failures all classify as data — bytes outside the disassembler's defined
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

## 2026-10-27 — end-to-end check turned into a property

- The execution check no longer compares against one fixed record: it asserts
  that the recovered constructor echoes whatever type and flags it is given,
  marks the record active and returns cleanly. Three input pairs pass.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks
- Still not a reference-emulator comparison.
- The port is not yet playable.

## 2026-10-27 — recovered function now runs to completion

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

## 2026-10-27 — first end-to-end execution check

- A recovered retail function now runs through the native recompiled path in an
  automated harness: emit, compile, execute, and assert its observable output.
- The check reproduces the function's previously recorded behaviour and fails
  if any of it regresses.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks
- Not yet a comparison against the reference emulator; that is the next step.
- The port is not yet playable.

## 2026-10-27 — doubleword rotate and hinted branches

- Added a doubleword rotate-mask primitive and accepted the hinted conditional
  branch forms, deriving the condition test from the branch's option field
  instead of a fixed list.
- Runtime tests: 103 passing
- Recompiler tests: 42 passing
- Coverage: 46,648 of 47,929 functions (97.3%); 353,518 native blocks.
  Remaining real gaps: 912; the other 369 "gaps" are embedded data.
- The port is not yet playable.

## 2026-10-27 — decode audit and integer arithmetic

- Coverage accounting now separates real code from embedded data using the
  analyser's own instruction map; a sixth of the previous "gaps" were data.
- Added integer divide, multiply-high and condition-register-move primitives,
  with undefined-case behaviour documented rather than assumed.
- Runtime tests: 103 passing
- Recompiler tests: 41 passing
- Coverage: 46,585 of 47,929 functions (97.2%); 352,335 native blocks.
  Real remaining gaps: 1,026 (the rest are data).
- The port is not yet playable.

## 2026-10-27 — system-call boundary

- Added a system-call boundary with a small, explicitly limited set of
  behaviours: mutex create/destroy/lock/unlock and elided sleeps. Anything
  else fails loudly with its call number instead of returning a guessed value.
- 522 of the 794 statically identified call sites now have defined behaviour.
- Runtime tests: 103 passing
- Recompiler tests: 40 passing
- Coverage: 46,122 of 47,929 functions (96.2%); 340,226 native blocks.
  Decode coverage is not capability: unimplemented calls fail at runtime.
- The port is not yet playable.

## 2026-10-27 — reservation-based atomic pair

- Added the load-reserve / store-conditional pair with a single-threaded
  reservation model and condition-register success reporting.
- Runtime tests: 102 passing
- Recompiler tests: 39 passing
- Coverage: 45,899 of 47,929 functions (95.8%); 336,396 native blocks
- The port is not yet playable.

## 2026-10-27 — deterministic timebase

- Added the timebase read (both encodings) backed by a deterministic counter
  advanced once per dispatched native block, so runs stay reproducible.
- Runtime tests: 102 passing
- Recompiler tests: 38 passing
- Coverage: 45,827 of 47,929 functions (95.6%); 334,786 native blocks
- The port is not yet playable.

## 2026-10-27 — subtract-from-immediate and shift fix

- Added a subtract-from-immediate primitive with carry recording, and fixed
  one shift form that previously ignored its recording bit.
- Runtime tests: 102 passing
- Recompiler tests: 37 passing
- Coverage: 45,685 of 47,929 functions (95.3%); 332,387 native blocks
- The port is not yet playable.

## 2026-10-27 — word shift primitives

- Added three 32-bit word shift primitives with masked shift counts,
  zero/sign extension and condition-register updates, unit-tested at the
  31/32-bit boundary.
- Runtime tests: 102 passing
- Recompiler tests: 36 passing
- Coverage: 45,566 of 47,929 functions (95.1%); 329,859 native blocks
- The port is not yet playable.

## 2026-10-27 — coverage rebased, reciprocal square root added

- Coverage measurement was corrected to cover the full analysed function
  inventory instead of a long-standing subset. Reported coverage therefore
  rises because the denominator was wrong, not because the port jumped.
- Added a reciprocal square-root estimate primitive; its exact result bits are
  implementation-defined and are not claimed.
- Runtime tests: 102 passing
- Recompiler tests: 35 passing
- Coverage: 45,435 of 47,929 functions (94.8%); 327,315 native blocks
- The port is not yet playable. Decode coverage is not behavioural correctness.

## 2026-10-27 — indexed float access and single-precision square root

- Added the indexed floating-point load/store family and a single-precision
  square root primitive; a prior label in the audit was corrected against the
  live analysis database.
- Runtime tests: 102 passing
- Recompiler tests: 34 passing
- Coverage: 12,963 of 14,732 functions; 148,296 native blocks
- The port is not yet playable.

## 2026-10-27 — bounded function-body manifests and vector subtract

- Coverage measurement is now bounded to analysed function bodies, so embedded
  data is no longer misread as code. This corrected the baseline: 208 reported
  gaps were data, not code.
- Added a vector single-precision subtract primitive with signed-zero and
  overflow coverage.
- Runtime tests: 102 passing
- Recompiler tests: 32 passing
- Coverage: 12,637 of 14,732 functions; 140,242 native blocks
- The port is not yet playable.

## 2026-10-27 — vector floating-point compares

- Added the three vector floating-point compare primitives, including their
  recording forms, with the architecture-defined condition-register summary
  and NaN handling.
- Runtime tests: 102 passing
- Recompiler tests: 31 passing
- Coverage: 12,407 of 14,732 functions; 141,034 native blocks
- The port is not yet playable.

## 2026-10-27 — vector single-precision add

- Added a vector single-precision add primitive with round-to-nearest
  semantics, including signed-zero and overflow coverage in tests.
- Runtime tests: 102 passing
- Recompiler tests: 30 passing
- Coverage: 12,384 of 14,732 functions; 140,349 native blocks
- The port is not yet playable.

## 2026-10-27 — vector integer and fused arithmetic primitives

- Added three more vector primitives: unsigned word add and subtract (modulo
  32-bit lanes, no flag changes) and a fused negative multiply-subtract with
  architecture-specified rounding and signed-zero behaviour.
- Runtime tests: 102 passing
- Recompiler tests: 28 passing
- Coverage: 12,325 of 14,732 functions; 139,990 native blocks
- The port is not yet playable.

## 2026-10-27 — vector conversion primitives

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
