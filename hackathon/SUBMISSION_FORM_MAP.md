# DEVPOST SUBMISSION FORM MAP

Source: live Devpost submission requirements fetched 2026-09-27.

Status vocabulary:
- READY — answer can be supported now.
- DRAFT — answer text can be prepared but needs final review.
- UNKNOWN — do not invent.
- BLOCKER — required external artifact is missing.
- USER_CONFIRM — factual checkbox/identity answer should be confirmed at final submit.

## Global deliverables

- Submission object: required.
- Video: REQUIRED.
- Public website: not globally required.
- ZIP file: not required.
- Public code repository: REQUIRED by custom field.
- Working demo/test build URL: custom field, marked optional in form, but strongly recommended by hackathon overview.

## Field 28261 — Submitter Type
Required: YES

Options:
- Individual
- Team
- Organization

Current answer:
`Individual`

Status:
USER_CONFIRM

## Field 28262 — Organization Name
Required: YES

Instruction:
Use "N/A" when not representing an organization.

Current draft:
`N/A`

Status:
USER_CONFIRM

## Field 28265 — Submitter Country of Residence
Required: YES

Current draft:
`Poland`

Status:
USER_CONFIRM

## Field 28266 — Canada province
Required: YES

Instruction:
"N/A" if not resident in Canada.

Current draft:
`N/A`

Status:
USER_CONFIRM

## Field 28267 — Track
Required: YES

Options:
- Coding and agentic engineering
- Best apps and agents
- Personal AI
- Physical AI

Current answer:
`Best apps and agents`

Status:
READY / RECOMMENDED

Reason:
The validated build uses Nebius Token Factory inference plus local FORGE repository authority, mutation, verification and rollback. The current Coding and Agentic Engineering wording expects coding agents and developer tools in Token Factory Sandboxes; this build does not claim a Sandbox slice. Best Apps and Agents is therefore the honest fit for the artifact that exists now.

## Field 28268 — New or existing before Aug 26, 2026
Required: YES

Current state:
`UNKNOWN — USER CONFIRMATION REQUIRED`

Evidence boundary:
The public repository snapshot was created during the hackathon period, while the local FORGE core may have existed earlier. The available evidence does not prove whether the project meets the form's Aug 26 cutoff. Do not submit `Existing` or `New` without the submitter's factual confirmation.

Status:
USER_CONFIRM

## Field 28269 — Significant update using Nebius tools
Required: NO, but relevant because project is existing.

Draft:

"ZNAK FORGE existed before the submission period as a local evidence-gated coding runtime. During the hackathon period we added a real Nebius Token Factory provider using NVIDIA Nemotron, bounded secret-filtered repository context selection, a strict JSON proposal contract, changed-function budget hardening, reproducible live dry-run/apply runners, forced-failure rollback evidence, and hackathon-specific receipts and submission documentation. We validated both a real Token Factory dry-run with zero source mutation and a live accepted repair with targeted, shadow and regression verification."

Status:
DRAFT / EVIDENCE_SUPPORTED

## Field 28270 — Public repository URL
Required: YES

Requirements:
- GitHub, GitLab or Bitbucket;
- approved OSI license;
- README setup instructions;
- highlight NVIDIA model;
- highlight where Token Factory accelerated workflow;
- mention other Nebius tools/services used.

Current:
`https://github.com/HumbleDrummer/znak-forge-nebius-nvidia-2026`

Status:
`READY / PUBLIC_REPO_CREATED`

Prepared:
- public-facing README;
- secret-scan checklist;
- live evidence summary.

License state:
- MIT license selected;
- root `LICENSE` added;
- package metadata already declares `MIT`.

Still required:
- final secret scan;
- public push.

## Field 28271 — Working demo / hosted app / test build URL
Required by field: NO

Current:
`https://znak-forge-demo.znakhumbledrummer.chatgpt.site`

Scope:
Public no-key deterministic test build. It demonstrates the accepted canonical repair and the rejected/rolled-back naive repair. It does not make a model call or mutate a repository; the live Nebius path remains in the public CLI repository.

Status:
READY / PUBLIC_TEST_BUILD_VERIFIED

## Field 28272 — Models used and why
Required: YES

Draft:

"We used NVIDIA Nemotron 3 Super 120B A12B through Nebius Token Factory. We chose the Super variant for a balance of reasoning quality, structured instruction-following and practical latency/cost for repository analysis. The model serves as the proposal brain; repository authority, mutation, verification and final acceptance remain local to FORGE."

Status:
DRAFT / SUPPORTED

## Field 28273 — Nemotron output quality 1–10
Required: YES

Current:
`UNKNOWN — NUMERIC RATING NOT YET JUSTIFIED`

Evidence available:
- dry-run valid proposal;
- live accepted patch;
- targeted PASS;
- shadow PASS;
- regression PASS;
- root-cause PASS.

Need:
at least several additional live tasks or a clearly disclosed limited rating basis.

Do not invent a score.

## Field 28274 — Fine-tuned / prompt-engineered / out of box
Required: YES

Draft:

"We used the base hosted Nemotron model through Token Factory and prompt-engineered the interaction around a strict JSON contract. The prompt requires evidence, localization, falsifiable hypotheses, bounded patch plans and explicit verification commands. We did not fine-tune the model for the current submission."

Status:
READY / DRAFT

## Field 28275 — Comparison with other models
Required: YES

Current:
`UNKNOWN — NO CONTROLLED A/B YET`

Rule:
Do not claim superiority without same-task, same-budget comparison.

Potential next experiment:
Nemotron Super vs one comparable model on identical fixture(s), measuring:
- valid structured response rate;
- gate pass rate;
- unnecessary changes;
- latency;
- token/cost if exposed.

## Field 28276 — Most valuable Nebius capabilities
Required: YES

Draft:

"The most valuable capability was Token Factory's OpenAI-compatible inference API for NVIDIA Nemotron. It let us add a remote reasoning layer with very little provider-specific code while keeping repository authority local. The API-key/project flow and live model endpoint were sufficient to validate both a no-mutation dry-run and an applied repair. We currently use Token Factory inference rather than AI Cloud compute or Serverless deployment."

Status:
DRAFT / SUPPORTED

## Field 28277 — Likelihood to recommend Nemotron on Nebius 1–10
Required: YES

Current:
`UNKNOWN — NUMERIC RATING NOT SET`

Qualitative evidence:
- API integration small;
- two successful live calls;
- onboarding/billing/API-key friction observed;
- model delivered a verified repair.

Set numeric rating only during final review.

## Field 28278 — Experience vs cloud/local environments 1–10
Required: YES

Current:
`UNKNOWN — NUMERIC RATING NOT SET`

Known comparison:
- Token Factory simplified remote model access;
- local execution preserved deterministic repository authority;
- live network latency exists;
- current measurements: 31.556 s dry-run, 16.670 s apply.

Do not generalize beyond current tests.

## Field 28279 — Improvements wanted
Required: YES

Draft:

"For this project, the main friction was onboarding clarity around trial credit, billing activation, promotional credits and API-key creation. A single hackathon onboarding path that clearly shows credit state, billing prerequisites, API-key creation and recommended model IDs would reduce time to first successful call. For coding-agent workflows, clearer examples that combine Token Factory reasoning with bounded repository execution and Sandbox options would also help."

Status:
DRAFT / SPECIFIC

## Field 28280 — What we want from Nemotron next
Required: YES

Draft candidate:

"More strong structured-output reliability for long repository contexts, explicit token/cost telemetry in developer workflows, and coding-agent examples that expose reasoning quality through reproducible evaluation rather than only single-demo success."

Status:
DRAFT

## Field 28282 — Tavily used?
Required: YES

Options:
- Yes
- No

Current truthful answer:
`No`

If Tavily is added:
must make a functional runtime API call as part of the solution.

Decision gate:
Only change to Yes if Tavily becomes a genuine evidence-retrieval mechanism and is demonstrated/tested.

Status:
READY CURRENTLY = NO

## Field 28281 — Builders & Brews IRL city
Required: NO

Form description:
select city if attending one of the 20 IRL events.

Current:
`BLANK / NOT_ASSUMED`

Do not select Warsaw unless attendance eligibility is factually established for this submission.

## Field 28283 — Age
Required checkbox: YES

Statement:
submitter/team are at least age of majority where they reside.

Status:
USER_CONFIRM

## Field 28284 — Employee
Required checkbox: YES

Statement:
submitter/team are not employees/representatives/agents of promotion entities.

Status:
USER_CONFIRM

## Video requirement

Public YouTube video:
- required;
- <= 3 minutes;
- must show project working;
- audio must explain Nebius Token Factory and NVIDIA model usage.

Current verified URL:
`https://youtu.be/BZf4hUlFIYs`

Observed state on 2026-09-29:
- public YouTube page;
- duration 2:48;
- title names Nebius Token Factory and NVIDIA Nemotron.

Prepared script:
`hackathon/VIDEO_SCRIPT_3MIN.md`

Status:
READY / PUBLIC_VIDEO_VERIFIED

## Feedback requirement

Required feedback should cover:
- model choice;
- output quality;
- prompting/fine-tuning;
- comparison;
- Nebius capabilities;
- recommend score;
- environment score;
- improvements;
- future Nemotron wishes.

Prepared:
`hackathon/REQUIRED_FEEDBACK.md`

## Final pre-submit blockers

1. Required numeric feedback answers: 28273, 28275, 28277 and 28278 need final honest values; do not infer them silently.
2. Field 28268 (New/Existing cutoff) needs factual submitter confirmation.
3. Identity and eligibility fields 28261, 28262, 28265, 28266, 28283 and 28284 need final confirmation.
4. Sync the current track, public demo URL and verified YouTube URL to Devpost.
5. Actual Devpost submit still requires explicit user confirmation.
