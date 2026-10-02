"""Apertus provider for ZNAK FORGE CODE via CSCS OpenAI-compatible inference.

Reads one BrainRequest JSON object from stdin and writes one BrainResponse JSON
object to stdout. Repository mutation remains exclusively inside FORGE.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

API_URL = os.environ.get(
    "APERTUS_API_URL",
    "https://api.inference.cscs.ch/v1/chat/completions",
)
MODEL = os.environ.get("APERTUS_MODEL", "swiss-ai/Apertus-v1.5-8B")
MAX_CONTEXT_CHARS = int(os.environ.get("ZNAK_PROVIDER_CONTEXT_CHARS", "90000"))
MAX_FILE_CHARS = int(os.environ.get("ZNAK_PROVIDER_FILE_CHARS", "14000"))

IGNORED_DIRS = {
    ".git", ".znak", ".venv", "venv", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
DENIED_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "secrets.json",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml",
    ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".rs", ".go",
}


def _api_key() -> str:
    for name in ("CSCS_INFERENCE_API_KEY", "SWISSAI_RESEARCH_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    raise RuntimeError(
        "No Apertus API key. Set CSCS_INFERENCE_API_KEY or SWISSAI_RESEARCH_API_KEY."
    )


def _task_terms(request: Dict[str, Any]) -> List[str]:
    task = request.get("task") or {}
    text = json.dumps(task, ensure_ascii=False).lower()
    return sorted({w for w in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{3,}", text)})


def _safe_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.name.lower() in DENIED_NAMES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 300_000:
                continue
        except OSError:
            continue
        yield path


def _rank_files(root: Path, terms: List[str]) -> List[Tuple[int, Path, str]]:
    ranked: List[Tuple[int, Path, str]] = []
    for path in _safe_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        haystack = (rel + "\n" + text[:30000]).lower()
        score = sum(4 for term in terms if term in rel.lower())
        score += sum(min(haystack.count(term), 3) for term in terms)
        if path.name.lower() in {"readme.md", "pyproject.toml", "package.json"}:
            score += 2
        ranked.append((score, path, text))
    ranked.sort(key=lambda item: (-item[0], item[1].as_posix()))
    return ranked


def build_repository_context(request: Dict[str, Any]) -> str:
    root = Path(str(request.get("authorized_repository", ""))).resolve()
    if not root.is_dir():
        raise RuntimeError("authorized_repository is not a directory")
    terms = _task_terms(request)
    chunks: List[str] = []
    used = 0
    for _, path, text in _rank_files(root, terms):
        rel = path.relative_to(root).as_posix()
        piece = f"\n--- FILE: {rel} ---\n{text[:MAX_FILE_CHARS]}\n"
        if used + len(piece) > MAX_CONTEXT_CHARS:
            continue
        chunks.append(piece)
        used += len(piece)
        if used >= MAX_CONTEXT_CHARS:
            break
    return "".join(chunks)


def build_prompt(request: Dict[str, Any], repo_context: str) -> str:
    return """You are the proposal brain for ZNAK FORGE CODE.
The local engine, not you, owns repository authority, mutation, verification,
rollback and final acceptance.

Return EXACTLY one JSON object and no markdown. It must have keys:
evidence, localization, hypotheses, patch_plan, unknowns.

Rules:
- Ground every claim in the repository context below.
- Use relative paths only.
- If evidence is insufficient, set localization or patch_plan to null and explain in unknowns.
- A patch change is a COMPLETE UTF-8 replacement for the target file.
- Keep changes minimal: <=3 files, <=1 new file, <=5 changed functions, <=120 changed LOC.
- Verifications should use safe Python unittest/pytest commands whenever possible.
- Evidence IDs referenced by localization/hypotheses/patch items must exist.
- Do not claim a test ran; you only propose verification commands.
- Do not expose secrets or request network/deployment actions.

BrainRequest:
""" + json.dumps(request, ensure_ascii=False, indent=2) + """

Selected repository context:
""" + repo_context


def _extract_json(text: str) -> Dict[str, Any]:
    value = text.strip()
    fence = chr(96) * 3
    if value.startswith(fence):
        value = re.sub(r"^" + re.escape(fence) + r"(?:json)?\s*", "", value)
        value = re.sub(r"\s*" + re.escape(fence) + r"$", "", value)
    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        start, end = value.find("{"), value.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError("model response did not contain a JSON object")
        result = json.loads(value[start:end + 1])
    if not isinstance(result, dict):
        raise RuntimeError("model response must be a JSON object")
    return result


def call_apertus(prompt: str) -> Dict[str, Any]:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "stream": False,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + _api_key(),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1200:]
        raise RuntimeError(f"Apertus HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Apertus request failed: {exc.reason}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("unexpected Apertus response shape") from exc
    return _extract_json(content)


def main() -> int:
    try:
        incoming = json.load(sys.stdin)
        if not isinstance(incoming, dict):
            raise RuntimeError("stdin must contain one JSON object")
        context = build_repository_context(incoming)
        result = call_apertus(build_prompt(incoming, context))
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        sys.stderr.write("apertus-provider: " + str(exc) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
