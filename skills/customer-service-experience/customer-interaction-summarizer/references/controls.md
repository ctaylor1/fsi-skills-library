# Controls — customer-interaction-summarizer

- **Risk tier:** R1 — informational. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the summary is delivered to the
  customer or written to a system of record; not required for the agent's own read.

## Prohibited (fail closed rather than do these)

- No **advice, recommendation, opinion, or next-best-action** — what the agent or customer
  should do, offer, say, or escalate next (route to `next-best-action-assistant`).
- No **determination**: whether a complaint is justified / should be upheld or rejected;
  whether conduct was compliant; whether the customer is vulnerable; whether a claim,
  coverage, refund, or benefit is eligible / approved / denied; whether activity is
  fraud/AML. Those belong to the adjacent decision-support skills, each with human
  adjudication.
- No **inventing** facts, promises, commitments, or outcomes not stated in the interaction;
  no attributing a commitment to a party who did not make it.
- No **merging** of multiple interactions, dates, or channels without explicit user
  confirmation.
- No **de-anonymizing** or echoing raw customer identifiers.

## Required "no-advice / no-determination" language screen

`scripts/validate_output.py` scans the narrative and any notes/assessment text for two
families of prohibited phrasing and **fails closed** on any hit:

- **Advice / next-best-action** — recommend, we suggest/advise, you/the agent should,
  next best action, best course of action, should offer/refund/waive/escalate, etc.
- **Determination** — complaint is upheld/justified/rejected, uphold/reject the complaint,
  this is fraud, customer is vulnerable, is (not) eligible, coverage/claim approved/denied,
  we will waive/refund/credit, etc.

Attributed, cited commitments and disclosures in the structured lists are **records of what
was said** and are not scanned as the assistant's own language — the screen targets the
narrative/assessment prose only. A standing disclaimer must be present: "Informational
summary only; not advice and not a determination. Commitments and disclosures are recorded
as stated in the interaction and must be verified against the system of record."

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)**.
- Mask customer identifiers to last 4 in all output; `validate_output` flags any run of 7+
  consecutive digits in the customer reference or narrative as an unmasked-identifier
  failure. Keep interaction content within the approved environment; never exfiltrate.
- Retain the summary + citations per records policy. Log: source read, summary creation,
  and any external-delivery approval (who/when).

## Reproducibility

Given the same interaction source and segments, the summary must be reproducible: the
`summary_id` binds the output to the exact interaction and citations used.
