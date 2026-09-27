# RESOURCE INTAKE — Nebius x NVIDIA Hackathon

Date: 2026-09-27

Status vocabulary:
- ACTIVE — already available on our accounts or runtime.
- CLAIMABLE — official benefit exists; activation/redemption still required.
- PREPARED — material collected and ready to use.
- HOLD — useful, but do not activate unless it improves the submission or has near-zero cost.
- UNKNOWN — benefit or exact amount cannot yet be verified from official sources.

## 1. Core hackathon credits

### Token Factory trial
Status: ACTIVE

Observed in the current Token Factory account:
- Trial credit: $1.00
- Remaining trial period shown by UI: 29 days at observation time.

Use:
- small live inference verification;
- submission demo calls only.

Rule:
Do not treat trial credit as the submission funding plan.

### Hackathon Token Factory promo
Status: CLAIMABLE

Official activation code:

`NEBIUS-DEVPOST-GLOBAL26`

Official benefit:
- $25 Token Factory credits.

Source:
- Devpost official Resources / Kickoff Tips.

Current state:
- code not yet confirmed redeemed.

### Nebius AI Builder Program
Status: CLAIMABLE

Hackathon-specific Devpost statement:
- another $25 Token Factory credits;
- Tavily credits;
- Nebius Academy credits;
- office hours.

Broader official Builder Program statement:
- free to join;
- $400+ in credits and discounts across the open AI stack;
- cookbooks and working examples;
- free courses;
- discounted certifications;
- office hours / engineer support;
- builder community.

Official partner ecosystem named by Nebius:
- NVIDIA
- LangChain
- Hugging Face
- Cognition
- OpenHands
- Tavily
- Toloka
- Composio
- Prime Intellect
- MiniMax
- Qwen

Important:
Do not treat "$400+" as cash or as $400 Token Factory credit. It is a bundle of credits and discounts across partners.

## 2. Tavily

### Tavily account
Status: ACTIVE

User account evidence:
- account has already consumed more than 100 Tavily credits previously.

### BBDEVPOST promo
Status: CLAIMABLE

Official hackathon build-session announcement:

`BBDEVPOST`

Purpose:
- Tavily Agentic Search credits.

Exact credit amount:
- UNKNOWN from the announcement itself.

Do not invent a value until redemption/account UI confirms it.

### Best Use of Tavily bonus
Status: OPTIONAL / HOLD

Prize:
- $3,000 cash
- 1 winner

Eligibility:
- project must make a functional runtime call to Tavily API as part of the solution.

Decision rule:
Do not add Tavily merely to qualify for the prize.
Promote only if external web evidence genuinely improves FORGE.

Candidate legitimate use:
- fetch current external documentation / issue evidence;
- keep Tavily output as an external evidence source;
- FORGE still must not treat search output as automatic truth.

## 3. Required feedback bonus

Status: PREPARED

Official submission requirement:
Feedback on Nebius and NVIDIA tools/models is mandatory.

Bonus:
- 10 winners
- $100 each
- NVIDIA swag pack

Prepared artifact:
`hackathon/REQUIRED_FEEDBACK.md`

We already have real measurements:
- live dry-run;
- live accepted apply;
- elapsed times;
- targeted/shadow/regression results;
- onboarding observations.

This is one of the cleanest bonus opportunities because it requires no extra runtime scope.

## 4. Nebius training / education

### Free Agentic AI course
Status: CLAIMABLE

Official Nebius newsletter:
- free hands-on course;
- Nebius + NVIDIA + Tavily;
- build/evaluate a deep research agent;
- tool calling;
- web search;
- subagent orchestration;
- evaluation;
- practical exercises measuring performance and cost;
- digital badge backed by all three partners.

Use for FORGE:
- evaluation design;
- tool-use architecture;
- cost measurement;
- optional Tavily evidence layer.

### Nebius Academy
Status: AVAILABLE

Official free learning resources include:
- Agentic Development;
- AI-Assisted Programming;
- LLM Engineering Essentials;
- inference;
- RAG;
- evaluation;
- monitoring;
- fine-tuning;
- reinforcement learning;
- scaling.

Do not block submission on course completion.

### LLM Engineering Essentials
Status: AVAILABLE / RESERVE

Official course:
- free;
- online;
- 12 weeks;
- LLM APIs;
- agents;
- RAG;
- evaluation;
- monitoring;
- fine-tuning;
- RL;
- scaling.

Use:
research reserve, not submission blocker.

## 5. Nebius certification

### Agentic AI Builder certification
Status: HOLD

Official early-bird:
- $1 exam registration;
- regular price listed as $100 later.

Exam:
- online proctored;
- roughly 60 minutes;
- agentic AI / Token Factory / Tavily focus.

Passing benefit:
- official certificate;
- Credly digital badge;
- additional free Nebius credits via promo code.

Reason for HOLD:
- not required for hackathon;
- costs $1;
- takes preparation/time;
- can become useful after submission or if free-credit value materially exceeds time cost.

## 6. Nebius technical support

### Builder Hours / office hours
Status: AVAILABLE

Official developer portal:
- regular office hours with Nebius engineers.

Specific user email:
- Token Factory office hours scheduled Sep 29.

Use:
- ask one narrow technical question if needed:
  "For Coding and Agentic Engineering, is local repository execution + Token Factory inference sufficient, or should Token Factory Sandboxes be demonstrated?"

### Nebius Discord
Status: AVAILABLE

Use:
- organizer clarification;
- track-fit question;
- technical support.

Do not depend on Discord answers over Official Rules unless an organizer clarification is explicit.

## 7. Official hackathon build materials

### Devpost build-session recording
Status: PREPARED / AVAILABLE

Official session:
"Live-Coding Your First App with Nebius"

Topics:
- Token Factory setup;
- hackathon tracks;
- promo credit;
- Hermes Desktop Agent;
- open-weight model comparison;
- LLM judge;
- Vision QA;
- iterative bug fixing.

Official recording:
https://youtu.be/j_jEXP2ix2E

### Hermes Agent installation
Status: AVAILABLE / RESERVE

Official build-session resource:
https://hermes-agent.nousresearch.com/docs/getting-started/installation

FORGE does not require Hermes.
Keep as reference only.

### Nebius developer portal
Status: AVAILABLE

https://dev.nebius.com/

Contains:
- Token Factory docs;
- AI Cloud docs;
- Serverless docs;
- cookbooks;
- Builder Program;
- Tavily;
- Builder Hours;
- GitHub examples;
- videos.

## 8. Google resources already on account

### Google AI Studio premium access
Status: ACTIVE

Official Google email confirms current plan unlocks:
- paid Gemini Pro models;
- Nano Banana Pro;
- Lyria Pro;
- higher usage limits;
- vibe coding in AI Studio without requiring an API key.

Use:
- coding/review/debug support;
- video/demo asset preparation;
- do not make Google a required runtime dependency of the hackathon project.

### Google GEAR
Status: ACTIVE

Official Google Developer Program email:
- membership active;
- 35 monthly Google Skills credits;
- Intro to Agents path;
- Build Intelligent Agents path;
- ADK;
- tool use;
- memory management.

These are education credits, not compute dollars.

## 9. NVIDIA resources

### Nemotron model ecosystem
Status: AVAILABLE

Current submission model:
`nvidia/nemotron-3-super-120b-a12b`

NVIDIA also publishes:
- Nemotron model resources;
- local deployment paths;
- vLLM / SGLang / TensorRT-LLM guidance;
- Hugging Face access.

Do not change the validated submission model unless an A/B test proves value.

### Nemotron VoiceChat early access
Status: RESERVE

NVIDIA Early Access exists for Nemotron VoiceChat.
Not relevant to current FORGE scope.

## 10. Prizes we can legitimately target without scope inflation

### Overall awards
- Grand Prize: $20,000
- 2nd: $10,000
- 3rd: $6,000

### Track award
Coding and Agentic Engineering:
- NVIDIA Jetson Orin Nano

### Most Valuable Feedback
- $100
- NVIDIA swag
- 10 winners

This is already aligned with our work.

### Best Use of Tavily
- $3,000
- only if Tavily becomes a genuine runtime component.

### City Winner
Status: NOT_ASSUMED

Official Rules tie this to attending a participating IRL city event.
The Resources page contains conflicting wording.
Treat Rules as controlling unless organizers clarify.

Warsaw event date has passed.

## 11. Upcoming / future events

### Builders & Brews remaining after Sep 27
Official Resources list includes:
- Berlin — Sep 29
- Paris — Oct 1
- Toronto — Sep 29
- Boston — Oct 2
- San Francisco — Oct 9
- Los Angeles — Oct 13

Status: HOLD

Reason:
travel cost conflicts with CASH_FIRST.
Do not plan travel unless a remote/credit benefit becomes available without spending.

### Nebius Build Week Berlin
Official Nebius email:
- Oct 16–18;
- workshops;
- certifications;
- office hours;
- hackathon/community activity.

Status: HOLD
Not needed for current submission.

## 12. Submission materials already collected

Prepared:
- `README.md`
- `HACKATHON.md`
- `hackathon/DEMO_RUNBOOK.md`
- `hackathon/RESEARCH_TO_SUBMISSION_MAP.md`
- `hackathon/REQUIRED_FEEDBACK.md`
- `hackathon/VIDEO_SCRIPT_3MIN.md`
- `hackathon/PUBLIC_RELEASE_CHECKLIST.md`

Live proof available locally:
- real Token Factory dry-run receipt;
- real accepted apply receipt;
- deterministic negative rollback receipt.

## 13. Activation order

### Priority A — zero-cost / directly useful
1. Redeem `NEBIUS-DEVPOST-GLOBAL26`.
2. Join Nebius AI Builder Program.
3. Claim Builder Program Token Factory/Tavily/Academy benefits.
4. Redeem `BBDEVPOST` in Tavily if account permits.
5. Keep Google AI Studio + GEAR as auxiliary build tools.
6. Use Sep 29 Token Factory office hours only if track-fit ambiguity remains.

### Priority B — useful only if it improves evidence
1. Tavily runtime evidence retrieval.
2. Builder Program partner tools.
3. Nebius cookbooks/examples.
4. free Agentic AI course.

### Priority C — reserve
1. $1 certification.
2. travel events.
3. new model families.
4. VoiceChat.
5. RL/MCTS additions.

## 14. Cost rule

Default:
`NO_NEW_SPEND_WITHOUT_EXPLICIT_VALUE`

Free credits, free courses, free memberships and already-paid subscriptions may be used.
Do not convert the project into a larger architecture merely to consume benefits.
