"""Offline regressions for exact-byte fixture binding and real shadow rollback."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import run_local_demo as demo

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "ZNAK_FORGE_CODE_v0_1"
FIXTURE = CORE / "fixtures" / "demo_repo"
POSITIVE = FIXTURE / "solve_task.json"
NEGATIVE = ROOT / "hackathon" / "fixtures" / "shadow_fail_task.json"


class DemoNewlineTests(unittest.TestCase):
    def setUp(self):
        """Prepare an isolated temporary fixture and register cleanup."""
        self.temp = tempfile.TemporaryDirectory(prefix="zfe_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = self.root / "fixture"
        shutil.copytree(FIXTURE, self.fixture)

    def run_case(self, eol, negative=False):
        """Execute one line-ending scenario and verify receipts and unchanged source templates."""
        path = self.fixture / "inventory.py"
        lf = path.read_bytes().replace(b"\r\n", b"\n")
        original = lf if eol == "LF" else lf.replace(b"\n", b"\r\n")
        path.write_bytes(original)
        name = "negative_shadow_fail" if negative else "positive"
        template = NEGATIVE if negative else POSITIVE
        template_before = template.read_bytes()
        meta = demo.scenario(name, template, self.root / "runs", self.fixture, CORE)
        folder = self.root / "runs" / name
        receipt = json.loads((folder / "run_artifacts" / "final_receipt.json").read_text())
        results = {v["kind"]: v for v in receipt["verification"].get("results", [])}
        self.assertEqual(path.read_bytes(), original, "original fixture was mutated")
        self.assertEqual(template.read_bytes(), template_before, "template was mutated")
        if negative:
            self.assertIn("SHADOW_TEST", results, "must execute shadow, not fail in apply")
            self.assertEqual(results["TARGETED_TEST"]["result_class"], "PASS")
            self.assertEqual(results["SHADOW_TEST"]["result_class"], "FAIL")
            self.assertEqual(results["SHADOW_TEST"]["exit_code"], 1)
            self.assertIn("ValueError not raised", results["SHADOW_TEST"]["stderr_summary"])
            self.assertEqual(meta["final_status"], "ROLLBACK")
            self.assertEqual(meta["mutation_status"], "ROLLED_BACK")
            self.assertTrue(receipt["rollback"]["verified"])
            self.assertEqual((folder / "demo_repo" / "inventory.py").read_bytes(), original)
            self.assertEqual(meta["exit_code"], 2)
        else:
            self.assertEqual(meta["final_status"], "ACCEPTED", receipt)
            self.assertEqual(meta["mutation_status"], "APPLIED_VERIFIED")
            self.assertEqual(meta["exit_code"], 0)
            self.assertEqual(set(results), {"TARGETED_TEST", "SHADOW_TEST", "REGRESSION_TESTS"})
            for result in results.values():
                self.assertEqual(result["result_class"], "PASS")
                self.assertEqual(result["exit_code"], 0)
            self.assertFalse(meta["source_unchanged"])
        self.assertGreater((folder / "run_artifacts" / "diff.patch").stat().st_size, 0)
        return meta, folder, original

    def test_lf_positive_executes_and_accepts(self):
        """Verify lf positive executes and accepts."""
        self.run_case("LF")

    def test_lf_negative_executes_shadow_then_rolls_back(self):
        """Verify lf negative executes shadow then rolls back."""
        self.run_case("LF", negative=True)

    def test_crlf_positive_executes_and_accepts(self):
        """Verify crlf positive executes and accepts."""
        self.run_case("CRLF")

    def test_crlf_negative_executes_shadow_then_rolls_back(self):
        """Verify crlf negative executes shadow then rolls back."""
        self.run_case("CRLF", negative=True)


    def test_strict_success_gate_checks_executed_negative_evidence(self):
        """Verify strict success gate checks executed negative evidence."""
        import copy
        positive, _, _ = self.run_case("LF")
        negative, _, _ = self.run_case("LF", negative=True)
        self.assertTrue(demo.demo_succeeded(positive, negative))
        for key, bad_value in (
            ("verification_results", []), ("rollback_verified", False),
            ("shadow_counterexample_observed", False), ("applied_diff_present", False),
            ("exit_code", 0), ("final_status", "BLOCKED"),
        ):
            with self.subTest(missing_or_wrong=key):
                broken = copy.deepcopy(negative)
                broken[key] = bad_value
                self.assertFalse(demo.demo_succeeded(positive, broken))



class DemoBindingTests(unittest.TestCase):
    def setUp(self):
        """Prepare an isolated temporary fixture and register cleanup."""
        self.temp = tempfile.TemporaryDirectory(prefix="zfb_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        demo.init_demo_repo(FIXTURE, self.work)
        self.dest = self.root / "bound_task.json"

    def bind(self, template=POSITIVE):
        """Bind a copied fixture to the selected template without modifying the template."""
        self.assertTrue(callable(getattr(demo, "bind_demo_task", None)))
        demo.bind_demo_task(template, self.work, self.dest)

    def test_binding_records_raw_bytes_and_preserves_template(self):
        """Verify binding records raw bytes and preserves template."""
        original = POSITIVE.read_bytes()
        for eol in (b"\n", b"\r\n"):
            raw = (FIXTURE / "inventory.py").read_bytes().replace(b"\r\n", b"\n").replace(b"\n", eol)
            (self.work / "inventory.py").write_bytes(raw)
            self.dest = self.root / ("bound_lf.json" if eol == b"\n" else "bound_crlf.json")
            self.bind()
            data = json.loads(self.dest.read_text())
            expected = hashlib.sha256(raw).hexdigest()
            self.assertEqual(data["brain_response"]["patch_plan"]["changes"][0]["expected_sha256"], expected)
            self.assertEqual(data["brain_response"]["evidence"][0]["sha256"], expected)
            self.assertEqual((self.work / "inventory.py").read_bytes(), raw)
        self.assertEqual(POSITIVE.read_bytes(), original)

    def test_changed_fixture_is_not_silently_rebound(self):
        """Verify changed fixture is not silently rebound."""
        with (self.work / "inventory.py").open("ab") as f:
            f.write(b"# unexpected change\n")
        with self.assertRaises(ValueError):
            self.bind()
        self.assertFalse(self.dest.exists())

    def test_missing_hash_is_not_repaired_into_authority(self):
        """Verify missing hash is not repaired into authority."""
        data = json.loads(POSITIVE.read_text())
        data["brain_response"]["patch_plan"]["changes"][0]["expected_sha256"] = ""
        template = self.root / "bad.json"
        template.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.bind(template)
        self.assertFalse(self.dest.exists())

    def test_inconsistent_evidence_hash_is_rejected(self):
        """Verify inconsistent evidence hash is rejected."""
        data = json.loads(POSITIVE.read_text())
        data["brain_response"]["evidence"][0]["sha256"] = "0" * 64
        template = self.root / "bad.json"
        template.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.bind(template)

    def test_foreign_target_is_rejected(self):
        """Verify foreign target is rejected."""
        data = json.loads(POSITIVE.read_text())
        data["brain_response"]["patch_plan"]["changes"][0]["target"] = "../outside.py"
        template = self.root / "bad.json"
        template.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.bind(template)

    def test_mixed_endings_are_rejected(self):
        """Verify mixed endings are rejected."""
        path = self.work / "inventory.py"
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(raw.replace(b"\n", b"\r\n", 1))
        with self.assertRaises(ValueError):
            self.bind()
        self.assertFalse(self.dest.exists())

    def test_lf_template_pin_can_bind_crlf_copy(self):
        """Verify lf template pin can bind crlf copy."""
        raw = (self.work / "inventory.py").read_bytes().replace(b"\r\n", b"\n")
        data = json.loads(POSITIVE.read_text())
        lf_pin = hashlib.sha256(raw).hexdigest()
        data["brain_response"]["patch_plan"]["changes"][0]["expected_sha256"] = lf_pin
        data["brain_response"]["evidence"][0]["sha256"] = lf_pin
        template = self.root / "lf_template.json"
        template.write_text(json.dumps(data))
        crlf = raw.replace(b"\n", b"\r\n")
        (self.work / "inventory.py").write_bytes(crlf)
        self.bind(template)
        bound = json.loads(self.dest.read_text())
        self.assertEqual(bound["brain_response"]["patch_plan"]["changes"][0]["expected_sha256"], hashlib.sha256(crlf).hexdigest())

    def test_existing_bound_task_is_never_overwritten(self):
        """Verify existing bound task is never overwritten."""
        self.dest.write_bytes(b"preserve me")
        with self.assertRaises(FileExistsError):
            self.bind()
        self.assertEqual(self.dest.read_bytes(), b"preserve me")

    def test_post_binding_eol_change_still_fails_exact_engine_hash(self):
        """Verify post binding eol change still fails exact engine hash."""
        path = self.work / "inventory.py"
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(raw)
        self.bind()
        changed = raw.replace(b"\n", b"\r\n")
        path.write_bytes(changed)
        # Lock a clean baseline after the edit: the old bound task must still fail.
        demo.run(["git", "-C", self.work, "add", "."])
        demo.run(["git", "-C", self.work, "commit", "--allow-empty", "-m", "changed after binding"])
        result = demo.run([demo.sys.executable, "-m", "znak_code", "solve", self.work, "--task", self.dest, "--apply"], cwd=CORE, check=False)
        self.assertNotEqual(result.returncode, 0)
        run_dir = next((self.work / ".znak" / "runs").iterdir())
        actions = (run_dir / "actions.jsonl").read_text()
        self.assertIn("target identity changed: inventory.py", actions)
        receipt = json.loads((run_dir / "final_receipt.json").read_text())
        self.assertEqual(receipt["verification"].get("results", []), [])
        self.assertNotEqual(receipt["final_status"], "ACCEPTED")
        self.assertEqual(path.read_bytes(), changed)

    def test_early_rollback_cannot_make_demo_successful(self):
        """Verify early rollback cannot make demo successful."""
        self.assertTrue(callable(getattr(demo, "demo_succeeded", None)))
        positive = {
            "final_status": "ACCEPTED", "mutation_status": "APPLIED_VERIFIED",
            "source_unchanged": False, "exit_code": 0, "applied_diff_present": True,
            "verification_results": [
                {"kind": kind, "result_class": "PASS", "exit_code": 0}
                for kind in ("TARGETED_TEST", "SHADOW_TEST", "REGRESSION_TESTS")
            ],
        }
        early = {"final_status": "ROLLBACK", "mutation_status": "ROLLED_BACK", "source_unchanged": True, "exit_code": 2}
        self.assertFalse(demo.demo_succeeded(positive, early))


class DemoInterruptedRunTests(unittest.TestCase):
    """Preserve failed-run evidence when a solver exits before its final receipt."""

    def setUp(self):
        """Isolate the fixtures and inject only the solver interruption boundary."""
        from unittest.mock import patch
        self.temp = tempfile.TemporaryDirectory(prefix="zfi_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core = self.root / "ZNAK_FORGE_CODE_v0_1"
        self.fixture = self.core / "fixtures" / "demo_repo"
        shutil.copytree(FIXTURE, self.fixture)
        self.hackathon = self.root / "hackathon"
        (self.hackathon / "fixtures").mkdir(parents=True)
        shutil.copyfile(NEGATIVE, self.hackathon / "fixtures" / "shadow_fail_task.json")
        real_run = demo.run

        def interrupted_solver(argv, **kwargs):
            """Run Git normally; substitute a real child that exits before finalization."""
            args = [str(value) for value in argv]
            if args[1:4] != ["-m", "znak_code", "solve"]:
                return real_run(argv, **kwargs)
            script = (
                "from pathlib import Path; import sys; "
                "p=Path(sys.argv[1])/'.znak'/'runs'/'interrupted'; "
                "p.mkdir(parents=True); "
                "(p/'run.json').write_text('{\"final_status\":\"ACCEPTED\"}'); "
                "print('solver stopped before receipt'); "
                "print('injected interruption',file=sys.stderr); sys.exit(17)"
            )
            return real_run([demo.sys.executable, "-c", script, args[4]], **kwargs)

        patcher = patch.object(demo, "run", side_effect=interrupted_solver)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_missing_final_receipt_preserves_metadata_without_acceptance(self):
        """An incomplete run must return failed evidence, never trust run.json alone."""
        for name, template in (("positive", POSITIVE), ("negative_shadow_fail", NEGATIVE)):
            with self.subTest(scenario=name):
                try:
                    meta = demo.scenario(name, template, self.root / "runs", self.fixture, self.core)
                except FileNotFoundError as exc:
                    self.fail("Missing receipt must preserve run_meta instead of raising: " + str(exc))
                folder = self.root / "runs" / name
                self.assertEqual(meta["exit_code"], 17)
                self.assertIsNone(meta["final_status"])
                self.assertEqual(meta["verification_results"], [])
                self.assertFalse(meta["rollback_verified"])
                self.assertTrue(meta["source_unchanged"])
                self.assertEqual(json.loads((folder / "run_meta.json").read_text()), meta)
                self.assertTrue((folder / "run_artifacts" / "run.json").is_file())
                self.assertIn("solver stopped", (folder / "solve_stdout.txt").read_text())
                self.assertIn("injected interruption", (folder / "solve_stderr.txt").read_text())
                self.assertFalse(demo.demo_succeeded(meta, meta))

    def test_interrupted_demo_writes_summary_and_returns_failure_code(self):
        """Both interrupted scenarios must still produce the summary and exit code 2."""
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch
        with patch.object(demo, "__file__", str(self.hackathon / "run_local_demo.py")):
            with redirect_stdout(StringIO()) as stream:
                try:
                    code = demo.main()
                except FileNotFoundError as exc:
                    self.fail("Missing receipt must not suppress summary.json: " + str(exc))
        self.assertEqual(code, 2)
        summaries = list((self.hackathon / "evidence").glob("local_*/summary.json"))
        self.assertEqual(len(summaries), 1)
        summary = json.loads(summaries[0].read_text())
        self.assertEqual(json.loads(stream.getvalue()), summary)
        self.assertEqual(set(summary), {"positive", "negative_shadow_fail"})
        for result in summary.values():
            self.assertEqual(result["exit_code"], 17)
            self.assertIsNone(result["final_status"])
            self.assertEqual(result["verification_results"], [])


if __name__ == "__main__":
    unittest.main()
