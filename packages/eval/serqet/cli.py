"""SERQET command line. Offline verification never calls a model provider."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from serqet.loader import load_scenarios
from serqet.models import dry_run_manifest, provider_key
from serqet.paths import repo_root
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

    baseline = sub.add_parser("baseline")
    baseline.add_argument("--all", action="store_true")

    run_models = sub.add_parser("run-models")
    run_models.add_argument("--model", required=True)
    run_models.add_argument("--trials", type=int, default=1)
    run_models.add_argument("--cost-cap-usd", type=float, default=0.0)
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
    bundle = public_bundle(scores)
    root = repo_root()
    write_json(root / "artifacts" / "summary.json", bundle)
    web_data = root / "apps" / "web" / "data"
    write_json(web_data / "benchmarks.json", bundle)
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
    print("verify --offline: controls separated; measurement_status=NOT_MEASURED")
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
    if not provider_key():
        print(
            "NOT_MEASURED: OPENROUTER_API_KEY or OPENAI_API_KEY is unset. "
            "No provider call was made.",
            file=sys.stderr,
        )
        return 2
    print(
        "NOT_MEASURED: a key and a positive cap were visible, but this command "
        "does not start a paid sweep from the default hackathon path. "
        "Use a dedicated pilot only after reviewing docs/EVAL_RUNBOOK.md.",
        file=sys.stderr,
    )
    return 2


def _report(source: Path, output: Path) -> int:
    bundle = public_bundle()
    runs = []
    if source.exists():
        for meta_path in sorted(source.glob("*/metadata.json")):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("kind") == "measured":
                runs.append(meta)
    if runs:
        bundle["measurement_status"] = "MEASURED"
        bundle["models"] = runs
    write_json(output, bundle)
    print(f"wrote {output} measurement_status={bundle['measurement_status']}")
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
    if relative.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    if name.endswith(".tsbuildinfo"):
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
