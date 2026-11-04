"""Load the human-authored scenario manifests."""

from __future__ import annotations

import hashlib
from functools import lru_cache

from serqet.paths import scenarios_dir
from serqet.schemas import Scenario


@lru_cache(maxsize=1)
def load_scenarios() -> tuple[Scenario, ...]:
    paths = sorted(scenarios_dir().glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no scenarios in {scenarios_dir()}")
    loaded = tuple(
        Scenario.model_validate_json(path.read_text(encoding="utf-8")) for path in paths
    )
    ids = [item.scenario_id for item in loaded]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate scenario id")
    return loaded


def dataset_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(scenarios_dir().glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
