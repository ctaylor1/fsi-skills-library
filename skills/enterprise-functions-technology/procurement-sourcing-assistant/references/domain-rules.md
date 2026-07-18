# Domain Rules — procurement-sourcing-assistant

Orientation references: the enterprise procurement / sourcing standard and its per-category
**required-sections**, **evaluation-weight**, and **required-approvals** contracts (versioned,
from the category playbook). These take precedence and are versioned contracts. This skill
applies the deterministic assembly and scoring rules below; it does not exercise sourcing
judgment or make the award.

## Weighted evaluation scorecard (deterministic)

Each `evaluation_criteria` entry carries a `criterion_id`, a `weight` (percentage points, meant
to sum to 100 across all criteria), and a `mandatory` flag. Each bidder carries a per-criterion
`scores` map (each score on a 0–10 scale) and a `mandatory_met` map for mandatory criteria.

For a bidder with a complete `scores` map:

```
weighted_score = round( sum( weight[c] * score[c] for c in criteria ) / 100 , 2 )   # 0–10 scale
```

The weight total (default expected 100) is recorded; a total other than 100 is **flagged**
(scoring may be miscalibrated) but the scorecard still ties out to the actual weights supplied.

## Bidder status (deterministic, per bidder)

| Status | Condition | Consequence |
| ------ | --------- | ----------- |
| `needs-data` | The bidder is missing a score for one or more criteria | Excluded from the ranking; `weighted_score` is null; listed as an `unscored-criterion` open item — never guessed |
| `knockout-flag` | Every criterion is scored but a **mandatory** criterion is not met (`mandatory_met[c]` is not `true`) | `weighted_score` is computed and shown (cited); excluded from the recommendation; listed as a `mandatory-unmet` open item for a human to confirm — never auto-eliminated |
| `scored` | Every criterion is scored and all mandatory criteria are met | Eligible for the ranking; `weighted_score` computed and cited |

Precedence: **`needs-data` (incomplete scoring) is checked before `knockout-flag`** — you cannot
knock out a bidder you have not fully scored.

## Ranking & draft recommendation

Among `scored` bidders (fully scored, mandatory met), rank by `weighted_score` descending; ties
break by `bidder_id` ascending for determinism. The top-ranked bidder is marked
`recommended-pending-approval`. This is a **draft recommendation**, never an award. If no bidder
is `scored`, the recommendation is `no-eligible-bidder` (needs human review) and an open item is
raised. `award_decision` is always `pending-human-approval`.

## Requirements, market scan, RFP content (captured, never invented)

- Requirements are `captured` with a citation (`source_ref`); a requirement missing an `owner`
  is still captured but raises a `missing-requirement-owner` open item.
- Market-scan suppliers are `identified` with a citation; the scan is context for the sourcing,
  not a recommendation.
- RFP-content sections are `drafted` with a citation; drafting is not issuing.

## Approvals capture (recorded, never assumed)

- Approvals with `status == "recorded"` are captured with `type`, `approver_role`, `approver`
  (masked), `date`, and `citation`.
- Every entry in `required_approvals` with no recorded approval becomes an **outstanding**
  approval and an open item. An approval is never assumed granted.
- `human_approval_required_before_delivery` is always `true` — the assembled pack is a draft; a
  human must approve before delivery or an award decision.

## Risk inputs (routed, never ruled)

Explicit `risk_inputs` and each bidder `risk_flag` become a `routed` risk-input entry with a
`route` to the specialist skill (`third-party-risk-assessor`,
`third-party-cyber-risk-reviewer`, or `third-party-ai-due-diligence-assistant`), a citation, and
an `outstanding-risk-review` open item. This skill flags and routes; it never makes the vendor
risk finding.

## Open-items taxonomy

`missing-requirement-owner` | `unscored-criterion` | `mandatory-unmet` | `outstanding-approval` |
`outstanding-risk-review` | `no-eligible-bidder`. Each open item names the item, its type, a
required human action, and (where evidence exists) its citation.

## Hard boundaries (fail closed)

- No **award / supplier selection / binding sourcing decision** (`award_decision` stays
  `pending-human-approval`).
- No **RFP issuance / delivery / bidder notification** (draft-only).
- No **negotiation / spend commitment / PO issuance**.
- No **vendor-risk or legal determination** (routed to specialists).
- No **fabrication** of requirements, scores, approvals, or citations.
- No **autonomous knockout / elimination** of a bidder.

## Sourcing-pack manifest — required contents

`sourcing_id`, `category`, `jurisdiction`, `as_of_date`, `config_version`, `template_version`,
`pack_status: draft-assembled`, `award_decision: pending-human-approval`,
`human_approval_required_before_delivery: true`, the canonical `sections` (pack summary,
requirements, market scan, evaluation criteria, RFP content, bidder comparison, risk inputs,
decision record, source index), the open-items list, and the standing note.
