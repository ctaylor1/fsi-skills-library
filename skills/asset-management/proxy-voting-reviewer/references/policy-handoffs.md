# Adjacent-Skill Handoffs — proxy-voting-reviewer

This mode produces a cited **consistency review** (`review_id`) over a human analyst's
proposed votes and stops. It does not collect the underlying evidence bundle, choose a firm
position, or cast/submit a vote.

## Upstream (feeds this mode)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `proxy-voting-reviewer` `evidence` mode | Agenda items, issuer disclosures, ownership/entitlement, the applicable voting policy, research-provider inputs, and precedent — assembled into one cited packet | `packet_id` (+ policy version, precedent set) |

This mode consumes that packet plus the analyst's `proposed_vote` per item. It does **not**
re-collect disclosures, ownership, or precedent, and never overrides entitlement/record-date
data — that is the packet's responsibility.

## Lateral / downstream (route the human to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `issuer-engagement-reviewer` | The deviation relates to an active stewardship engagement or a firm position on the issuer, not a policy comparison | issuer + `review_id` |
| `investment-mandate-reviewer` | The question is whether portfolios/proposed trades breach mandate, guideline, concentration, ESG, or restriction rules — not vote-vs-policy consistency | portfolio/mandate scope |

## Human / ops handoff (not a skill)

The **vote decision, change, casting, and submission** are **not** skills. A `deviation`,
`case_by_case`, or `no_policy` finding routes to the **proxy-voting analyst / voting
committee**, who document rationale, adjudicate, and record the vote in the proxy-voting
**system of record**. This mode never performs or recommends that step; it hands over the
cited review and the required-action list.

## Duplicate-execution prevention

- This mode computes **consistency findings only**; it must not assemble the evidence
  bundle (`proxy-voting-reviewer` `evidence` mode), decide a firm position
  (`issuer-engagement-reviewer`), or cast/submit a vote (human + system of record).
- Downstream steps reuse the `review_id` and the upstream `packet_id` rather than
  recomputing the comparison.

This document is scoped to `policy` mode. A handoff to `evidence` requires a separately prepared request `{mode: "evidence", input: <native request>}` with reviewed source mappings. The current output is not the other mode's input. No automatic adapter or vote execution is supplied.
