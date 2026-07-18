# Controls — iso-20022-message-interpreter

- **Risk tier:** R2 — analytical / explanatory support; no binding decision. **Action
  mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before an interpretation is delivered
  outside the analyst's own working context (e.g., sent to a counterparty/beneficiary bank,
  attached to a customer communication, or written to a system of record). Not required for
  the analyst's own read.
- **Scheduled agent:** `no`. This skill runs interactively; it never monitors or acts on a
  schedule.

## Prohibited (fail closed rather than do these)

- No **repair, correction, resubmission, cancellation, return, or fund-movement** of any
  payment, and no instruction to do so. Interpretation is read-only.
- No **regulated determination**: not fraudulent / not sanctioned / sanctions-clear /
  AML-clear / compliant / "safe to release" / "will settle". These belong to monitoring,
  investigation, and compliance functions.
- No **personalized financial, legal, or tax advice**, and no recommendation of a next
  action ("you should…", "we recommend…").
- No **silent correction** of a control-total break, invalid identifier, truncation, or
  unknown code — surface it as a finding; never overwrite the message.
- No **guessing** an unlisted status/reason/purpose code — report it as unknown with a
  pointer to the governing code list.

## Required no-advice / prohibited-claim screen

`scripts/validate_output.py` scans the narrative, finding messages, and notes for
remediation directives (resubmit, repair, release funds, retry, approve, "you should", "we
recommend") and regulated determinations (fraud, sanctions/AML clearance, "is compliant",
"guaranteed/will settle"). **Any hit fails closed.** A standing disclaimer must be present:
"Interpretation and explanation only; not a payment instruction, repair authorization, or
compliance/fraud determination."

## Deterministic gates

- `scripts/validate_input.py` — schema/structure, required identifiers and citations,
  datetime format (errors); control-total, currency, truncation, character-set, and
  missing-reason data-quality issues (warnings the explanation must surface).
- `scripts/calculate_or_transform.py` — deterministic classification, tie-outs, identifier
  checks (IBAN mod-97, BIC shape, UETR UUIDv4), truncation/character-set detection, and
  status decoding; produces the cited interpretation object.
- `scripts/validate_output.py` — citation coverage, control-total consistency, the no-advice
  screen, disclaimer presence, and rejected-status reason coverage (fail closed).

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII; cardholder data)**. ISO 20022
  messages carry names, account/IBAN numbers, agent identifiers, and remittance detail; some
  scheme flows carry card data.
- **Minimize and mask**: show account/IBAN and card identifiers masked (last 4) in any
  human-facing output; keep full values only inside the approved environment. Never place
  message content in URLs, logs at large, or external destinations.
- Keep interpretation and message content within the approved environment; never exfiltrate.
- **Log**: source read, interpretation produced (with the input identifiers and schema
  version), and any external-delivery approval (who / when). Retain per records policy.

## Reproducibility

Given the same message JSON and the same referenced schema/usage-guideline/code-list
versions, the interpretation must be reproducible: the same classification, tie-outs,
findings, and citations. Version identifiers are part of the output so a reviewer can
reproduce it.

## Escalation

- A control-total break, invalid mandatory identifier, or unknown mandatory code →
  surface as a finding and route to the appropriate diagnosis/investigation workflow
  (see [handoffs.md](handoffs.md)); do not resolve it here.
- Any request to act on the payment → decline and route to the approval-gated repair
  workflow or a licensed operations specialist.
