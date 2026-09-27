"""Bounded repository inspection and command execution."""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def summarize(value: str, limit: int = 2000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...<truncated {} chars>".format(len(value) - limit)


def python_changed_functions(before: str, after: str) -> set[str]:
    """Derive changed Python function identities from source rather than provider claims."""

    def snapshot(source: str) -> tuple[Dict[str, str], str]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {}, source

        functions: Dict[str, str] = {}
        module_nodes = []

        def visit_body(
            body: List[ast.stmt],
            prefix: str = "",
            include_module_nodes: bool = True,
        ) -> None:
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = "{}{}".format(prefix, node.name)
                    functions[name] = ast.dump(node, include_attributes=False)
                    visit_body(node.body, name + ".", False)
                elif isinstance(node, ast.ClassDef):
                    visit_body(node.body, "{}{}.".format(prefix, node.name), False)
                    if include_module_nodes:
                        class_body = [
                            ast.dump(child, include_attributes=False)
                            for child in node.body
                            if not isinstance(
                                child,
                                (ast.FunctionDef, ast.AsyncFunctionDef),
                            )
                        ]
                        module_nodes.append(
                            "ClassDef(name={!r}, bases={}, keywords={}, decorators={}, body={})".format(
                                node.name,
                                [ast.dump(item, include_attributes=False) for item in node.bases],
                                [ast.dump(item, include_attributes=False) for item in node.keywords],
                                [
                                    ast.dump(item, include_attributes=False)
                                    for item in node.decorator_list
                                ],
                                class_body,
                            )
                        )
                elif include_module_nodes:
                    module_nodes.append(ast.dump(node, include_attributes=False))

        visit_body(tree.body)
        module_dump = "\n".join(module_nodes)
        return functions, module_dump

    before_functions, before_module = snapshot(before)
    after_functions, after_module = snapshot(after)
    changed = {
        name
        for name in set(before_functions) | set(after_functions)
        if before_functions.get(name) != after_functions.get(name)
    }
    if before_module != after_module:
        changed.add("module")
    return changed


def is_protected_component(value: str) -> bool:
    """Match protected Windows/Unix path spellings conservatively."""
    return value.rstrip(" .").casefold() in {".git", ".znak"}


@dataclass
class CommandResult:
    argv: List[str]
    cwd: str
    started_at: str
    exit_code: int
    duration_seconds: float
    stdout_summary: str
    stderr_summary: str
    result_class: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CommandRejected(ValueError):
    pass


class CommandExecutor:
    """Run explicit argv lists without a shell and reject dangerous command classes."""

    _PYTHON_EXECUTABLE = re.compile(r"^python(?:3(?:\.\d+)?)?(?:\.exe)?$")
    _UNITTEST_FLAGS = {"-b", "-f", "-q", "-v"}
    _PYTEST_FLAGS = {"-q", "-v", "-x"}

    def __init__(self, repository: Path):
        self.repository = repository.resolve()

    def _validate_test_selector(self, value: str) -> None:
        """Keep path-shaped selectors inside the authorized repository."""
        path_part = value.split("::", 1)[0]
        candidate = Path(path_part)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise CommandRejected("test selector escapes repository: {}".format(value))
        resolved = (self.repository / candidate).resolve()
        try:
            relative = resolved.relative_to(self.repository)
        except ValueError as exc:
            raise CommandRejected("test selector escapes repository: {}".format(value)) from exc
        if relative.parts and is_protected_component(relative.parts[0]):
            raise CommandRejected("test selector reaches protected repository metadata")

    def _validate_pytest_args(self, args: List[str]) -> None:
        for value in args:
            if value.startswith("-"):
                if value not in self._PYTEST_FLAGS:
                    raise CommandRejected("pytest option is not allowed: {}".format(value))
                continue
            self._validate_test_selector(value)

    def _validate_python(self, argv: List[str]) -> None:
        if len(argv) == 2 and not argv[1].startswith("-"):
            script = (self.repository / argv[1]).resolve()
            try:
                relative = script.relative_to(self.repository)
            except ValueError as exc:
                raise CommandRejected("verification script escapes repository") from exc
            if relative.parts and is_protected_component(relative.parts[0]):
                raise CommandRejected("verification script reaches protected repository metadata")
            if script.suffix != ".py" or not script.is_file():
                raise CommandRejected("direct Python verifier must be a repository .py file")
            return
        if len(argv) < 3 or argv[1] != "-m":
            raise CommandRejected("Python verifier must be a script or an allowed -m module")
        module = argv[2]
        if module == "pytest":
            self._validate_pytest_args(argv[3:])
            return
        if module != "unittest":
            raise CommandRejected("Python module is not an allowed verifier: {}".format(module))
        for value in argv[3:]:
            if value.startswith("-"):
                if value not in self._UNITTEST_FLAGS:
                    raise CommandRejected("unittest option is not allowed: {}".format(value))
                continue
            self._validate_test_selector(value)

    def validate(self, argv: List[str]) -> None:
        if not argv or not all(isinstance(part, str) and part for part in argv):
            raise CommandRejected("command must be a non-empty argv string list")
        executable_path = Path(argv[0])
        executable = executable_path.name.lower()
        is_qualified = executable_path.name != argv[0]
        is_exact_runtime = executable_path.is_absolute() and os.path.normcase(
            os.path.abspath(argv[0])
        ) == os.path.normcase(os.path.abspath(sys.executable))
        if is_qualified and not (
            is_exact_runtime and self._PYTHON_EXECUTABLE.fullmatch(executable)
        ):
            raise CommandRejected("qualified verifier executable path is not allowed")
        if self._PYTHON_EXECUTABLE.fullmatch(executable):
            self._validate_python(argv)
            return
        if executable in {"pytest", "pytest.exe"}:
            self._validate_pytest_args(argv[1:])
            return
        raise CommandRejected("verification executable is not allowlisted: {}".format(executable))

    def run(self, argv: List[str], timeout_seconds: int = 60) -> CommandResult:
        self.validate(argv)
        started_at = utc_now()
        started = time.monotonic()
        try:
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                argv,
                cwd=str(self.repository),
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                shell=False,
                check=False,
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            result_class = "PASS" if exit_code == 0 else "FAIL"
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            result_class = "TIMEOUT"
        duration = round(time.monotonic() - started, 6)
        return CommandResult(
            argv=list(argv),
            cwd=str(self.repository),
            started_at=started_at,
            exit_code=exit_code,
            duration_seconds=duration,
            stdout_summary=summarize(stdout),
            stderr_summary=summarize(stderr),
            result_class=result_class,
        )


class GitRepository:
    def __init__(self, path: Path):
        self.path = path.resolve()

    def _git(self, args: List[str]) -> str:
        completed = subprocess.run(
            ["git"] + args,
            cwd=str(self.path),
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "git {} failed: {}".format(" ".join(args), summarize(completed.stderr, 800))
            )
        return completed.stdout

    def assert_repository(self) -> None:
        if self._git(["rev-parse", "--is-inside-work-tree"]).strip() != "true":
            raise RuntimeError("path is not inside a Git working tree")
        root = Path(self._git(["rev-parse", "--show-toplevel"]).strip()).resolve()
        if root != self.path:
            raise RuntimeError("PATH must be the Git repository root: {}".format(root))

    @staticmethod
    def _is_engine_artifact_path(path: str) -> bool:
        normalized = path.strip().strip('"')
        return normalized == ".znak" or normalized.startswith(".znak/")

    @classmethod
    def _is_engine_artifact_status(cls, line: str) -> bool:
        # Porcelain v1 prefixes paths with two status columns and a space.
        # A rename is ignorable only when both source and destination are engine artifacts.
        path = line[3:] if len(line) >= 4 else line
        if " -> " in path:
            source, destination = path.split(" -> ", 1)
            return cls._is_engine_artifact_path(source) and cls._is_engine_artifact_path(
                destination
            )
        return cls._is_engine_artifact_path(path)

    def working_status(self) -> List[str]:
        lines = self._git(["status", "--porcelain=v1", "--untracked-files=all"]).splitlines()
        return [line for line in lines if not self._is_engine_artifact_status(line)]

    @staticmethod
    def status_path(line: str) -> str:
        path = line[3:] if len(line) >= 4 else line
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        return path.strip().strip('"')

    def baseline(self) -> Dict[str, Any]:
        self.assert_repository()
        head = self._git(["rev-parse", "HEAD"]).strip()
        branch = self._git(["branch", "--show-current"]).strip() or "(detached)"
        status = self.working_status()
        unstaged = self._git(["diff", "--no-ext-diff", "--binary"])
        staged = self._git(["diff", "--no-ext-diff", "--binary", "--cached"])
        return {
            "repository_absolute_path": str(self.path),
            "branch": branch,
            "head": head,
            "baseline_head": head,
            "dirty": bool(status),
            "status_porcelain": status,
            "diff": unstaged,
            "staged_diff": staged,
            "captured_at": utc_now(),
        }

    def current_head(self) -> str:
        return self._git(["rev-parse", "HEAD"]).strip()

    def topology(self, limit: int = 200) -> List[Dict[str, str]]:
        """Return a bounded first localization layer with relevance rationale."""
        entries: List[Dict[str, str]] = []
        for root, dirs, files in os.walk(str(self.path)):
            dirs[:] = sorted(item for item in dirs if item not in {".git", ".znak", "__pycache__"})
            for name in sorted(files):
                relative = str((Path(root) / name).relative_to(self.path))
                entries.append(
                    {
                        "path": relative,
                        "why_relevant": "repository topology candidate; not yet selected for mutation",
                    }
                )
                if len(entries) >= limit:
                    return entries
        return entries

    def resolve_target(self, relative: str) -> Path:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("target must be a repository-relative path")
        if not candidate.parts or is_protected_component(candidate.parts[0]):
            raise ValueError("engine metadata and Git internals cannot be mutation targets")
        resolved = (self.path / candidate).resolve()
        try:
            resolved_relative = resolved.relative_to(self.path)
        except ValueError as exc:
            raise ValueError("target escapes the authorized repository") from exc
        if resolved_relative.parts and is_protected_component(resolved_relative.parts[0]):
            raise ValueError("resolved target reaches protected repository metadata")
        return resolved

    def file_sha256(self, relative: str) -> Optional[str]:
        target = self.resolve_target(relative)
        if not target.exists():
            return None
        if not target.is_file():
            raise ValueError("target is not a regular file: {}".format(relative))
        return sha256_bytes(target.read_bytes())


def changed_line_count(before: str, after: str) -> int:
    import difflib

    count = 0
    for line in difflib.unified_diff(before.splitlines(), after.splitlines()):
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith(("+", "-")):
            count += 1
    return count


def unified_patch(changes: Iterable[Dict[str, str]]) -> str:
    import difflib

    chunks: List[str] = []
    for change in changes:
        target = change["target"]
        before = change["before"]
        after = change["after"]
        before_label = "a/{}".format(target) if change["existed"] == "true" else "/dev/null"
        after_label = "b/{}".format(target)
        chunks.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=before_label,
                tofile=after_label,
            )
        )
    return "".join(chunks)
