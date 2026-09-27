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


def bind_demo_task(template: Path, work: Path, destination: Path) -> None:
    """Bind this fixture template once, before solve, without relaxing engine hashes.

    Only LF/CRLF representations of the already-pinned fixture are allowed.
    Unexpected content, missing pins and inconsistent evidence fail closed.
    """
    data = json.loads(template.read_text(encoding="utf-8"))
    brain = data["brain_response"]
    changes = brain["patch_plan"]["changes"]
    evidence = [item for item in brain["evidence"] if item["source"] == "inventory.py"]
    if len(changes) != 1 or changes[0]["target"] != "inventory.py" or len(evidence) != 1:
        raise ValueError("unsupported demo binding scope")
    target = work / "inventory.py"
    if target.is_symlink() or target.resolve().parent != work.resolve():
        raise ValueError("demo target must be a local regular file")
    raw = target.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    pin = changes[0].get("expected_sha256")
    allowed = {hashlib.sha256(value).hexdigest() for value in (lf, crlf)}
    if b"\r" in lf or raw not in (lf, crlf) or pin not in allowed:
        raise ValueError("fixture differs from pinned content beyond LF/CRLF")
    if evidence[0].get("sha256") != pin:
        raise ValueError("inconsistent demo evidence identity")
    exact_hash = hashlib.sha256(raw).hexdigest()
    changes[0]["expected_sha256"] = exact_hash
    evidence[0]["sha256"] = exact_hash
    # Never overwrite a previously prepared contract or the source template.
    with destination.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(data, indent=2) + "\n")


def demo_succeeded(positive: dict, negative: dict) -> bool:
    def check(meta, kind, code):
        values = [v for v in meta.get("verification_results", []) if v.get("kind") == kind]
        return (len(values) == 1 and values[0].get("exit_code") == code
                and values[0].get("result_class") == ("PASS" if code == 0 else "FAIL"))

    return (
        positive.get("exit_code") == 0
        and positive.get("final_status") == "ACCEPTED"
        and positive.get("mutation_status") == "APPLIED_VERIFIED"
        and positive.get("source_unchanged") is False
        and positive.get("applied_diff_present") is True
        and all(check(positive, kind, 0) for kind in ("TARGETED_TEST", "SHADOW_TEST", "REGRESSION_TESTS"))
        and negative.get("exit_code") == 2
        and negative.get("final_status") == "ROLLBACK"
        and negative.get("mutation_status") == "ROLLED_BACK"
        and negative.get("source_unchanged") is True
        and negative.get("rollback_verified") is True
        and negative.get("applied_diff_present") is True
        and negative.get("shadow_counterexample_observed") is True
        and check(negative, "TARGETED_TEST", 0)
        and check(negative, "SHADOW_TEST", 1)
        and check(negative, "REGRESSION_TESTS", 1)
    )


def scenario(name: str, task: Path, evidence_root: Path, fixture: Path, core: Path):
    out = evidence_root / name
    work = out / "demo_repo"
    out.mkdir(parents=True, exist_ok=True)
    init_demo_repo(fixture, work)
    before = sha256(work / "inventory.py")
    bound_task = out / "bound_task.json"
    bind_demo_task(task, work, bound_task)

    started = time.perf_counter()
    result = run(
        [
            sys.executable,
            "-m",
            "znak_code",
            "solve",
            str(work),
            "--task",
            str(bound_task),
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
    receipt = {}
    if run_dirs:
        shutil.copytree(run_dirs[0], out / "run_artifacts")
        receipt = json.loads((run_dirs[0] / "final_receipt.json").read_text(encoding="utf-8"))
        final_status = receipt.get("final_status")
        mutation_status = receipt.get("mutation_status")

    results = receipt.get("verification", {}).get("results", [])
    diff_file = out / "run_artifacts" / "diff.patch"
    meta = {
        "scenario": name,
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "source_unchanged": before == after,
        "final_status": final_status,
        "mutation_status": mutation_status,
        "template_sha256": sha256(task),
        "bound_task_sha256": sha256(bound_task),
        "verification_results": [
            {key: item.get(key) for key in ("kind", "result_class", "exit_code")}
            for item in results
        ],
        "rollback_verified": receipt.get("rollback", {}).get("verified", False),
        "applied_diff_present": diff_file.is_file() and diff_file.stat().st_size > 0,
        "shadow_counterexample_observed": any(
            item.get("kind") == "SHADOW_TEST"
            and item.get("exit_code") == 1
            and "ValueError not raised" in item.get("stderr_summary", "")
            for item in results
        ),
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

    ok = demo_succeeded(positive, negative)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
