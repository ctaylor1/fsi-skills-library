# Source Map — reserving-analysis-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Claims data mart / loss triangles** | Paid & incurred loss + ALAE by origin × development period (the triangle — system of record for losses) | Read-only |
| 2 | **Policy administration** | Earned premium, earned exposure, in-force, segment mapping | Read-only |
| 3 | **Underwriting / rating rules** | Segmentation basis, large-loss threshold definitions, line-of-business grouping | Read-only |
| 4 | **Actuarial / catastrophe data** | Large-loss register, catastrophe loss tags, prior selected assumptions/tail factors (versioned) | Read-only |
| 5 | **Document intelligence** | Prior actuarial reports, assumption memos, method rationale, page/section citations | Read-only |
| 6 | **Producer / agency systems** | Booking source context, program identifiers | Read-only |
| 7 | **Reserving parameter set** (methods, tail, thresholds) | Deterministic computation configuration | Read-only |

The reserving parameter set and large-loss thresholds are a **versioned contract**
(`dataset_version`). Never hard-code a factor, tail, or threshold that contradicts the
current actuarial parameter set; record the version on every analysis.

## Citation format

`{system}:{ref}@{date/version}` — e.g.
`claims-datamart:triangle=AUTO-LIAB;basis=incurred@2026-06-30`,
`policy-admin:earned_exposure=AUTO-LIAB@2026-06-30`,
`actuarial-data:large_loss=CAT-778@2026-06-30`, `config:reserving-2026Q2`.

## Freshness / effective dates

- The triangle is read as of a stated **valuation_date**; a stale diagonal changes every
  indicated ultimate. Record the valuation date on every exhibit.
- Development factors, tail, and large-loss thresholds come from the **current** actuarial
  parameter set (`dataset_version`); a superseded parameter set changes the indications.
- Paid vs. incurred basis must be stated per segment; do not mix bases within a triangle.

## Least-privilege operations (deployment)

- `claims.get_triangle(segment_id, basis, valuation_date)` → cumulative paid/incurred by
  origin × dev — read-only.
- `policy.get_exposure(segment_id, valuation_date)` / `policy.get_premium(...)` — read-only.
- `actuarial.get_parameters(dataset_version)` → methods, tail, thresholds — read-only.
- `actuarial.get_large_losses(segment_id, threshold)` — read-only.
- `docs.get_prior_report(segment_id)` — read-only controlled content.
No mutation from this skill. Reserve **selection**, the Statement of Actuarial Opinion, and
any booking to the general ledger are performed by the appointed actuary and finance
**outside** this skill after review.
