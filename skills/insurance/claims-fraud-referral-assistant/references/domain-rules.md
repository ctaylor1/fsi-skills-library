# Domain Rules — claims-fraud-referral-assistant

Orientation references: NAIC Insurance Fraud Prevention Model Act and state SIU/anti-fraud
plan requirements; Coalition Against Insurance Fraud red-flag guidance. The insurer's own
anti-fraud plan and its **approved fraud-indicator configuration** take precedence and are
versioned contracts. Indicators are *red flags that warrant human review*, never proof of fraud.

## Fraud-indicator scoring (deterministic, documented)

The score is computed from explainable indicators; the mapping is configuration, not
judgment. Weights and thresholds are the versioned default in
[scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py); deployments may
override via `indicator_config`.

| Indicator ID | Condition (default) | Weight |
| ------------ | ------------------- | ------ |
| `FR-LATE-REPORT` | Reported > 30 days after date of loss | +2 |
| `FR-EARLY-LOSS` | Loss within 60 days of policy inception | +3 |
| `FR-POST-INCREASE` | Loss within 30 days of a coverage increase | +3 |
| `FR-CLAIM-FREQ` | ≥ 3 prior claims in trailing 24 months | +2 |
| `FR-NO-REPORT` | Reportable loss with no police/fire report on file | +2 |
| `FR-DOC-GAP` | Supporting documentation incomplete | +1 |
| `FR-INCONSISTENT` | ≥ 2 flagged statement inconsistencies | +2 |
| `FR-LAPSE-REINSTATE` | Loss adjacent to a coverage lapse/reinstatement | +2 |
| `FR-PRIOR-SIU` | Insured has prior SIU referral history | +3 (also **forces** referral) |

Bands: **Refer** score ≥ 6 **or** any prior-SIU flag; **Monitor** 3–5; **Insufficient** ≤ 2.
The band drives a routing recommendation for a human, never a fraud conclusion.

Recommendations (the ONLY values this skill may emit):
`refer-to-siu` | `monitor` | `insufficient-indicators` | `needs-data`.

- `FR-PRIOR-SIU` is an **override**: a prior SIU history forces `refer-to-siu` regardless of
  score (analogous to a hard-routing flag), because the pattern belongs with human SIU intake.
- Only the nine indicator IDs above are approved. Any invented indicator ID fails the output
  screen. Every triggered indicator must carry evidence and a citation.

## Needs-data (never guessed away)

If policy inception date is missing/invalid, or the reportable-loss classification is
unknown, the claim is `needs-data`: the skill lists exactly what is missing and does not
fabricate the missing context to reach a recommendation.

## Hard boundaries (fail closed)

- No **fraud finding / determination** — indicators are red flags, not conclusions.
- No **adverse customer decision**: no claim denial, closure, rescission, or policy voiding.
- No **SIU decision on SIU's behalf** (no "referral accepted"/"no further action").
- No **accusatory customer-facing text** (defamation risk).
- No **indicator outside the approved catalogue**; no un-cited indicator.
- **Draft-only**: never send/submit/transmit the referral; a human routes it.

## Referral package — required contents

Durable `referral_id`; masked insured; policy/peril; loss and report dates; a chronology;
each triggered indicator with evidence and citation; the primary claim citation; the routing
recommendation, score, and band; and required human approvals recorded as **pending**
(referring-adjuster attestation and SIU intake acknowledgment). The drafted document follows
[../assets/output-template.md](../assets/output-template.md) and must contain every required
section header.
