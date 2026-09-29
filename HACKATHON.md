# ZNAK FORGE â€” Nebius x NVIDIA Global AI Hackathon

## Track
Best Apps and Agents (recommended for the current validated build).

The present runtime uses Nebius Token Factory for NVIDIA Nemotron inference and local FORGE authority, mutation, verification and rollback. It does not currently claim Token Factory Sandboxes, so the Coding and Agentic Engineering track is not asserted.

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

## Public test build

- URL: https://znak-forge-demo.znakhumbledrummer.chatgpt.site
- Scope: public, no-key deterministic test of accepted verification and rejected/rolled-back false acceptance.
- Evidence boundary: the page makes no model call and changes no repository; the real Nebius Token Factory inference path remains `hackathon/run_live_demo.py`.

## Current blockers

- The live submission still needs the final required custom-answer ratings and the two eligibility checkboxes confirmed by the submitter.
- The Devpost project must be synced with the public demo link and the honest track choice before final submission.

## Operational note (not a submission blocker)

- Promotional credit was not applied to the Token Factory account during preparation. The public test build does not require it; additional live calls still require a valid user-owned Token Factory key.

## Public repository
https://github.com/HumbleDrummer/znak-forge-nebius-nvidia-2026

## Next submission gate

1. Sync the public demo URL and Best Apps and Agents track to the Devpost project.
2. Verify the required custom-answer ratings and identity/eligibility confirmations.
3. Submit only after the final user confirmation.
