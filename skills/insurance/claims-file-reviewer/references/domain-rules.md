# Domain Rules — claims-file-reviewer

The review checks and how they map to a **review-readiness band**. Thresholds and required
document sets are configuration (versioned, owned by claims operations), not hard-coded
judgments, and never tuned to an individual claim to reach a desired outcome. The firm's
claims-handling standard and jurisdiction fair-claims rules take precedence.

## Review checks (findings)

| Check | Category | Severity | Fires when |
| ----- | -------- | -------- | ---------- |
| Coverage citation missing | coverage | **blocking** | A policy coverage has no policy/endorsement citation (cannot be reviewed against a source form) |
| Loss outside policy period | coverage | **blocking** | `loss_date` not within `[effective_date, expiration_date]` (a threshold question for the adjuster) |
| Report precedes loss | chronology | **blocking** | `report_date < loss_date` (data-integrity issue) |
| Late report | chronology | info | Reporting lag > `report_lag_days` (note for late-notice review, not a coverage conclusion) |
| Chronology gap | chronology | info | Largest gap between recorded events > `stale_days` |
| Missing document | documentation | warning | A required document for the `claim_type` is absent |
| Reserve unsupported | reserve | warning | An indemnity reserve has no supporting evidence document in the file |
| Reserve/severity mismatch | reserve | warning | Indemnity reserve deviates from its supporting estimate by more than `reserve_support_tolerance` |
| Payment authority missing | decision | **blocking** | A payment has no approval-authority reference (delegated authority unverifiable) |
| Payment evidence missing | decision | warning | A payment has no supporting evidence reference |
| Decision untraceable | decision | warning | A recorded decision lacks rationale, authority, or source citation |
| Open issue stale | open_issue | warning | An open task/diary item has aged past `stale_days` with no recorded resolution |

Findings are **independent and additive**; each fired check reports its own evidence. There
is no opaque composite "coverage score" and no automated coverage or reserve conclusion.

## Review-readiness mapping (deterministic, documented)

| Band | Rule |
| ---- | ---- |
| **documentation_complete** | No blocking and no warning findings (only info or none) |
| **follow_up_required** | One or more warning findings, no blocking finding |
| **escalate** | One or more **blocking** findings |

Readiness is a **triage suggestion for a human adjuster** — it describes the state of the
file, not the merits of the claim. It is not a coverage or reserve determination and never
triggers a payment, reserve change, closure, or filing.

## Descriptive severity band (not a decision)

`total_incurred = reserves_total + paid_total`. Band: **Severe** ≥ `large_loss_threshold`;
**Moderate** ≥ 10% of it; else **Minor**. This is a descriptive size label for routing and
context, not a reserve opinion.

## Hard boundaries (fail closed)

- Never state or imply that coverage applies / is denied, or that a reserve should be a
  particular amount — describe gaps factually and attribute conclusions to the human.
- Never approve/deny/pay/settle a claim, change a reserve, close a case, or file anything.
- Never assert fraud; route indicators to `claims-fraud-referral-assistant` (draft-only).
- Never tune thresholds or required-doc sets to force a readiness band for a specific claim.

## Reviewer considerations (always include when any finding fired)

Coverage/exclusion interpretation is the adjuster's call; reserve adequacy is an
actuarial/adjuster judgement; jurisdiction rules (late-notice, fair-claims deadlines) change
how a finding is weighted; a "missing" document may already exist outside the file. The pack
must invite the reviewer to weigh these before acting.
