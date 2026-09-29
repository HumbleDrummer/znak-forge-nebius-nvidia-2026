# Public Release / Secret Scan Checklist

Run this before any public push or video recording.

## Must not appear in Git

- Nebius API key
- `NEBIUS_API_KEY` value
- DPAPI secret blob
- RSA transfer keys/ciphertexts
- browser cookies/session data
- billing/card information
- account IDs not required by the submission
- private local paths containing personal data, when avoidable

## Expected secret storage

The active Nebius key is stored outside the repository in the Windows user profile via DPAPI.

The public repository should require users to provide their own:

`NEBIUS_API_KEY`

## Scan targets

Search tracked and untracked project files for:

- `v1.` key-like strings;
- `NEBIUS_API_KEY=`;
- `Bearer `;
- `sk-`;
- `api_key` assignments containing literals;
- `.env`;
- credential/private-key file names.

## Evidence hygiene

Hackathon receipts may contain:

- local repository paths;
- timestamps;
- model IDs;
- commands;
- hashes.

Before publishing receipts, redact only data that is not relevant to reproducibility. Do not modify technical verdicts or fabricate cleaner evidence.

## FEEDBACK + DEMO PITCH

This is a submission gate, not optional polish.

### FEEDBACK

- [ ] Explicitly name **Nebius Token Factory** and the **NVIDIA model** used.
- [ ] Explain what Token Factory / the model did in the project.
- [ ] Include the zero-to-first-call onboarding path.
- [ ] State concrete things that worked well.
- [ ] State concrete friction / what could be better.
- [ ] Answer whether we would use it again, with a project-specific reason.
- [ ] Keep measured facts separate from opinion.
- [ ] Do not invent token usage, cost, credit status, or other unknown values.
- [ ] Use `hackathon/REQUIRED_FEEDBACK.md` as the canonical source.

### DEMO PITCH

- [ ] Keep the public demo under **3:00**; target **2:45–2:55**.
- [ ] Pitch order: **problem -> working solution -> intended user/value -> Nebius/NVIDIA usage -> evidence/result**.
- [ ] Say **Nebius Token Factory** and **NVIDIA Nemotron** explicitly in the audio.
- [ ] Show Nebius/NVIDIA names on screen as well as in the submission text / Built With.
- [ ] Show a real working runtime path and final evidence/statuses, not slides alone.
- [ ] Keep secrets, billing/account screens, and private credentials out of the recording.
- [ ] Use `hackathon/VIDEO_SCRIPT_3MIN.md` as the canonical recording script.

## Public test build

- URL: https://znak-forge-demo.znakhumbledrummer.chatgpt.site
- [x] No-key deterministic accepted/rollback test is publicly reachable.
- [x] Scope is disclosed: browser test build does not call the model or mutate a repository.
- [x] Live Nebius Token Factory CLI path is linked from the public build.

## Public repository

- URL: `https://github.com/HumbleDrummer/znak-forge-nebius-nvidia-2026`
- Visibility: PUBLIC
- License: MIT

## Release blockers

- Final Devpost custom-answer ratings and user-owned eligibility confirmations remain to be completed before the actual submit.
- A public YouTube demo is now verified at https://youtu.be/BZf4hUlFIYs (2:48).
