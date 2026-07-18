# Controls — claim-readiness-checker

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the readiness assessment goes to
  the policyholder/producer or is written to the claim system of record.

## Prohibited (fail closed)

- No **coverage or eligibility determination** — never state or imply that a loss **is / is
  not covered**, that an **exclusion applies**, or that the claim is/should be **eligible**.
- No **claim adjudication** — never **approve, deny, close, settle, price, or pay** a claim,
  or recommend that action as a decision.
- No **settlement or payout amount**, reserve figure, or "we will pay …".
- No **fraud determination** — never assert a claim is fraudulent; potential-fraud handling
  is a separate skill and a human referral (`claims-fraud-referral-assistant`).
- No **legal advice** on the policyholder's rights, deadlines, or dispute strategy.
- No **threshold tuning to the individual claim**; use only the versioned config catalog.

Readiness is a **completeness and timeliness triage suggestion** (`Ready` / `Ready with minor
gaps` / `Not ready`), never a decision on the claim.

## Required output screens (`scripts/validate_output.py`)

- Every check that carries evidence rows cites each row (document, form, and deadline
  evidence is traceable to a source).
- Every gap names an `item` and a `category`.
- `readiness_status` equals the deterministic mapping from the gap set (see
  [domain-rules.md](domain-rules.md)).
- No coverage/eligibility/claim-decision/settlement/fraud language (regex screen: "is
  covered", "not covered", "coverage is confirmed/denied", "claim is approved/denied",
  "approve/deny the claim", "is/not eligible", "excluded under the policy", "settlement
  amount", "we will pay", "payout of", "issue payment", "fraudulent", etc.).
- Standing disclaimer present: "Readiness and completeness check only; not a coverage,
  eligibility, or claim decision. No claim has been adjudicated, approved, denied, or paid."
- `considerations` included whenever any gap exists.

## Fairness / conduct

- Do not use protected-class attributes or proxies in any check or narrative.
- Describe gaps factually (what is missing/expiring); do not characterize the claimant or
  speculate about motive.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask policy/claim identifiers where feasible
  (last 4). Minimize claimant data in output to what evidences a gap or a present item.
- Retain the readiness assessment + citations + `config_version` per records policy; log the
  read and any external-delivery / system-of-record approval.

## Reproducibility

`readiness_id` binds the output to the exact inputs, claim type, and **config version**;
re-running with the same inputs and config reproduces the checks, gaps, and status.
