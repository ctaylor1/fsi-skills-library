# Controls — privacy-impact-assessment-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The assessment is a *recommendation with evidence* for a human.
- **Human approval:** `required` — before any approval of the processing, any lawful-basis of
  record, any case closure, any prior consultation with a supervisory authority, and any
  filing. Assembling the draft is not itself an approval.

## Prohibited (fail closed)

- **Approving, authorizing, or clearing the processing to go live**, or communicating any such
  decision.
- **Setting or changing a lawful basis of record** (the assessment documents the basis; it does
  not establish it in the RoPA/system).
- **Case closure**, **filing a DPIA/report with a supervisory authority**, or initiating **prior
  consultation** (a human step).
- **Writing a system of record** or **sending/submitting** the assessment (draft-only).
- **Data-flow mapping, third-party risk, or AI risk** as a *conclusion* — route to the
  specialist and package the cited result.
- **Deciding a data-subject request** (access/erasure/objection) or drafting customer-facing
  determinations from this skill.

## Packaging states (this skill may set only these)

`blocked` (hard boundary) | `needs-information` (any evidence gap) | `ready-for-adjudication`
(complete, no hard boundary). It may **not** set `approved`, `authorized`, `live`, `closed`,
`filed`, or any decision/sign-off state.

## Hard boundaries (unlawful-processing indicators → `blocked`)

Any of the following forces `packaging_status = blocked`, band
`Unlawful-processing-proximity`, and a route to privacy counsel / the DPO — the skill makes no
disposition:

- `no_lawful_basis` — no lawful basis identified for the processing.
- `special_category_no_condition` — special-category (Art 9) data with no Art 9 condition.
- `international_transfer_no_mechanism` — a restricted transfer with no valid transfer mechanism.

## Required output screens (`../scripts/validate_output.py`)

- `packaging_status` is one of the three allowed draft states.
- **Template fidelity:** all fourteen required sections present (see
  [../assets/output-template.md](../assets/output-template.md)).
- **No unsupported claims:** every `present` evidence section carries citations.
- **Required approvals recorded:** the ledger covers every required role; any `obtained`
  entry names an approver **and** date (no fabricated sign-off).
- **Hard-boundary consistency:** an unlawful-processing indicator / `Unlawful-processing-proximity`
  band forces `blocked`.
- **Language screens:** no decision/sign-off language (`processing is approved`, `cleared to go
  live`, `case closed`, `lawful basis set in the RoPA`, …); no filing language (`filed the
  DPIA`, `submitted to the supervisory authority`, …); no send/submit language.
- **Standing note present** (draft-only / no-decision limitation).

## Segregation of duties

Assessment-drafting entitlements are distinct from adjudication and from any system-of-record
write. The same person/skill must not both assemble the assessment and approve the processing,
set the lawful basis of record, or decide the outcome.

## Data classification, privacy, records

- Handle as **Restricted**. The assessment describes personal data; it must **not embed actual
  personal data** — cite sources and use the masked `processing_ref` and category-level
  descriptions (data minimization applies to the assessment itself).
- Where the processing touches AML/BSA casework, SAR-confidentiality and tipping-off controls
  still apply: never produce customer-facing content revealing monitoring or SAR activity.
- Retain the assessment, citations, and config/template versions per records-retention policy;
  log the author identity on every read and every assessment assembly.
