# Controls — management-reporting-packager

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a DRAFT management report package for human review.
- **Human approval:** `external-delivery` — human approval is required before the pack is
  delivered externally (board, committee, investors, regulator) or posted to any system of
  record. The reviewer's own read needs no approval. Internal drafting is reviewer-sampled.

## Prohibited (fail closed)

- **Delivering, submitting, distributing, emailing, or posting** the pack (to the board, a
  committee, a regulator, or the GL/system of record). Draft-only, always.
- **Marking any figure final / board-approved / certified**, or recording the **delivery**
  approval. Delivery sign-off is a human/operations action.
- **Unsupported claims:** any KPI figure without a `source_ref`, or any commentary line
  without a `commentary_source_ref`. An unsupported KPI blocks the package.
- **Overriding, netting, or explaining away a reconciliation break** beyond tolerance.
- **Forward-looking guarantees or investment advice** (e.g., "guaranteed to beat budget",
  "the stock is a buy").
- Marking a package `ready-for-review` while any unsupported claim, unreconciled break, or
  missing required approval remains.

## Package states (this skill may set only these)

`blocked` (any blocking reason present) | `ready-for-review` (all KPIs supported, all
reconciliations tie, preparer + reviewer recorded). It may **not** set `approved`,
`delivered`, `sent`, `posted`, or `final`. `delivery_status` is always `draft`.

## Required output screens (`scripts/validate_output.py`)

- All eight approved template sections are present (exact titles).
- `delivery_status` is `draft`; no send/submit/distribute/post language appears.
- Every KPI carries a citation; no KPI is `unsupported` when status is `ready-for-review`.
- `package_status` is consistent with unsupported claims, breaks, and missing approvals.
- Preparer and reviewer approvals are recorded; the delivery role is not recorded.
- No final-approval claims, no forward-looking guarantee / investment-advice language.
- The standing note & distribution-control disclaimer is present.

## Segregation of duties

Packaging is distinct from the underlying analysis (FP&A variance, GL reconciliation),
from certification/posting (close orchestration), and from delivery. The same skill must not
both draft the pack and obtain its delivery approval.

## Data classification, privacy, records

- **Confidential (financial records)** — may include pre-release, market-sensitive results.
  Minimize data in the pack to what the report requires; mask individual approver identities.
- Retain the assembled package, its citations, and the `config_version` per records policy;
  log the read and any external-delivery approval obtained by a human downstream.
- Pre-release financial results are price-sensitive: never distribute, and treat the draft
  as need-to-know until the named human approvals and delivery occur outside this skill.
