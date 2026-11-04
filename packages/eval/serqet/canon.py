"""Canonical JSON and SHA-256 helpers. Local hash chaining is tamper-evident only."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

EPOCH = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def logical_time(step: int) -> str:
    return (EPOCH + timedelta(minutes=step)).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_instant(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def within_period(period: dict[str, str], moment: datetime) -> bool:
    start = parse_instant(period["start"]) if period.get("start") else None
    end = parse_instant(period["end"]) if period.get("end") else None
    if start is not None and moment < start:
        return False
    if end is not None and moment > end:
        return False
    return True
