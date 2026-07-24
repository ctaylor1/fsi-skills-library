# Adjacent-Skill Handoffs — voting-policy-consistency-checker

This skill produces a cited **consistency review** (`review_id`) over a human analyst's
proposed votes and stops. It does not collect the underlying evidence bundle, choose a firm
position, or cast/submit a vote.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `proxy-meeting-evidence-packet` | Agenda items, issuer disclosures, ownership/entitlement, the applicable voting policy, research-provider inputs, and precedent — assembled into one cited packet | `packet_id` (+ policy version, precedent set) |

This skill consumes that packet plus the analyst's `proposed_vote` per item. It does **not**
re-collect disclosures, ownership, or precedent, and never overrides entitlement/record-date
data — that is the packet's responsibility.

## Lateral / downstream (route the human to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `engagement-history-brief` | The deviation relates to an active stewardship engagement or a firm position on the issuer, not a policy comparison | issuer + `review_id` |
| `mandate-compliance-monitor` | The question is whether portfolios/proposed trades breach mandate, guideline, concentration, ESG, or restriction rules — not vote-vs-policy consistency | portfolio/mandate scope |

## Human / ops handoff (not a skill)

The **vote decision, change, casting, and submission** are **not** skills. A `deviation`,
`case_by_case`, or `no_policy` finding routes to the **proxy-voting analyst / voting
committee**, who document rationale, adjudicate, and record the vote in the proxy-voting
**system of record**. This skill never performs or recommends that step; it hands over the
cited review and the required-action list.

## Duplicate-execution prevention

- This skill computes **consistency findings only**; it must not assemble the evidence
  bundle (`proxy-meeting-evidence-packet`), decide a firm position
  (`engagement-history-brief`), or cast/submit a vote (human + system of record).
- Downstream steps reuse the `review_id` and the upstream `packet_id` rather than
  recomputing the comparison.
