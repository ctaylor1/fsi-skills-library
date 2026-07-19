# Domain Rules — claims-triage-assistant

Orientation references: NAIC Unfair Claims Settlement Practices model, state prompt-pay /
acknowledgement timeframes, and the carrier's claims-handling standard. The firm's approved
**severity map** and **triage config** take precedence and are versioned contracts. Every
number below is a *default* that a deployment overrides via `severity_map` / `triage_config`
on the input; the version used is recorded on each triage record.

All bands and routes are **recommendations for human adjudication**. Nothing here decides
coverage, liability, reserve, payment, assignment, or closure.

## Severity / complexity (deterministic, documented)

Handling-complexity score = claim-type base + explainable drivers. It is **not** an exposure
or reserve figure.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Claim-type base | bodily-injury / general / auto / products / professional **liability** +3; property-damage, business-interruption +2; auto physical-damage, theft, other +1 |
| Estimated exposure | ≥ 250k +3, ≥ 100k +2, ≥ 25k +1 (first match only) |
| Injuries | +2 |
| Fatality | +3 |
| Litigation | +3 |
| Coverage question surfaced | +2 |
| Multiple parties (> 2 on file) | +1 |

Bands: **S1 (Complex)** score ≥ 7; **S2 (Moderate)** 3–6; **S3 (Standard)** ≤ 2.

## Urgency / service level (deterministic, documented)

| Input | Contribution (default) |
| ----- | ---------------------- |
| Fatality | +3 |
| Injuries | +2 |
| Catastrophe event | +2 |
| Statutory deadline within 60 days of report | +2 |
| Business interruption | +2 |
| Vulnerable claimant | +1 |

Bands: **U1 (Immediate)** score ≥ 5; **U2 (Prompt)** 2–4; **U3 (Routine)** ≤ 1. Suggested
first-touch service level (default): U1 = 4 hours, U2 = 1 business day, U3 = 3 business days.
The service level is a recommended target, not a guarantee.

## Coverage questions (surfaced, never answered)

A coverage question is **flagged for a human**; the skill never states whether cover applies.
Triggers:

- Policy status shown as `lapsed` (or otherwise not in force) — confirm cover at date of loss.
- Loss date falls **outside** the policy period — confirm cover was in force.
- One or more `exclusion_hits` — a human assesses whether the exclusion applies.

Any surfaced question raises the severity score (+2) and routes to `coverage-gap-analyzer`.

## Routing recommendations (order applied)

| Trigger | Recommended owner | Kind |
| ------- | ----------------- | ---- |
| Fraud indicators present | `claims-fraud-referral-assistant` (SIU referral) | skill |
| Subrogation potential | `subrogation-opportunity-screener` | skill |
| Coverage question(s) surfaced | `coverage-gap-analyzer` | skill |
| Catastrophe event | Catastrophe / major-loss unit | human |
| Vulnerable claimant | Accommodation / support team | human |
| Litigation (matter in suit) | Claims litigation / legal counsel | human |
| Severity S1 (Complex) | `claims-file-reviewer` (deeper file review) | skill |

A claim may carry several routes; each names its owner and reason. Routing is a recommendation
a human confirms — the skill never assigns the claim in the system of record.

## Dispositions (this skill may set only these)

| Disposition | When |
| ----------- | ---- |
| `draft-ready` | Classified, no specialist route indicated — standard queue at the recommended bands |
| `refer-specialist` | One or more specialist/human routes recommended |
| `needs-data` | `claim_type` is not in the severity map (never guessed a band) |
| `needs-review` | Liability claim with **undetermined** liability — fails closed to human adjudication |

It may **not** set `assigned`, `covered`, `denied`, `approved`, `reserved`, `settled`,
`closed`, or `filed`.

## Hard boundaries (fail closed)

- No **coverage determination** — questions are surfaced, never answered.
- No **reserve** setting/change, **approval/denial**, **payment/settlement**, or **closure**.
- No **assignment** in the system of record — a queue is recommended, a human assigns.
- No **fraud or liability conclusion** — fraud indicators are a referral signal; liability is
  a human adjudication.
- No **sending/filing** — no claimant/producer contact and no regulatory report.

## Draft triage summary — required sections

Every `draft-ready` / `refer-specialist` record renders all six sections (verbatim headings)
from [../assets/output-template.md](../assets/output-template.md): **Claim summary**;
**Severity and complexity**; **Urgency and service level**; **Coverage questions to resolve**;
**Recommended routing**; **Human adjudication required** — plus the DRAFT marker, cited
drivers, the pending `triage_lead_review` / `claims_supervisor_approval` approvals, and the
standing note.
