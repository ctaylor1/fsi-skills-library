# Controls — investment-data-quality-exception-detector

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the queue is delivered to another
  team, written to a case/system of record, or used to drive a correction.

## Prohibited (fail closed)

- No **data correction, override, fill, or normalization**. The queue emits findings only; it
  carries no `corrected_value`, `override_value`, `canonical_value`, `applied_fix`, or
  `resolution` field.
- No **suppression, waiver, dismissal, or closure** of an exception — every emitted exception
  has `status: open`. Disposition belongs to a human/case, not this detector.
- No **choosing the canonical feed / value** and no statement that "the correct value is …";
  approved-source disagreements are **routed**, not resolved.
- No **personalized investment advice**, NAV adjustment, or trade instruction derived from a
  detection.
- No **threshold or severity tuning to an individual instrument**; use only the versioned
  config.
- No **opaque quality score** presented as decisive; checks are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every exception has ≥1 cited evidence row **with an as-of**, a `severity` in
  {Low, Medium, High, Critical}, and `status` = `open`.
- `queue_priority` equals the deterministic mapping from the exception set's severities.
- No forbidden correction/override/resolution fields anywhere in the queue.
- Reference-data-conflict exceptions (`conflicting_classification`) carry
  `route_to = investment-vendor-feed-reconciler`.
- No correction/suppression/canonical-choice/advice language (regex screen: "corrected the",
  "auto-corrected", "overrode", "set the price to", "canonical value is", "the correct value
  is", "suppress", "waive", "close the exception", "adjust the nav", etc.).
- Standing disclaimer present: "Detection evidence only; exceptions are open findings. No data
  has been corrected, overridden, or suppressed, and no canonical value has been chosen."

## Fairness / conduct

- Data quality only; no protected-class attributes are used. Describe exceptions factually and
  attribute any judgement about the underlying data to the source owner / reconciler.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Minimize holdings/pricing data in the
  queue to what evidences an exception; mask portfolio/account identifiers where the audience
  does not need them.
- Retain the queue + citations + `config_version` per records policy; log the read and any
  external-delivery approval.

## Reproducibility

`exception_queue_id` binds output to the exact snapshot inputs and **config version**;
re-running with the same inputs and config reproduces the exceptions, severities, routing, and
priority.
