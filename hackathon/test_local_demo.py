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
        self.temp = tempfile.TemporaryDirectory(prefix="zfe_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = self.root / "fixture"
        shutil.copytree(FIXTURE, self.fixture)

    def run_case(self, eol, negative=False):
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
        self.run_case("LF")

    def test_lf_negative_executes_shadow_then_rolls_back(self):
        self.run_case("LF", negative=True)

    def test_crlf_positive_executes_and_accepts(self):
        self.run_case("CRLF")

    def test_crlf_negative_executes_shadow_then_rolls_back(self):
        self.run_case("CRLF", negative=True)


    def test_strict_success_gate_checks_executed_negative_evidence(self):
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
        self.temp = tempfile.TemporaryDirectory(prefix="zfb_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        demo.init_demo_repo(FIXTURE, self.work)
        self.dest = self.root / "bound_task.json"

    def bind(self, template=POSITIVE):
        self.assertTrue(callable(getattr(demo, "bind_demo_task", None)))
        demo.bind_demo_task(template, self.work, self.dest)

    def test_binding_records_raw_bytes_and_preserves_template(self):
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
        with (self.work / "inventory.py").open("ab") as f:
            f.write(b"# unexpected change\n")
        with self.assertRaises(ValueError):
            self.bind()
        self.assertFalse(self.dest.exists())

    def test_missing_hash_is_not_repaired_into_authority(self):
        data = json.loads(POSITIVE.read_text())
        data["brain_response"]["patch_plan"]["changes"][0]["expected_sha256"] = ""
        template = self.root / "bad.json"
        template.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.bind(template)
        self.assertFalse(self.dest.exists())

    def test_inconsistent_evidence_hash_is_rejected(self):
        data = json.loads(POSITIVE.read_text())
        data["brain_response"]["evidence"][0]["sha256"] = "0" * 64
        template = self.root / "bad.json"
        template.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.bind(template)

    def test_foreign_target_is_rejected(self):
        data = json.loads(POSITIVE.read_text())
        data["brain_response"]["patch_plan"]["changes"][0]["target"] = "../outside.py"
        template = self.root / "bad.json"
        template.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.bind(template)

    def test_mixed_endings_are_rejected(self):
        path = self.work / "inventory.py"
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(raw.replace(b"\n", b"\r\n", 1))
        with self.assertRaises(ValueError):
            self.bind()
        self.assertFalse(self.dest.exists())

    def test_lf_template_pin_can_bind_crlf_copy(self):
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
        self.dest.write_bytes(b"preserve me")
        with self.assertRaises(FileExistsError):
            self.bind()
        self.assertEqual(self.dest.read_bytes(), b"preserve me")

    def test_post_binding_eol_change_still_fails_exact_engine_hash(self):
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


if __name__ == "__main__":
    unittest.main()
