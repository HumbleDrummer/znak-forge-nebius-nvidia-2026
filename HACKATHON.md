# ZNAK FORGE — Nebius x NVIDIA Global AI Hackathon

## Track
Coding and Agentic Engineering.

## Project
ZNAK FORGE / ROBAK CODE CORE is an evidence-gated coding agent runtime.
The model proposes evidence, localization, hypotheses and a patch plan.
The local engine alone owns repository authority, mutation, verification,
rollback and final acceptance.

## Hackathon integration
Nebius Token Factory is connected through a standalone provider executable:
hackathon/nebius_provider.py

Default model:
nvidia/nemotron-3-super-120b-a12b

The provider uses the OpenAI-compatible Token Factory chat-completions endpoint,
but depends only on the Python standard library.
## Safety boundary
- NEBIUS_API_KEY is read only from the environment.
- .env, common credential files, private keys and build/cache directories are
  excluded from repository context.
- The remote model never edits files directly.
- The remote model cannot mark its own patch as accepted.
- FORGE independently checks clean Git state, change budgets, localization,
  hypotheses, allowed verification commands, exact diffs and rollback.
- Hash equality is treated as identity evidence, not semantic truth.

## Local verification completed
- FORGE engine suite: 40/40 PASS on the current Windows host.
- Nebius provider suite: 5/5 PASS.
- Deterministic demo: positive path = ACCEPTED / APPLIED_VERIFIED.
- Deterministic negative path = ROLLBACK / ROLLED_BACK with exact source hash restored.

## Live Nebius verification completed
- Token Factory access and API key: ACTIVE.
- Model: `nvidia/nemotron-3-super-120b-a12b`.
- Live dry-run `20260927T004704Z-1ce102a39e`:
  `DRY_RUN_NO_SOURCE_MUTATION`, exit 0, 31.556 s, source SHA unchanged.
- Live apply `20260927T004815Z-7243136b3f`:
  `ACCEPTED / APPLIED_VERIFIED`, exit 0, 16.670 s.
- Targeted, shadow and regression verification all PASS.
- R1 and A1 are SATISFIED; root-cause verdict PASS.
- The generated API key is stored outside the repository as a Windows user DPAPI secret.

## Research-backed submission map
Canonical map: `hackathon/RESEARCH_TO_SUBMISSION_MAP.md`.

It separates implemented mechanisms from partial research candidates and reserve ideas,
and binds every promoted mechanism to a test, a demo moment and a judging criterion.
Research is motivation; executable tests and run receipts remain the evidence boundary.

Core demo mechanisms: provenance, falsifiable hypotheses, bounded patches,
independent verification, rollback/receipts and anti-loop control.

## Run
Set the API key in the shell without committing it:

    $env:NEBIUS_API_KEY = "<token-factory-key>"

Optional model override:

    $env:NEBIUS_MODEL = "nvidia/nemotron-3-super-120b-a12b"

From ZNAK_FORGE_CODE_v0_1 run:

    python -m znak_code solve <repo> --task <task.json> --provider-executable python --provider-arg ..\hackathon\nebius_provider.py

Start without --apply for a proposal-only dry run.
Add --apply only after the proposal passes the engine mutation gate.
## Significant hackathon-period update
The pre-existing local FORGE engine is being significantly updated during the
hackathon submission period with:
1. a real Nebius Token Factory / NVIDIA Nemotron reasoning provider;
2. bounded, secret-filtered repository context selection;
3. strict JSON provider contract compatible with the existing authority boundary;
4. regression hardening of Python changed-function accounting;
5. a reproducible Nebius-backed coding-agent demo and submission evidence.

## Submission preparation completed
- Public-facing root README: PREPARED.
- Required Nebius/NVIDIA feedback draft: PREPARED.
- 3-minute video script/run order: PREPARED.
- Public release / secret-scan checklist: PREPARED.
- Resource/credits/program intake: PREPARED.
- Live Devpost submission-field map: PREPARED.
- Local secret scan: 0 key/private-key hits.
- Validated runtime remains unchanged.

## Current blockers
- Hackathon promotional credit has not yet been applied to the Token Factory account.
- Public YouTube demo URL does not exist yet.

## Public repository
https://github.com/HumbleDrummer/znak-forge-nebius-nvidia-2026

## Next submission gate
1. Apply `NEBIUS-DEVPOST-GLOBAL26` manually in the Token Factory billing UI if automation remains blocked.
2. Run the final secret scan, then publish the repository with the root MIT `LICENSE` visible.
3. Record the 3-minute demo from the verified dry-run, accepted live run and rollback case.
4. Upload the final video publicly to YouTube and attach the URL to the submission.
