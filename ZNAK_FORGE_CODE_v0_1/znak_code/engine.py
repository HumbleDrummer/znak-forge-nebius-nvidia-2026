"""Deterministic evidence-gated engine for one coherent patch transaction."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import (
    BrainRequest,
    BrainResponse,
    ChangeBudget,
    EvidenceItem,
    GateDecision,
    Hypothesis,
    LocalizationProof,
    PatchPlan,
    RunState,
    TaskContract,
)
from .providers import BrainProvider
from .repo import (
    CommandExecutor,
    GitRepository,
    changed_line_count,
    python_changed_functions,
    sha256_bytes,
    unified_patch,
    utc_now,
)


class IllegalTransition(RuntimeError):
    pass


ENGINE_CHANGE_BUDGET_CEILING = ChangeBudget(
    max_files=3,
    max_new_files=1,
    max_changed_functions=5,
    max_changed_loc=120,
)
ENGINE_MAX_VERIFICATION_TIMEOUT_SECONDS = 120


ALLOWED_TRANSITIONS = {
    RunState.BOOT: {RunState.ORIENT},
    RunState.ORIENT: {RunState.BASELINE, RunState.BLOCKED},
    RunState.BASELINE: {RunState.REQUIREMENT_RECOVERY, RunState.BLOCKED},
    RunState.REQUIREMENT_RECOVERY: {RunState.LOCALIZE, RunState.UNKNOWN},
    RunState.LOCALIZE: {RunState.HYPOTHESIS, RunState.UNKNOWN, RunState.BLOCKED},
    RunState.HYPOTHESIS: {RunState.PATCH_PLAN, RunState.UNKNOWN, RunState.BLOCKED},
    RunState.PATCH_PLAN: {RunState.MUTATION_GATE, RunState.LOCALIZE, RunState.UNKNOWN},
    RunState.MUTATION_GATE: {
        RunState.APPLY,
        RunState.FINAL_REVIEW,
        RunState.BLOCKED,
        RunState.UNKNOWN,
        RunState.LOCALIZE,
    },
    RunState.APPLY: {RunState.VERIFY_FUNCTIONAL, RunState.ROLLBACK, RunState.BLOCKED},
    RunState.VERIFY_FUNCTIONAL: {RunState.VERIFY_CONTRACT},
    RunState.VERIFY_CONTRACT: {RunState.VERIFY_SHADOW},
    RunState.VERIFY_SHADOW: {RunState.FINAL_REVIEW},
    RunState.FINAL_REVIEW: {
        RunState.ACCEPTED,
        RunState.ROLLBACK,
        RunState.UNKNOWN,
        RunState.BLOCKED,
    },
    RunState.ACCEPTED: set(),
    RunState.ROLLBACK: set(),
    RunState.BLOCKED: set(),
    RunState.UNKNOWN: set(),
}


class ArtifactStore:
    REQUIRED = {
        "run.json": {},
        "task_contract.json": {},
        "baseline.json": {},
        "evidence.jsonl": None,
        "hypotheses.jsonl": None,
        "actions.jsonl": None,
        "patch_plan.json": {},
        "verification.json": {},
        "final_receipt.json": {},
        "diff.patch": None,
    }

    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=False)
        for name, default in self.REQUIRED.items():
            target = self.path / name
            if default is None:
                target.write_text("", encoding="utf-8")
            else:
                self.write_json(name, default)

    def write_json(self, name: str, value: Any) -> None:
        target = self.path / name
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(str(temporary), str(target))

    def append_jsonl(self, name: str, value: Any) -> None:
        with (self.path / name).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")

    def write_text(self, name: str, value: str) -> None:
        target = self.path / name
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(value, encoding="utf-8")
        os.replace(str(temporary), str(target))


class RetryTracker:
    """An equivalent attempt needs new evidence before a third execution."""

    def __init__(self):
        self._seen: Dict[str, Tuple[int, int, str]] = {}

    def record(
        self, fingerprint: str, result_class: str, evidence_version: int
    ) -> Tuple[str, int]:
        previous = self._seen.get(fingerprint)
        if previous is None or previous[1] != evidence_version or previous[2] != result_class:
            count = 1
        else:
            count = previous[0] + 1
        self._seen[fingerprint] = (count, evidence_version, result_class)
        if count >= 3:
            return "BLOCKED_LOOP_DETECTED", count
        if count == 2:
            return "RETRY_WITHOUT_INFORMATION_GAIN", count
        return "OK", count


class ForgeEngine:
    def __init__(self, repository: Path):
        self.repository = Path(repository).resolve()

    def begin(self, task: str) -> "ForgeRun":
        run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:10]
        run_path = self.repository / ".znak" / "runs" / run_id
        return ForgeRun(self.repository, run_id, run_path, task)

    def solve(
        self,
        contract: TaskContract,
        provider: BrainProvider,
        apply: bool = False,
    ) -> "ForgeRun":
        run = self.begin(contract.goal)
        if not run.orient():
            return run
        run.recover_requirements(contract)
        request = BrainRequest(
            task=contract.to_dict(),
            baseline=run.baseline or {},
            evidence=list(run.evidence_dicts),
            authorized_repository=str(self.repository),
        )
        try:
            response = provider.complete(request)
        except Exception as exc:
            run.unknown("PROVIDER_ERROR: {}".format(exc))
            return run
        run.consume_response(response)
        if (
            run.state == RunState.LOCALIZE
            and run.last_gate
            and not run.last_gate.allow
        ):
            run.block(run.last_gate.reason)
            return run
        if run.state != RunState.MUTATION_GATE or not run.last_gate or not run.last_gate.allow:
            return run
        if not apply:
            run.finish_dry_run()
            return run
        if run.apply_patch():
            run.verify()
        return run


class ForgeRun:
    def __init__(self, repository: Path, run_id: str, run_path: Path, task: str):
        self.repository = repository
        self.run_id = run_id
        self.task = task
        self.started_at = utc_now()
        self.state = RunState.BOOT
        self.repo = GitRepository(repository)
        self.executor = CommandExecutor(repository)
        self.store = ArtifactStore(run_path)
        self.baseline: Optional[Dict[str, Any]] = None
        self.contract: Optional[TaskContract] = None
        self.evidence: Dict[str, EvidenceItem] = {}
        self.evidence_dicts: List[Dict[str, Any]] = []
        self.localization: Optional[LocalizationProof] = None
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.plan: Optional[PatchPlan] = None
        self.last_gate: Optional[GateDecision] = None
        self._backups: Dict[str, Optional[bytes]] = {}
        self._attempted_diff = ""
        self._verification: Dict[str, Any] = {}
        self._retry = RetryTracker()
        self.mutation_status = "NOT_ATTEMPTED"
        self.final_status = "IN_PROGRESS"
        self.trajectory = {
            "files_read": 0,
            "files_re_read": 0,
            "commands_run": 0,
            "repeated_commands": 0,
            "patch_attempts": 0,
            "rollbacks": 0,
            "hypotheses_falsified": 0,
            "new_evidence_count": 0,
        }
        self._write_run()

    @property
    def run_path(self) -> Path:
        return self.store.path

    def _write_run(self) -> None:
        self.store.write_json(
            "run.json",
            {
                "run_id": self.run_id,
                "repository_absolute_path": str(self.repository),
                "start_time": self.started_at,
                "task": self.task,
                "state": self.state.value,
                "mutation_status": self.mutation_status,
                "final_status": self.final_status,
                "source_files_inspected": sorted(
                    {item.source for item in self.evidence.values() if item.source}
                ),
                "trajectory_entropy": self.trajectory,
            },
        )

    def _action(self, action_type: str, **details: Any) -> None:
        value = {"at": utc_now(), "action_type": action_type}
        value.update(details)
        self.store.append_jsonl("actions.jsonl", value)

    def transition(self, target: RunState, reason: str) -> None:
        if target not in ALLOWED_TRANSITIONS[self.state]:
            raise IllegalTransition("illegal transition {} -> {}".format(self.state.value, target.value))
        previous = self.state
        self.state = target
        self._action(
            "STATE_TRANSITION", from_state=previous.value, to_state=target.value, reason=reason
        )
        self._write_run()

    def orient(self) -> bool:
        self.transition(RunState.ORIENT, "start bounded repository orientation")
        try:
            self.baseline = self.repo.baseline()
            topology = self.repo.topology()
        except Exception as exc:
            self._action("BASELINE_INSPECTION", result="FAIL", error=str(exc))
            self.transition(RunState.BLOCKED, "BLOCKED_REPOSITORY_ORIENTATION")
            self._finish("BLOCKED_REPOSITORY_ORIENTATION")
            return False
        self.store.write_json("baseline.json", self.baseline)
        self._action(
            "BASELINE_INSPECTION",
            result="PASS",
            commands=[
                ["git", "rev-parse", "HEAD"],
                ["git", "branch", "--show-current"],
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                ["git", "diff", "--no-ext-diff", "--binary"],
            ],
            topology=topology,
        )
        if self.baseline["dirty"]:
            self.transition(RunState.BLOCKED, "BLOCKED_DIRTY_WORKTREE")
            self._finish("BLOCKED_DIRTY_WORKTREE")
            return False
        self.transition(RunState.BASELINE, "clean baseline locked")
        return True

    def recover_requirements(self, contract: TaskContract) -> None:
        self.transition(RunState.REQUIREMENT_RECOVERY, "task converted to explicit contract")
        self.contract = contract
        self.store.write_json("task_contract.json", contract.to_dict())

    def add_evidence(self, item: EvidenceItem) -> None:
        if not item.observed_at:
            item.observed_at = utc_now()
        if item.evidence_id in self.evidence:
            self.trajectory["files_re_read"] += 1
        else:
            self.trajectory["new_evidence_count"] += 1
            if item.source:
                self.trajectory["files_read"] += 1
        self.evidence[item.evidence_id] = item
        self.evidence_dicts.append(item.to_dict())
        self.store.append_jsonl("evidence.jsonl", item.to_dict())
        self._write_run()

    def localize(
        self, proof: Optional[LocalizationProof], evidence: Optional[List[EvidenceItem]] = None
    ) -> None:
        self.transition(RunState.LOCALIZE, "progressive evidence cone narrowed")
        for item in evidence or []:
            self.add_evidence(item)
        self.localization = proof
        self._action(
            "LOCALIZATION_PROOF",
            result="RECORDED" if proof else "MISSING",
            proof=proof.to_dict() if proof else None,
        )

    def form_hypotheses(self, hypotheses: List[Hypothesis]) -> None:
        self.transition(RunState.HYPOTHESIS, "hypothesis ledger opened before patch planning")
        for hypothesis in hypotheses:
            self.hypotheses[hypothesis.hypothesis_id] = hypothesis
            self.store.append_jsonl("hypotheses.jsonl", hypothesis.to_dict())

    def plan_patch(self, plan: Optional[PatchPlan]) -> None:
        self.transition(RunState.PATCH_PLAN, "proof-carrying patch prepared")
        self.plan = plan
        self.store.write_json("patch_plan.json", plan.to_dict() if plan else {})

    def consume_response(self, response: BrainResponse) -> None:
        self.localize(response.localization, response.evidence)
        if not response.localization:
            self.unknown("LOCALIZATION_GATE_UNKNOWN")
            return
        self.form_hypotheses(response.hypotheses)
        if not response.hypotheses:
            self.unknown("HYPOTHESIS_MISSING")
            return
        self.plan_patch(response.patch_plan)
        if not response.patch_plan:
            self.unknown("PATCH_PLAN_MISSING")
            return
        self.mutation_gate()

    def _gate_failure(self, reason: str, details: List[str], target: RunState) -> GateDecision:
        decision = GateDecision(False, reason, details)
        self.last_gate = decision
        self._action("MUTATION_GATE", result="DENY", decision=decision.to_dict())
        self.transition(target, reason)
        if target in {RunState.BLOCKED, RunState.UNKNOWN}:
            self._finish(reason)
        return decision

    def mutation_gate(self) -> GateDecision:
        self.transition(RunState.MUTATION_GATE, "evaluate authority and proof gates")
        if (
            not self.baseline
            or self.repo.current_head() != self.baseline["baseline_head"]
            or bool(self.repo.working_status())
        ):
            return self._gate_failure("BLOCKED_STALE_BASELINE", [], RunState.BLOCKED)
        if not self.localization or not self.localization.complete():
            return self._gate_failure(
                "LOCALIZATION_GATE_UNKNOWN", ["localization proof incomplete"], RunState.UNKNOWN
            )
        missing_evidence = [
            ref for ref in self.localization.evidence_refs if ref not in self.evidence
        ]
        semantic_evidence = [
            self.evidence[ref]
            for ref in self.localization.evidence_refs
            if ref in self.evidence and self.evidence[ref].carries_semantic_evidence
        ]
        if missing_evidence or not semantic_evidence:
            return self._gate_failure(
                "LOCALIZATION_GATE_UNKNOWN",
                ["missing evidence: {}".format(", ".join(missing_evidence))]
                if missing_evidence
                else ["hash equality is not semantic evidence"],
                RunState.UNKNOWN,
            )
        without_falsifier = [
            item.hypothesis_id for item in self.hypotheses.values() if not item.falsifier.strip()
        ]
        if not self.hypotheses or without_falsifier:
            return self._gate_failure(
                "HYPOTHESIS_FALSIFIER_REQUIRED", without_falsifier, RunState.UNKNOWN
            )
        if not self.plan or not self.plan.items or not self.plan.changes:
            return self._gate_failure("PROOF_CARRYING_PATCH_MISSING", [], RunState.UNKNOWN)

        targets = {change.target for change in self.plan.changes}
        if self.localization.target_file not in targets:
            return self._gate_failure(
                "PROOF_CARRYING_PATCH_INVALID",
                ["localized target is absent from the patch"],
                RunState.UNKNOWN,
            )
        new_files = 0
        changed_loc = 0
        changed_function_ids = set()
        validation_errors: List[str] = []
        for change in self.plan.changes:
            try:
                target = self.repo.resolve_target(change.target)
            except ValueError as exc:
                validation_errors.append(str(exc))
                continue
            if target.exists():
                if not target.is_file():
                    validation_errors.append(
                        "target is not a regular file: {}".format(change.target)
                    )
                    continue
                try:
                    before = target.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    validation_errors.append(
                        "target cannot be read as UTF-8: {} ({})".format(
                            change.target, type(exc).__name__
                        )
                    )
                    continue
            else:
                before = ""
                new_files += 1
                if not target.parent.is_dir():
                    validation_errors.append(
                        "parent directory must already exist: {}".format(change.target)
                    )
                    continue
            changed_loc += changed_line_count(before, change.content)
            if target.suffix.casefold() == ".py":
                derived_functions = python_changed_functions(before, change.content)
            else:
                derived_functions = {"module"} if before != change.content else set()
            declared_functions = set(change.changed_functions)
            if declared_functions != derived_functions:
                validation_errors.append(
                    "changed_functions mismatch for {}: declared={} derived={}".format(
                        change.target,
                        sorted(declared_functions),
                        sorted(derived_functions),
                    )
                )
            changed_function_ids.update(
                (change.target, function_name) for function_name in derived_functions
            )
        item_targets = {item.target for item in self.plan.items}
        for change in self.plan.changes:
            if change.target not in item_targets:
                validation_errors.append(
                    "file change has no proof-carrying patch item: {}".format(change.target)
                )
        for item in self.plan.items:
            if item.target not in targets:
                validation_errors.append("patch item target has no file change: {}".format(item.target))
            if not item.requirement_refs or not item.evidence_refs or not item.hypothesis_ref:
                validation_errors.append("patch item mapping incomplete: {}".format(item.patch_item_id))
            if item.hypothesis_ref not in self.hypotheses:
                validation_errors.append("unknown hypothesis: {}".format(item.hypothesis_ref))
            if any(ref not in self.evidence for ref in item.evidence_refs):
                validation_errors.append("patch item cites unknown evidence: {}".format(item.patch_item_id))
            if not item.verification_refs:
                validation_errors.append("patch item lacks verification refs: {}".format(item.patch_item_id))
        verification_ids = {item.verification_id for item in self.plan.verifications}
        known_requirement_refs = set()
        if self.contract:
            known_requirement_refs.update(
                "R{}".format(index + 1)
                for index in range(len(self.contract.explicit_requirements))
            )
            known_requirement_refs.update(
                "A{}".format(index + 1)
                for index in range(len(self.contract.acceptance_conditions))
            )
            known_requirement_refs.update(
                "I{}".format(index + 1)
                for index in range(len(self.contract.implicit_requirement_candidates))
            )
        for item in self.plan.items:
            if any(ref not in verification_ids for ref in item.verification_refs):
                validation_errors.append("patch item cites unknown verification: {}".format(item.patch_item_id))
            if any(ref not in known_requirement_refs for ref in item.requirement_refs):
                validation_errors.append("patch item cites unknown requirement: {}".format(item.patch_item_id))
        if new_files and len(self.plan.abstraction_tax) < new_files:
            validation_errors.append("new files require an abstraction-tax record")
        if validation_errors:
            return self._gate_failure("PROOF_CARRYING_PATCH_INVALID", validation_errors, RunState.UNKNOWN)

        budget = self.plan.budget
        effective_budget = ChangeBudget(
            max_files=min(budget.max_files, ENGINE_CHANGE_BUDGET_CEILING.max_files),
            max_new_files=min(
                budget.max_new_files, ENGINE_CHANGE_BUDGET_CEILING.max_new_files
            ),
            max_changed_functions=min(
                budget.max_changed_functions,
                ENGINE_CHANGE_BUDGET_CEILING.max_changed_functions,
            ),
            max_changed_loc=min(
                budget.max_changed_loc, ENGINE_CHANGE_BUDGET_CEILING.max_changed_loc
            ),
        )
        over_budget = []
        if len(targets) > effective_budget.max_files:
            over_budget.append("files")
        if new_files > effective_budget.max_new_files:
            over_budget.append("new_files")
        if len(changed_function_ids) > effective_budget.max_changed_functions:
            over_budget.append("changed_functions")
        if changed_loc > effective_budget.max_changed_loc:
            over_budget.append("changed_loc")
        if over_budget:
            return self._gate_failure("CHANGE_BUDGET_EXCEEDED", over_budget, RunState.LOCALIZE)

        decision = GateDecision(
            True,
            "MUTATION_EARNED",
            [
                "files={}".format(len(targets)),
                "new_files={}".format(new_files),
                "changed_functions={}".format(len(changed_function_ids)),
                "changed_loc={}".format(changed_loc),
            ],
        )
        self.last_gate = decision
        self._action("MUTATION_GATE", result="ALLOW", decision=decision.to_dict())
        return decision

    def record_retry(
        self, action_type: str, target: str, relevant_input: str, result_class: str
    ) -> str:
        fingerprint = "\x1f".join((action_type, target, relevant_input))
        status, count = self._retry.record(
            fingerprint, result_class, self.trajectory["new_evidence_count"]
        )
        if count > 1:
            self.trajectory["repeated_commands"] += 1
        self._action(
            "RETRY_CHECK",
            fingerprint=sha256_bytes(fingerprint.encode("utf-8")),
            result_class=result_class,
            repetition=count,
            status=status,
        )
        self._write_run()
        return status

    def finish_dry_run(self) -> None:
        self.transition(RunState.FINAL_REVIEW, "dry-run refuses source mutation")
        self.transition(RunState.UNKNOWN, "DRY_RUN_NO_SOURCE_MUTATION")
        self._finish("DRY_RUN_NO_SOURCE_MUTATION")

    def _run_command(self, argv: List[str], timeout_seconds: int, purpose: str) -> Dict[str, Any]:
        result = self.executor.run(argv, timeout_seconds)
        self.trajectory["commands_run"] += 1
        value = result.to_dict()
        value["purpose"] = purpose
        self._action("COMMAND", **value)
        self._write_run()
        return value

    def apply_patch(self) -> bool:
        if not self.last_gate or not self.last_gate.allow or not self.plan:
            raise RuntimeError("mutation gate has not allowed this patch")
        if (
            self.repo.current_head() != self.baseline["baseline_head"]  # type: ignore[index]
            or bool(self.repo.working_status())
        ):
            self.transition(RunState.BLOCKED, "BLOCKED_STALE_BASELINE")
            self._finish("BLOCKED_STALE_BASELINE")
            return False
        self.transition(RunState.APPLY, "begin one coherent mutation transaction")
        self.trajectory["patch_attempts"] += 1
        attempted: List[Dict[str, str]] = []
        try:
            for change in self.plan.changes:
                target = self.repo.resolve_target(change.target)
                before_bytes = target.read_bytes() if target.exists() else None
                if change.expected_sha256:
                    current_hash = sha256_bytes(before_bytes or b"")
                    if current_hash != change.expected_sha256:
                        raise RuntimeError("target identity changed: {}".format(change.target))
                self._backups[change.target] = before_bytes
                before = (before_bytes or b"").decode("utf-8")
                attempted.append(
                    {
                        "target": change.target,
                        "before": before,
                        "after": change.content,
                        "existed": "true" if before_bytes is not None else "false",
                    }
                )
            self._attempted_diff = unified_patch(attempted)
            self.store.write_text("diff.patch", self._attempted_diff)
            for change in self.plan.changes:
                target = self.repo.resolve_target(change.target)
                target.write_text(change.content, encoding="utf-8")
            self.mutation_status = "APPLIED_PENDING_VERIFICATION"
            self._action(
                "PATCH_APPLY",
                result="APPLIED",
                changed_files=[item.target for item in self.plan.changes],
                diff_sha256=sha256_bytes(self._attempted_diff.encode("utf-8")),
            )
            self._write_run()
        except Exception as exc:
            self._action("PATCH_APPLY", result="FAIL", error=str(exc))
            self._rollback("PATCH_APPLY_FAILED")
            return False

        syntax_failures = []
        for change in self.plan.changes:
            if not change.target.endswith(".py"):
                continue
            try:
                compile(change.content, change.target, "exec")
                self._action("SYNTAX_GATE", target=change.target, result="PASS")
            except Exception as exc:
                location = getattr(exc, "lineno", None)
                syntax_failures.append(
                    "{}:{}".format(change.target, location if location is not None else type(exc).__name__)
                )
                self._action(
                    "SYNTAX_GATE", target=change.target, result="FAIL", error=str(exc)
                )
        for argv in self.plan.syntax_commands:
            try:
                result = self._run_command(argv, 60, "SYNTAX_STATIC_GATE")
                if result["exit_code"] != 0:
                    syntax_failures.append("command: {}".format(argv))
            except Exception as exc:
                syntax_failures.append(
                    "command rejected/failed: {} ({})".format(argv, type(exc).__name__)
                )
                self._action(
                    "SYNTAX_GATE", target=argv, result="FAIL", error=str(exc)
                )
        if syntax_failures:
            self._verification = {"syntax_static_gate": "FAIL", "failures": syntax_failures}
            self.store.write_json("verification.json", self._verification)
            self._rollback("SYNTAX_STATIC_GATE_FAILED")
            return False
        return True

    @staticmethod
    def _verdict(results: List[Dict[str, Any]], missing: str = "UNKNOWN") -> str:
        if not results:
            return missing
        return "PASS" if all(item["exit_code"] == 0 for item in results) else "FAIL"

    def verify(self) -> None:
        if not self.plan or not self.contract:
            raise RuntimeError("verification requires a patch plan and task contract")
        self.transition(RunState.VERIFY_FUNCTIONAL, "run narrowest functional checks first")
        results: List[Dict[str, Any]] = []
        for spec in self.plan.verifications:
            try:
                timeout_seconds = min(
                    max(int(spec.timeout_seconds), 1),
                    ENGINE_MAX_VERIFICATION_TIMEOUT_SECONDS,
                )
                value = self._run_command(
                    spec.argv, timeout_seconds, "{}_{}".format(spec.kind, spec.verification_id)
                )
            except Exception as exc:
                value = {
                    "argv": spec.argv,
                    "cwd": str(self.repository),
                    "exit_code": None,
                    "result_class": "BLOCKED",
                    "stderr_summary": str(exc),
                }
                self._action("COMMAND_REJECTED", purpose=spec.verification_id, error=str(exc))
            value.update(
                {
                    "verification_id": spec.verification_id,
                    "kind": spec.kind.upper(),
                    "requirement_refs": spec.requirement_refs,
                }
            )
            results.append(value)

        targeted = [item for item in results if item["kind"] == "TARGETED_TEST"]
        related = [item for item in results if item["kind"] == "RELATED_TESTS"]
        regression = [item for item in results if item["kind"] == "REGRESSION_TESTS"]
        functional_result = self._verdict(targeted)
        related_result = self._verdict(related, "NOT_APPLICABLE")
        regression_result = self._verdict(regression, "NOT_APPLICABLE")

        self.transition(RunState.VERIFY_CONTRACT, "map executed checks back to requirements")
        requirement_status: Dict[str, str] = {}
        requirements = []
        requirements.extend(("R{}".format(i + 1), value) for i, value in enumerate(self.contract.explicit_requirements))
        requirements.extend(("A{}".format(i + 1), value) for i, value in enumerate(self.contract.acceptance_conditions))
        supported_refs = {
            ref for item in self.evidence.values() for ref in item.supports
        }
        requirements.extend(
            ("I{}".format(i + 1), value)
            for i, value in enumerate(self.contract.implicit_requirement_candidates)
            if "I{}".format(i + 1) in supported_refs
        )
        for ref, statement in requirements:
            relevant = [item for item in results if ref in item["requirement_refs"]]
            if not relevant:
                status = "UNKNOWN"
            elif any(item["exit_code"] != 0 for item in relevant):
                status = "VIOLATED"
            else:
                status = "SATISFIED"
            requirement_status[ref] = status
        contract_result = (
            "PASS"
            if all(status == "SATISFIED" for status in requirement_status.values())
            else "FAIL"
            if any(status == "VIOLATED" for status in requirement_status.values())
            else "UNKNOWN"
        )
        if not requirement_status:
            contract_result = "UNKNOWN"

        self.transition(RunState.VERIFY_SHADOW, "run neighboring counterexample checks")
        shadow = [item for item in results if item["kind"] == "SHADOW_TEST"]
        shadow_result = self._verdict(shadow)

        self.transition(RunState.FINAL_REVIEW, "independent verdicts and root-cause check")
        planned_targets = {item.target for item in self.plan.changes}
        status_targets = {self.repo.status_path(line) for line in self.repo.working_status()}
        target_content_intact = all(
            self.repo.resolve_target(item.target).is_file()
            and self.repo.resolve_target(item.target).read_text(encoding="utf-8") == item.content
            for item in self.plan.changes
        )
        baseline_integrity = (
            "PASS"
            if self.repo.current_head() == self.baseline["baseline_head"]  # type: ignore[index]
            and status_targets.issubset(planned_targets)
            and target_content_intact
            else "FAIL"
        )
        root_cause_answers = {
            "observed_symptom": self.localization.failure_or_requirement if self.localization else "UNKNOWN",
            "mechanism": self.hypotheses[next(iter(self.hypotheses))].statement
            if self.hypotheses
            else "UNKNOWN",
            "owner": self.localization.target_symbol_or_region if self.localization else "UNKNOWN",
            "mechanism_change": self.plan.items[0].expected_effect if self.plan.items else "UNKNOWN",
            "counterexample": shadow[0]["verification_id"] if shadow else "UNKNOWN",
        }
        root_cause_result = (
            "PASS"
            if all(value != "UNKNOWN" and bool(value) for value in root_cause_answers.values())
            and shadow_result == "PASS"
            and functional_result == "PASS"
            else "UNKNOWN"
        )
        stale_test_review = {
            "changed_semantic_exercised": functional_result == "PASS",
            "obsolete_test_risk_checked": regression_result in {"PASS", "NOT_APPLICABLE"},
            "new_neighbor_case_present": shadow_result == "PASS",
        }
        self._verification = {
            "results": results,
            "requirement_status": requirement_status,
            "stale_missing_test_review": stale_test_review,
            "root_cause_check": root_cause_answers,
            "verdicts": {
                "functional_result": functional_result,
                "contract_result": contract_result,
                "regression_result": regression_result,
                "related_result": related_result,
                "shadow_result": shadow_result,
                "root_cause_result": root_cause_result,
                "baseline_integrity": baseline_integrity,
            },
        }
        self.store.write_json("verification.json", self._verification)
        acceptable = (
            functional_result == "PASS"
            and contract_result == "PASS"
            and regression_result in {"PASS", "NOT_APPLICABLE"}
            and related_result in {"PASS", "NOT_APPLICABLE"}
            and shadow_result == "PASS"
            and root_cause_result == "PASS"
            and baseline_integrity == "PASS"
        )
        if acceptable:
            self.mutation_status = "APPLIED_VERIFIED"
            self.transition(RunState.ACCEPTED, "all independent verdicts permit acceptance")
            self._finish("ACCEPTED")
        else:
            self._rollback("POST_MUTATION_VERIFICATION_NOT_ACCEPTED")

    def _rollback(self, reason: str) -> None:
        self.trajectory["rollbacks"] += 1
        self._action("ROLLBACK_REQUESTED", reason=reason)
        errors = []
        for relative, before in self._backups.items():
            target = self.repo.resolve_target(relative)
            try:
                if before is None:
                    if target.exists():
                        target.unlink()
                else:
                    target.write_bytes(before)
            except Exception as exc:
                errors.append("{}: {}".format(relative, exc))
        verified = True
        for relative, before in self._backups.items():
            target = self.repo.resolve_target(relative)
            if before is None:
                verified = verified and not target.exists()
            else:
                verified = verified and target.exists() and target.read_bytes() == before
        self.mutation_status = "ROLLED_BACK" if verified and not errors else "ROLLBACK_FAILED"
        self._action(
            "ROLLBACK_EXECUTED",
            result="PASS" if verified and not errors else "FAIL",
            errors=errors,
        )
        if self.state in ALLOWED_TRANSITIONS and RunState.ROLLBACK in ALLOWED_TRANSITIONS[self.state]:
            self.transition(RunState.ROLLBACK, reason)
        self._finish("ROLLBACK" if verified and not errors else "BLOCKED_ROLLBACK_FAILED")

    def unknown(self, reason: str) -> None:
        if RunState.UNKNOWN in ALLOWED_TRANSITIONS[self.state]:
            self.transition(RunState.UNKNOWN, reason)
        self._finish(reason)

    def block(self, reason: str) -> None:
        if RunState.BLOCKED in ALLOWED_TRANSITIONS[self.state]:
            self.transition(RunState.BLOCKED, reason)
        self._finish(reason)

    def _finish(self, status: str) -> None:
        self.final_status = status
        receipt = {
            "run_id": self.run_id,
            "task": self.task,
            "start_time": self.started_at,
            "finished_at": utc_now(),
            "final_state": self.state.value,
            "final_status": status,
            "baseline": self.baseline or {},
            "mutation_status": self.mutation_status,
            "actions_file": "actions.jsonl",
            "diff_file": "diff.patch",
            "diff_sha256": sha256_bytes(self._attempted_diff.encode("utf-8")),
            "verification": self._verification,
            "rollback": {
                "requested": self.trajectory["rollbacks"] > 0,
                "executed": self.mutation_status in {"ROLLED_BACK", "ROLLBACK_FAILED"},
                "verified": self.mutation_status == "ROLLED_BACK",
            },
            "trajectory_entropy": self.trajectory,
        }
        self.store.write_json("final_receipt.json", receipt)
        self._write_run()
