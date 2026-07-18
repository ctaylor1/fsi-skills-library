# Changelog — iso-20022-message-interpreter

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new` relative to the AWS
baseline; authored fresh here).

- **Scope:** read-only, explanatory interpretation of a single ISO 20022 payment message
  (pain / pacs / camt and related families) with source-linked findings.
- **Triggers:** positive (interpret/explain a message, decode status/reason codes, tie out
  control totals, validate identifiers, detect truncation); negative (repair/resubmit,
  fund-release, sanctions/fraud/compliance determination) with routing to adjacent skills.
- **Controls:** R2; read-only; no repair/resubmission/fund movement; no regulated
  determination; no silent correction of breaks or codes; deterministic no-advice /
  prohibited-claim screen + standing disclaimer + citation coverage; external-delivery human
  approval.
- **Tools/data:** ISO 20022 schema/message-repository, usage guidelines (CBPR+/HVPS+/SEPA/
  FedNow/RTP), validation engine, external code sets, ISO-to-MT transformation maps, payment
  status data — all read-only.
- **Scripts:** `validate_input.py` (schema, identifiers, citations, datetime; control-total,
  currency, truncation, character-set, missing-reason warnings), `calculate_or_transform.py`
  (classification, tie-outs, IBAN/BIC/UETR checks, truncation/character-set detection, status
  decoding), and `validate_output.py` (citation coverage, tie-out consistency, no-advice
  screen, disclaimer, rejected-status reason coverage). Each carries a `--selftest`.
- **Evaluations:** trigger/routing, golden normal (pacs.008) + rejection edge (pacs.002),
  deterministic script checks, a fail-closed safety check on a non-compliant interpretation,
  a bad-input safety check, prompt-injection, and external-delivery authorization.
- **Handoffs:** downstream to `payment-failure-diagnoser`, `payment-exception-investigator`,
  and `payment-repair-assistant`; related `settlement-report-summarizer`,
  `settlement-break-reconciler`, and `transaction-reconciliation-helper` kept distinct.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (schema/message repository, code-set retrieval, validation
  engine, transformation maps) at deployment.
- Broaden the status/reason/purpose code coverage per scheme and version; add HVPS+ and SEPA
  usage-guideline fixtures.
- With/without benchmark vs. no-skill baseline.
