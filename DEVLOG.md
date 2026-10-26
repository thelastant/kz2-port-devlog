# Development log

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
