# Adjacent-Skill Handoffs — adverse-media-investigator

Adverse-media investigation (this skill) builds the **evidence bundle and a disposition
recommendation**. It is a separate control activity from the decisions it feeds: sanctions
adjudication, EDD sign-off, risk-rating change, and SAR filing all belong to other skills or
to a human owner. This skill emits a durable `case_id` and hands off; it never performs the
downstream regulated decision.

## Downstream (this skill recommends / routes to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `enhanced-due-diligence-packager` | `recommend-escalate-edd` — material adverse media resolved to the subject | `case_id` + evidence bundle + materiality band |
| `sanctions-match-adjudicator` | `recommend-route-sanctions-pep` — sanctions/PEP list proximity on a name-matched hit | `case_id` + list-hit evidence (identity **not** adjudicated here) |
| `customer-risk-rating-reviewer` | Adverse media may change the customer's risk rating | `case_id` + matched-hit summary |
| `due-diligence-packager` | Onboarding/periodic DD needs the adverse-media section | `case_id` + evidence bundle |
| `suspicious-activity-report-drafter` | **Only** if a downstream investigation later concludes a SAR may be warranted — never directly from this skill | the investigator's approved case |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `kyc-customer-due-diligence-screener` | Onboarding/periodic screening surfaces name / adverse-media hits to investigate |
| `beneficial-ownership-verifier` | Resolved beneficial owners / UBOs to screen for adverse media |
| `aml-alert-triager` / `transaction-monitoring-alert-investigator` | An AML case needing adverse-media context on the entity |
| `merchant-onboarding-risk-reviewer` / `customer-onboarding-document-checker` | Onboarding risk review requesting an adverse-media assessment |

If no catalog skill fits a particular next step (for example, final EDD sign-off, a
regulated determination, or a filing decision), the handoff is to a **human owner** — the
financial-crime investigator, MLRO/BSA officer, or licensed specialist — not to an automated
skill.

## Duplicate-execution prevention

- This skill **does not** adjudicate sanctions/PEP, recompute risk ratings, sign off EDD, or
  draft/file SARs — those belong downstream.
- The downstream owner consumes this skill's `case_id` and evidence bundle rather than
  re-investigating from raw hits.
- A discarded namesake is recorded with its disambiguator so a reviewer does not re-open it,
  and an unresolved subject stays `needs-data` until a human supplies identifiers.
