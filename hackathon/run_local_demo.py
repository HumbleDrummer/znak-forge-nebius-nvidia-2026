from __future__ import annotations

import hashlib
import json
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


def init_demo_repo(source: Path, dest: Path) -> None:
    shutil.copytree(source, dest)
    run(["git", "-C", dest, "init"])
    run(["git", "-C", dest, "config", "user.name", "ZNAK Demo"])
    run(["git", "-C", dest, "config", "user.email", "demo@local.invalid"])
    run(["git", "-C", dest, "add", "."])
    run(["git", "-C", dest, "commit", "-m", "demo baseline"])


def scenario(name: str, task: Path, evidence_root: Path, fixture: Path, core: Path):
    out = evidence_root / name
    work = out / "demo_repo"
    out.mkdir(parents=True, exist_ok=True)
    init_demo_repo(fixture, work)
    before = sha256(work / "inventory.py")

    started = time.perf_counter()
    result = run(
        [
            sys.executable,
            "-m",
            "znak_code",
            "solve",
            str(work),
            "--task",
            str(task),
            "--apply",
        ],
        cwd=core,
        check=False,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    (out / "solve_stdout.txt").write_text(result.stdout, encoding="utf-8")
    (out / "solve_stderr.txt").write_text(result.stderr, encoding="utf-8")

    after = sha256(work / "inventory.py")
    runs_dir = work / ".znak" / "runs"
    run_dirs = sorted(
        (p for p in runs_dir.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if runs_dir.exists() else []
    final_status = None
    mutation_status = None
    if run_dirs:
        shutil.copytree(run_dirs[0], out / "run_artifacts")
        run_json = json.loads((run_dirs[0] / "run.json").read_text(encoding="utf-8"))
        final_status = run_json.get("final_status")
        mutation_status = run_json.get("mutation_status")

    meta = {
        "scenario": name,
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "source_unchanged": before == after,
        "final_status": final_status,
        "mutation_status": mutation_status,
    }
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    core = root / "ZNAK_FORGE_CODE_v0_1"
    fixture = core / "fixtures" / "demo_repo"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_root = Path(__file__).resolve().parent / "evidence" / f"local_{stamp}"

    positive = scenario(
        "positive",
        fixture / "solve_task.json",
        evidence_root,
        fixture,
        core,
    )
    negative = scenario(
        "negative_shadow_fail",
        Path(__file__).resolve().parent / "fixtures" / "shadow_fail_task.json",
        evidence_root,
        fixture,
        core,
    )

    summary = {"positive": positive, "negative_shadow_fail": negative}
    (evidence_root / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))

    ok = (
        positive["final_status"] == "ACCEPTED"
        and positive["source_unchanged"] is False
        and negative["final_status"] != "ACCEPTED"
        and negative["source_unchanged"] is True
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
