# Public test build

URL: https://znak-forge-demo.znakhumbledrummer.chatgpt.site

The public build is a no-key, deterministic browser test of the ZNAK FORGE authority boundary. It demonstrates two paths over the same normalized-SKU fixture:

- a canonical repair reaches `ACCEPTED / APPLIED_VERIFIED` after targeted, shadow and regression checks;
- a naive raw-string repair is blocked after the normalized shadow check fails, then marked `ROLLED_BACK`.

The page does not call a model, change a repository, collect credentials or send test-button data over the network. It is the accessible test build for judges and reviewers.

The live Nebius path remains in this repository:

- provider: NVIDIA Nemotron 3 Super 120B A12B;
- service: Nebius Token Factory;
- dry-run: `python hackathon/run_live_demo.py`;
- apply: `python hackathon/run_live_demo.py --apply`;
- setup and evidence: [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md).

The public browser build and the live CLI path are intentionally labeled separately. The browser build demonstrates the deterministic authority/verification layer; the CLI path demonstrates the real Token Factory inference call.
