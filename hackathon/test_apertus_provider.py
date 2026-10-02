from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import apertus_provider as provider


class _FakeResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self._body


class ApertusProviderTests(unittest.TestCase):
    def test_extract_json_accepts_plain_object(self):
        value = provider._extract_json('{"evidence":[],"unknowns":[]}')
        self.assertEqual(value["evidence"], [])

    def test_context_excludes_secret_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "solver.py").write_text("VISIBLE = True\n", encoding="utf-8")
            (root / ".env").write_text("SECRET=never-send\n", encoding="utf-8")
            request = {"authorized_repository": str(root), "task": {"goal": "solver"}}
            context = provider.build_repository_context(request)
            self.assertIn("VISIBLE", context)
            self.assertNotIn("never-send", context)

    def test_prompt_preserves_forge_authority_boundary(self):
        request = {"authorized_repository": ".", "task": {"goal": "repair"}}
        prompt = provider.build_prompt(request, "--- FILE: a.py ---\npass\n")
        self.assertIn("engine, not you, owns repository authority", prompt)
        self.assertIn("Return EXACTLY one JSON object", prompt)

    def test_missing_key_fails_closed(self):
        old = {k: os.environ.pop(k, None) for k in (
            "CSCS_INFERENCE_API_KEY", "SWISSAI_RESEARCH_API_KEY"
        )}
        try:
            with self.assertRaisesRegex(RuntimeError, "Apertus API key"):
                provider._api_key()
        finally:
            for key, value in old.items():
                if value is not None:
                    os.environ[key] = value

    def test_live_shape_adapter_without_network(self):
        body = {
            "choices": [{
                "message": {
                    "content": '{"evidence":[],"localization":null,"hypotheses":[],"patch_plan":null,"unknowns":[]}'
                }
            }]
        }
        with patch.dict(os.environ, {"CSCS_INFERENCE_API_KEY": "test-only"}, clear=False):
            with patch.object(provider.urllib.request, "urlopen", return_value=_FakeResponse(body)) as mocked:
                value = provider.call_apertus("prompt")
        self.assertEqual(value["evidence"], [])
        request = mocked.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], provider.MODEL)
        self.assertEqual(request.headers["Authorization"], "Bearer test-only")


if __name__ == "__main__":
    unittest.main()
