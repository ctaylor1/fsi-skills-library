# Controls — agent-permission-scope-reviewer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis (a recommended disposition is a *proposal* for a human adjudicator, not an
  access decision).
- **Human approval:** `required` — before any entitlement is granted, revoked, or
  provisioned, before the agent is cleared for an environment, and before the review is
  closed or a waiver/exception is filed.

## Prohibited (fail closed)

- No **access decision**: do not approve, deny, condition-as-final, or clear a scope for
  production. Recommend only.
- No **entitlement action** or instruction to act: grant, revoke, provision, de-provision,
  rotate, or issue a token/role/credential.
- No **review closure**, risk **acceptance**, or **waiver/exception filing** — those are
  adjudicator/GRC actions.
- No **rule invention**: every finding must use an approved rule id from the versioned
  policy; no ad-hoc severities.
- No **default-safe assumptions**: a missing field is `not_evaluable`, never silently
  treated as compliant.

## Recommended-disposition states (this skill may set only these)

`Remediate-before-approval` | `Conditional-adjudication-required` | `Review-minor-findings`
| `No-exceptions-adjudication-required`. It may **not** set `approved`, `denied`,
`granted`, `provisioned`, `cleared`, `closed`, or `waived`.

## Required output screens (`scripts/validate_output.py`)

- Every finding uses an **approved rule id** and has ≥1 cited evidence row.
- `recommended_disposition` equals the deterministic mapping from the findings' severities.
- No **autonomous decision/approval/provisioning/closure/filing language** (regex screen:
  "scope approved", "access approved", "approved for production", "grant the role/access",
  "provision the token/credential", "revoke the token/credential", "close the review",
  "file a waiver/exception", "no human review needed", "certify … compliant", etc.).
- `human_adjudication_required` is present and `true`.
- Standing disclaimer present: "Least-privilege review evidence only; not an access approval
  or denial. No entitlement has been granted, revoked, or provisioned, and no review has
  been closed. Human adjudication is required."

## Segregation of duties

Reviewing scope is distinct from adjudicating it and from provisioning it. The same person/
skill must not both produce the review and approve/grant the entitlement. The skill's own
entitlements are read-only across IAM, catalog, logs, and policy — it holds no grant path.

## Data classification, privacy, records

- **Confidential** (system entitlement metadata). The skill does not read customer data from
  the reviewed sources; it reasons about *access to* those sources.
- Retain the review, findings, citations, and `policy_version` per records policy; log the
  reviewer identity on every read and any downstream adjudication reference.

## Reproducibility

`review_id` binds the output to the exact manifest, `as_of`, and **policy version**;
re-running with the same manifest and policy reproduces the findings and recommended
disposition.
