# ZNAK FORGE — 3-Minute Demo Script

Target length: **2:45–2:55**.  
Hard limit: **under 3:00**.

The audio must explicitly name **Nebius Token Factory** and **NVIDIA Nemotron**.

## 0:00–0:20 — Problem

**Screen:** buggy `inventory.py` + two tests.

**Voice:**

"AI coding agents can produce a patch that looks right and even passes one visible test, while still violating the underlying requirement. ZNAK FORGE separates model reasoning from repository authority."

## 0:20–0:45 — Architecture

**Screen:** simple architecture diagram or terminal + README authority boundary.

**Voice:**

"We use NVIDIA Nemotron 3 Super 120B A12B through Nebius Token Factory as the proposal brain. Nemotron proposes evidence, localization, a falsifiable hypothesis, and a bounded patch plan. The local FORGE engine alone controls mutation, verification, rollback, and final acceptance."

On-screen chain:

`Nemotron / Token Factory -> proposal -> FORGE gates -> patch -> independent verification -> receipt`

## 0:45–1:15 — Real Nebius dry-run

**Screen:** run:

```text
python hackathon/run_live_demo.py
```

Then show receipt/status.

**Voice:**

"This is a real Token Factory runtime call. The first run is deliberately dry. It finished with DRY_RUN_NO_SOURCE_MUTATION. The source SHA before and after is identical, proving the remote model had no direct write authority."

Show:

- model: Nemotron 3 Super;
- run ID `20260927T004704Z-1ce102a39e`;
- `exit_code=0`;
- `source_unchanged=true`.

## 1:15–1:55 — Accepted repair

**Screen:** run:

```text
python hackathon/run_live_demo.py --apply
```

Show changed function and verification receipt.

**Voice:**

"After the proposal passes the mutation gate, FORGE applies one bounded transaction. The repair checks duplicates after canonical normalization. Targeted, shadow, and regression verification all pass, and FORGE returns ACCEPTED / APPLIED_VERIFIED."

Show:

- run ID `20260927T004815Z-7243136b3f`;
- targeted PASS;
- shadow PASS;
- regression PASS;
- root-cause PASS.

## 1:55–2:30 — False-accept prevention

**Screen:** deterministic negative demo or saved receipt from the naive patch.

**Voice:**

"Now we try a plausible but wrong repair: reject only identical raw SKU strings. It passes the obvious case but fails the normalization-equivalent shadow test. FORGE refuses a false ACCEPT, rolls back the transaction, and verifies that the restored source hash matches the original."

Show:

`ROLLBACK / ROLLED_BACK`

and:

`SHA before == SHA after`

## 2:30–2:50 — Why it matters

**Screen:** receipt files + research map.

**Voice:**

"FORGE turns coding-agent output into falsifiable, auditable claims. Research ideas only enter the submission when they map to an implemented mechanism, a test, and demo evidence."

## 2:50–2:58 — Close

**Screen:** title + Nebius/NVIDIA labels.

**Voice:**

"ZNAK FORGE: Nemotron proposes. Evidence decides. FORGE owns the write."

## Recording checklist

- Keep browser/account/API-key screens out of the recording.
- Do not show DPAPI secret paths containing any secret bytes.
- Use a fresh demo fixture.
- Make terminal font large enough for judges.
- Show final statuses, not long logs.
- Show Nebius Token Factory and NVIDIA Nemotron names in both audio and on-screen text.
- No copyrighted background music.
- Export under 3 minutes.
- Upload publicly to YouTube only after secret scan.

## Required captured proof

1. real dry-run status;
2. unchanged SHA;
3. real accepted apply status;
4. three verification PASS results;
5. negative shadow failure;
6. rollback and restored SHA;
7. repository/README setup instructions.
