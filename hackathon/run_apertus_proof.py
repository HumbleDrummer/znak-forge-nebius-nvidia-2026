from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    provider = Path(__file__).resolve().parent / "apertus_provider.py"

    core = root / "ZNAK_FORGE_CODE_v0_1"
    fixture = core / "fixtures" / "demo_repo"
    if not fixture.is_dir():
        print("BLOCKED: demo fixture missing", file=sys.stderr)
        return 20

    if not args.live:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "-v", "test_apertus_provider.py"],
            cwd=str(provider.parent),
            text=True,
        )
        print(json.dumps({
            "mode": "DRY",
            "provider": "Apertus",
            "model": os.environ.get("APERTUS_MODEL", "swiss-ai/Apertus-v1.5-8B"),
            "core_modified": False,
            "test_exit_code": result.returncode,
        }, indent=2))
        return result.returncode

    if not (os.environ.get("CSCS_INFERENCE_API_KEY") or os.environ.get("SWISSAI_RESEARCH_API_KEY")):
        print(
            "BLOCKED: live Apertus key absent; no network request made.",
            file=sys.stderr,
        )
        return 21

    argv = [
        sys.executable, "-m", "znak_code", "solve", str(fixture),
        "--task", str(fixture / "task.json"),
        "--provider-executable", sys.executable,
        "--provider-arg", str(provider),
    ]
    result = subprocess.run(argv, cwd=str(core), text=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
