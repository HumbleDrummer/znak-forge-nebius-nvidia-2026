from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import nebius_provider as provider


class NebiusProviderTests(unittest.TestCase):
    def test_extract_json_accepts_plain_object(self):
        value = provider._extract_json('{"evidence":[],"unknowns":[]}')
        self.assertEqual(value["evidence"], [])

    def test_extract_json_accepts_fenced_object(self):
        fence = chr(96) * 3
        text = fence + 'json\n{"evidence":[],"unknowns":[]}\n' + fence
        value = provider._extract_json(text)
        self.assertEqual(value["unknowns"], [])

    def test_context_excludes_secret_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "solver.py").write_text(
                "def solve_bug():\n    return 'visible-marker'\n", encoding="utf-8"
            )
            (root / ".env").write_text(
                "NEBIUS_API_KEY=should-never-leave-host\n", encoding="utf-8"
            )
            request = {
                "authorized_repository": str(root),
                "task": {"goal": "fix solve_bug"},
                "baseline": {},
                "evidence": [],
            }
            context = provider.build_repository_context(request)
            self.assertIn("visible-marker", context)
            self.assertNotIn("should-never-leave-host", context)

    def test_prompt_preserves_authority_boundary(self):
        request = {
            "authorized_repository": ".",
            "task": {"goal": "repair one bug"},
            "baseline": {},
            "evidence": [],
        }
        prompt = provider.build_prompt(request, "--- FILE: a.py ---\npass\n")
        self.assertIn("engine, not you, owns repository authority", prompt)
        self.assertIn("Return EXACTLY one JSON object", prompt)

    def test_missing_api_key_fails_closed(self):
        import os
        old = os.environ.pop("NEBIUS_API_KEY", None)
        try:
            with self.assertRaisesRegex(RuntimeError, "NEBIUS_API_KEY"):
                provider.call_nebius("no network should happen")
        finally:
            if old is not None:
                os.environ["NEBIUS_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
