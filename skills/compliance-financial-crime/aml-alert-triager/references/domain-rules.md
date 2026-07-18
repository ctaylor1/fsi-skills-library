# Domain Rules — aml-alert-triager

Orientation references: BSA/FinCEN recordkeeping and SAR-confidentiality, 2026 FINRA report
(AML). The firm's AML program standard and its **approved suppression rule set** take
precedence and are versioned contracts.

## Priority scoring (deterministic, documented)

Priority is computed from explainable inputs; the mapping is configuration, not judgment.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Customer risk rating | High +3, Medium +1, Low 0 |
| Aggregate alert amount | ≥ 100k +3, ≥ 25k +2, ≥ 10k +1 |
| Sanctions/adverse-media proximity flag | +4 (also forces route to specialist) |
| Typology hint (e.g., rapid movement, structuring-adjacent) | +2 |
| High-risk geography exposure | +2 |
| Velocity (alerts on this entity in 90d) | +1 per prior alert, capped +3 |

Bands: **P1 (Elevated)** total ≥ 7 or any sanctions/adverse-media flag; **P2 (Standard)**
3–6; **P3 (Low)** ≤ 2. Priority is a triage rank for a human, not a typology conclusion.

## Approved suppression rules (the ONLY suppressions permitted)

| Rule ID | Condition | Evidence required |
| ------- | --------- | ----------------- |
| `SUP-DUP-01` | Exact duplicate of an open alert/case (same entity, rule, period, txns) | Parent `case_id` + matched txn IDs |
| `SUP-WL-INTERNAL` | Both legs are firm-whitelisted internal accounts on the approved list | Whitelist entry ID + both account refs |
| `SUP-SEASONAL-01` | Matches a documented seasonal false-positive pattern approved for this rule | Pattern ID + qualifying txns |

Any alert **not** matching one of these is **not** suppressible by this skill. Suppression
is logged with the rule ID and the approved-rule-set version, and is subject to reviewer
sampling. Suppression is **not** case closure and never applies to a genuine alert.

## Hard boundaries (fail closed)

- No **substantive case closure**, **exoneration**, or **SAR filing/drafting**.
- No **suppression** outside the three approved rules above.
- No **tipping-off**: never produce customer-facing text revealing monitoring/SAR activity.
- No **typology determination**; typology *hints* are for routing only.
- No **auto-merge** of entities/cases; dedup **links** for human confirmation.

## Escalation bundle — required contents

Durable `case_id`; chronology of alerted activity; parties (masked) with roles; amounts and
instruments; KYC summary + customer risk rating; sanctions/adverse-media flags; linked
prior cases; the triggering rule + period; citations for every item; recommended priority.
