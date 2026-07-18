# Domain Rules — ai-evaluation-benchmark-builder

Orientation references: SR 11-7 (model risk management — development, implementation, and use;
benchmarking and outcomes analysis), NIST AI RMF (Measure function), ISO/IEC 42001 and the
firm's AI Model Evaluation Standard. The firm's evaluation methodology and its **approved
threshold catalog** take precedence and are versioned contracts (`spec_version`).

## Evaluation dimensions (the approved taxonomy — the ONLY dimensions permitted)

| Dimension | What it measures | Example metrics |
| --------- | ---------------- | --------------- |
| `task` | Core capability on representative tasks | accuracy, f1, exact_match, groundedness |
| `trigger` | Correct activation/routing vs out-of-scope | trigger_precision, trigger_recall, routing_accuracy |
| `regression` | No degradation vs the prior approved version | pass_rate |
| `safety` | Harmful-output resistance, jailbreaks, PII leakage | jailbreak_success_rate, pii_leak_rate, toxicity_rate, prompt_injection_success_rate |
| `robustness` | Stability under perturbation/adversarial input | robust_accuracy_drop, adversarial_success_rate |
| `latency` | Responsiveness under representative load | p50_latency_ms, p95_latency_ms |
| `cost` | Unit economics under the representative traffic mix | cost_per_1k_tokens_usd, cost_per_task_usd |

A requested evaluation outside this taxonomy is `needs-data` (map it first). Metric direction
is checked: a `higher-is-better` metric must use `>=`/`>`; a `lower-is-better` metric must use
`<=`/`<`. A contradiction is `direction-mismatch` — never silently reinterpret the operator.

## Required coverage by inherent risk rating (deterministic)

| Risk rating | Required dimensions |
| ----------- | ------------------- |
| **High** | task, trigger, regression, safety, robustness, latency, cost (all 7) |
| **Medium** | task, regression, safety, latency |
| **Low** | task, regression |

Coverage is `complete` only when every required dimension is present. A missing required
dimension keeps the package `draft-incomplete`; it never blocks governance from adding more.

## Documented minimum sample sizes (deterministic)

| Dimension | Minimum sample |
| --------- | -------------- |
| task | 100 |
| trigger | 50 |
| regression | 100 |
| safety | 200 |
| robustness | 100 |
| latency | 30 |
| cost | 30 |

An evaluation below its minimum is `insufficient-sample`. These are configuration, not
judgment, and are overridable only through the versioned methodology.

## Threshold & baseline provenance (never invent a number)

- A threshold or baseline `value` whose `source_id` is in `approved_sources` is `approved`.
- A `value` supplied without an approved `source_id` is `proposed` — a placeholder that keeps
  the evaluation `needs-calibration` until governance approves it.
- No `value` at all is `missing`.
- An evaluation is `ready-for-review` only when it has a representative dataset, an **approved**
  acceptance threshold, an **approved** baseline, an adequate sample, and a consistent
  direction. Anything else is flagged, not forced.

## Hard boundaries (fail closed)

- No **running/scoring** an evaluation; no pass/fail results.
- No **go/no-go, release, deployment, or promotion** decision.
- No **certification** (safe/fair/compliant/fit for purpose) or compliance/risk determination.
- No **self-approval**; `governance_approval` stays `pending` and needs human sign-off.
- No **invented** thresholds or baselines; unsourced values are `proposed`, never `approved`.

## Benchmark package — required contents

`spec_version`; system-under-eval identity + inherent risk rating; per-evaluation spec
(dimension, representative dataset, metric + direction, acceptance rule with operator/value/
provenance/source, baseline with provenance/source, sample size vs minimum, status, notes,
citations); coverage matrix vs the required set; approvals block (`governance_approval:
pending`, `reviewer_signoff_required: true`); summary counts; the standing note.
