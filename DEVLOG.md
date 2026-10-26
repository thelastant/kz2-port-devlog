# Development log

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
