# Conflicts of Interest Reviewer — Phase 1 method

- Numeric thresholds come from an explicit supplied institution policy/configuration; they are not statutory thresholds. Missing policy evidence or necessary magnitude/MNPI facts makes the relevant indicator `Unknown`, never a zero-value or non-MNPI assumption.
- Gifts require supplied aggregate completeness before a below-threshold indicator. This calculator does not build a cross-record annual gift ledger or decide legal exclusions. Review aggregation, direction, recipient and applicable legal rules separately.
- Documentary checks assess dated disclosures, scoped sourced controls and supplied approvals. An approval must state decision, item scope, source, date and expiry covering the assessment date. Future/stale disclosure records and expired/out-of-scope approval claims do not satisfy the checklist.
- Document presence earns no mitigation credit. Each `residual_risk` and `matter_residual_risk` is `not_assessed`; the separate inherent indicator guides review. Source authenticity and control effectiveness remain unverified even when the documentary checklist is complete.
- Unknown facts or missing required records route to a conflicts/ethics reviewer. A below supplied threshold result is not an exemption, no-conflict finding or clearance.

## Supplied schema

Matter/as-of/config version, subject, cited conflict items, magnitude/MNPI facts, disclosures, scoped controls, approval claims and institution policy configuration. `aggregation_complete` is a supplied evidence assertion. Numeric fields are finite and nonnegative.

The authoritative executable shape check is `scripts/validate_input.py`. `scripts/calculate_or_transform.py`
contains the bounded calculation. The worked source fixture is `evals/files/matter_example.json`;
it is explicitly synthetic and must not be used as current law or institutional policy.

Default control checklists are illustrative triage prompts, not jurisdiction-specific law or a verified institution approval matrix. No approvals are authenticated, no mitigation effectiveness assessed, and no matter is cleared, waived, closed, filed or entered into a register.
