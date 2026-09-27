"""Vendor-neutral proposal providers. The engine remains the authority boundary."""

from __future__ import annotations

import json
import subprocess
from typing import List, Protocol

from .contracts import BrainRequest, BrainResponse


class BrainProvider(Protocol):
    def complete(self, request: BrainRequest) -> BrainResponse:
        ...


class MockProvider:
    """Deterministic provider for tests and reproducible local demos."""

    def __init__(self, response: BrainResponse):
        self.response = response
        self.requests: List[BrainRequest] = []

    def complete(self, request: BrainRequest) -> BrainResponse:
        self.requests.append(request)
        return self.response


class SubprocessProvider:
    """Exchange one JSON request/response with a user-selected executable."""

    def __init__(self, argv: List[str], timeout_seconds: int = 120):
        if not argv or not all(isinstance(part, str) and part for part in argv):
            raise ValueError("provider argv must be a non-empty string list")
        self.argv = list(argv)
        self.timeout_seconds = timeout_seconds

    def complete(self, request: BrainRequest) -> BrainResponse:
        result = subprocess.run(
            self.argv,
            input=json.dumps(request.to_dict()),
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            shell=False,
            check=False,
        )
        if result.returncode != 0:
            summary = result.stderr[-1000:].replace("\n", " ")
            raise RuntimeError(
                "provider exited with code {}: {}".format(result.returncode, summary)
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("provider did not return one valid JSON object") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("provider response must be a JSON object")
        return BrainResponse.from_dict(payload)

