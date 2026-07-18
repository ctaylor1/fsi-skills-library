# Controls — ai-evaluation-benchmark-builder

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The benchmark package is a *proposal* for model-risk governance.
- **Human approval:** `required` — model-risk governance (MRM/MRG) must review and approve
  the benchmark, its acceptance thresholds, and its baselines before it is used to evaluate,
  gate, or release any model. This skill drafts and packages only.

## Prohibited (fail closed)

- **Running or scoring** an evaluation; producing pass/fail results (this skill designs the
  benchmark; a separate harness/skill executes it).
- **Go/no-go, release, deployment, or promotion** decisions.
- **Certifying** the model safe, fair, compliant, unbiased, or fit for purpose.
- **Self-approving** the benchmark or governance (`governance_approval` stays `pending`).
- **Inventing** a threshold or baseline number; any asserted value must trace to an approved
  source or be flagged `proposed` for calibration.
- **Compliance / risk determinations** about the model.

## Benchmark statuses (this skill may set only these)

Per evaluation: `ready-for-review` | `needs-calibration` | `insufficient-sample` |
`direction-mismatch` | `needs-data`. Package: `draft-incomplete` |
`ready-for-governance-review`. It may **not** set `approved`, `passed`, `certified`,
`released`, or any result state.

## Required output screens (`scripts/validate_output.py`)

- Template fidelity: required sections + per-evaluation fields present; every dimension is in
  the approved 7-dimension taxonomy (`task, trigger, regression, safety, robustness, latency,
  cost`).
- No unsupported/unapproved claims: a value marked `approved` cites a source; a
  `ready-for-review` eval is fully approved-sourced, sample-adequate, and direction-consistent.
- Coverage integrity: `coverage.complete` consistent with `missing_required`; a
  `ready-for-governance-review` package is genuinely complete and fully ready.
- Required approvals: `governance_approval == "pending"`; `reviewer_signoff_required == true`.
- No determination/certification/release language (regex: "approved for production",
  "certified safe/compliant/fair", "the model passed/failed/meets all", "production-ready",
  "fit for purpose", "go/no-go decision", "no further review required", "governance sign-off
  complete").
- Standing note present.

## Segregation of duties

Designing the benchmark, **running** it, **analyzing** its results, and **approving** the
model for release are distinct control activities with distinct entitlements. The same person
or skill must not both author the acceptance thresholds and approve them; MRM/MRG approval is
independent of the model owner.

## Data classification, privacy, records

- **Confidential.** Evaluation datasets may contain customer or proprietary content; reference
  datasets by catalog id and lineage rather than embedding records; apply data minimization.
- Retain the drafted benchmark, `spec_version`, source citations, and reviewer sign-off with
  the model record per model-risk recordkeeping; log every read and every package produced
  with the author identity.
