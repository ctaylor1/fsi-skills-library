# Domain Rules — claim-settlement-authority-packet

The authority matrix governs (versioned). Orientation: package a settlement-authority *request*
and identify the required approver tier by a deterministic lookup. The packet requests; the human
approves.

## Computation (deterministic)
| Metric | Definition |
| ------ | ---------- |
| `total_exposure` | `indemnity_estimate + expense_estimate` (from the supplied evaluation) |
| `required_tier` | The smallest matrix tier whose `max_amount ≥ total_exposure` |
| `required_approver` | The `approver_role` of the required tier |
| `exceeds_matrix` | True when `total_exposure` is above every tier cap → escalate |

Exposure is taken from the evaluation as supplied; the packet never re-estimates the claim value.
The matrix is a **versioned contract**; caps/roles are never guessed.

## Completeness (deterministic)
- Each `required_item` (e.g. claim_summary, evaluation_basis, evidence_index,
  coverage_confirmation) must be present; a missing one is a completeness gap.

## Disposition mapping (review-only)
- `packet-ready` — required tier resolved and all checklist items present.
- `gaps-for-review` — a completeness gap or `exceeds_matrix`. A triage suggestion for the approver,
  **not** an approval.

## Hard boundaries (fail closed)
- Never approve a settlement, grant/exercise authority, or authorize payment; never set or
  re-estimate the amount; never approve an exceeds-matrix exposure at the top tier — escalate.
