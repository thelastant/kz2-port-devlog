# kz2-port

A native Windows Rust port of Killzone 2, developed against a user-supplied
retail disc dump. The original game is used only as a behavioral and data
reference. No game binaries, assets, or decompiled output are distributed.

## Goal

A 1:1 playable port with no PS3 emulation layer in the runtime: boot, menus,
level load, gameplay, saves, and settings. Each system is accepted only after a
passing behavioral comparison with the original game running in RPCS3 on the
same input. RPCS3 is an oracle; its code is not used.

## Current status

- Native archive, serialized-object, texture, mesh, skeleton, and skinning
  readers.
- Native static-recompiler pipeline for the original PowerPC code, including a
  basic-block dispatcher and recursive direct-call import.
- Boot reaches graphics initialisation, configures the display, and captures the first
  command submission the game makes itself (15,376 words, nine distinct methods):
  **4,057,575** executed blocks.
- Current closure: **49,070 functions** and **428,755 native basic blocks** compiled
  from the retail executable, driven through a dispatcher that follows real control
  flow rather than per-function tests.
- Test suite: **379 tests** across the workspace, including 13 in the boot harness that
  cover display and audio output and 5 in the graphics layer. Real-disc tests are opt-in
  and skipped by default.
- Coverage is measured over the full analysed function inventory; decode
  coverage is not behavioural correctness.
- The game is not yet playable. Menus, level scripting, the full animation
  pipeline, SPU jobs, physics, AI runtime, audio, input, saves, and settings are
  still in progress.

## Repository layout

```text
notes/        private findings, audits, and subsystem notes
rust/         native Rust workspace
tools/        local analysis and validation tools
ghidra_scripts/  local static-analysis scripts
```

Generated code, dumps, and game data stay outside git.

## Building

Use the workspace-local Rust and mingw toolchain described in
`notes/build.md`, then run from `rust/`:

```text
cargo test --workspace
cargo run -p kz2-recomp -- --help
```

Real-disc tests require `KZ2_PSARC` and are opt-in.

## Legal

No game data or derived binaries are distributed. The port reads only from a
user-selected local disc dump. Killzone 2 and related trademarks belong to their
respective owners.
