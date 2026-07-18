<!--
SIU Fraud Referral — controlled output template for claims-fraud-referral-assistant.
Every drafted referral MUST contain all of these sections (checked by
scripts/validate_output.py: REQUIRED_SECTIONS). Fill only from cited claim-system evidence.
This is a DRAFT for human review; it never makes a fraud finding or any claim decision.
Do NOT delete or rename the "##" section headers — they are the template-fidelity contract.
-->

# SIU Fraud Referral (DRAFT) — {CLAIM_ID}

Referral ID: FR-{CLAIM_ID}  |  Referring adjuster: {NAME / to be recorded}  |  Status: DRAFT — pending human review

## Claim Summary
- Claim: {CLAIM_ID}
- Insured (masked): {MASKED_INSURED_ID}
- Policy: {POLICY_REF}
- Peril: {PERIL}
- Date of loss: {LOSS_DATE}  |  Reported: {REPORT_DATE}

## Fraud Indicators Observed
Observed indicators (red flags) only — NOT a determination of fraud. One line per indicator,
each with its evidence and an inline source citation. Use ONLY approved indicator IDs
(`FR-*`, see references/domain-rules.md). Example:
- **FR-EARLY-LOSS** (weight 3): loss 17d after policy inception 2026-05-15
  Source: `claimsys:claim=CLM-3001`

## Chronology
Ordered timeline of the policy/loss/report events drawn from the claim record. Example:
- 2026-05-15 — Policy inception
- 2026-06-01 — Date of loss
- 2026-07-10 — Claim reported

## Supporting Evidence
State that every indicator above is sourced to the claim-system record, and list the primary
citations. No indicator may appear without a citation.

## Recommendation
State the routing recommendation (`refer-to-siu` | `monitor` | `insufficient-indicators` |
`needs-data`), the indicator score, and the band. Make explicit that this is a routing
recommendation for SIU intake, NOT a fraud finding or a coverage/claim decision.

## Required Human Approvals
- Referring adjuster attestation: pending
- SIU intake acknowledgment: pending

(These remain `pending` in any draft this skill produces; the skill never records human
approval as granted.)

## Limitations
No fraud finding has been made. No claim has been denied, closed, or otherwise decided, and
no adverse customer action has been taken. SIU adjudication and any decision require human
review. This draft is decision-support only.
