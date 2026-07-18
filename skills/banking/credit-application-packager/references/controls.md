# Controls — credit-application-packager

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft package for human review, not a filing or a
  decision.
- **Human approval:** `external-delivery` — a human must review and approve before the
  package is delivered, relied on for underwriting, or treated as a system-of-record change.
  Internal analytical assembly may be reviewer-sampled.

## Prohibited (fail closed)

- **Credit decisions**: approval, denial, adverse action, or any statement that the borrower
  qualifies / is cleared to close / ready to fund. These belong to the underwriter.
- **Completeness certification**: any claim that the package/file is complete, certified,
  fully documented, has no open items/exceptions, or meets all requirements. Formal
  certification is a separate control (`loan-package-completeness-checker`).
- **Delivery / submission**: sending, submitting, filing, transmitting, or delivering the
  package. Draft-only.
- **Fabrication**: inventing a document, value, approval, or borrower attribute. Missing
  items are open items.
- **Auto-merge** of conflicting borrower identities. Mismatches are `unresolved` for a human.

## Package assembly states (this skill may set only these)

Per component: `included` | `stale` | `unresolved` | `open-item` (missing) | `not-required`.
Package: `draft-assembled` only. It may **not** set `certified`, `complete`, `approved`,
`submitted`, or `delivered`.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (mirrors [../assets/output-template.md](../assets/output-template.md)).
- Every `included`/`stale`/`unresolved` component entry carries a citation (no unsupported
  or unapproved claims).
- Recorded approvals carry `type`, `approver_role`, `date`, and `citation`; missing required
  approvals appear as outstanding open items; `human_approval_required_before_delivery` is
  `true`.
- No credit-decision, completeness-certification, or send/submit/deliver language.
- `assembly_status` equals `draft-assembled`.
- Standing note present: "Draft credit package for human review only. This package is not a
  completeness certification, not a credit decision or adverse-action notice, and has not
  been submitted or delivered."

## Segregation of duties

Packaging entitlements are distinct from completeness certification and from credit
decisioning. The same person/skill must not both assemble the package and certify it complete
or approve the credit.

## Data classification, privacy, records

- **Highly Confidential — customer NPI/PII.** Mask borrower and account identifiers to what
  the package requires; never expose full account numbers or government IDs.
- Retain the package manifest, citations, and config/template versions per the bank's
  credit-file recordkeeping policy; log the analyst identity on every read and assembly.
- Keep data within the deployment's residency boundary.
