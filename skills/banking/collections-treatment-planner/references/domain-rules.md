# Domain Rules — collections-treatment-planner

How the engine derives a **delinquency band**, runs the **suppression** and
**contact-frequency** screens, flags **enhanced care**, and maps a case to **eligible
treatment options**. Thresholds and eligibility rules are configuration (versioned, owned by
the collections policy team), not hard-coded judgments, and are never tuned to an individual.
Orientation references: the firm's collections & hardship standard, FDCPA / Regulation F
(consumer debt collection conduct and call-frequency presumption), and UDAAP guidance take
precedence over anything here.

## Delinquency bands (by days past due)

| Band | DPD (default config) |
| ---- | -------------------- |
| Current | 0 |
| Early | 1–29 |
| Mid | 30–59 |
| Late | 60–89 |
| Severe | 90+ |

## Suppression screen (hard boundary — honor before any outreach)

If any of these flags is set, outreach is **suppressed** and no channel is eligible; the case
routes to the appropriate specialist/legal path:

- `cease_communication` (FDCPA 1692c(c) — stop communicating except permitted notices)
- `attorney_represented` (contact counsel, not the consumer)
- `dispute_pending` (pause collection until the dispute/validation is resolved)
- `do_not_contact_window_active`
- `bankruptcy_flag` (automatic stay)

`servicemember_scra_flag` is surfaced for specialist handling (SCRA rate/process protections).

## Contact-frequency screen (Regulation F 7-in-7 presumption)

Count phone attempts in the trailing `call_cap_window_days` (default 7). If attempts ≥
`call_cap` (default 7), phone outreach is **not eligible** — additional calls would exceed the
presumed-compliant frequency. Quiet-hours (local 08:00–21:00) are surfaced for the human to
respect; the engine does not schedule calls.

## Treatment eligibility (config-driven)

| Treatment | Rule id | Eligible when (default config) |
| --------- | ------- | ------------------------------ |
| `payment_reminder` | TRT-REM-01 | 1 ≤ DPD ≤ `reminder_max_dpd` (89) |
| `promise_to_pay` | TRT-PTP-02 | DPD ≥ 1 |
| `payment_arrangement` | TRT-ARR-03 | DPD ≥ `arrangement_min_dpd` (30) **and** disclosed monthly surplus > 0 (indicative) |
| `hardship_forbearance` | TRT-HRD-04 | any vulnerability indicator or declared hardship |
| `due_date_change` | TRT-DDC-05 | DPD ≤ `due_date_change_max_dpd` (29) |
| `re_age_review` | TRT-RAG-06 | DPD ≥ `re_age_min_dpd` (60) — flagged for a human eligibility check |
| `settlement_referral` | TRT-STL-07 | DPD ≥ `settlement_min_dpd` (90) — referral to a specialist, not an offer |
| `external_credit_counseling_referral` | TRT-CCR-08 | any vulnerability indicator or declared hardship |
| `specialist_referral` | TRT-SPC-09 | any vulnerability indicator (enhanced-care routing) |

Each treatment is reported with `eligible`, a `rationale`, cited `evidence`, and
`requires_human_review: true`. `recommended_treatments` is exactly the set of eligible
options — a **shortlist for the specialist to consider**, not a decision. Ineligible options
are shown with the rule they missed for transparency.

## Enhanced-care handling (vulnerability)

When any vulnerability indicator is present the case is enhanced-care: prefer
forbearance/affordability-based options, offer specialist support and a counseling referral,
soften outreach tone, and never use the hardship as an adverse input.

## Hard boundaries (fail closed)

- Never **approve/deny, grant, modify, waive, settle, re-age, close, charge off, file, or
  report** — recommend and evidence only; the specialist adjudicates and an authorized system
  executes.
- Never breach a **suppression flag** or the **contact-frequency** presumption.
- Never make a **threat** or any FDCPA/UDAAP-prohibited statement.
- Never make an **affordability/credit determination**; the surplus figure is indicative.
- Never **tune eligibility rules to the individual**; use only the versioned config.
