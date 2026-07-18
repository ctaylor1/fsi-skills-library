# Domain Rules — service-recovery-assistant

Orientation references: fair-treatment-of-customers / complaint-handling principles and the
firm's service-recovery standard. The firm's **approved goodwill / redress matrix**,
**approval thresholds**, and **approved apology language** take precedence and are versioned
contracts (`config:svc-recovery@<version>`). All scoring below is configuration, not
judgment, and is reproduced by `scripts/calculate_or_transform.py`.

## Severity scoring (deterministic)

| Input | Contribution (default) |
| ----- | ---------------------- |
| Failure type | service_outage +3; payment_delay / incorrect_fee / data_error / misinformation / processing_delay +2; missed_callback +1; other +1 |
| Downtime | ≥48h +3, ≥24h +2, ≥4h +1 |
| Repeat failure (same issue) | +2 |
| Missed commitment | +1 |

Bands: **High** ≥ 6, **Medium** 3–5, **Low** ≤ 2.

## Customer-impact scoring (deterministic)

| Input | Contribution (default) |
| ----- | ---------------------- |
| Financial detriment | ≥ $500 +3, ≥ $100 +2, ≥ $1 +1 |
| Distress | high +3, medium +2, low +1 |
| Inconvenience | high +2, medium +1 |
| Vulnerability flag | +2 (also forces Tier 3 approval + specialist referral) |
| Tenure | ≥ 10y +2, ≥ 3y +1 |

Bands: **High** ≥ 7, **Medium** 4–6, **Low** ≤ 3.

## Goodwill matrix (the ONLY source of a goodwill gesture)

| Severity \ Impact | High | Medium | Low |
| ----------------- | ---- | ------ | --- |
| **High** | $200 | $150 | $100 |
| **Medium** | $120 | $75 | $40 |
| **Low** | $60 | $30 | $15 |

Cap: **$200**. Goodwill is never proposed above the cap. Any case the business believes
warrants more than the matrix allows is escalated to a manager as an exception — the skill
does not draft a figure above the cap.

## Direct redress (factual reimbursement, not goodwill)

- Direct redress reimburses a **documented** financial detriment (an actual overcharge,
  fee, or quantified loss on file). If the detriment is **not documented**, the case is
  `needs-data` and **no redress is proposed** — the skill never invents or estimates a
  reimbursement.
- `total = direct_redress + goodwill_gesture`.

## Approval authority tiers (versioned thresholds)

| Tier | Role | Default |
| ---- | ---- | ------- |
| Tier 1 | Service agent | total ≤ $50 |
| Tier 2 | Team lead | total ≤ $150 |
| Tier 3 | Operations manager | total > $150, any vulnerability, or above standard authority |

## Hard boundaries (fail closed)

- No **sending / delivery / payment / posting** — draft only.
- No **goodwill above cap**; no **redress of an undocumented detriment**.
- No **liability / negligence admission**, **guarantee**, or **entitlement** language.
- No **unsupported monetary figure** in the drafted communication.
- No **investment / legal / tax advice**.
- No **formal complaint decision** — refer to `complaint-resolution-assistant`.

## Draft package — required contents

Durable `case_id`; failure assessment (severity band, cited); customer impact (impact band,
vulnerability); precedent + applicable policy and a fair-value note; proposed remediation
(direct redress + goodwill = total, reason codes, `matrix_version`, cap check, cited); draft
customer communication (apology, explanation, remediation offer, next steps — approved
language, computed figures only, cited); required approval (tier + approver role, status
pending); sources; standing note.
