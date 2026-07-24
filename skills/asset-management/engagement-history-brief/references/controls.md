# Controls — engagement-history-brief

- **Risk tier:** R3 — regulated / control decision support. The brief supplies *evidence and
  recommendations-of-fact* only; every downstream decision requires human adjudication.
- **Action mode:** Draft-only; no system-of-record change. The skill assembles a draft
  artifact and writes nothing to the engagement log or any register.
- **Human approval:** `required` — a stewardship analyst reviews and a stewardship lead (or
  the stewardship committee, per firm policy) adjudicates before the brief informs any
  objective, position, or vote.

## Prohibited (fail closed)

- **Choosing an engagement objective** — `engagement_objective.selected` must stay `null`.
- **Representing / stating a firm position or view** on the issuer —
  `firm_position.represented` must stay `false`; no first-person firm advocacy.
- **Casting, proposing, or recommending a vote** (for / against / abstain / withhold).
- **Judging a commitment "met"** as substance — status is factual and date-based only.
- **Writing the engagement log / system of record**, closing a follow-up, or marking state.
- **Uncited claims** — every assembled row must trace to a source ref.
- **Finalizing / submitting / publishing** — the brief is draft-only.

## Draft states (this skill may set only these)

`draft`. It may **not** set `final`, `published`, `submitted`, `approved`, `sent`, or `filed`.
`validate_output` rejects any non-draft status.

## Required output screens (`scripts/validate_output.py`)

- `draft` is true and `status == "draft"` (no finalize/submit/publish).
- All required template sections present (issuer profile, chronology, commitments & progress,
  attendees, source documents, unresolved follow-ups, engagement objective, firm position).
- Every engagement / commitment / disclosed-progress / follow-up / source-document item cited.
- `engagement_objective.selected` is `null` **and** `firm_position.represented` is `false`.
- No prohibited-decision / firm-representation / vote language in assembled content (regex:
  vote for/against, "we will/recommend vote", "the firm's position/view is", "our position
  is", "we support/oppose the", "the objective of the next engagement", "on behalf of the
  firm", "the firm believes/supports/opposes").
- Required approver roles recorded (`Stewardship analyst`, `Stewardship lead`).
- Standing note present.

Fail closed on any miss. The non-compliant fixture `evals/files/brief_bad.json` MUST exit 1.

## Segregation of duties

Assembling the history (this skill) is distinct from choosing an objective, adjudicating a
position, and deciding a vote. The analyst who runs the brief does not thereby set the
objective or the firm's position; those require the stewardship lead / committee and, for
votes, the proxy-voting workflow.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Engagement content may include
  material non-public information and client-attributable holdings.
- Minimize to what the brief needs; carry issuer-side attendees at **role level** with
  de-identified ids; never export MNPI to unauthorized destinations.
- Retain the brief, citations, and `brief_version` / `source_hierarchy_version` per the firm's
  stewardship recordkeeping and applicable Stewardship Code disclosure regime; log analyst
  identity on every assembly.
