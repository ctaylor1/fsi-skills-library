# Domain Rules & Thresholds — knowledge-answer-composer

These are the deterministic **answerability** rules the composer applies. Thresholds are
defaults; a deployment may tune them per jurisdiction pack. The rules are enforced by
[`scripts/validate_input.py`](../scripts/validate_input.py) (source governance/freshness) and
[`scripts/validate_output.py`](../scripts/validate_output.py) (grounding, source fidelity,
prohibited-language screen).

## R1 — Citation-coverage rule

Every factual statement in `answer_text` must be backed by a claim that carries a citation
and a `source_id`. Target coverage is **100%**: an answered response with an uncited factual
sentence fails closed. The grounding check requires each claim's text to appear in
`answer_text`, so narrative and citations cannot drift apart.

## R2 — Approval / governance gate

A source is usable only when `status == "approved"`. Content that is `draft`, `pending`,
`expired`, or `retired` is **excluded** and surfaced as a data gap. The output validator
re-checks every `sources_used` entry and fails closed on any non-approved basis.

## R3 — Freshness window

A source is in effect only when `effective_date <= as_of_date` **and** (`expiry_date` absent
or `expiry_date >= as_of_date`). Service-status sources use a tighter window — default **same
business day**; a status older than the window is treated as stale and re-fetched before it
is stated.

## R4 — Jurisdiction match

A source tagged to a jurisdiction other than the request's is excluded unless the question is
explicitly cross-jurisdiction. The default jurisdiction is `US`; additional packs are wired
per deployment (`aws-fsi-jurisdictions`).

## R5 — Conflict rule

When two **approved, in-effect** sources give conflicting answers, do not silently pick one.
Present both with citations, note the conflict, and stop for human review. The source
hierarchy in [`source-map.md`](source-map.md) orders precedence but never suppresses a
conflicting approved source.

## R6 — Uncertainty / partial-coverage rule

- If approved sources cover the question **fully**, answer and cite.
- If they cover it **partially**, answer the covered part, cite it, and list the uncovered
  part explicitly under uncertainty — never extrapolate.
- If they **do not cover** it at all, set `unanswered=true`, state that it cannot be answered
  from approved sources, and route to a human/specialist. Never fill the gap with general
  knowledge.

## R7 — Plain-language rule

Write at a service-desk reading level. Explain any product or regulatory term on first use
using the approved glossary; do not introduce jargon the sources do not define. Keep the
answer to the question asked — do not append unrequested offers or opinions.

## R8 — No-advice / no-determination rule

The hard boundary. The composer states what approved sources say; it never recommends,
advises, or determines coverage/eligibility/fraud/complaint/account outcomes. Enforced by the
prohibited-language screen in [`controls.md`](controls.md); advice and determination routes
are in [`handoffs.md`](handoffs.md).
