# Controls — scenario-sensitivity-generator

## Version 0.2.0 contract

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.

This engine evaluates a supplied arithmetic graph only. It has no native three-statement, DCF or credit-runner adapter and cannot establish economic coherence, financing feasibility, calibrated scenario probabilities or full instrument repricing. Model formulas must be mapped and independently checked before reuse; a model_id alone does not prove integration. Invalid/non-finite formulas and unsupported argument shapes fail explicitly.


- **Risk tier:** R2 — analytical. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — required before the pack is delivered to a
  client or written to a deal file, model repository, or published research.

## Prohibited (fail closed)

- No **investment recommendation, rating, buy/sell/hold, or price target presented as
  advice**; no "is this a good investment", "attractive entry", or "implies upside".
- No **fair-value or fairness opinion**; the skill reports mechanics, not conclusions.
- No **fabricated drivers** or formulas; no driver without provenance (`source_ref`).
- No **re-origination of a valuation** (that is the upstream modeling skills' job).
- No **extrapolation beyond a tested bracket**; no asserting a breakeven is unique when the
  output is non-monotonic.

## Required output screen (`scripts/validate_output.py`)

Independently re-derives every base/scenario/sensitivity/two-way/breakeven/threshold value
from the stated drivers + formulas and confirms tie-outs; every driver has provenance and
every output has a formula; a converged breakeven/threshold plugged back hits its target;
`model_id`/`config_version` present; and **no investment-advice language**, with the standing
disclaimer present. Any miss fails closed.

## Data classification, privacy, records

- **MNPI / client-confidential.** Treat model contents/driver values as material non-public
  information; honor information barriers; never co-mingle across walls.
- Minimize client identifiers to what the exhibit needs; never exfiltrate model/client data.
- Retain analysis + assumption set + `config_version`; log the read and any external-delivery
  approval.

## Reproducibility

`analysis_id` binds the output to the exact model, drivers, and `config_version`; identical
inputs must reproduce identical numbers or the exhibit cannot be defended in review.
