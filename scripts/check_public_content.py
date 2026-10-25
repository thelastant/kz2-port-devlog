#!/usr/bin/env python3
"""Reject public devlog pushes that expose game-derived technical detail."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = [
    (re.compile(r"\b0x[0-9A-Fa-f]{3,}\b"), "hex address/value"),
    (re.compile(r"\b[0-9A-Fa-f]{8,}\b"), "long hex string"),
    (re.compile(r"\b(?:file|byte)[- ]offset\b", re.IGNORECASE), "file offset"),
    (re.compile(r"\bhex dump\b", re.IGNORECASE), "hex dump"),
    (re.compile(r"\baddress range\b", re.IGNORECASE), "address range"),
]
SKIP_PREFIXES = ("scripts/", ".githooks/")


def tracked_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files"], text=True
    )
    return [line for line in out.splitlines() if line]


def main() -> int:
    failures: list[str] = []
    for relative in tracked_files():
        if relative.startswith(SKIP_PREFIXES):
            continue
        path = ROOT / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for pattern, kind in PATTERNS:
                if pattern.search(line):
                    failures.append(f"{relative}:{number}: {kind}")
    if not failures:
        print("public devlog check passed")
        return 0
    print("public devlog check failed:", file=sys.stderr)
    for failure in failures:
        print(f"  {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
