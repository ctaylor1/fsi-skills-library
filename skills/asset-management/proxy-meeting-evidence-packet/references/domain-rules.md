# Domain Rules — proxy-meeting-evidence-packet

Orientation references: the firm's **proxy voting policy / guidelines** and stewardship charter,
the custodian's **record-date entitlement** system, and the approved **proxy-evidence config**.
The firm's policy and its versioned config take precedence and are **versioned contracts**. This
skill compiles evidence for a human decision; it never decides, casts, or proposes a vote.

## Source hierarchy (observed → hypothesis)

Collected items are classed by this hierarchy. Rank informs how authoritative an item is **for
reference**; it does **not** determine a vote (the analyst and committee do).

| Rank | Source type | Class |
| ---- | ----------- | ----- |
| 1 | `meeting_notice` — agenda item from the official notice | observation |
| 2 | `issuer_disclosure` — proxy statement / filing (board recommendation) | observation |
| 3 | `policy_clause` — the firm's documented voting-policy clause | observation |
| 4 | `research_provider` — a provider's published recommendation | observation |
| 5 | `precedent_vote` — the firm's recorded prior vote on an analogous item | observation |
| 6 | `analyst_inference` / `market_commentary` / `estimated_outcome` / `draft_rationale` | hypothesis |

**Rule:** an item whose `source_type` is a hypothesis is tagged `fact_type: hypothesis` and is
never counted as an observed fact. A cited board / provider / precedent **direction** is an
observed fact about someone else's position — recording it is not proposing a vote.

## Required vs expected evidence categories

| Category | `source_type` | Absence effect |
| -------- | ------------- | -------------- |
| Agenda item | `meeting_notice` | **Required** — absent → `needs-data` |
| Issuer disclosure | `issuer_disclosure` | **Required** — absent → `needs-data` |
| Voting policy | `policy_clause` | **Required** — absent → `needs-data` |
| Ownership / entitlement | `ownership` block | **Required** — absent → `needs-data`; inconsistent → `entitlement-discrepancy-flagged` |
| Research-provider input | `research_provider` | **Expected** — absent → gap noted, +1 review priority |
| Precedent | `precedent_vote` | **Expected** — absent → gap noted, +1 review priority |

## Entitlement / record-date integrity (never overridden)

The ownership block is checked, never edited:

- `ownership.record_date` must equal `meeting.record_date`.
- `shares_entitled` must be present and greater than zero.

If either check fails, the item disposition is **`entitlement-discrepancy-flagged`**: both values
are cited, the discrepancy is described, and the item is routed to the custodian and proxy
operations to reconcile. The skill **never** writes a corrected record date or share count. An
entitlement/record-date gap forces the top review-priority band (P1).

## Contested items (observed fact, not a resolution)

An item is `contested` when the cited **board recommendation** disagrees with a **research
provider**, or two providers disagree. This is surfaced as an **observed fact** with the
disagreeing sources listed; the packet does **not** recommend how to resolve it. A contested item
forces the top review-priority band (P1) so the committee sees it first.

## Review-priority scoring (deterministic, documented)

Review priority is a triage rank for the committee queue, computed from explainable inputs —
**not** a vote or an outcome prediction.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Sensitive proposal type (`say_on_pay`, `shareholder_proposal`, `merger`, `contested_election`, `compensation_plan`, `bylaw_amendment`, `board_declassification`, `capital_authorization`) | +2 |
| Missing expected category (`research_provider`, `precedent_vote`) | +1 each |
| Materiality (`pct_outstanding`) | ≥ 5% +2, else ≥ 1% +1 |
| Deadline proximity (business days from `as_of` to `vote_deadline`) | ≤ 3 bd +2, else ≤ 7 bd +1 |

Bands: **P1 (Elevated)** total ≥ 7 **or** any `contested` item; **P2 (Standard)** 3–6;
**P3 (Low)** ≤ 2. `validate_output` recomputes the band from the score (+ contested override) for
`packet-assembled`, and requires **P1 (Elevated)** for `entitlement-discrepancy-flagged`; any
mismatch fails closed.

## Dispositions (this skill may set only these)

`packet-assembled` | `entitlement-discrepancy-flagged` | `needs-data`. It may **not** set
`vote-cast`, `vote-proposed`, `vote-recommended`, `voted`, `ballot-submitted`, `submitted`,
`entitlement-overridden`, `record-date-overridden`, `closed`, `resolved`, `finalized`, or
`final`.

## Durable case & job IDs

- Per-item case: `PME-{meeting_id}-{item_id}` (stable, reproducible).
- Packet job: `PME-JOB-{meeting_id}`.

These IDs are the handoff anchors to `voting-policy-consistency-checker`, the proxy committee, and
the custodian; they are deterministic, so re-running the same meeting/item yields the same IDs and
no duplicate case is opened.

## Hard boundaries (fail closed)

- No **casting, submitting, or proposing/recommending a vote direction** (FOR/AGAINST/ABSTAIN/
  WITHHOLD), and no stating "the vote should be …".
- No **override of entitlement or record-date data**; discrepancies are flagged, never corrected.
- No **hypothesis presented as an observed fact**.
- No **closure/resolution/finalization** of a case; disposition is recommendation-only.
- No **outcome decision** — issuer/provider/precedent directions are cited context, not a firm
  instruction.

## Evidence bundle — required contents

Durable `case_id`; the `proposal_type` and `proponent`; a chronology of collected items with as-of
dates and observation/hypothesis tags; parties (issuer, policy owner, research providers,
precedent source, custodian, proponent); amounts (`shares_entitled`, `pct_outstanding`); an
`observed_facts` block (board recommendation, research inputs, precedent directions — all cited);
a `hypotheses` list; the policy reference and version; the entitlement block with its consistency
result; `contested` and its kinds; `gaps`; the source-hierarchy reference; `review_priority`; a
`recommended_next_step` that states **no vote direction**; `adjudication: human-required`; and a
citation for every item.
