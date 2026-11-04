"""SERQET command line. Offline verification never calls a model provider."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from serqet.budget import HARNESS_CEILING_USD, BudgetError, BudgetLedger
from serqet.evidence import evidence_problems
from serqet.harness import Limits, run_episode
from serqet.integrity import apply_trials, collect_trials, write_episode
from serqet.loader import load_scenarios
from serqet.models import dry_run_manifest
from serqet.paths import repo_root
from serqet.provider import credential
from serqet.reporting import public_bundle, write_json
from serqet.suite import run_controls, separation_problems

EXCLUDE_DIRS = {
    ".git",
    ".next",
    ".vercel",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "playwright-report",
    "test-results",
    "blob-report",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".mp4", ".mov", ".png", ".jpg", ".jpeg", ".webp", ".zip"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="serqet")
    sub = parser.add_subparsers(dest="command", required=True)

    scenarios = sub.add_parser("scenarios")
    scenarios_sub = scenarios.add_subparsers(dest="scenarios_command", required=True)
    scenarios_sub.add_parser("list")

    verify = sub.add_parser("verify")
    verify.add_argument("--offline", action="store_true")

    sub.add_parser("audit")

    baseline = sub.add_parser("baseline")
    baseline.add_argument("--all", action="store_true")

    run_models = sub.add_parser("run-models")
    run_models.add_argument("--model", required=True)
    run_models.add_argument("--provider", default="openrouter", choices=["openrouter", "openai"])
    run_models.add_argument("--mode", default="shadow", choices=["shadow", "enforced", "both"])
    run_models.add_argument("--scenarios", default="")
    run_models.add_argument("--trials", type=int, default=1)
    run_models.add_argument("--cost-cap-usd", type=float, default=0.0)
    run_models.add_argument("--input-usd-per-mtok", type=float, default=None)
    run_models.add_argument("--output-usd-per-mtok", type=float, default=None)
    run_models.add_argument("--max-turns", type=int, default=8)
    run_models.add_argument("--max-output-tokens", type=int, default=700)
    run_models.add_argument("--timeout-s", type=float, default=90)
    run_models.add_argument("--measured-dir", default="")
    run_models.add_argument("--dry-run", action="store_true")

    report = sub.add_parser("report")
    report.add_argument("--input", required=True)
    report.add_argument("--output", required=True)

    package = sub.add_parser("package")
    package.add_argument("--output", required=True)
    package.add_argument("--skip-extract-check", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "scenarios":
        return _list_scenarios()
    if args.command == "verify":
        return _verify()
    if args.command == "audit":
        return _audit()
    if args.command == "baseline":
        return _baseline()
    if args.command == "run-models":
        return _run_models(args)
    if args.command == "report":
        return _report(Path(args.input), Path(args.output))
    if args.command == "package":
        return _package(Path(args.output), extract_check=not args.skip_extract_check)
    parser.error(f"unknown command {args.command}")
    return 2


def _list_scenarios() -> int:
    for scenario in load_scenarios():
        print(f"{scenario.scenario_id}\t{scenario.family}\t{scenario.polarity}")
    return 0


def _verify() -> int:
    scores = run_controls()
    problems = separation_problems(scores)
    bundle = _published_bundle(scores)
    root = repo_root()
    write_json(root / "artifacts" / "summary.json", bundle)
    write_json(root / "apps" / "web" / "data" / "benchmarks.json", bundle)
    for scenario in bundle["scenarios"]:
        demo = {
            "kind": "simulated_demo",
            "not_model_results": True,
            "label": "SIMULATED DEMO",
            "scenario_id": scenario["scenario_id"],
            "demo": scenario["demo"],
        }
        write_json(root / "artifacts" / "demo" / f"{scenario['scenario_id']}.json", demo)
    measured = root / "artifacts" / "measured"
    measured.mkdir(parents=True, exist_ok=True)
    readme = measured / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Measured runs\n\nNo model API has been called. This directory is `NOT_MEASURED`.\n",
            encoding="utf-8",
        )
    _print_matrix(bundle)
    if problems:
        print("CONTROL SEPARATION FAILED", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"verify --offline: controls separated; measurement_status={bundle['measurement_status']}")
    return 0


def _audit() -> int:
    """Replay controls and measured trials without writing the evidence files."""
    scores = run_controls()
    problems = separation_problems(scores)
    root = repo_root()
    measured = root / "artifacts" / "measured"
    accepted, rejected = collect_trials(measured)
    problems.extend(evidence_problems(measured))
    problems.extend(rejected)
    if len(accepted) != 31:
        problems.append(f"expected 31 accepted trials, found {len(accepted)}")
    cost = sum(float(trial["cost_usd"]) for trial in accepted)
    if abs(cost - 0.547108) > 0.0000005:
        problems.append(f"cost sum {cost:.6f} does not match 0.547108")
    passed = sum(1 for trial in accepted if trial["task_pass"])
    print(f"audit accepted={len(accepted)} rejected={len(rejected)} passed={passed} cost_usd={cost:.6f}")
    for model in ("openai/gpt-6-sol", "anthropic/claude-sonnet-5.5"):
        for mode in ("shadow", "enforced"):
            rows = [trial for trial in accepted if trial["model"] == model and trial["mode"] == mode]
            if not rows:
                continue
            ok = sum(1 for trial in rows if trial["task_pass"])
            attempts = sum(1 for trial in rows if trial["unauthorized_attempt"])
            effects = sum(1 for trial in rows if trial["unauthorized_effect"])
            print(f"{model}\t{mode}\t{ok}/{len(rows)}\tattempts={attempts}\teffects={effects}")
    if problems:
        print("AUDIT FAILED", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("audit: controls separated and the frozen measured bytes still match")
    return 0


def _baseline() -> int:
    scores = run_controls()
    problems = separation_problems(scores)
    bundle = public_bundle(scores)
    _print_matrix(bundle)
    if problems:
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    return 0


def _print_matrix(bundle: dict[str, Any]) -> None:
    print("agent\tmode\tpassed\ttotal\tnote")
    for agent, modes in bundle["controls"].items():
        for mode, payload in modes.items():
            print(f"{agent}\t{mode}\t{payload['passed']}\t{payload['total']}\treference control")
    print(f"measurement_status\t{bundle['measurement_status']}")


def _published_bundle(scores: list[Any] | None = None) -> dict[str, Any]:
    bundle = public_bundle(scores)
    accepted, _rejected = collect_trials(repo_root() / "artifacts" / "measured")
    if accepted:
        return apply_trials(bundle, accepted)
    return bundle


def _run_models(args: argparse.Namespace) -> int:
    if args.dry_run:
        manifest = dry_run_manifest(args.model, args.trials)
        write_json(repo_root() / "artifacts" / "dry-run.json", manifest)
        print(
            f"dry-run: {len(manifest['prompts'])} prompts hashed for {args.model}; "
            "no provider call"
        )
        return 0
    if args.cost_cap_usd <= 0:
        print(
            "NOT_MEASURED: refusing provider calls because --cost-cap-usd is 0. "
            "Pass an explicit positive cap only when a key is already configured.",
            file=sys.stderr,
        )
        return 2
    if credential(args.provider) is None:
        env_name = "OPENROUTER_API_KEY" if args.provider == "openrouter" else "OPENAI_API_KEY"
        print(
            f"NOT_MEASURED: {env_name} is unset for provider {args.provider}. "
            "No provider call was made.",
            file=sys.stderr,
        )
        return 2
    if args.input_usd_per_mtok is None or args.output_usd_per_mtok is None:
        print(
            "NOT_MEASURED: pass --input-usd-per-mtok and --output-usd-per-mtok. "
            "Missing prices abort before the first request.",
            file=sys.stderr,
        )
        return 2
    try:
        ledger = BudgetLedger(repo_root() / "artifacts" / "budget" / "ledger.json")
    except BudgetError as exc:
        print(f"NOT_MEASURED: {exc}", file=sys.stderr)
        return 2
    print(
        "shared_budget "
        f"ceiling_usd={ledger.ceiling_usd:.2f} "
        f"spent_usd={ledger.spent_usd:.6f} "
        f"remaining_usd={ledger.remaining_usd:.6f} "
        f"process_cap_usd={min(args.cost_cap_usd, HARNESS_CEILING_USD):.2f}"
    )
    if ledger.remaining_usd <= 0:
        print("NOT_MEASURED: shared harness budget is exhausted", file=sys.stderr)
        return 2
    limits = Limits(
        max_turns=args.max_turns,
        max_output_tokens=args.max_output_tokens,
        timeout_s=args.timeout_s,
        input_usd_per_mtok=args.input_usd_per_mtok,
        output_usd_per_mtok=args.output_usd_per_mtok,
        cost_cap_usd=min(args.cost_cap_usd, HARNESS_CEILING_USD),
    )
    selected = {item for item in args.scenarios.split(",") if item}
    scenarios = [
        scenario
        for scenario in load_scenarios()
        if not selected or scenario.scenario_id in selected
    ]
    if not scenarios:
        print("NOT_MEASURED: no scenarios matched --scenarios", file=sys.stderr)
        return 2
    modes = ["shadow", "enforced"] if args.mode == "both" else [args.mode]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    slug = "".join(char if char.isalnum() else "-" for char in args.model)[:48]
    destination = Path(args.measured_dir) if args.measured_dir else (
        repo_root() / "artifacts" / "measured" / f"{stamp}-{args.provider}-{slug}"
    )
    spent = 0.0
    for scenario in scenarios:
        for mode in modes:
            for trial in range(1, args.trials + 1):
                episode = run_episode(
                    scenario,
                    mode,
                    model=args.model,
                    provider=args.provider,
                    trial=trial,
                    limits=limits,
                    spent_usd=spent,
                    ledger=ledger,
                )
                spent += episode.cost_usd
                trial_dir = destination / scenario.scenario_id / mode / f"trial-{trial}"
                write_episode(trial_dir, episode, provider=args.provider, model=args.model)
                print(
                    f"{scenario.scenario_id}\t{mode}\ttrial {trial}\t"
                    f"stop={episode.stop_reason}\tcost_usd={episode.cost_usd:.6f}"
                )
                if episode.stop_reason in {"budget_exhausted", "pricing_missing", "provider_error"}:
                    accepted, rejected = collect_trials(destination)
                    print(
                        f"NOT_MEASURED: stopped at {episode.stop_reason}. "
                        f"accepted={len(accepted)} rejected={len(rejected)}",
                        file=sys.stderr,
                    )
                    return 2
    accepted, rejected = collect_trials(destination)
    print(f"measured_dir={destination} accepted={len(accepted)} rejected={len(rejected)}")
    if not accepted:
        print("NOT_MEASURED: no trial passed integrity validation", file=sys.stderr)
        return 2
    print(
        "Cost figures are estimates or provider-reported usage, not a billing guarantee. "
        "Publish with: serqet report --input <measured-dir> --output artifacts/summary.json"
    )
    return 0


def _report(source: Path, output: Path) -> int:
    bundle = public_bundle()
    accepted, rejected = collect_trials(source)
    if not accepted:
        write_json(output, bundle)
        for item in rejected:
            print(f"rejected: {item}", file=sys.stderr)
        print(f"wrote {output} measurement_status=NOT_MEASURED")
        return 2 if rejected else 0
    published = apply_trials(bundle, accepted)
    write_json(output, published)
    write_json(repo_root() / "artifacts" / "summary.json", published)
    write_json(repo_root() / "apps" / "web" / "data" / "benchmarks.json", published)
    print(
        f"wrote {output} measurement_status=MEASURED trials={len(accepted)} "
        f"rejected={len(rejected)}"
    )
    return 0


def _package(output: Path, *, extract_check: bool) -> int:
    root = repo_root()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if not _include(relative):
                continue
            archive.write(path, relative.as_posix())
            count += 1
    size = output.stat().st_size
    print(f"wrote {output} files={count} bytes={size}")
    if size > 50 * 1024 * 1024:
        print("ZIP exceeds 50 MB", file=sys.stderr)
        return 1
    if extract_check:
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(output) as archive:
                archive.extractall(temp)
            extracted = Path(temp)
            if not (extracted / "packages" / "eval" / "pyproject.toml").is_file():
                print("extracted package is missing the eval project", file=sys.stderr)
                return 1
            if not tuple((extracted / "packages" / "eval" / "scenarios").glob("*.json")):
                print("extracted package is missing scenarios", file=sys.stderr)
                return 1
            checked = subprocess.run(
                [
                    "uv",
                    "run",
                    "--offline",
                    "--project",
                    str(extracted / "packages" / "eval"),
                    "serqet",
                    "verify",
                    "--offline",
                ],
                cwd=extracted,
                check=False,
            )
            if checked.returncode != 0:
                print("extracted tree failed offline verify", file=sys.stderr)
                return checked.returncode
    return 0


def _include(relative: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in relative.parts):
        return False
    name = relative.name
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return False
    if relative.parts[:2] == ("artifacts", "budget"):
        return False
    if relative.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    if name.endswith(".tsbuildinfo"):
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
