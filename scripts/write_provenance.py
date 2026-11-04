"""Write docs/MEASUREMENT_PROVENANCE.md from the measured JSON bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASURED = ROOT / "artifacts" / "measured"


def main() -> None:
    files = sorted(path for path in MEASURED.rglob("*.json") if path.is_file())
    pairs = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        pairs.append(f"{path.relative_to(MEASURED).as_posix()} {digest}")
    rollup = hashlib.sha256("\n".join(pairs).encode()).hexdigest()
    rows = []
    for meta_path in sorted(MEASURED.rglob("metadata.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        score = json.loads((meta_path.parent / "score.json").read_text(encoding="utf-8"))
        rows.append(
            {
                **meta,
                "task_pass": score["task_pass"],
                "attempt": score["unauthorized_attempt"],
                "effect": score["unauthorized_effect"],
                "path": meta_path.parent.relative_to(MEASURED).as_posix(),
            }
        )
    lines = [
        "# Measurement provenance",
        "",
        "Evidence freeze for the 4 November 2026 OpenRouter runs. The hashes below were computed from the trial JSON bytes on main at `2ca957a0ee7bb9a7baae04cccac09bd4ae955343`. Production health at freeze time reported that same commit.",
        "",
        "This file is a manifest. It is not a new measurement. The trial JSON files are the evidence.",
        "",
        "## Frozen identifiers",
        "",
        "- Dataset `serqet-2026-11-04.2`",
        "- Dataset hash `66d337d04e7bb603b9dc37ca62f0556ff415e67eebbec25f6a372b5212ed1732`",
        "- Policy `khepri-authority-v1`",
        "- Runner that sent the requests: `97c1044d1f93ae26156d810964aa832de3c83401`",
        "- Results merged to main as `2ca957a0ee7bb9a7baae04cccac09bd4ae955343`",
        "- Provider OpenRouter. Models `openai/gpt-6-sol` and `anthropic/claude-sonnet-5.5`.",
        "- Temperature 0, max turns 8, max output tokens 700.",
        "- CI on that main commit: https://github.com/ybedoyab/serqet/actions/runs/41834165803",
        "- Pull request: https://github.com/ybedoyab/serqet/pull/4",
        "- Production at freeze: https://serqet-liard.vercel.app",
        "",
        "## Counts and cost",
        "",
        f"- Accepted trial directories: {len(rows)}",
        f"- Sum of cost_usd: {sum(row['cost_usd'] for row in rows):.6f}",
        "- Provider account usage observed after those runs, and not re-queried for this manifest: USD 0.5471084.",
        "",
        "| Model | Mode | Trials | Passed | Attempts | Effects | Cost USD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model in ("openai/gpt-6-sol", "anthropic/claude-sonnet-5.5"):
        for mode in ("shadow", "enforced"):
            group = [row for row in rows if row["model"] == model and row["mode"] == mode]
            if not group:
                continue
            lines.append(
                "| {model} | {mode} | {n} | {passed} | {attempts} | {effects} | {cost:.6f} |".format(
                    model=model,
                    mode=mode,
                    n=len(group),
                    passed=sum(row["task_pass"] for row in group),
                    attempts=sum(row["attempt"] for row in group),
                    effects=sum(row["effect"] for row in group),
                    cost=sum(row["cost_usd"] for row in group),
                )
            )
    lines.extend(["", "## Trial scores", "", "| Path | Pass | Attempt | Effect | Cost USD | Started |", "| --- | --- | --- | --- | ---: | --- |"])
    for row in rows:
        lines.append(
            "| `{path}` | {passed} | {attempt} | {effect} | {cost:.6f} | {started} |".format(
                path=row["path"],
                passed=row["task_pass"],
                attempt=row["attempt"],
                effect=row["effect"],
                cost=row["cost_usd"],
                started=row["started_at"],
            )
        )
    lines.extend(
        [
            "",
            "## File SHA-256",
            "",
            f"Rollup over the sorted relative-path and SHA-256 lines: `{rollup}`.",
            "",
            "```",
            *pairs,
            "```",
            "",
        ]
    )
    destination = ROOT / "docs" / "MEASUREMENT_PROVENANCE.md"
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(rollup)


if __name__ == "__main__":
    main()
