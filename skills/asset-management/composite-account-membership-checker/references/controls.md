# Controls — composite-account-membership-checker

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — mandatory human adjudication before any composite-membership,
  methodology, or performance change is made in an authorized system of record. This skill only
  produces evidence; it decides and writes nothing.

## Prohibited (fail closed)

The **HARD BOUNDARY**: never change a composite, its membership, the methodology, or reported
performance. Concretely, this skill must never (and `validate_output.py` screens for the
language of):

- **Change composite membership** — add, remove, reassign, or "correct" a portfolio's composite
  assignment, or edit a composite definition. It flags the exception; the human/authorized system
  applies any change.
- **Change methodology or reported performance** — restate, recalculate, or recompute a
  composite's returns or performance. Return/attribution work routes to
  `performance-attribution-builder`.
- **Dispose of an exception** — close, resolve, approve, file, or mark an exception done, or write
  to a system of record. Every exception is emitted with `status: for_review`.
- **Determine discretion or suitability** as a binding decision — surface the evidence
  (client-restriction / discretion flags) for the analyst; do not adjudicate it.
- **Apply a newer rule version retroactively** — evaluate against the `rule_version` in effect for
  the `as_of` date; never silently upgrade the ruleset (that is a methodology change).

## Required output screens (`scripts/validate_output.py`)

- Every exception has >= 1 cited evidence row **and** a rule citation (`rule_id` + `rule_version`).
- `queue_priority` equals the deterministic mapping from the exception-type set.
- No prohibited membership/methodology/performance/closure/filing language (regex screen:
  `reassigned`, `restated`, `recalculated`, `changed the composite`, `corrected the composite`,
  `case closed`, `filed the ...`, `posted to the system of record`, etc.).
- Every exception `status == for_review`; `human_adjudication_required == true` when exceptions
  exist.
- Standing disclaimer present: "Composite-membership exceptions are evidence for analyst
  adjudication only; this skill does not modify composites, methodology, or reported performance."

A non-compliant pack (prohibited language, a disposed status, or a missing disclaimer) **fails
closed** (`evals/files/pack_with_action.json`, `expect_exit 1`).

## Segregation of duties

Rule-checking (this skill) is separated from composite maintenance and from performance
restatement. The performance analyst adjudicates; the composite management committee / performance
operations (a human/authorized system) applies any membership or performance change under its own
controls. This skill never performs both sides.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Minimize account data to what evidences an
  exception; reference portfolios by identifier, not client name.
- Retain the queue + citations + `ruleset_version` per records policy; log the read and the
  adjudication hand-off. Never exfiltrate holdings or client data.

## Reproducibility

`review_id` binds the queue to the exact inputs, `as_of`, and **ruleset version**; re-running with
the same inputs and ruleset reproduces every exception, its evidence, and the queue priority.
