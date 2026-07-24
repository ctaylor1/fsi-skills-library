# Adjacent-Skill Handoffs — engagement-history-brief

Assembling an issuer's **engagement history** (this skill) is a separate control activity from
deciding a vote, checking a vote against policy, or representing the firm externally. Each has
distinct entitlements and outputs. This skill emits a cited history bundle keyed to a durable
`brief_id` and routes onward; it never performs the downstream work.

## Downstream / parallel (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `proxy-meeting-evidence-packet` | A specific meeting/vote needs a decision evidence packet (agenda items, issuer disclosures, ownership, voting policy, research-provider inputs, precedent) | `brief_id` + issuer id + relevant engagement citations |
| `voting-policy-consistency-checker` | A human has *proposed* a vote and it must be checked against documented policy and analogous prior cases | `brief_id` + the proposed vote (human-supplied) |
| `fund-commentary-drafter` | External, firm-attributed stewardship/fund narrative is needed (represents the firm to clients/public; approval-gated) | `brief_id` + approved messaging inputs |
| `investment-thesis-monitor` | The request is *ongoing monitoring* of thesis KPIs/catalysts rather than assembling engagement history | issuer id + thesis reference |

## Escalation to humans (no skill performs these)

- **Choosing the engagement objective** — the analyst proposes and the **stewardship lead /
  stewardship committee** decides what the next engagement should achieve. No skill in the
  catalog chooses an objective; this is a human decision.
- **Representing / setting the firm's position** on an issuer — a human stewardship decision,
  governed by firm policy; external expression of it is drafted (approval-gated) via
  `fund-commentary-drafter`, never asserted by this brief.
- **Casting a vote** — the proxy-voting workflow and the responsible human, informed by
  `proxy-meeting-evidence-packet` and `voting-policy-consistency-checker`.

## Upstream (feeds this skill)

The engagement log / stewardship CRM, document intelligence (notes, disclosures, filings), and
approved-source retrieval populate the raw record. This skill is **interactive** (
`aws-fsi-scheduled-agent: no`); a monitor such as `investment-thesis-monitor` or
`mandate-compliance-monitor` may surface a reason to build a brief, but does not assemble or
decide.

## Duplicate-execution prevention

- This skill **does not** cast/propose votes, build vote-decision packets, run policy
  consistency checks, or draft external commentary — those belong to the skills above.
- Downstream skills consume the `brief_id` and its citations rather than re-assembling the
  history.
- The *Engagement objective* and *Firm position* sections are deliberately left unset for a
  human; they are never auto-filled here.
