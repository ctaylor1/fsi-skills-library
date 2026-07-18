# Domain Rules — ai-risk-assessment-builder

Orientation references: NIST AI RMF, ISO/IEC 42001, SR 11-7 (model risk management), and
EU AI Act risk framing. The firm's **control framework / risk-domain taxonomy** takes
precedence and is a versioned contract (`framework_version`). All scoring below is
configuration, not judgment — a reviewer may override during adjudication, but the draft
states the computed value.

## Required risk domains (all ten, always scored)

`data`, `model`, `fairness`, `explainability`, `security`, `privacy`, `third_party`,
`human_oversight`, `resilience`, `monitoring`. A pack missing any domain is `needs-data`, not
a completed assessment.

## Inherent risk (likelihood x impact matrix)

Likelihood and impact are each `Low` (1), `Medium` (2), `High` (3). Inherent score is the
product; the band uses a standard 3x3 matrix:

| inherent_score = L x I | Band |
| ---------------------- | ---- |
| ≥ 6 | **High** |
| 3–4 | **Medium** |
| ≤ 2 | **Low** |

## Control coverage

For each domain, count only **applicable** controls (`status != not_applicable`). Weight:
`implemented` = 1.0, `partial` = 0.5, `missing` = 0.0. A control **without an `evidence_ref`
is unproven** and is treated as `missing` (weight 0.0) regardless of its declared status.

`coverage_pct = sum(weights) / count(applicable)` (0.0 if none applicable).

| coverage_pct | Coverage tier | Likelihood reduction |
| ------------ | ------------- | -------------------- |
| ≥ 0.80 | **Strong** | −2 steps |
| ≥ 0.50 | **Moderate** | −1 step |
| > 0.00 | **Weak** | 0 |
| = 0.00 | **None** | 0 |

## Residual risk (controls reduce likelihood, never impact)

`residual_likelihood = max(1, likelihood − reduction)`. `residual_score = residual_likelihood
x impact`; the residual band uses the same matrix thresholds. **Impact is never reduced** by
declared controls, and residual is **never scored to zero** — a material use case stays
material and requires ongoing monitoring. Strong controls on a High-impact domain typically
leave a **Medium** residual, not Low.

## Findings (open items requiring adjudication)

A finding is generated for a domain when:

- `residual_band == High`; **or**
- `residual_band == Medium` **and** coverage tier is `Weak` or `None`.

Each finding carries: `domain`, `severity` (= residual band), `gap_controls` (the
`missing`/`partial`/unproven control IDs), `recommended_remediation` (from each gap control's
`recommended_action`, else a domain default), `owner`, `source_refs`, `status: open`, and
`adjudication_required: true`. A finding is **never** closed, resolved, or waived here.

## Overall residual rating and approver routing

`overall_residual_rating` = the **highest** residual band across the ten domains
(highest-wins). Routing (approval `status` is always `pending`):

| Overall residual | Required approvers |
| ---------------- | ------------------ |
| **High** | Model Risk Committee; Chief Risk Officer (or delegate) |
| **Medium** | AI Risk Officer; Accountable Business Owner |
| **Low** | AI Risk Officer |

## Hard boundaries (fail closed)

- No **approval, certification, risk acceptance, or deployment clearance**.
- No **final / binding risk determination**; the residual band is a computed recommendation.
- No **closing / resolving / waiving** a finding.
- No **unsupported assertion**: every domain cited; every finding sourced and remediated;
  every counted control has evidence.
- No **guessing a score**: a missing domain, likelihood, or impact is `needs-data`.
