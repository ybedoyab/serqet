"""Repository paths derived from this file so commands work from any cwd."""

from __future__ import annotations

from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def scenarios_dir() -> Path:
    bundled = Path(__file__).resolve().parent / "scenarios"
    sibling = package_root() / "scenarios"
    if sibling.is_dir():
        return sibling
    if bundled.is_dir():
        return bundled
    raise FileNotFoundError("scenarios directory not found")
