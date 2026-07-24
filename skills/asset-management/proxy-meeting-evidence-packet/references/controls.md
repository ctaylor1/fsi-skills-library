# Controls — proxy-meeting-evidence-packet

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis
  (the packet is evidence + recommendations; no writes, nothing staged for execution).
- **Human approval:** `required` — the vote decision is the proxy-voting analyst's and the proxy
  committee's; any entitlement/record-date correction is the custodian's. This skill only compiles
  and proposes next steps.

## Prohibited (fail closed)

- **Casting or submitting a vote / ballot**, or **proposing/recommending a vote direction**
  (FOR/AGAINST/ABSTAIN/WITHHOLD); stating "the vote should be …".
- **Overriding entitlement or record-date data**; writing a corrected record date or share count.
- Presenting a **hypothesis** (inference / commentary / estimate / draft rationale) **as an
  observed fact**.
- **Closing / resolving / finalizing** a case (recommendation-only).
- **Deciding the outcome** — cited board/provider/precedent directions are context, not an
  instruction; a contested item is surfaced, never resolved.

## Case states (this skill may set only these)

`packet-assembled` | `entitlement-discrepancy-flagged` | `needs-data`. It may **not** set
`vote-cast`, `vote-proposed`, `vote-recommended`, `voted`, `ballot-submitted`, `submitted`,
`entitlement-overridden`, `record-date-overridden`, `closed`, `resolved`, `finalized`, or
`final`.

## Required output screens (`scripts/validate_output.py`)

- Durable `job_id` and per-case `case_id` present.
- Only the three allowed dispositions appear; no vote/ballot/closure/override states.
- No prohibited decision fields anywhere (`recommended_vote`, `proposed_vote`, `vote_decision`,
  `vote_direction`, `vote_instruction`, `cast_vote`, `our_vote`, `final_vote`, `ballot`,
  `override_shares`, `override_record_date`, `overridden_record_date`, `adjusted_entitlement`,
  `corrected_shares`, `corrected_record_date`). Cited `board_recommendation` /
  `provider_recommendation` / `precedent_direction` are observed-fact fields and are **allowed**.
- Every collected item carries a `fact_type` **consistent with its `source_type`** — no hypothesis
  tagged as an observed fact.
- Every `packet-assembled` and `entitlement-discrepancy-flagged` case has a cited evidence bundle
  and `adjudication: human-required`.
- `review_priority` equals the deterministic mapping (score + contested override) for
  `packet-assembled`; `entitlement-discrepancy-flagged` is forced to **P1 (Elevated)**.
- No vote-casting / vote-proposal / entitlement-override language in the packet's **own authored
  text** (recommendations, narrative, standing note). The screen deliberately does **not** scan
  the cited source text of evidence items — a cited disclosure that reads "the Board recommends a
  vote FOR" is an observed fact, not the packet proposing a vote.
- Standing note present: "Proxy-meeting evidence packet only; no vote has been cast, proposed, or
  recommended, and no entitlement or record-date data has been overridden. Cited board,
  research-provider, and precedent directions are observed facts for the proxy-voting analyst and
  proxy committee to adjudicate."

## Segregation of duties

The analyst who compiles the packet does **not** cast the vote alone: the vote decision is the
proxy-voting analyst's/committee's under policy; entitlement correction is the custodian's;
policy-consistency review of a human-proposed instruction is `voting-policy-consistency-checker`.
The same person/skill must not both compile the evidence and unilaterally cast or override.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Holdings, entitlement, and pre-meeting
  voting intentions are market- and client-sensitive; research-provider recommendations may be
  **licensed** — cite provenance and do not redistribute raw provider content beyond entitlement.
- Mask account/holder identifiers to what evidences the item.
- Retain packets, citations, and the evidence/policy config versions per records policy; log the
  analyst identity on every read and every packet generation. Observe any applicable
  vote-disclosure / N-PX recordkeeping obligations at the firm level (this skill only compiles
  evidence; it neither discloses nor files).
