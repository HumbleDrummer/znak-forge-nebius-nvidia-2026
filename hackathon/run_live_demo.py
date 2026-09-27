from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, *, cwd=None, check=True):
    return subprocess.run(
        [str(x) for x in argv],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("NEBIUS_API_KEY"):
        try:
            import win32crypt
            encrypted = (
                Path(os.environ["LOCALAPPDATA"])
                / "ZNAK"
                / "secrets"
                / "nebius_api_key.dpapi"
            ).read_bytes()
            _, decrypted = win32crypt.CryptUnprotectData(
                encrypted, None, None, None, 0
            )
            os.environ["NEBIUS_API_KEY"] = decrypted.decode("utf-8")
        except Exception:
            print(
                "BLOCKED: no NEBIUS_API_KEY environment variable or local DPAPI secret. "
                "No network request was made.",
                file=sys.stderr,
            )
            return 20

    hackathon_root = Path(__file__).resolve().parent.parent
    core = hackathon_root / "ZNAK_FORGE_CODE_v0_1"
    fixture = core / "fixtures" / "demo_repo"
    provider = Path(__file__).resolve().parent / "nebius_provider.py"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence = Path(__file__).resolve().parent / "evidence" / f"live_{stamp}"
    work = evidence / "demo_repo"
    work.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture, work)

    run(["git", "-C", work, "init"])
    run(["git", "-C", work, "config", "user.name", "ZNAK Demo"])
    run(["git", "-C", work, "config", "user.email", "demo@local.invalid"])
    run(["git", "-C", work, "add", "."])
    run(["git", "-C", work, "commit", "-m", "demo baseline"])

    model = os.environ.setdefault(
        "NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b"
    )
    before = sha256(work / "inventory.py")

    argv = [
        sys.executable,
        "-m",
        "znak_code",
        "solve",
        str(work),
        "--task",
        str(work / "task.json"),
        "--provider-executable",
        sys.executable,
        "--provider-arg",
        str(provider),
    ]
    if args.apply:
        argv.append("--apply")

    started = time.perf_counter()
    result = run(argv, cwd=core, check=False)
    elapsed_ms = round((time.perf_counter() - started) * 1000)

    (evidence / "solve_stdout.txt").write_text(result.stdout, encoding="utf-8")
    (evidence / "solve_stderr.txt").write_text(result.stderr, encoding="utf-8")

    after = sha256(work / "inventory.py")
    runs_dir = work / ".znak" / "runs"
    run_dirs = sorted(
        (p for p in runs_dir.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if runs_dir.exists() else []
    if run_dirs:
        shutil.copytree(run_dirs[0], evidence / "run_artifacts")

    meta = {
        "timestamp": stamp,
        "model": model,
        "apply": args.apply,
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "source_unchanged": before == after,
    }
    (evidence / "run_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(json.dumps(meta, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
