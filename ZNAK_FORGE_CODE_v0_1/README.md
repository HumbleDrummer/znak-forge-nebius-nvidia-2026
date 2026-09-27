# ZNAK FORGE CODE v0.1

Codename: **ROBAK CODE CORE**.

This is a small, local coding-engine harness. It is not a wrapper around a coding-agent product. A vendor-neutral provider may propose evidence, a hypothesis and a patch, but the engine alone owns repository access, authority, state transitions, mutation, verification, rollback and receipts.

The default is dry-run. Source mutation requires `--apply`, a clean Git worktree, an unchanged baseline HEAD, semantic localization evidence, a falsifiable hypothesis, a proof-carrying patch within budget, and mapped verification commands.

## Run

Python 3.9+ is supported; Python 3.12+ is preferred.

```text
python -m znak_code orient PATH
python -m znak_code solve PATH --task TASK_FILE
python -m znak_code solve PATH --task TASK_FILE --apply
python -m znak_code status RUN_ID --repo PATH
python -m znak_code verify RUN_ID --repo PATH
python -m znak_code explain RUN_ID --repo PATH
```

From this directory, run the tests without installing dependencies:

```text
python -m unittest discover -s tests -v
```

Or install the local CLI:

```text
python -m pip install -e .
znak-code --help
```

## Task/provider contract

`solve` accepts a JSON task contract. For deterministic testing, the file may also contain a `brain_response` object. In normal use, select a local JSON-speaking executable with `--provider-executable`; request JSON arrives on stdin and response JSON must be written to stdout. The executable proposes; it never gets repository authority from the engine.

Every run writes `.znak/runs/<RUN_ID>/` in the authorized repository. `explain` reads those artifacts rather than generating a new narrative.

## Demo fixture

`fixtures/demo_repo` contains a duplicate-SKU bug. Checking raw duplicate spellings would make the targeted test pass, while the shadow test still fails for whitespace/case-equivalent SKUs. The root-cause repair must detect duplicates after canonical normalization.

Copy the fixture to a standalone directory, initialize Git there, commit every fixture file as a clean baseline, and run `solve` from the project directory with the standalone repository and its task file:

```text
cp -R fixtures/demo_repo /tmp/znak-demo
git -C /tmp/znak-demo init
git -C /tmp/znak-demo add .
git -C /tmp/znak-demo commit -m baseline
python -m znak_code solve /tmp/znak-demo --task /tmp/znak-demo/solve_task.json --apply
```

The engine test suite exercises the same accepted pipeline with isolated temporary repositories; the commands above exercise the packaged fixture itself.

## Safety boundaries

- The repository must be clean; `.znak/` receipts are excluded from dirty detection.
- Targets cannot escape the repository or touch `.git`/`.znak`.
- Verification uses explicit argv with `shell=False` and an allowlist limited to repository Python scripts, `unittest`, and `pytest` with bounded argument shapes.
- Verification still executes repository test code. Use an OS sandbox or disposable environment when accepting proposals from an untrusted provider.
- A patch transaction keeps exact byte backups. Failed syntax or material verification restores only files owned by that run and verifies the restoration.
- A recorded SHA-256 proves identity only, never semantic correctness.

## Known limitations

- v0.1 applies complete UTF-8 text replacements, not AST edits or binary patches.
- New-file parents must already exist; rollback does not create or manage directory trees.
- `verify RUN_ID` audits artifacts and baseline identity; it deliberately does not re-execute historical commands.
- Dirty-worktree opt-in, HTTP providers, Windows CI and network/deployment actions are intentionally absent.
- Provider quality is outside the trust boundary; malformed or unsupported proposals fail closed.
