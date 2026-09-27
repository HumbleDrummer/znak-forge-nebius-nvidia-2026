# Design notes

The core cycle is deterministic:

```text
BOOT -> ORIENT -> BASELINE -> REQUIREMENT_RECOVERY -> LOCALIZE
     -> HYPOTHESIS -> PATCH_PLAN -> MUTATION_GATE -> APPLY
     -> VERIFY_FUNCTIONAL -> VERIFY_CONTRACT -> VERIFY_SHADOW
     -> FINAL_REVIEW -> ACCEPTED | ROLLBACK
```

`BLOCKED` and `UNKNOWN` are valid terminal outcomes. The transition table rejects shortcuts such as `ORIENT -> APPLY`.

Five control planes remain separate:

1. The task file carries intent.
2. Evidence records observations and their provenance.
3. The mutation gate decides authority.
4. The transaction performs one bounded change.
5. Independent verdicts decide acceptance or verified rollback.

The evidence cone begins with a bounded topology inventory. Provider evidence then narrows to source/locator, dependency neighbors and a localization proof. Hash-only evidence cannot pass the semantic evidence check.

The MVP uses full text replacements because they make the proposed end state, budget and rollback exact and inspectable. Each replacement is still coupled to requirement, evidence, hypothesis and verification references. This is intentionally smaller than a general patch language.

The engine accepts only when functional, contract, shadow, root-cause and baseline verdicts pass, and regression/related checks are either passing or explicitly not applicable. Any required unknown prevents acceptance.

