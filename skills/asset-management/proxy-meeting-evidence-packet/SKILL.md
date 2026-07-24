---
name: proxy-meeting-evidence-packet
description: >-
  Assemble a cited proxy-meeting evidence packet for a shareholder meeting: collect agenda items,
  issuer disclosures and board recommendations, ownership and record-date entitlement,
  voting-policy clauses, research-provider inputs (e.g., ISS / Glass Lewis), and analogous
  precedent into a durable per-item evidence bundle with a case_id for the proxy-voting analyst and
  proxy committee. Use when preparing evidence for an AGM/EGM or special meeting, gathering the
  record behind an agenda item, surfacing where the issuer, providers, and precedent agree or
  disagree, or checking whether a packet is complete before committee review. Every collected item
  is tagged an OBSERVED FACT or a HYPOTHESIS. HARD BOUNDARY: NEVER casts, proposes, or recommends a
  vote, submits a ballot, closes the case, or overrides entitlement/record-date data; it produces
  cited evidence and recommendations only, which the analyst, committee, and custodian adjudicate.
  Routes a human-proposed instruction to voting-policy-consistency-checker.
license: MIT
compatibility: Amazon Quick Desktop; requires meeting-notice/vote-agent, issuer-disclosure/filings, custodian/record-date-entitlement, voting-policy, proxy-research-provider (ISS/Glass Lewis), and voting-precedent MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Proxy-voting analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Proxy Meeting Evidence Packet

## Purpose and outcome
Take the agenda of an upcoming shareholder meeting and make each item **adjudication-ready**:
collect the agenda item, the issuer's disclosure and board recommendation, the fund's ownership
and **record-date entitlement**, the governing **voting-policy clause**, the **research-provider**
inputs (e.g., ISS / Glass Lewis), and analogous **precedent**, then assemble an audit-ready
**evidence packet** — a durable `case_id` per agenda item plus an evidence bundle (chronology,
parties, amounts, citations). The outcome is a cited, committee-ready packet that ranks items by
review priority and, for each, **recommends a next step** — never a vote. Every collected item is
explicitly tagged **observed fact** or **hypothesis**. The skill never casts, proposes, or
recommends a vote and never edits entitlement/record-date data — the analyst, proxy committee, and
custodian do.

## Use when
- "Build the evidence packet for the XYZ AGM / prioritize these agenda items for review."
- "Gather the record supporting agenda item 2 (say-on-pay) — disclosure, policy, ISS/GL, precedent."
- "Where do the issuer and the research providers disagree on this meeting?"
- "Is this packet complete before it goes to the proxy committee?"

## Do not use
- **Testing a proposed vote against policy / precedent** (deviation analysis on a human's proposed
  instruction) → `voting-policy-consistency-checker`.
- **Casting, proposing, or recommending a vote**, submitting a ballot, or stating "vote FOR/
  AGAINST" → not permitted here; package the evidence and route to the proxy committee.
- **Correcting entitlement / record-date data** → the human **custodian / proxy operations**; this
  skill flags the discrepancy, never fixes it.
- Any request to **decide the outcome, close, or finalize** a case → refuse; produce the packet.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Evidence **collection/packaging** (this
skill) is deliberately separated from **policy-consistency review** of a human-proposed instruction
(`voting-policy-consistency-checker`) and from the **vote decision / ballot submission**
(downstream human adjudication). This skill emits a durable `case_id` + evidence bundle; it must not
test a proposed vote against policy or cast the ballot. Adjacent skills referenced here exist in the
catalog; the vote decision and entitlement correction are human handoffs (no skill decides them).

## Inputs and prerequisites
- The meeting: `issuer_id`, `meeting_id`, `meeting_type`, `meeting_date`, `record_date`, optional
  `vote_deadline`; the versioned `config_version` and `policy_version`; and the agenda items. Per
  item: `item_id`, `proposal_type`, `proponent`, an `ownership` block (`record_date`,
  `shares_entitled`, `pct_outstanding`, `custodian_ref`), a `source_ref`, and the **evidence**
  list (each item with `source_id`, `source_type`, `as_of`, and — where applicable — a cited
  `board_recommendation` / `provider_recommendation` / `precedent_direction`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the meeting notice/vote agent, issuer disclosures, custodian/record-date
  entitlement, the versioned voting policy, proxy research providers, and the prior-vote record.
  All read-only.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The meeting notice and issuer disclosures
are the authoritative agenda/board-recommendation sources; the custodian is the system of record
for entitlement (read-only — never edited here); policy, provider, and precedent inputs are cited
with as-of/version. Observed facts (notice, disclosure, policy clause, published provider
recommendation, recorded precedent) are distinguished from hypotheses (analyst inference, market
commentary, estimated outcome, draft rationale). Config, policy, and hierarchy are **versioned
contracts** recorded on every case.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the meeting and each item have ids,
   dates, a `source_ref`, and evidence; flag inputs that block assessment (`needs-data`).
2. **Classify each collected item** — tag every evidence item `observation` or `hypothesis` from
   its `source_type` via the documented source hierarchy. A hypothesis is never treated as an
   observed fact. See [references/domain-rules.md](references/domain-rules.md).
3. **Check completeness & entitlement (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): confirm the required
   categories (agenda item / issuer disclosure / policy clause / ownership) are present, and
   reconcile `ownership.record_date` and `shares_entitled` to the meeting record date. A missing
   required category is `needs-data`; an entitlement/record-date mismatch is
   `entitlement-discrepancy-flagged` (flagged, **never** corrected).
4. **Surface agreement / disagreement (observed fact)** — record the cited board, provider, and
   precedent directions as observed facts and set `contested` when the issuer and a provider (or
   two providers) disagree. This is descriptive evidence, **not** a recommended resolution.
5. **Score review priority (deterministic)** — a documented, explainable band (P1–P3) from proposal
   sensitivity, missing expected categories, materiality, and deadline proximity — a triage rank
   for the committee, **not** a vote. A contested item or an entitlement gap forces P1.
6. **Assemble the evidence bundle** — for each item build the chronology, parties, amounts
   (shares / % outstanding), observed-facts and hypotheses blocks, policy reference, entitlement
   block, citations, and a durable `case_id`; set `adjudication: human-required` and an advisory
   `recommended_next_step`. Never cast, propose, or recommend a vote; never edit entitlement.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output screen enforces: durable `job_id`/`case_id` present; only allowed dispositions (no
`vote-cast`/`ballot-submitted`/`entitlement-overridden`/`closed`); no prohibited decision fields
(`recommended_vote`, `cast_vote`, `override_record_date`, …); every collected item carries a
`fact_type` consistent with its source (**no hypothesis presented as an observed fact**); every
bundle is cited with `adjudication: human-required`; review priority ties to the deterministic
mapping; no vote-casting / vote-proposal / entitlement-override language in the packet's authored
text; standing note present. Fail closed on any miss.

## Human approval
`required`. This skill is decision-**support**: it compiles evidence and recommendations only. The
vote decision is the **proxy-voting analyst's / proxy committee's** under policy; any
entitlement/record-date correction is the **custodian's**; policy-consistency review of a proposed
instruction is `voting-policy-consistency-checker`. This skill proposes and packages; humans decide.

## Failure handling
- **Missing required category** (no agenda item / disclosure / policy clause / ownership) →
  `needs-data`, list exactly what is missing; do not guess to complete a packet.
- **Entitlement/record-date mismatch or missing shares** → `entitlement-discrepancy-flagged`; cite
  both values; route to the custodian; **never** write a corrected value.
- **Missing expected category** (no research provider / no precedent) → assemble the packet, note
  the gap, and raise review priority; do not fabricate a recommendation or precedent.
- **Conflicting sources** (issuer vs provider, provider vs provider) → set `contested`; cite each
  direction as an observed fact; do not resolve it.
- **Stale/unversioned config or policy** → record the version and as-of; if missing/stale, fail
  closed and flag it.
- **Tool timeout / partial agenda** → return the partial packet with an explicit incomplete flag;
  assume no retry and no step-up authorization.

## Output contract
1. **Agenda queue** — per item: `case_id`, disposition (`packet-assembled` |
   `entitlement-discrepancy-flagged` | `needs-data`), review-priority band, `contested`, one-line
   cited reason.
2. **Evidence bundle** (per assembled/flagged item) — chronology, parties (masked), amounts
   (shares / % outstanding), `observed_facts` (board / provider / precedent directions, cited),
   `hypotheses` list, policy reference, entitlement block, `gaps`, review priority, citations,
   `recommended_next_step` (no vote direction), `adjudication: human-required`.
3. **Observed-fact-vs-hypothesis ledger** — every collected item tagged `observation`/`hypothesis`.
4. **Data gaps / needs-data list.**
5. **Machine-readable** — the agenda records + bundles keyed by `case_id`, under `job_id`.
6. **Standing note** — "Proxy-meeting evidence packet only; no vote has been cast, proposed, or
   recommended, and no entitlement or record-date data has been overridden. Cited board,
   research-provider, and precedent directions are observed facts for the proxy-voting analyst and
   proxy committee to adjudicate."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Holdings, entitlement, and pre-meeting voting
intentions are market- and client-sensitive; research-provider recommendations may be **licensed** —
cite provenance, do not redistribute raw provider content beyond entitlement. Mask account/holder
identifiers to what evidences the item. Retain packets, citations, and the evidence/policy config
versions per records policy; log every read and every packet generation with the analyst identity.
Observe firm-level vote-disclosure / N-PX recordkeeping obligations — this skill only compiles
evidence and neither discloses nor files.

## Gotchas
- **Recording ≠ recommending.** A cited board / ISS / precedent direction is an observed fact about
  someone else's position; the packet never turns it into a proposed vote. Presenting a proposed
  vote direction is a hard failure.
- **Observed fact ≠ hypothesis.** Analyst inference, market commentary, an estimated outcome, or a
  draft rationale is context, not an observed fact — and never fills a missing authoritative source.
- **Flag entitlement, never fix it.** A record-date/share mismatch is cited and routed to the
  custodian; the skill never writes a corrected record date or share count.
- **Contested means cite both.** Do not collapse an issuer/provider disagreement into a resolution;
  the disagreement and both cited directions are the evidence.
- **Config is versioned.** Record the evidence/policy config version on every case so the packet is
  reproducible and reviewable.
