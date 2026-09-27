from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from znak_code.contracts import (
    BrainResponse,
    ChangeBudget,
    EvidenceItem,
    FileChange,
    Hypothesis,
    LocalizationProof,
    PatchItem,
    PatchPlan,
    RunState,
    TaskContract,
    VerificationSpec,
)
from znak_code.engine import ForgeEngine, IllegalTransition
from znak_code.providers import MockProvider, SubprocessProvider
from znak_code.repo import CommandExecutor, CommandRejected, GitRepository


def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(path), text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class EngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Test User")
        (self.repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.repo / "verify_pass.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        (self.repo / "verify_fail.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
        git(self.repo, "add", "app.py", "verify_pass.py", "verify_fail.py")
        git(self.repo, "commit", "-q", "-m", "baseline")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def contract(self) -> TaskContract:
        return TaskContract(
            goal="Change the owned value safely",
            explicit_requirements=["The value is changed."],
            acceptance_conditions=["The neighboring invariant still passes."],
        )

    def response(
        self,
        *,
        content: str = "VALUE = 2\n",
        evidence_kind: str = "SOURCE",
        falsifier: str = "If app.py does not define VALUE, the hypothesis is false.",
        budget: ChangeBudget = None,  # type: ignore[assignment]
        targeted_exit: int = 0,
        regression_exit: int = None,  # type: ignore[assignment]
        shadow_exit: int = 0,
        contract_exit: int = None,  # type: ignore[assignment]
        shadow_refs=None,
    ) -> BrainResponse:
        evidence = EvidenceItem(
            evidence_id="E1",
            source="app.py",
            locator="app.py:1",
            kind=evidence_kind,
            claim="VALUE is owned by this module.",
            supports=["R1"],
            sha256=hashlib.sha256((self.repo / "app.py").read_bytes()).hexdigest(),
        )
        localization = LocalizationProof(
            target_file="app.py",
            target_symbol_or_region="VALUE",
            failure_or_requirement="VALUE must change without adjacent regressions.",
            evidence_refs=["E1"],
            dependency_neighbors=["tests"],
            why_this_location="app.py directly defines the observed value.",
            why_not_obvious_alternatives="No other file owns the definition.",
        )
        hypothesis = Hypothesis(
            hypothesis_id="H1",
            statement="The old literal causes the observed behavior.",
            evidence_for=["E1"],
            evidence_against=[],
            falsifier=falsifier,
            expected_observation_if_true="Changing the literal makes the targeted check pass.",
        )
        verifications = [
            VerificationSpec(
                "V1",
                "TARGETED_TEST",
                [sys.executable, "verify_pass.py" if targeted_exit == 0 else "verify_fail.py"],
                ["R1"],
            ),
            VerificationSpec(
                "V2",
                "SHADOW_TEST",
                [sys.executable, "verify_pass.py" if shadow_exit == 0 else "verify_fail.py"],
                shadow_refs if shadow_refs is not None else ["A1"],
            ),
        ]
        if regression_exit is not None:
            verifications.append(
                VerificationSpec(
                    "V3",
                    "REGRESSION_TESTS",
                    [sys.executable, "verify_pass.py" if regression_exit == 0 else "verify_fail.py"],
                )
            )
        if contract_exit is not None:
            verifications.append(
                VerificationSpec(
                    "V4",
                    "CONTRACT_CHECK",
                    [sys.executable, "verify_pass.py" if contract_exit == 0 else "verify_fail.py"],
                    ["R1", "A1"],
                )
            )
        plan = PatchPlan(
            items=[
                PatchItem(
                    patch_item_id="P1",
                    target="app.py",
                    requirement_refs=["R1"],
                    evidence_refs=["E1"],
                    hypothesis_ref="H1",
                    expected_effect="Change the mechanism at its owning literal.",
                    risk="A dependent may require the old value.",
                    verification_refs=[item.verification_id for item in verifications],
                )
            ],
            changes=[
                FileChange(
                    target="app.py",
                    content=content,
                    expected_sha256=hashlib.sha256((self.repo / "app.py").read_bytes()).hexdigest(),
                    changed_functions=["module"],
                )
            ],
            verifications=verifications,
            budget=budget or ChangeBudget(),
        )
        return BrainResponse(
            evidence=[evidence],
            localization=localization,
            hypotheses=[hypothesis],
            patch_plan=plan,
        )

    def prepared_run(self, response: BrainResponse = None):  # type: ignore[assignment]
        response = response or self.response()
        run = ForgeEngine(self.repo).begin(self.contract().goal)
        self.assertTrue(run.orient())
        run.recover_requirements(self.contract())
        run.consume_response(response)
        return run

    def test_t01_clean_repository_orientation_succeeds(self):
        run = ForgeEngine(self.repo).begin("orient")
        self.assertTrue(run.orient())
        self.assertEqual(run.state, RunState.BASELINE)
        self.assertFalse(run.baseline["dirty"])

    def test_t02_dirty_repository_is_blocked_by_default(self):
        (self.repo / "app.py").write_text("VALUE = 9\n", encoding="utf-8")
        run = ForgeEngine(self.repo).begin("orient")
        self.assertFalse(run.orient())
        self.assertEqual(run.final_status, "BLOCKED_DIRTY_WORKTREE")

    def test_t03_head_change_before_mutation_blocks_apply(self):
        run = self.prepared_run()
        (self.repo / "marker.txt").write_text("new baseline\n", encoding="utf-8")
        git(self.repo, "add", "marker.txt")
        git(self.repo, "commit", "-q", "-m", "move head")
        self.assertFalse(run.apply_patch())
        self.assertEqual(run.final_status, "BLOCKED_STALE_BASELINE")
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 1\n")

    def test_t04_missing_localization_evidence_blocks_mutation(self):
        response = self.response()
        response.localization = None
        run = ForgeEngine(self.repo).solve(self.contract(), MockProvider(response), apply=True)
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.final_status, "LOCALIZATION_GATE_UNKNOWN")

    def test_t05_hypothesis_without_falsifier_blocks_mutation(self):
        run = self.prepared_run(self.response(falsifier=""))
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.final_status, "HYPOTHESIS_FALSIFIER_REQUIRED")

    def test_t06_change_budget_overflow_causes_reorientation(self):
        run = self.prepared_run(self.response(budget=ChangeBudget(max_changed_loc=0)))
        self.assertEqual(run.state, RunState.LOCALIZE)
        self.assertEqual(run.last_gate.reason, "CHANGE_BUDGET_EXCEEDED")
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 1\n")

    def test_t07_dry_run_creates_no_source_mutation(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(), MockProvider(self.response()), apply=False
        )
        self.assertEqual(run.final_status, "DRY_RUN_NO_SOURCE_MUTATION")
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 1\n")

    def test_t08_apply_produces_exact_recorded_diff(self):
        run = self.prepared_run()
        self.assertTrue(run.apply_patch())
        diff = (run.run_path / "diff.patch").read_text(encoding="utf-8")
        self.assertIn("-VALUE = 1", diff)
        self.assertIn("+VALUE = 2", diff)
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 2\n")

    def test_t09_syntax_failure_triggers_verified_rollback(self):
        run = self.prepared_run(self.response(content="def broken(:\n"))
        self.assertFalse(run.apply_patch())
        self.assertEqual(run.state, RunState.ROLLBACK)
        self.assertEqual(run.mutation_status, "ROLLED_BACK")
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 1\n")

    def test_t10_targeted_pass_and_regression_fail_is_not_accepted(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(), MockProvider(self.response(regression_exit=1)), apply=True
        )
        self.assertEqual(run.state, RunState.ROLLBACK)
        verdicts = json.loads((run.run_path / "verification.json").read_text())["verdicts"]
        self.assertEqual(verdicts["functional_result"], "PASS")
        self.assertEqual(verdicts["regression_result"], "FAIL")

    def test_t11_functional_pass_contract_violation_is_not_accepted(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(), MockProvider(self.response(contract_exit=1)), apply=True
        )
        self.assertEqual(run.state, RunState.ROLLBACK)
        verdicts = json.loads((run.run_path / "verification.json").read_text())["verdicts"]
        self.assertEqual(verdicts["functional_result"], "PASS")
        self.assertEqual(verdicts["contract_result"], "FAIL")

    def test_t12_shadow_failure_is_not_accepted(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(), MockProvider(self.response(shadow_exit=1)), apply=True
        )
        self.assertEqual(run.state, RunState.ROLLBACK)
        verdicts = json.loads((run.run_path / "verification.json").read_text())["verdicts"]
        self.assertEqual(verdicts["shadow_result"], "FAIL")

    def test_t13_three_equivalent_retries_trigger_loop_block(self):
        run = ForgeEngine(self.repo).begin("retry")
        self.assertEqual(run.record_retry("COMMAND", "app.py", "same", "FAIL"), "OK")
        self.assertEqual(
            run.record_retry("COMMAND", "app.py", "same", "FAIL"),
            "RETRY_WITHOUT_INFORMATION_GAIN",
        )
        self.assertEqual(
            run.record_retry("COMMAND", "app.py", "same", "FAIL"),
            "BLOCKED_LOOP_DETECTED",
        )

    def test_t14_changed_evidence_permits_new_attempt(self):
        run = ForgeEngine(self.repo).begin("retry")
        run.record_retry("COMMAND", "app.py", "same", "FAIL")
        run.record_retry("COMMAND", "app.py", "same", "FAIL")
        run.add_evidence(
            EvidenceItem("E2", "app.py", "line 1", "SOURCE", "A new observation")
        )
        self.assertEqual(run.record_retry("COMMAND", "app.py", "same", "FAIL"), "OK")

    def test_t15_receipt_contains_baseline_actions_diff_and_verification(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(), MockProvider(self.response()), apply=True
        )
        self.assertEqual(run.state, RunState.ACCEPTED)
        receipt = json.loads((run.run_path / "final_receipt.json").read_text())
        self.assertTrue(receipt["baseline"]["baseline_head"])
        self.assertEqual(receipt["actions_file"], "actions.jsonl")
        self.assertEqual(receipt["diff_file"], "diff.patch")
        self.assertIn("verdicts", receipt["verification"])

    def test_t16_rollback_does_not_destroy_unrelated_files(self):
        run = self.prepared_run()
        self.assertTrue(run.apply_patch())
        (self.repo / "unrelated.txt").write_text("preserve me\n", encoding="utf-8")
        run._rollback("TEST_ROLLBACK")
        self.assertEqual((self.repo / "unrelated.txt").read_text(), "preserve me\n")
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 1\n")

    def test_t17_hash_equality_is_not_semantic_truth(self):
        run = self.prepared_run(self.response(evidence_kind="HASH"))
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.last_gate.reason, "LOCALIZATION_GATE_UNKNOWN")

    def test_t18_unknown_required_acceptance_condition_blocks_accepted(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(),
            MockProvider(self.response(shadow_refs=["R1"])),
            apply=True,
        )
        self.assertEqual(run.state, RunState.ROLLBACK)
        verification = json.loads((run.run_path / "verification.json").read_text())
        self.assertEqual(verification["requirement_status"]["A1"], "UNKNOWN")
        self.assertEqual(verification["verdicts"]["contract_result"], "UNKNOWN")

    def test_illegal_direct_orient_to_apply_transition_is_rejected(self):
        run = ForgeEngine(self.repo).begin("illegal")
        run.transition(RunState.ORIENT, "test")
        with self.assertRaises(IllegalTransition):
            run.transition(RunState.APPLY, "forbidden")

    def test_subprocess_provider_exchanges_json(self):
        provider_script = self.repo / "provider.py"
        provider_script.write_text(
            "import json, sys\njson.load(sys.stdin)\njson.dump({'unknowns': ['no proposal']}, sys.stdout)\n",
            encoding="utf-8",
        )
        response = SubprocessProvider([sys.executable, str(provider_script)]).complete(
            type("Request", (), {"to_dict": lambda self: {"task": "x"}})()
        )
        self.assertEqual(response.unknowns, ["no proposal"])

    def test_worktree_change_after_gate_blocks_apply(self):
        run = self.prepared_run()
        (self.repo / "unrelated.txt").write_text("user work\n", encoding="utf-8")
        self.assertFalse(run.apply_patch())
        self.assertEqual(run.final_status, "BLOCKED_STALE_BASELINE")
        self.assertEqual((self.repo / "unrelated.txt").read_text(), "user work\n")

    def test_inline_interpreter_verification_is_rejected(self):
        with self.assertRaises(CommandRejected):
            CommandExecutor(self.repo).validate([sys.executable, "-c", "print('unsafe')"])

    def test_non_allowlisted_verification_executable_is_rejected(self):
        with self.assertRaises(CommandRejected):
            CommandExecutor(self.repo).validate(["echo", "not a verifier"])

    def test_protected_bare_test_selectors_are_rejected(self):
        executor = CommandExecutor(self.repo)
        for selector in ("..", ".git", ".GIT", ".znak"):
            with self.subTest(selector=selector):
                with self.assertRaises(CommandRejected):
                    executor.validate([sys.executable, "-m", "unittest", selector])

    def test_spoofed_qualified_python_executable_is_rejected(self):
        with self.assertRaises(CommandRejected):
            CommandExecutor(self.repo).validate(
                [str(self.repo / "tools" / "python3"), "verify_pass.py"]
            )

    def test_relative_path_to_runtime_executable_is_rejected(self):
        relative_runtime = os.path.relpath(sys.executable, start=Path.cwd())
        with self.assertRaises(CommandRejected):
            CommandExecutor(self.repo).validate([relative_runtime, "verify_pass.py"])

    def test_protected_target_cannot_be_reached_through_symlink(self):
        alias = self.repo / "metadata_alias"
        try:
            alias.symlink_to(self.repo / ".git", target_is_directory=True)
        except OSError as exc:
            self.skipTest("symlinks unavailable: {}".format(exc))
        with self.assertRaises(ValueError):
            GitRepository(self.repo).resolve_target("metadata_alias/config")

    def test_protected_target_spelling_is_case_and_windows_suffix_insensitive(self):
        repository = GitRepository(self.repo)
        for target in (".GIT/config", ".git. /config", ".ZNAK /runs/demo"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    repository.resolve_target(target)

    def test_directory_target_is_denied_by_mutation_gate(self):
        (self.repo / "folder").mkdir()
        (self.repo / "folder" / "tracked.txt").write_text("keep\n", encoding="utf-8")
        git(self.repo, "add", "folder/tracked.txt")
        git(self.repo, "commit", "-q", "-m", "add directory target")
        response = self.response()
        response.localization.target_file = "folder"
        response.patch_plan.items[0].target = "folder"
        response.patch_plan.changes[0].target = "folder"
        run = self.prepared_run(response)
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.last_gate.reason, "PROOF_CARRYING_PATCH_INVALID")

    def test_non_utf8_target_is_denied_by_mutation_gate(self):
        (self.repo / "app.py").write_bytes(b"\xff\xfe")
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-q", "-m", "add non-UTF-8 target")
        run = self.prepared_run(self.response())
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.last_gate.reason, "PROOF_CARRYING_PATCH_INVALID")

    def test_rejected_syntax_command_triggers_rollback(self):
        response = self.response()
        response.patch_plan.syntax_commands = [["bash", "-c", "exit 0"]]
        run = self.prepared_run(response)
        self.assertFalse(run.apply_patch())
        self.assertEqual(run.state, RunState.ROLLBACK)
        self.assertEqual(run.mutation_status, "ROLLED_BACK")
        self.assertEqual((self.repo / "app.py").read_text(), "VALUE = 1\n")

    def test_solve_closes_budget_reorientation_as_blocked(self):
        run = ForgeEngine(self.repo).solve(
            self.contract(),
            MockProvider(self.response(budget=ChangeBudget(max_changed_loc=0))),
            apply=True,
        )
        self.assertEqual(run.state, RunState.BLOCKED)
        self.assertEqual(run.final_status, "CHANGE_BUDGET_EXCEEDED")


    def test_unmapped_file_change_is_rejected(self):
        response = self.response()
        response.patch_plan.changes.append(
            FileChange(
                target="extra.py",
                content="EXTRA = True\n",
                changed_functions=["module"],
            )
        )
        run = self.prepared_run(response)
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.last_gate.reason, "PROOF_CARRYING_PATCH_INVALID")
        self.assertTrue(
            any(
                "file change has no proof-carrying patch item: extra.py" in detail
                for detail in run.last_gate.details
            )
        )

    def test_provider_cannot_raise_engine_change_budget_ceiling(self):
        response = self.response(
            budget=ChangeBudget(
                max_files=999,
                max_new_files=999,
                max_changed_functions=999,
                max_changed_loc=999999,
            )
        )
        for index in range(2, 5):
            target = "extra{}.py".format(index)
            response.patch_plan.items.append(
                PatchItem(
                    patch_item_id="P{}".format(index),
                    target=target,
                    requirement_refs=["R1"],
                    evidence_refs=["E1"],
                    hypothesis_ref="H1",
                    expected_effect="Exercise the engine-owned file ceiling.",
                    risk="Synthetic test change.",
                    verification_refs=["V1", "V2"],
                )
            )
            response.patch_plan.changes.append(
                FileChange(
                    target=target,
                    content="VALUE = {}\n".format(index),
                    changed_functions=["module"],
                )
            )
            response.patch_plan.abstraction_tax.append(
                {"target": target, "reason": "synthetic ceiling test"}
            )
        run = self.prepared_run(response)
        self.assertEqual(run.state, RunState.LOCALIZE)
        self.assertEqual(run.last_gate.reason, "CHANGE_BUDGET_EXCEEDED")
        self.assertIn("files", run.last_gate.details)

    def test_verification_timeout_is_clamped_to_engine_ceiling(self):
        response = self.response()
        response.patch_plan.verifications[0].timeout_seconds = 999999
        run = self.prepared_run(response)
        captured = []
        original_run_command = run._run_command

        def capture(argv, timeout_seconds, purpose):
            captured.append(timeout_seconds)
            return original_run_command(argv, timeout_seconds, purpose)

        run._run_command = capture
        self.assertTrue(run.apply_patch())
        run.verify()
        self.assertTrue(captured)
        self.assertLessEqual(max(captured), 120)

    def test_rename_from_source_into_znak_is_not_filtered_as_engine_artifact(self):
        repository = GitRepository(self.repo)
        self.assertFalse(
            repository._is_engine_artifact_status("R  app.py -> .znak/app.py")
        )
        self.assertTrue(
            repository._is_engine_artifact_status(
                "R  .znak/old.json -> .znak/new.json"
            )
        )


    def test_hidden_function_changes_are_rejected(self):
        (self.repo / "app.py").write_text(
            "\n".join(
                "def f{}():\n    return {}".format(index, index)
                for index in range(6)
            )
            + "\n",
            encoding="utf-8",
        )
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-q", "-m", "function baseline")
        response = self.response(
            content="\n".join(
                "def f{}():\n    return {}".format(index, index + 10)
                for index in range(6)
            )
            + "\n"
        )
        response.patch_plan.changes[0].changed_functions = []
        run = self.prepared_run(response)
        self.assertEqual(run.state, RunState.UNKNOWN)
        self.assertEqual(run.last_gate.reason, "PROOF_CARRYING_PATCH_INVALID")
        self.assertTrue(
            any("changed_functions mismatch for app.py" in detail for detail in run.last_gate.details)
        )

    def test_derived_function_budget_blocks_six_changed_functions(self):
        (self.repo / "app.py").write_text(
            "\n".join(
                "def f{}():\n    return {}".format(index, index)
                for index in range(6)
            )
            + "\n",
            encoding="utf-8",
        )
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-q", "-m", "function baseline")
        response = self.response(
            content="\n".join(
                "def f{}():\n    return {}".format(index, index + 10)
                for index in range(6)
            )
            + "\n"
        )
        response.patch_plan.changes[0].changed_functions = [
            "f{}".format(index) for index in range(6)
        ]
        run = self.prepared_run(response)
        self.assertEqual(run.state, RunState.LOCALIZE)
        self.assertEqual(run.last_gate.reason, "CHANGE_BUDGET_EXCEEDED")
        self.assertIn("changed_functions", run.last_gate.details)

    def test_same_named_functions_in_different_files_count_separately(self):
        response = self.response()
        response.patch_plan.changes[0].content = (
            "def read():\n    return 2\n\n"
            "def write():\n    return 2\n"
        )
        (self.repo / "app.py").write_text(
            "def read():\n    return 1\n\n"
            "def write():\n    return 1\n",
            encoding="utf-8",
        )
        for name in ("extra2.py", "extra3.py"):
            (self.repo / name).write_text(
                "def read():\n    return 1\n\n"
                "def write():\n    return 1\n",
                encoding="utf-8",
            )
        git(self.repo, "add", "app.py", "extra2.py", "extra3.py")
        git(self.repo, "commit", "-q", "-m", "collision baseline")
        response.patch_plan.changes[0].changed_functions = ["read", "write"]
        for index, name in enumerate(("extra2.py", "extra3.py"), start=2):
            response.patch_plan.items.append(
                PatchItem(
                    patch_item_id="P{}".format(index),
                    target=name,
                    requirement_refs=["R1"],
                    evidence_refs=["E1"],
                    hypothesis_ref="H1",
                    expected_effect="Exercise cross-file function accounting.",
                    risk="Synthetic test change.",
                    verification_refs=["V1", "V2"],
                )
            )
            response.patch_plan.changes.append(
                FileChange(
                    target=name,
                    content=(
                        "def read():\n    return 2\n\n"
                        "def write():\n    return 2\n"
                    ),
                    changed_functions=["read", "write"],
                )
            )
        run = self.prepared_run(response)
        self.assertEqual(run.state, RunState.LOCALIZE)
        self.assertEqual(run.last_gate.reason, "CHANGE_BUDGET_EXCEEDED")
        self.assertIn("changed_functions", run.last_gate.details)

    def test_verifier_import_does_not_leave_bytecode_artifacts(self):
        (self.repo / "helper_module.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.repo / "verify_import.py").write_text(
            "import helper_module\nraise SystemExit(0)\n",
            encoding="utf-8",
        )
        executor = CommandExecutor(self.repo)
        result = executor.run([sys.executable, "verify_import.py"])
        self.assertEqual(result.exit_code, 0)
        self.assertFalse((self.repo / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
