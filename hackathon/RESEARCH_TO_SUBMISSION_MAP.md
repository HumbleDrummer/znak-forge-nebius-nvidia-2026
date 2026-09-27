# RESEARCH -> MECHANISM -> TEST -> DEMO -> JUDGING CRITERION

Status vocabulary:
- `IMPLEMENTED` - mechanism exists in the current runtime and has local evidence.
- `PARTIAL` - useful subset exists; the full research concept is not implemented.
- `RESERVE` - research only; keep out of the core submission until a measured need exists.

Judging criteria used here: Implementation, Design, Impact, Quality of Idea.

## Canonical map

| Status | Research | Mechanism in submission | Test / evidence gate | Demo moment | Judging criterion |
|---|---|---|---|---|---|
| PARTIAL / PROMOTE | ORIENT multilevel: orient before acting; narrow an evidence cone instead of guessing | Clean baseline orientation + explicit localization proof before mutation | T01 clean orientation; T04 missing localization -> UNKNOWN. Future A/B: same task with/without full ORIENT | Nemotron must identify the exact file/symbol and evidence before FORGE permits planning | Design, Implementation, Impact |
| IMPLEMENTED / CORE | Provenance + claim typing; hash identity is not semantic truth | Evidence ledger with source/locator/kind/claim; semantic-evidence gate | T17 HASH-only evidence -> localization remains UNKNOWN | Show a plausible model proposal rejected because its "evidence" is only identity metadata | Quality of Idea, Implementation |
| IMPLEMENTED / CORE | HYPOTHESIS -> TEST -> RESULT; no patch before falsifiable explanation | Every accepted proposal needs a hypothesis with a falsifier and expected observation | T05 missing falsifier -> UNKNOWN | Nemotron states what it thinks is wrong and what observation would falsify it before any write | Design, Quality of Idea |
| IMPLEMENTED / CORE | Bounded action / smallest justified change | Proof-carrying patch + engine-owned file/function/LOC budgets | T06 budget overflow; six-function and same-name-function budget regressions | Oversized model patch is denied/reoriented without source mutation | Implementation, Impact |
| IMPLEMENTED / CORE | Independent verification instead of self-reported success | Separate functional, contract, shadow and regression verdicts | T10 targeted PASS + regression FAIL; T11 contract FAIL; T12 shadow FAIL -> no ACCEPT | A patch can "fix the test" yet FORGE refuses success when a second lane contradicts it | Implementation, Design, Impact |
| IMPLEMENTED / CORE | Transactional mutation + recovery | Exact byte backups, syntax/static gate, rollback, diff and final receipt | T09 syntax failure -> ROLLBACK; T15 receipt completeness; T16 unrelated files survive rollback | Intentionally bad patch is applied in a bounded transaction, fails, and exact source is restored | Implementation, Impact |
| IMPLEMENTED / CORE | Anti-loop / evidence-change discipline | Retry fingerprints + trajectory counters; changed evidence can permit a new attempt | T13 repeated equivalent failure -> BLOCKED_LOOP_DETECTED; T14 changed evidence permits retry | Repeat the same failed action until FORGE stops it; then show a new-evidence path | Design, Impact |
| PARTIAL / PROMOTE LATER | Structured memory / continuity rather than narrative transcript | Run artifacts, status/verify/explain and receipts preserve state; full episodic/semantic memory is not integrated | Existing artifact audit + future resume test: receipt may restore orientation but cannot upgrade truth | Reopen a prior run and reconstruct task/evidence/tests without asking the model to invent history | Design, Quality of Idea, Impact |
| PARTIAL / MEASURE | Load/capacity/coherence as operational signals, not "emotion" | Existing trajectory: files read/re-read, commands, repeated commands, patch attempts, rollback count, falsified hypotheses, new evidence | Compare successful/blocked runs; add wall-time/token/cost once live Nebius run exists | Show why a run stopped or continued using measurable trajectory, not a narrative claim | Impact, Design |
| RESERVE | RL / MDP / PPO / MCTS research | No direct mechanism in current Coding Agent runtime | No promotion without an A/B showing better action selection or lower cost | Not shown in core demo | N/A |
| RESERVE | MEDUSA / game-agent research | Separate candidate product/track, not required for FORGE Coding submission | Keep isolated unless a shared mechanism is independently tested | Not shown in core demo | N/A |

## Promotion decision

**CORE DEMO:** provenance, falsifiable hypothesis, bounded patch, independent verification,
rollback/receipt and anti-loop behavior.

**SECONDARY / A-B:** ORIENT depth and continuity. Promote only when the same tasks can be
measured with and without the mechanism.

**RESERVE:** RL/MCTS and MEDUSA. Do not enlarge the submission merely because research exists.

## Demo protocol

1. Use a small real Git fixture with a non-trivial bug and a clean baseline.
2. Run NVIDIA Nemotron through Nebius Token Factory as the proposal brain.
3. Require evidence -> localization -> falsifiable hypothesis -> bounded patch plan.
4. First run in dry-run mode: prove the model cannot mutate the repository directly.
5. Apply only after the FORGE mutation gate passes.
6. Execute targeted + contract + shadow + regression verification.
7. Show one positive run and one deliberately failing run that rolls back.
8. Open the receipt: baseline, actions, evidence, diff identity, verification and final verdict.

## Submission metrics

- False ACCEPT count on negative fixtures: target = 0.
- Exact rollback restoration: target = PASS for every forced failure case.
- Budget bypass regressions: target = 0.
- Unsupported localization/hypothesis acceptance: target = 0.
- Repeated-equivalent-action loop: must block at the configured threshold.
- Live Nebius run: record model, tokens/cost if exposed, wall time and final gate state.
- A/B ORIENT experiment: compare unsupported claims, unnecessary reads/actions, time and cost.

## Evidence boundary

Research documents motivate mechanisms; they do not prove runtime behavior.
Only executable tests, run artifacts and live demo receipts count as execution evidence.
A hash proves artifact identity only, never correctness of its claims.
