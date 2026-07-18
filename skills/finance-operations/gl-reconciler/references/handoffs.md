# Adjacent-Skill Handoffs — gl-reconciler

This skill produces a reconciliation with a classified break list, lineage, and
**proposed-only** correction entries (durable `reconciliation_id`), then stops. It does not
post journals, resolve subledger exceptions to disposition, explain operating variances, or
package audit deliverables.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `accounts-payable-exception-resolver` | A break is an AP subledger exception (unmatched invoice/payment, duplicate) needing a resolution workflow, not just a GL correction | `reconciliation_id` + the break rows |
| `fpa-variance-analyzer` | The GL/subledger gap is actually an operating or budget **variance to explain**, not a reconciliation break | account + period + amounts |
| `regulatory-reporting-data-validator` | The reconciled account feeds a regulatory return and needs data-quality validation | `reconciliation_id` + reconciled balance |
| `audit-evidence-packager` | The reconciliation + proposed corrections become evidence for an audit request | `reconciliation_id` + breaks + lineage |
| `financial-statement-audit-assistant` | Substantive reconciliation support is being assembled into an audit workpaper | `reconciliation_id` + tie-out |

## Upstream (may call this skill)

`month-end-close-orchestrator` sequences the close and may request an account reconciliation
as a close task; it consumes the `reconciliation_id` and tie-out status. The orchestrator (an
approval-gated R4 workflow) — not this skill — gates the eventual posting of any approved
correction.

## Posting the proposed corrections (human / authorized system)

There is **no catalog skill that posts journal entries**, by design. Approved corrections are
posted by an **authorized human (controller / senior accountant) in the ERP** under
segregation-of-duties controls. This skill hands over `PROPOSED` entries and the supporting
evidence; the review, approval, and posting happen outside it.

## Not this skill (route elsewhere)

- **Payment / settlement reconciliation** (cash vs settlement network, nostro/vostro) →
  `settlement-break-reconciler` or `transaction-reconciliation-helper` (Payments), not GL
  control-account reconciliation.

## Duplicate-execution prevention

- This skill **classifies and evidences breaks and proposes corrections only**; it must not
  post, adjudicate which side is correct, resolve subledger exceptions to disposition, or
  approve its own corrections — those belong to the human reviewer and the downstream skills.
- Downstream skills reuse the `reconciliation_id`, breaks, and lineage rather than
  recomputing the match.
