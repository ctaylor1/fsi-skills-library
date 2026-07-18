# Controls — customer-onboarding-document-checker

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the gap report is sent to the
  customer/applicant or written to the onboarding case/system of record.

## Prohibited (fail closed)

- No **onboarding approval** or statement/implication that the package is **approved**,
  the applicant is **cleared/eligible to onboard**, or the account may be **opened**.
- No **identity verification** determination ("identity verified/confirmed", "customer is
  verified") — this skill checks that documents are present and consistent, not that the
  identity is genuine.
- No **KYC / CIP / CDD / sanctions / PEP determination** ("KYC passed", "CIP satisfied",
  "no sanctions match", "not a PEP") — those belong to the compliance screening skills and
  a human adjudicator.
- No **waiving** of a required document, signature, or exception — a waiver is an approval
  decision reserved for an authorized human.
- No **account action** (open, activate, fund) or recommendation to take one.
- No **threshold/checklist tuning to the individual**; use only the versioned config.

## Required output screens (`scripts/validate_output.py`)

- Every fired check has ≥1 cited evidence row (document, field, config requirement, or
  exception).
- No determination/approval/action language (regex screen: "approved for onboarding",
  "identity verified/confirmed", "customer is verified", "KYC/CIP passed/cleared",
  "no sanctions match", "not a PEP", "open the account", "waive the requirement", etc.).
- `readiness_status` equals the deterministic mapping from the fired checks + severities.
- Standing disclaimer present: "Completeness check only; not an onboarding approval,
  identity verification, or KYC/CIP determination. No account has been opened."
- Remediation prompts included when any check fired.

## Fairness / conduct

- Do not use protected-class attributes or proxies as completeness signals.
- Describe document gaps and field mismatches factually; do not infer intent, character, or
  legitimacy from a discrepancy.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask ID/TIN/account numbers to last 4.
- Minimize customer data in the output to what evidences a finding.
- Retain the checklist result + citations + `config_version` per records policy; log the
  read and any external-delivery approval. Never exfiltrate customer data.

## Reproducibility

`checklist_id` binds the output to the exact package inputs, `as_of` date, and **config
version**; re-running with the same inputs and config reproduces the findings and the
readiness status.
