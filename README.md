# ZNAK FORGE

**Evidence-gated coding agent runtime for the Nebius x NVIDIA Global AI Hackathon**

ZNAK FORGE separates model reasoning from repository authority.

NVIDIA Nemotron proposes evidence, localization, a falsifiable hypothesis, and a bounded patch plan through Nebius Token Factory. The local FORGE engine independently decides whether that proposal may mutate source code, then runs verification, rollback, and receipt generation.

The model can propose. It cannot declare its own success.

## Hackathon track

**Best Apps and Agents (recommended for the current validated build)**

The current submission uses Nebius Token Factory for NVIDIA Nemotron inference and keeps repository authority, mutation, verification and rollback in the local FORGE engine. It does not claim Token Factory Sandboxes in the present build, so the Best Apps and Agents track is the honest fit. A future Sandbox integration would require a fresh track review.

FORGE is designed around a real repository workflow:

`orient -> evidence -> localization -> hypothesis -> bounded patch -> verification -> final verdict`

The current hackathon integration uses **Nebius Token Factory** for NVIDIA Nemotron inference and a local authority runtime for repository access and test execution.

## Why this exists

A coding model can produce a plausible patch that passes one visible test and is still wrong.

FORGE therefore treats a patch as a claim that must carry evidence and survive independent checks.

Core controls include:

- semantic evidence and source provenance;
- explicit localization before mutation;
- falsifiable hypotheses;
- file/function/LOC change budgets;
- clean-Git and unchanged-baseline gates;
- targeted, contract, shadow, and regression verification;
- verified rollback;
- anti-loop retry control;
- deterministic run receipts.

## Nebius + NVIDIA integration

Provider:

`hackathon/nebius_provider.py`

Default model:

`nvidia/nemotron-3-super-120b-a12b`

Endpoint:

`https://api.tokenfactory.nebius.com/v1/chat/completions`

The provider sends a bounded, secret-filtered repository context to Token Factory. Common secret files such as `.env`, credential files, private keys, and cache/build directories are excluded.

The remote model never receives direct repository mutation authority.

## Verified live results

### Live dry-run

Run ID:

`20260927T004704Z-1ce102a39e`

Result:

- model: NVIDIA Nemotron 3 Super 120B A12B;
- Nebius Token Factory runtime call: PASS;
- final status: `DRY_RUN_NO_SOURCE_MUTATION`;
- process exit: `0`;
- elapsed time: `31.556 s`;
- source SHA before = source SHA after.

This proves that a real remote reasoning call can complete while source mutation remains disabled.

### Live apply

Run ID:

`20260927T004815Z-7243136b3f`

Result:

- final status: `ACCEPTED`;
- mutation status: `APPLIED_VERIFIED`;
- process exit: `0`;
- elapsed time: `16.670 s`;
- targeted test: PASS;
- shadow test: PASS;
- regression tests: PASS;
- root-cause check: PASS;
- requirements `R1` and `A1`: SATISFIED.

### Deterministic negative case

A deliberately naive patch fixes the obvious raw-string duplicate case but misses normalization-equivalent SKUs.

FORGE detects the independent shadow failure, refuses a false ACCEPT, rolls the mutation back, and verifies that the restored source hash equals the original source hash.

## Demo task

The included fixture contains an inventory aggregation bug.

Two SKUs may differ in whitespace/case but normalize to the same canonical identifier. A naive raw-input duplicate check appears to fix the visible symptom while leaving the underlying invariant broken.

The intended repair must reject duplicates **after canonical normalization**.

Files:

- `ZNAK_FORGE_CODE_v0_1/fixtures/demo_repo/inventory.py`
- `ZNAK_FORGE_CODE_v0_1/fixtures/demo_repo/test_inventory.py`
- `ZNAK_FORGE_CODE_v0_1/fixtures/demo_repo/task.json`

## Quick start

Requirements:

- Python 3.9+;
- Git;
- a Nebius Token Factory API key.

Set the key only in your local environment:

### PowerShell

```powershell
$env:NEBIUS_API_KEY="<your-token-factory-key>"
```

### Bash

```bash
export NEBIUS_API_KEY="<your-token-factory-key>"
```

Do not commit the key.

Run provider tests:

```text
cd hackathon
python -m unittest -v test_nebius_provider.py
```

Run the FORGE suite:

```text
cd ZNAK_FORGE_CODE_v0_1
python -m unittest discover -s tests -v
```

Current verified result: **40/40 PASS**.

## Public test build

A no-key browser test build is available at:

https://znak-forge-demo.znakhumbledrummer.chatgpt.site

It deterministically demonstrates both the accepted canonical repair and the rejected naive repair with independent shadow verification and rollback. The buttons make no model call and change no repository. The real Nebius Token Factory path remains the CLI demo below and requires the user’s own `NEBIUS_API_KEY`.

See [`hackathon/PUBLIC_DEMO.md`](hackathon/PUBLIC_DEMO.md) for the evidence boundary.

## Live demo

Dry-run first:

```text
python hackathon/run_live_demo.py
```

Expected:

`DRY_RUN_NO_SOURCE_MUTATION`

Only after the dry-run passes:

```text
python hackathon/run_live_demo.py --apply
```

The runner works on a fresh copy of the demo repository, not on the FORGE source tree.

## Authority boundary

Nemotron may propose:

- evidence,
- localization,
- hypotheses,
- a patch plan,
- verification commands.

FORGE owns:

- repository authorization;
- baseline identity;
- state transitions;
- mutation permission;
- allowed verification command shapes;
- patch budgets;
- exact file writes;
- verification;
- rollback;
- final ACCEPT / BLOCKED / UNKNOWN state;
- receipts.

## Research-backed design

The research-to-submission mapping is documented in:

`hackathon/RESEARCH_TO_SUBMISSION_MAP.md`

Research motivates mechanisms; it is not treated as execution proof.

The core demo promotes only mechanisms with executable evidence. RL/PPO/MCTS and unrelated game-agent research remain reserve material rather than being added merely to make the project look larger.

## Significant updates during the hackathon period

The pre-existing local FORGE core was significantly extended during the submission period with:

1. a real Nebius Token Factory / NVIDIA Nemotron provider;
2. bounded secret-filtered repository context selection;
3. a strict JSON provider contract compatible with the engine authority boundary;
4. changed-function budget hardening;
5. reproducible live dry-run and apply runners;
6. positive and forced-failure demo paths;
7. hackathon-specific evidence receipts and submission documentation.

## Security

- API keys are never stored in this repository.
- The demo defaults to dry-run.
- Verification executes repository test code; use a disposable environment for untrusted repositories.
- A SHA-256 match is treated as identity evidence, not proof of semantic correctness.
- Public release must pass a final secret scan.

## Repository map

```text
hackathon/
  DEMO_RUNBOOK.md
  RESEARCH_TO_SUBMISSION_MAP.md
  REQUIRED_FEEDBACK.md
  VIDEO_SCRIPT_3MIN.md
  nebius_provider.py
  run_live_demo.py
  run_local_demo.py
  test_nebius_provider.py

ZNAK_FORGE_CODE_v0_1/
  znak_code/
  tests/
  fixtures/demo_repo/
```

## License

This repository is licensed under the **MIT License**. See [`LICENSE`](LICENSE).

The package metadata in `ZNAK_FORGE_CODE_v0_1/pyproject.toml` also declares `MIT`, so the repository-level license and package metadata are aligned.

## Submission evidence

See:

- `HACKATHON.md`
- `hackathon/DEMO_RUNBOOK.md`
- `hackathon/RESEARCH_TO_SUBMISSION_MAP.md`
- `hackathon/REQUIRED_FEEDBACK.md`
- `hackathon/VIDEO_SCRIPT_3MIN.md`
- `hackathon/PUBLIC_RELEASE_CHECKLIST.md`
- `hackathon/RESOURCE_INTAKE_2026-09-27.md`
- `hackathon/SUBMISSION_FORM_MAP.md`
