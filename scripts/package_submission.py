"""Build the code-only submission ZIP and smoke-check the extracted tree."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    output = ROOT / "dist" / "serqet-micro1-submission.zip"
    verify = subprocess.run(
        ["uv", "run", "--project", str(ROOT / "packages" / "eval"), "serqet", "verify", "--offline"],
        cwd=ROOT,
        check=False,
    )
    if verify.returncode != 0:
        return verify.returncode
    packaged = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(ROOT / "packages" / "eval"),
            "serqet",
            "package",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
    )
    return packaged.returncode


if __name__ == "__main__":
    raise SystemExit(main())
