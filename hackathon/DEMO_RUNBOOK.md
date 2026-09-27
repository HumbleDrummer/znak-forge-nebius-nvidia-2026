# ZNAK FORGE Hackathon Demo Runbook

## Goal

Demonstrate that NVIDIA Nemotron on Nebius Token Factory can propose a repair,
while ZNAK FORGE independently controls repository authority, mutation,
verification, rollback and acceptance.

## A. Live Nebius dry-run — first external proof

Precondition:
- Token Factory API key exists in `NEBIUS_API_KEY`.
- Do not commit or print the key.
- Start without `--apply`.

Run:

    powershell -ExecutionPolicy Bypass -File .\hackathon\run_live_demo.ps1

Expected evidence:
1. Nebius/Nemotron returns one valid BrainResponse JSON.
2. Evidence and localization identify the canonical-SKU overwrite bug.
3. A falsifiable hypothesis exists.
4. The patch stays inside the engine change budget.
5. FORGE returns `DRY_RUN_NO_SOURCE_MUTATION`.
6. `source_sha256_before == source_sha256_after`.
7. Run artifacts are copied under `hackathon/evidence/live_<timestamp>/`.

This is the first proof that the submission performs a real runtime call to
Nebius Token Factory while the remote model has no direct mutation authority.

## B. Positive apply demo

Only after A passes:

    python .\hackathon\run_live_demo.py --apply

Expected:
- exact duplicate test PASS;
- normalized shadow duplicate test PASS;
- regression PASS;
- final verdict ACCEPTED;
- diff and receipt preserved.

## C. Negative / false-accept prevention demo

Use the existing deterministic regression evidence:
- `test_t10_targeted_pass_and_regression_fail_is_not_accepted`
- `test_t11_functional_pass_contract_violation_is_not_accepted`
- `test_t12_shadow_failure_is_not_accepted`
- `test_t09_syntax_failure_triggers_verified_rollback`

Show one case where a superficially successful patch is rejected because an
independent verification lane fails. Then show rollback and the final receipt.

## 3-minute video spine

0:00-0:25 — Problem: coding agents can claim success after a plausible patch.
0:25-0:50 — Architecture: Nemotron proposes; FORGE owns authority.
0:50-1:35 — Live dry-run: evidence -> localization -> hypothesis -> bounded plan.
1:35-2:10 — Positive apply: tests pass and receipt is produced.
2:10-2:40 — Negative case: shadow/regression failure -> no false ACCEPT -> rollback.
2:40-3:00 — Why it matters: reproducible evidence, bounded changes, measurable safety.

## Evidence boundary

Research documents motivate the design. They are not execution proof.
Execution proof comes from tests, Git state, run artifacts, receipts and the
live Token Factory call.
