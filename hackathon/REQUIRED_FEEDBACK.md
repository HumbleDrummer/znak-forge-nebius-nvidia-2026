# Required Nebius / NVIDIA Feedback

This file is prepared for the hackathon submission form. It records concrete observations from the ZNAK FORGE integration. Keep factual measurements separate from opinion.

## What we used

### Nebius

- Nebius Token Factory
- OpenAI-compatible chat completions API
- Project API key
- NVIDIA Nemotron inference

### NVIDIA

- `nvidia/nemotron-3-super-120b-a12b`

## What Token Factory did in the project

Token Factory provides the remote reasoning layer.

Nemotron receives a bounded repository context and returns a strict JSON proposal containing:

- evidence;
- localization;
- falsifiable hypotheses;
- patch plan;
- verification commands.

The local FORGE runtime retains repository authority and independently decides whether mutation and acceptance are permitted.

## Zero-to-first-call onboarding

Observed path:

1. Sign in to Nebius Token Factory.
2. Complete billing profile activation.
3. Open `API keys`.
4. Create a project API key.
5. Configure the key outside the repository.
6. Call the OpenAI-compatible Token Factory endpoint.

The key is shown once at creation, so the integration stores it only outside the repository.

## What worked well

- OpenAI-compatible endpoint made the provider small and dependency-light.
- Nemotron returned enough structured reasoning to support evidence, localization, hypotheses, and patch planning.
- A live dry-run completed with source mutation disabled.
- A live apply run produced a patch that passed targeted, shadow, and regression verification.
- The same provider contract can be tested deterministically with a local mock.

## Measured live results

### Dry-run

- model: `nvidia/nemotron-3-super-120b-a12b`
- run: `20260927T004704Z-1ce102a39e`
- final status: `DRY_RUN_NO_SOURCE_MUTATION`
- exit code: `0`
- elapsed: `31.556 s`
- source unchanged: YES

### Apply

- model: `nvidia/nemotron-3-super-120b-a12b`
- run: `20260927T004815Z-7243136b3f`
- final status: `ACCEPTED`
- mutation status: `APPLIED_VERIFIED`
- exit code: `0`
- elapsed: `16.670 s`
- targeted verification: PASS
- shadow verification: PASS
- regression verification: PASS
- root-cause verdict: PASS

## Friction / what could be better

Observed onboarding friction:

- API key creation was blocked until billing details were fully activated.
- The relationship between initial trial credit, billing activation, and promo credits was not immediately obvious in the UI.
- The API-key flow is security-conscious, but the one-time display means users must have a secure storage plan ready before closing the dialog.
- The current project architecture intentionally executes repository mutations/tests locally, so Token Factory is used for inference rather than direct repository authority.

Do not overstate these points: they are project-specific observations, not claims about every user's onboarding experience.

## Would we use it again?

**Current project answer: yes.**

Reason:

Token Factory gives access to an open NVIDIA model through a familiar API while allowing FORGE to keep its local authority boundary. That separation is useful for an evidence-gated coding agent: model capability can change without granting the model direct mutation rights.

## Still unknown / measure before final submission

- exact token usage for the two live runs;
- exact monetary cost of the two live runs;
- whether the hackathon promotional credit was successfully applied;
- whether a Token Factory Sandbox integration will be added or remain outside the current submission scope.

Do not invent values for these fields.
