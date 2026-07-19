# Controls — adverse-media-investigator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis; every disposition is a *recommendation*, never an action.
- **Human approval:** `required` — for every escalation, EDD, sanctions/PEP determination,
  rating change, case closure, and any filing. This skill proposes and evidences; humans
  decide.

## Prohibited (fail closed)

- **Case closure**, **customer clearance**, **exoneration**, or any **final determination**
  (including confirming a sanctions/PEP true match).
- **SAR drafting or filing**, or asserting a SAR has been / will be filed.
- **Attributing adverse media to a subject on a name match alone** — an unresolved
  common-name subject is `needs-data`, not a match.
- **Adjudicating sanctions/PEP** proximity (route to the specialist).
- **Recalculating the customer risk rating** (route to the rating reviewer).
- **Tipping-off**: any customer-facing content revealing screening, monitoring, or SAR
  activity.

## Case dispositions (this skill may set only these — all recommendations)

`recommend-escalate-edd` | `recommend-monitor` | `recommend-no-material-adverse-media` |
`recommend-route-sanctions-pep` | `needs-data`.

It may **not** set `cleared`, `closed`, `no-adverse-media` (as a determination),
`confirmed-match`, `filed`, or `no-action`.

## Required output screens (`scripts/validate_output.py`)

- Every case carries a durable `case_id` (`AMI-...`).
- Disposition is one of the allowed recommendations (no closure/clearance/determination/
  filing states).
- `materiality_band` ties out to `materiality_score`; disposition is coherent with the band;
  routing carries a sanctions/PEP hit + named specialist; `needs-data` lists what is missing.
- Every evidence item is cited — matched hits, chronology entries, and the bundle citation
  list are non-empty.
- No closure/determination/filing language (regex incl. "close the case", "cleared the
  customer", "confirmed true match", "we have determined", "file the sar", "exonerat").
- No tipping-off language (customer-facing disclosure of screening/monitoring/SAR).
- Standing note present: "Adverse-media investigation is decision support only; no case has
  been closed, no customer cleared or determined, and no filing has been made."

## Segregation of duties

Adverse-media investigation is distinct from sanctions adjudication, risk-rating review, EDD
sign-off, and SAR filing. The same person/skill must not both build the evidence and make the
regulated decision it supports.

## Data classification, privacy, records

- **Restricted (AML/BSA).** SAR-confidentiality and tipping-off controls apply.
- Mask government identifiers and reduce DOB to year in output; retain named parties only as
  evidenced by cited sources.
- Retain the case, evidence bundle, discarded-namesake rationale, citations, and scoring
  `config_version` per BSA recordkeeping; log analyst identity on every read and disposition.
