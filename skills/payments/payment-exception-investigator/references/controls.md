# Controls — payment-exception-investigator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis
  (every next step is a *proposed* action via the approval broker).
- **Human approval:** `required` — before any camt.029 recall response, return, repair,
  resubmission, release of funds, case closure, or system-of-record change. This skill produces
  **evidence + a recommendation**; a human adjudicates.

## Prohibited (fail closed)

- **Moving money**: no return, reissue, release, debit, credit, or posting. Fund movement is
  `payment-repair-assistant` under approval — never here.
- **Case closure / determination / filing**: no closing, clearing, exonerating, or "final
  determination"; no regulatory filing.
- **Issuing scheme responses**: no camt.029 (recall answer), pacs.004 (return), or pacs.002
  status is *sent* from this skill; the message is drafted as a recommendation only.
- **Auto-merge** of exceptions/cases: a match is **linked** (`possible-duplicate`) for human
  confirmation.
- **Sanctions / fraud adjudication**: routed to the specialist; never decided here.

## Dispositions (this skill may set only these — all RECOMMENDATIONS)

`recommend-repair-and-resubmit` | `recommend-return-to-originator` | `recommend-honor-recall` |
`recommend-reject-recall` | `recommend-request-information` | `route-specialist` |
`needs-data` | `possible-duplicate`.

It may **not** set `closed`, `filed`, `settled`, `posted`, `determined`, `returned`, or
`released`, and may not carry an `executed_action` / `system_write` field.

## Required output screens (`scripts/validate_output.py`)

- Durable `case_id` present on every record (`PEI-<id>`).
- Disposition is one of the recommendation states above; `decision_authority` =
  `human-adjudication-required`; each recommendation is `requires_approval: true`.
- Every evidence item is cited: bundle citations non-empty and each chronology event cited.
- `route-specialist` targets a known specialist skill.
- `priority_band` ties out to `priority_score` using the same thresholds the builder used
  (`priority_thresholds`, from the priority config) and the same fraud/sanctions risk override —
  the `route-specialist` disposition alone does not raise the band.
- No closure / determination / fund-movement / filing language (regex screen).
- Standing note present.

## Segregation of duties

Investigation (evidence + recommendation) is distinct from **diagnosis** (upstream) and from
**repair execution** (downstream, money movement). The same person/skill must not both
recommend a repair and execute it. Entitlements, metrics, and case states differ.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Mask debtor/creditor account and
  name identifiers to what the evidence requires.
- Retain investigation records, evidence bundles, citations, and the `reason_code_set_version` /
  `config_version` per payments recordkeeping; log analyst identity on every read, recommendation,
  and route.
