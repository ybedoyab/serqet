"""Frozen checksum of the 4 November 2026 measured JSON files.

The constant is the SHA-256 of the sorted lines ``relative-path digest``.
It covers the 155 trial JSON files and nothing else.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

EVIDENCE_ROLLUP = "779ca52c9ca82ac3a3849a1a6e2de118a56cab84ac260753793244ac45c4cba1"


def measured_rollup(root: Path) -> str:
    files = sorted(path for path in root.rglob("*.json") if path.is_file())
    lines = [
        f"{path.relative_to(root).as_posix()} {hashlib.sha256(path.read_bytes()).hexdigest()}"
        for path in files
    ]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def evidence_problems(root: Path) -> list[str]:
    if not root.is_dir():
        return ["measured directory is missing"]
    actual = measured_rollup(root)
    if actual != EVIDENCE_ROLLUP:
        return [f"measured JSON bytes changed: {actual}"]
    return []
