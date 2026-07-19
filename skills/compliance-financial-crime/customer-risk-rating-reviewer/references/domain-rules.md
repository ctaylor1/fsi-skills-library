# Domain Rules — customer-risk-rating-reviewer

How the customer risk rating is **recomputed** from the approved weighted-factor methodology
and how the findings map to a **recommended review outcome**. Weights, thresholds, and floors
are configuration (versioned, owned by the financial-crime program), not hard-coded judgments,
and are never tuned to an individual. The firm's approved CRR methodology and applicable
AML/BSA program standards take precedence; this file documents the reference defaults.

## Factor catalog (default config)

| Factor | Max weight | Scale | Required | Floor at max |
| ------ | ---------- | ----- | -------- | ------------ |
| `customer_type` | 15 | 1..5 | yes | — |
| `geography` | 20 | 1..5 | yes | — |
| `product_channel` | 15 | 1..5 | yes | — |
| `pep_status` | 15 | 1..5 | yes | **High** |
| `sanctions_nexus` | 20 | 1..5 | yes | **Prohibited** |
| `adverse_media` | 10 | 1..5 | no | — |
| `transaction_behavior` | 5 | 1..5 | no | — |

Each factor contributes `(risk_value / scale_max) * weight`. The score is the percentage of
provided weight: `score_pct = 100 * sum(contribution) / sum(provided weight)`. The score is an
**explainable weighted sum**, never an opaque number, and never tuned to the individual.

## Band mapping (deterministic, documented)

| Band | Rule (`score_pct` cut-off) |
| ---- | -------------------------- |
| **Low** | `score_pct <= 30` |
| **Medium** | `30 < score_pct <= 60` |
| **High** | `60 < score_pct <= 85` |
| **Prohibited** | `score_pct > 85` |

**Mandatory floors** raise the band above the score-derived band: a `pep_status` at scale
maximum forces at least **High**; a `sanctions_nexus` at scale maximum forces **Prohibited**.
`recomputed_band = max_band(band_for_score(score_pct), floor_band)`.

## Findings

| Finding type | Fires when | Severity |
| ------------ | ---------- | -------- |
| `rating_discrepancy` | `recomputed_band != rating_of_record.band` | high if >= 2 bands apart, else medium |
| `mandatory_floor` | A floor-bearing factor is at scale maximum | high |
| `expired_override` | An override's `expiry_date` is before the review date | high |
| `undocumented_override` | An override lacks `approver_role` or `rationale` | high |
| `unassessed_trigger` | A review-triggering event is unassessed and medium/high severity | high/medium |
| `stale_factor` | A factor's `observed_date` is older than the staleness window (365d) | medium |
| `missing_required_factor` | A required factor is absent (recomputation low-confidence) | high |

Every finding carries its own cited evidence. There is no opaque composite "risk score" that
stands in for the rating.

## Recommended review outcome (deterministic precedence)

Evaluated highest-first (`escalate > remediate > re-rate > align`):

| Outcome | Rule |
| ------- | ---- |
| **Escalate-For-Adjudication** | `floor_band == Prohibited`, OR any `expired_override` / `undocumented_override` / `unassessed_trigger` finding |
| **Remediate-Data-First** | (not escalating) any `missing_required_factor` finding — recomputation is low-confidence until data is supplied |
| **Re-Rate-Recommended** | (not above) `recomputed_band != rating_of_record.band` |
| **Align-No-Change** | none of the above — the record and the recomputation agree with no blocking finding |

The outcome is a **recommendation for a human adjudicator**. It is not a rating decision, an
override approval, or a trigger disposition, and it never writes the system of record.

## Hard boundaries (fail closed)

- Never **set, change, or confirm** a customer risk rating, or write it to the record.
- Never **approve, validate, or extend** an override; a lapsed or undocumented override is a
  finding, not a justification the skill may endorse.
- Never **dispose of** a sanctions/PEP, adverse-media, or monitoring trigger — route it.
- Never **close** a periodic review/case or suppress a finding.
- Never **tune** weights, thresholds, or floors to the individual.

## Benign-explanation prompts (include when relevant)

A valid, currently-in-force override the reviewer can evidence; an already-scheduled periodic
review that will refresh stale factors; a same-name adverse-media collision (verify entity
resolution before attaching); a factor value awaiting a documented, in-progress refresh. The
pack invites the adjudicator to weigh these before acting.
