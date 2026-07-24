# Controls — valuation-exception-packet

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis
  (the packet is evidence + recommendations; no writes, nothing staged for execution).
- **Human approval:** `required` — the price selection/override is the Valuation Committee's;
  NAV striking/certification is fund accounting / NAV oversight's. This skill only proposes.

## Prohibited (fail closed)

- **Price selection or override**; stating the "correct" / final price for a security.
- **NAV certification or striking**; posting an accounting entry.
- Presenting a **hypothesis** (matrix/model/indicative/carry-forward) **as an observed price**.
- **Closing / resolving / finalizing** an exception (recommendation-only).
- **Auto-suppressing** a move (e.g., on corporate-action grounds) instead of citing context and
  routing to the committee.

## Case states (this skill may set only these)

`exception-confirmed` | `needs-data` | `no-exception-detected`. It may **not** set
`price-selected`, `valuation-overridden`, `nav-certified`, `nav-struck`, `mark-approved`,
`closed`, `resolved`, or `final`.

## Required output screens (`scripts/validate_output.py`)

- Durable `job_id` and per-case `case_id` present.
- Only the three allowed dispositions appear; no closure/decision states.
- No prohibited decision fields (`final_price`, `selected_price`, `chosen_price`,
  `override_price`, `certified_nav`, `struck_nav`, `nav`).
- Every candidate price carries a `price_type` **consistent with its `source_type`** — no
  hypothesis tagged as an observation.
- Every `exception-confirmed` case has a cited evidence bundle and `adjudication: human-required`.
- Severity band equals the deterministic mapping (score + open-challenge override).
- No price-selection / override / NAV-certification language (regex screen).
- Standing note present: "Valuation exception packet only; no price has been selected or
  overridden and no NAV has been certified or struck. Observed prices and hypotheses are
  evidence for the valuation committee's decision."

## Segregation of duties

The analyst who compiles the packet does **not** adjudicate the mark. Price selection is the
Valuation Committee's; NAV striking/certification is fund accounting / NAV oversight's;
independent price verification is a separate control. The same person/skill must not both
compile the exception and decide the valuation.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Holdings, vendor marks, and broker
  quotes are market- and client-sensitive; vendor pricing may be **licensed** — cite provenance
  and do not redistribute raw vendor data beyond entitlement.
- Mask account/holder identifiers to what evidences the exception.
- Retain packets, citations, and the tolerance/hierarchy versions per records policy; log the
  analyst identity on every read and every packet generation.
