"""Shared spend ledger. Separate processes cannot each spend the authorized ceiling."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

AUTHORIZED_CEILING_USD = 5.0
HARNESS_CEILING_USD = 4.5
_STALE_RESERVATION_S = 300.0
_STALE_LOCK_S = 120.0


class BudgetError(RuntimeError):
    """The ledger cannot be used without risking an overspend."""


class BudgetLedger:
    def __init__(
        self,
        path: Path,
        *,
        ceiling_usd: float = HARNESS_CEILING_USD,
        absolute_usd: float = AUTHORIZED_CEILING_USD,
    ) -> None:
        if absolute_usd > AUTHORIZED_CEILING_USD + 1e-9:
            raise BudgetError("absolute ceiling exceeds the authorized 5 USD")
        if ceiling_usd > absolute_usd + 1e-9:
            raise BudgetError("harness ceiling exceeds the absolute ceiling")
        self.path = path
        self._ceiling_usd = ceiling_usd
        self._absolute_usd = absolute_usd
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock():
            self._write(self._load())

    @property
    def ceiling_usd(self) -> float:
        return float(self._read()["ceiling_usd"])

    @property
    def spent_usd(self) -> float:
        return float(self._read()["spent_usd"])

    @property
    def remaining_usd(self) -> float:
        state = self._read()
        reserved = sum(float(item["usd"]) for item in state["reservations"])
        return max(0.0, float(state["ceiling_usd"]) - float(state["spent_usd"]) - reserved)

    def authorize(self, amount: float) -> str | None:
        if amount < 0:
            raise BudgetError("cannot reserve a negative amount")
        with self._lock():
            state = self._load()
            self._drop_stale(state)
            reserved = sum(float(item["usd"]) for item in state["reservations"])
            if float(state["spent_usd"]) + reserved + amount > float(state["ceiling_usd"]) + 1e-12:
                self._write(state)
                return None
            reservation_id = uuid.uuid4().hex
            state["reservations"].append(
                {"id": reservation_id, "usd": amount, "at": _now(), "epoch": time.time()}
            )
            self._write(state)
            return reservation_id

    def settle(self, reservation_id: str, actual: float) -> None:
        if actual < 0:
            raise BudgetError("cannot record a negative charge")
        with self._lock():
            state = self._load()
            state["reservations"] = [
                item for item in state["reservations"] if item["id"] != reservation_id
            ]
            state["spent_usd"] = float(state["spent_usd"]) + actual
            state["entries"].append({"at": _now(), "kind": "settle", "usd": actual})
            self._write(state)

    def release(self, reservation_id: str) -> None:
        with self._lock():
            state = self._load()
            state["reservations"] = [
                item for item in state["reservations"] if item["id"] != reservation_id
            ]
            state["entries"].append({"at": _now(), "kind": "release"})
            self._write(state)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "ceiling_usd": self._ceiling_usd,
                "absolute_usd": self._absolute_usd,
                "spent_usd": 0.0,
                "reservations": [],
                "entries": [],
            }
        state = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise BudgetError("budget ledger is not an object")
        absolute = float(state.get("absolute_usd", 0))
        ceiling = float(state.get("ceiling_usd", 0))
        if absolute > AUTHORIZED_CEILING_USD + 1e-9 or ceiling > absolute + 1e-9:
            raise BudgetError("budget ledger ceiling is above the authorized limit")
        if ceiling > self._ceiling_usd + 1e-9 or absolute > self._absolute_usd + 1e-9:
            raise BudgetError("budget ledger is above this process ceiling")
        if float(state.get("spent_usd", 0)) < 0:
            raise BudgetError("budget ledger spent total is negative")
        reservations = state.get("reservations")
        if not isinstance(reservations, list):
            raise BudgetError("budget ledger reservations are missing")
        state["reservations"] = reservations
        state["entries"] = state.get("entries") if isinstance(state.get("entries"), list) else []
        return state

    def _drop_stale(self, state: dict[str, Any]) -> None:
        fresh: list[dict[str, Any]] = []
        now = time.time()
        for item in state["reservations"]:
            epoch = float(item.get("epoch", now))
            if now - epoch > _STALE_RESERVATION_S:
                state["entries"].append({"at": _now(), "kind": "expire", "usd": float(item["usd"])})
            else:
                fresh.append(item)
        state["reservations"] = fresh

    def _read(self) -> dict[str, Any]:
        with self._lock():
            return self._load()

    def _write(self, state: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)

    def _lock(self) -> _Lock:
        return _Lock(self.path.with_suffix(".lock"))


class _Lock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd: int | None = None

    def __enter__(self) -> _Lock:
        deadline = time.time() + 30
        while True:
            try:
                self._fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if self._stale():
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                if time.time() > deadline:
                    raise BudgetError("budget ledger lock timed out") from None
                time.sleep(0.05)

    def __exit__(self, *_exc: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    def _stale(self) -> bool:
        try:
            return time.time() - self.path.stat().st_mtime > _STALE_LOCK_S
        except FileNotFoundError:
            return False


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
