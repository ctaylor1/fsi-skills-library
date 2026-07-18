# Domain Rules — credit-application-packager

Orientation references: the bank's credit-file / loan-package standard and its per-product,
per-jurisdiction **required-components** and **required-approvals** contracts (versioned).
These take precedence and are versioned contracts. This skill applies the deterministic
assembly rules below; it does not exercise credit judgment.

## Assembly status (deterministic, per required component)

For each component in `required_components`, find its supporting document(s) and assign:

| Status | Condition | Consequence |
| ------ | --------- | ----------- |
| `included` | A supporting document exists, borrower identity matches, and it is not past its `expires` date | Cited in its package section |
| `stale` | Supporting document exists but `expires` < `as_of_date` | Cited **and** listed as an open item (refresh) |
| `unresolved` | Supporting document exists but its borrower `id`/`name` conflicts with the package borrower | Cited **and** listed as an open item (reconcile) — never auto-merged |
| `open-item` | No supporting document for a required component | Listed as a missing-component open item — never fabricated |
| `not-required` | Component is not in `required_components` for this product/jurisdiction | Section noted as not required |

Precedence when multiple conditions apply: **identity mismatch (`unresolved`) is checked
before staleness (`stale`)** — an identity conflict is the more serious flag and is surfaced
first. Every asserted status (`included`/`stale`/`unresolved`) must carry a citation.

## Borrower / entity consistency

A document conflicts when its `borrower_id` differs from the package `borrower.borrower_id`,
or its `borrower_name` differs from the package `borrower.legal_name`. Conflicts are marked
`unresolved` for human reconciliation. Documents that carry no borrower identity are packaged
on their component match but noted (the input validator warns that consistency is limited).

## Approvals capture (recorded, never assumed)

- Approvals with `status == "recorded"` are captured with `type`, `approver_role`,
  `approver` (masked), `date`, and `citation`.
- Every entry in `required_approvals` that has no recorded approval becomes an **outstanding**
  approval and an open item. An approval is never assumed granted.
- `human_approval_required_before_delivery` is always `true` — the assembled package is a
  draft; a human must approve before delivery.

## Conditions

Outstanding conditions (`status` not `satisfied`/`cleared`) are listed as open items with
their description and citation. Satisfied conditions are not open items.

## Open-items taxonomy

`missing-component` | `stale-document` | `identity-unresolved` | `outstanding-approval` |
`outstanding-condition`. Each open item names the item, its type, a required human action,
and (where a document exists) its citation.

## Hard boundaries (fail closed)

- No **credit decision** (approval/denial/adverse action/qualification/clear-to-close).
- No **completeness certification** (complete/certified/fully-documented/no-exceptions).
- No **delivery/submission** of the package (draft-only).
- No **fabrication** of documents, values, approvals, or borrower attributes.
- No **auto-merge** of conflicting borrower identities.

## Package manifest — required contents

`package_id`, `product`, `jurisdiction`, `as_of_date`, `config_version`, `template_version`,
`assembly_status: draft-assembled`, `human_approval_required_before_delivery: true`, the
canonical `sections` (package summary, borrower profile, application, financial information,
collateral, KYC/onboarding, approvals, open items, source index), the open-items list, and
the standing note.
