# Controls — identity-access-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human control owner must adjudicate every finding and
  approve every staged revocation before any access change, certification, or system-of-record
  write occurs. The skill produces evidence and staged candidates only.

## Prohibited (fail closed)

- No **access decision**: never grant, deny, approve, or reject access, and never state that
  access "is approved/denied".
- No **execution**: never revoke, remove, disable, deprovision, or otherwise change an
  entitlement or account. Staged revocations are **candidates** (`status: staged_for_approval`),
  not writes.
- No **certification / attestation**: never mark an entitlement certified/recertified, sign an
  attestation, or complete a certification campaign.
- No **closure or filing**: never close the review/case, suppress a finding outside the
  documented deterministic logic, or file a control result to a system of record.
- No **threshold tuning to the individual**: use only the versioned config (SoD rules,
  inactivity/dormancy/certification thresholds).
- No **opaque scoring** presented as decisive; findings are explainable, rule-based, and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥ 1 cited evidence row.
- `suggested_priority` equals the deterministic mapping from `fired_findings`.
- No decision / execution / closure / filing / certification language in the narrative,
  notes, or finding reasons (regex screen: "revoked", "disabled the account", "deprovisioned",
  "certification complete", "recertified", "closed the review", "access approved", etc.).
- Every staged revocation is a candidate (`status` ∈ {staged_for_approval, pending_approval,
  recommended}) tied to a **fired** finding — an executed/completed status fails closed.
- Standing disclaimer present: "Access-review evidence and staged recommendations only; not an
  access decision. No entitlement has been revoked, disabled, or certified."
- `context_prompts` included when any finding fired.

## Segregation of duties (conduct)

- The skill supports the SoD control; it does not *own* the SoD decision. Flag toxic pairs
  with evidence and stage a candidate for the control owner — never choose which side to
  remove as a final decision.
- Do not use protected-class attributes or proxies in any finding rule.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Identity and entitlement data is sensitive; minimize
  output to the accounts/grants that evidence a fired finding.
- Do not expose broader HR PII — worker **status** only is needed for `orphaned_account`.
- Retain the review + citations + `config_version` per records policy; log the read and any
  control-owner approval of staged revocations.

## Reproducibility

`review_id` binds the output to the exact extract, `as_of`, and **config version**; re-running
with the same inputs and config reproduces the findings, staged candidates, and priority.
