# Domain Rules - investment-banking-pitch-builder

Orientation references: the firm's pitch/marketing-materials standard, control-room /
information-barrier policy, and the approved pitch **template** (a versioned contract). The
firm's standards and the template version take precedence and are versioned contracts.

## Page-inventory rules (every substantive page)

A page is `ready` only when **all** of the following hold; otherwise it is blocked:

| Requirement | Blocking status if missing |
| ----------- | -------------------------- |
| A one-line **takeaway** ("so what") | `needs-source` (completeness) |
| At least one **source citation** | `needs-source` |
| Every **claim** maps to an **approved** `source_ref` | `unsupported-claim` |
| Content **approval** recorded (`approved`) | `needs-approval` |

The first blocking condition found sets the page status. A page with an unsupported claim is
never `ready`, regardless of other approvals.

## Claim substantiation (no unsupported assertions)

- Every quantitative or qualitative claim must trace to an approved source. Unsourced or
  unapproved claims are flagged; they are **never** back-filled with a "reasonable" figure.
- **Prohibited language** (unsupported/promissory, blocked by `validate_output`): guarantee/
  guaranteed, risk-free, no risk, "can't lose", "will outperform/double/triple/beat the
  market", assured returns, "promise of returns", "certain to rise/deliver", and
  personalized advice ("you should buy/sell/invest").

## Template fidelity & completeness

- The assembled draft must contain every section in the template's `required_sections`
  (default: cover, executive-summary, market-overview, valuation, process-and-timeline,
  disclaimer). A missing required section blocks `approved-for-delivery`.
- Pages are ordered by the template's section order. The template `id@version` is recorded.

## Required approvals for external delivery

| Approval role | Owner | Purpose |
| ------------- | ----- | ------- |
| `banker_signoff` | Deal-captain / MD | Content, positioning, and accuracy sign-off |
| `compliance_control_room` | Control room / compliance | MNPI, conflicts, wall-cross, information barriers |
| `legal_disclaimers` | Legal | Confidentiality, no-offer / no-advice disclaimer set |

`approved-for-delivery` is permitted **only** when all required approvals are recorded and
`approved`; otherwise the draft stays `hold-for-approval`.

## MNPI / information barriers

Pitch materials routinely contain material non-public information. Control-room clearance and
wall-cross checks are required before external use; no selective disclosure. Distribution is
to cleared recipients only, by a person.

## Hard boundaries (fail closed)

- Never **send / submit / distribute / email / file**; never set a delivered state.
- Never **fabricate** a figure, chart, or source; never include an unapproved claim.
- No **personalized investment/legal/tax advice**; no guarantee/promissory language.
- Never **self-approve** the required control approvals (segregation of duties).

## Assembled draft - required contents

`engagement_id`; template `id@version`; ordered pages each with takeaway, sources, claims
(with approved `source_ref`), and status; `sections_present`/`sections_missing`; recorded
`required_approvals` + `approvals` with status; `unsupported_claims` list; `delivery_status`;
draft-only notice and standing note.
