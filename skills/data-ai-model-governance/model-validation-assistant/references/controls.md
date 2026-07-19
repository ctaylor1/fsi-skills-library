# Controls — model-validation-assistant

- **Risk tier:** R3 — regulated / control decision support. Evidence + recommendations with
  **mandatory human adjudication**. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `required` — every finding, the overall severity, and the recommended
  disposition are reviewed and adjudicated by the model validation lead and the routed approver
  (per the overall severity) before any validation decision. Internal drafting may be
  reviewer-sampled.

## Prohibited (fail closed)

- **Approval, certification, or clearance of a model for use / production.** The pack is a draft
  with a `pending` validation-outcome block; a human decides.
- **Final / binding validation decision or rating.** The skill computes and recommends; it does
  not decide the model's fitness for use.
- **Closing, resolving, or waiving a finding**, or setting a finding to anything but `open`.
- **Assembling, finalizing, or filing the governed model documentation pack**, or writing the
  model registry / any system of record. Documentation assembly is a separate control activity
  (`model-risk-documenter`); this skill produces validation findings only.
- **Unsupported / unapproved assertions** — any validation statement or finding not backed by a
  cited source; any `pass` credited without independent evidence.
- **Personalized legal, investment, or compliance advice.**

## Pack / finding / outcome states (this skill may set only these)

Pack: `draft-validation-report` (completed draft) | `needs-data` (incomplete intake). Validation
outcome: `pending` only. Findings: `open` only. It may **not** set `approved`, `certified`,
`accepted`, `cleared`, `closed`, `resolved`, `waived`, or `filed`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** all seven required areas present — `conceptual_soundness`, `data`,
  `performance`, `outcomes`, `limitations`, `controls`, `monitoring`.
- **Source mapping / no unsupported claim:** every area carries at least one citation; every
  finding carries a source ref and a recommended remediation; any area asserted `pass` is
  **independently sourced** (the engine-carried `independently_sourced` flag = `independent_evidence`
  **and** an independent `source_ref`) **and** cited — a citation drawn only from a test working
  paper does not by itself make a `pass` independent.
- **Deterministic tie-out:** each area's declared `validated_status` equals the recompute from
  `declared_status` + independence + test outcomes, using the **same** independence gate the engine
  applied (the carried `independently_sourced` flag, not a re-derived proxy, so engine and guardrail
  cannot diverge; a missing/false flag fails closed); every `deficiency`/`not_tested` area carries
  an open finding; `overall_finding_severity` equals the highest finding severity.
- **Approval discipline (R3):** `validation_outcome.status == pending`, `adjudication_required`
  true, and `required_approvers` non-empty and consistent with the overall severity.
- **No autonomous-decision / filing / documentation-assembly language** (regex): `model approved
  for`, `approved for use/production`, `validation passed`, `cleared for production`, `authorized
  for use`, `fit for use`, `no further review/validation required`, `we certify`, `risk
  accepted`, `final validation determination`, `sign-off complete`, `auto-approved`, finding
  closure phrases, `documentation pack finalized/filed`, `filed the validation report`, `written
  to the model inventory / system of record`.
- Standing note present: the draft-only / no-decision / no-documentation-assembly disclaimer.

## Segregation of duties

Independent validation is distinct from model development, from documentation assembly, and from
the validation decision. The same person/skill must not both draft the validation and adjudicate
or approve it, and validation independence from development must be preserved.

## Data classification, privacy, records

- **Confidential.** The pack describes a model, its tests, and controls; reference model/data
  assets by catalog ID rather than copying sensitive datasets. Customer NPI/PII stays in the
  owning system's controls, not in this pack.
- Retain the draft pack, `framework_version`, citations, and validator sign-off with the
  validation record; log every read and every pack produced with the validator identity.
