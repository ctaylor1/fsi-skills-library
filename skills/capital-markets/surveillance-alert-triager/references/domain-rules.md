# Domain Rules — surveillance-alert-triager

Orientation references: firm market-conduct / market-abuse surveillance program standard,
e-comms supervision & recordkeeping obligations, and the venue/regulator scenario library
(e.g., spoofing/layering, wash trades, marking-the-close, insider/MNPI-adjacency, comms
lexicon). The firm's surveillance program standard and its **approved suppression rule set**
take precedence and are versioned contracts.

## Priority scoring (deterministic, documented)

Priority is computed from explainable inputs; the mapping is configuration, not judgment.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Account/desk risk rating | High +3, Medium +1, Low 0 |
| Aggregate alerted notional | >= 1,000,000 +3, >= 250,000 +2, >= 50,000 +1 |
| Restricted-list / watch-list proximity flag | +4 (also forces escalation) |
| Scenario severity hint (e.g., MNPI-adjacent, manipulation-adjacent) | +2 |
| Cross-product / cross-venue linkage | +2 |
| Velocity (alerts on this account/desk in 90d) | +1 per prior alert, capped +3 |

Bands: **P1 (Elevated)** total >= 7 or any restricted-list proximity flag; **P2 (Standard)**
3–6; **P3 (Low)** <= 2. Priority is a triage rank for a human, not a scenario conclusion.

## Approved suppression rules (the ONLY suppressions permitted)

| Rule ID | Condition | Evidence required |
| ------- | --------- | ----------------- |
| `SUP-DUP-01` | Exact duplicate of an open alert/case (same entity, scenario, period, and its evidence is a subset of the parent's) | Parent `case_id` + matched evidence IDs |
| `SUP-WL-KNOWN` | Both legs are firm-approved known-benign accounts on the whitelist (e.g., approved market-maker books) | Whitelist entry + both account refs |
| `SUP-CALIB-01` | Matches a documented calibration/tuning false-positive pattern approved for this scenario | Pattern ID + qualifying evidence |

Any alert **not** matching one of these is **not** suppressible by this skill. A
restricted-list / watch-list proximity flag **overrides** all suppression and forces
escalation. Suppression is logged with the rule ID and the approved-rule-set version and is
subject to reviewer sampling. Suppression is **not** case closure and never applies to a
genuine alert.

## Hard boundaries (fail closed)

- No **case closure**, **market-abuse / manipulation / insider-trading determination**,
  **exoneration**, or **regulatory filing**.
- No **suppression** outside the three approved rules above.
- No **scenario/typology determination**; scenario *hints* are for routing only.
- No **auto-merge** of entities/cases; dedup **links** for human confirmation.

## Evidence bundle — required contents

Durable `case_id`; deterministic chronology of the alerted activity (each event cited);
parties (masked) with roles; notional and instruments; account/desk risk context; scenario
and period; restricted-list/watch-list flags; linked prior cases; citations for every item;
recommended priority. Built deterministically by `scripts/calculate_or_transform.py`.
