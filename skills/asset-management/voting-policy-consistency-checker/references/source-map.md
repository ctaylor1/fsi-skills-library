# Source Map — voting-policy-consistency-checker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Voting policy** (versioned, effective-dated; controlled content library) | The authoritative policy position per proposal category | Read-only |
| 2 | **Voting-record / precedent store** | Analogous prior firm votes and their rationale | Read-only |
| 3 | **Ballot / meeting agenda** (proxy-voting system; incl. the analyst's `proposed_vote`) | The items under review and the human's proposed votes to be checked | Read-only |
| 4 | **Research-provider inputs** (e.g. proxy advisor recommendations) | Advisory context only — subordinate to firm policy | Read-only |

The `proposed_vote` is the object under review, never authority for the policy position. A
proxy-advisor recommendation never overrides firm policy; where they conflict, cite firm
policy and note the advisor position as context. If the policy record and a precedent
conflict, cite both and flag for the reviewer — do not resolve silently.

## Citation format

- Policy: `policy:{policy_ref}@{version};eff={effective_date}` —
  e.g. `policy:PXY-POL-2025 3.4@PXY-POL-2025;eff=2025-01-01`.
- Precedent: `precedent:{case_id}@{meeting_date}` — e.g. `precedent:PXY-2025-0731@2025-03-22`.

Every `deviation`, `aligned`, and `case_by_case` finding cites the exact guideline used;
every precedent count cites the specific prior cases.

## Freshness / effective dates

- Select the policy guideline whose `effective_date ≤ meeting_date`, latest such
  (references/domain-rules.md). Guidelines effective after the meeting are ignored and
  flagged by `validate_input`.
- The output records `policy_version` and the cited guideline version so a review is
  reproducible.
- Precedents are matched by category and strictly earlier `meeting_date`.

## Upstream evidence bundle

At deployment the cited policy, precedent, and disclosure inputs are assembled by
`proxy-meeting-evidence-packet` (durable `packet_id`). This skill consumes that bundle plus
the analyst's proposed votes; it does not re-collect disclosures or precedent. See
references/handoffs.md.

## Least-privilege operations (deployment)

- `policy.get(category, as_of=meeting_date)` → effective guideline(s) with version/effective-date.
- `voting_record.query(category, before=meeting_date)` → analogous prior votes.
- `ballot.read(meeting_id)` → agenda items + the analyst's proposed votes.
- `research.get(meeting_id)` → advisory recommendations (context only).

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
agendas as resumable stages. No write, submit, or vote-casting operation is bound.
