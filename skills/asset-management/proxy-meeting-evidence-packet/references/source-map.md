# Source Map — proxy-meeting-evidence-packet

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Meeting notice / agenda** (issuer or vote-agent notice) | Authoritative agenda items, item ids, meeting/record/deadline dates | Read-only |
| 2 | **Issuer disclosures / filings** (proxy statement / DEF 14A, 8-K) | Proposal detail, board recommendation, proponent | Read-only |
| 3 | **Custodian / record-date entitlement** (system of record for entitlement) | Shares entitled to vote, record date, account/custodian ref | Read-only |
| 4 | **Voting policy / guidelines** (versioned) | The firm's documented policy clause governing the item | Read-only |
| 5 | **Proxy research providers** (e.g., ISS, Glass Lewis) | Published research-provider recommendation for the item | Read-only |
| 6 | **Voting precedent / prior-vote record** | The firm's recorded prior vote on an analogous item | Read-only |

The **custodian / record-date entitlement** is the system of record for what the fund is
entitled to vote. It is **evidence, not a control the skill may edit** — the packet reads it,
reconciles it to the meeting record date, and **flags** any inconsistency for the custodian and
proxy operations. This skill never writes back to any of these systems and never alters
entitlement or record-date data.

## Observed fact vs hypothesis (by `source_type`)

| `source_type` | Class | Notes |
| ------------- | ----- | ----- |
| `meeting_notice` | **observation** | Agenda item text from the official meeting notice. |
| `issuer_disclosure` | **observation** | Proxy statement / filing; carries the cited board recommendation. |
| `policy_clause` | **observation** | The firm's documented voting-policy clause text/ref. |
| `research_provider` | **observation** | A provider's *published* recommendation (the fact that ISS/GL recommended X). |
| `precedent_vote` | **observation** | The firm's recorded prior vote on an analogous item. |
| `analyst_inference` | **hypothesis** | Analyst's interpretive read; not yet sourced. |
| `market_commentary` | **hypothesis** | Third-party press/commentary; not authoritative. |
| `estimated_outcome` | **hypothesis** | Projected vote outcome / pass probability. |
| `draft_rationale` | **hypothesis** | Working rationale not tied to an authoritative source. |

A cited third-party **recommendation** (board / provider / precedent direction) is an
**observed fact** about what someone else recommended or did — the packet records it, it is
**not** the packet proposing a vote. A hypothesis is context, never an observed fact, and never a
substitute for a missing authoritative source. See [domain-rules.md](domain-rules.md).

## Citation format

`{system}:{ref}@{as_of/version}` — e.g.
`meeting:meeting=MTG-2026-XYZ-AGM;item=ITEM-1@2026-07-01`,
`issuer:DEF14A@2026-07-01`,
`custodian:CUST-77;record_date=2026-06-30`,
`policy:proxy-voting-guidelines@v2026.05`,
`research:ISS@2026-07-30`,
`precedent:PV-2025@2025-08-10`,
`config:proxy-evidence-config@v2026.07`.

## Freshness / effective dates

- Every collected item carries an **as-of** date; the meeting carries `record_date`,
  `meeting_date`, and (where available) `vote_deadline`. The `record_date` must be on or before
  the `meeting_date`, and each item's `ownership.record_date` must reconcile to the meeting
  `record_date`.
- The evidence config, the voting policy, and the source hierarchy are **versioned contracts**;
  the versions are recorded on every case for reproducibility. If a version is missing or stale,
  fail closed and flag it rather than assessing against an unknown rule set.

## Least-privilege operations (deployment)

- `meetings.read(issuer|meeting_id)`, `agenda.read(meeting_id)` — read-only agenda/notice.
- `filings.read(issuer_id, form, as_of)` — read-only issuer disclosures.
- `entitlement.read(account, meeting_id, record_date)` — read-only shares/record date; **no write**.
- `policy.get('proxy-voting-guidelines', version)` — read-only versioned policy.
- `research.read(provider, meeting_id, item_id)`, `precedent.read(issuer, proposal_type)` — read-only.

No mutation from this skill. It reads sources and emits a packet; casting/submitting the ballot
and any entitlement correction are separate, human-approved actions in other systems/skills.
