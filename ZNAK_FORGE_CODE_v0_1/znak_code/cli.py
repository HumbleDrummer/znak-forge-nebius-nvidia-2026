"""Command-line interface for ZNAK FORGE CODE."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from .contracts import BrainResponse, TaskContract
from .engine import ArtifactStore, ForgeEngine
from .providers import MockProvider, SubprocessProvider
from .repo import GitRepository


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("task file must contain a JSON object")
    return value


def _run_path(repository: Path, run_id: str) -> Path:
    result = repository.resolve() / ".znak" / "runs" / run_id
    if not result.is_dir():
        raise FileNotFoundError("run not found: {}".format(run_id))
    return result


def _read_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def command_orient(args: argparse.Namespace) -> int:
    run = ForgeEngine(Path(args.path)).begin("orientation only")
    ok = run.orient()
    print(json.dumps({"run_id": run.run_id, "state": run.state.value, "run_path": str(run.run_path)}))
    return 0 if ok else 2


def command_solve(args: argparse.Namespace) -> int:
    task_path = Path(args.task).resolve()
    try:
        payload = _load_json(task_path)
        contract = TaskContract.from_dict(payload.get("task_contract", payload))
    except json.JSONDecodeError:
        text = task_path.read_text(encoding="utf-8").strip()
        contract = TaskContract(goal=text, explicit_requirements=[text])
        payload = {}
    if args.provider_executable:
        provider = SubprocessProvider([args.provider_executable] + list(args.provider_arg or []))
    else:
        provider = MockProvider(BrainResponse.from_dict(payload.get("brain_response", {})))
    run = ForgeEngine(Path(args.path)).solve(contract, provider, apply=args.apply)
    print(
        json.dumps(
            {
                "run_id": run.run_id,
                "state": run.state.value,
                "final_status": run.final_status,
                "run_path": str(run.run_path),
            }
        )
    )
    return 0 if run.state.value == "ACCEPTED" or (not args.apply and run.last_gate and run.last_gate.allow) else 2


def command_status(args: argparse.Namespace) -> int:
    run_path = _run_path(Path(args.repo), args.run_id)
    run = _read_json(run_path / "run.json")
    print(json.dumps(run, indent=2, ensure_ascii=False))
    return 0


def command_verify(args: argparse.Namespace) -> int:
    repository = Path(args.repo).resolve()
    run_path = _run_path(repository, args.run_id)
    missing = [name for name in ArtifactStore.REQUIRED if not (run_path / name).exists()]
    receipt = _read_json(run_path / "final_receipt.json")
    diff_bytes = (run_path / "diff.patch").read_bytes() if (run_path / "diff.patch").exists() else b""
    diff_ok = hashlib.sha256(diff_bytes).hexdigest() == receipt.get("diff_sha256")
    baseline = _read_json(run_path / "baseline.json")
    try:
        head_ok = GitRepository(repository).current_head() == baseline.get("baseline_head")
    except Exception:
        head_ok = False
    result = {
        "artifact_set_complete": not missing,
        "missing_artifacts": missing,
        "recorded_diff_integrity": diff_ok,
        "baseline_head_unchanged": head_ok,
        "note": "artifact audit only; recorded test commands are not re-executed",
    }
    print(json.dumps(result, indent=2))
    return 0 if not missing and diff_ok and head_ok else 2


def command_explain(args: argparse.Namespace) -> int:
    run_path = _run_path(Path(args.repo), args.run_id)
    run = _read_json(run_path / "run.json")
    baseline = _read_json(run_path / "baseline.json")
    contract = _read_json(run_path / "task_contract.json")
    actions = _read_jsonl(run_path / "actions.jsonl")
    evidence = _read_jsonl(run_path / "evidence.jsonl")
    hypotheses = _read_jsonl(run_path / "hypotheses.jsonl")
    plan = _read_json(run_path / "patch_plan.json")
    verification = _read_json(run_path / "verification.json")
    receipt = _read_json(run_path / "final_receipt.json")
    localization = next(
        (item.get("proof") for item in reversed(actions) if item.get("action_type") == "LOCALIZATION_PROOF"),
        None,
    )
    sections = [
        ("TASK", run.get("task")),
        ("BASELINE", baseline),
        ("REQUIREMENTS", contract),
        ("LOCALIZED_TARGET", localization),
        ("EVIDENCE", evidence),
        ("HYPOTHESIS", hypotheses),
        ("PATCH", plan),
        ("TESTS", verification),
        ("UNKNOWN", contract.get("unknowns", [])),
        ("FINAL_VERDICT", receipt.get("final_status", run.get("final_status"))),
    ]
    for heading, value in sections:
        print(heading)
        print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="znak-code", description="ROBAK CODE CORE v0.1")
    subparsers = parser.add_subparsers(dest="command", required=True)

    orient = subparsers.add_parser("orient", help="capture and lock a repository baseline")
    orient.add_argument("path")
    orient.set_defaults(handler=command_orient)

    solve = subparsers.add_parser("solve", help="run the evidence-gated solve pipeline")
    solve.add_argument("path")
    solve.add_argument("--task", required=True)
    solve.add_argument("--apply", action="store_true", help="permit mutation after all gates pass")
    solve.add_argument("--provider-executable")
    solve.add_argument("--provider-arg", action="append", default=[])
    solve.set_defaults(handler=command_solve)

    for name, handler in (
        ("status", command_status),
        ("verify", command_verify),
        ("explain", command_explain),
    ):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("run_id")
        subparser.add_argument("--repo", default=".")
        subparser.set_defaults(handler=handler)
    return parser


def main(argv: List[str] = None) -> int:  # type: ignore[assignment]
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print("znak-code: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

