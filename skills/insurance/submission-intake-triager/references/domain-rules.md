# Domain Rules — submission-intake-triager

Deterministic **normalization, reconciliation, gap detection, and appetite triage** for a
commercial-insurance submission, and how the appetite findings map to a **routing
recommendation band**. Thresholds are configuration (versioned, owned by the underwriting
appetite/portfolio team), never hard-coded judgments and never tuned to a broker or insured.
The firm's approved underwriting appetite/guideline standard takes precedence.

## Normalization

- **Monetary / count fields** (`total_insured_value`, `annual_revenue`, `building_count`,
  `loss_count`): strip `$`, commas, `%`; accept `k`/`m`/`b` suffixes → canonical float.
- **`prior_loss_ratio`**: canonical float (e.g., `0.72`).
- **`insured_state`**: 2-letter code (full state names mapped).
- **`catastrophe_zone`**: lower-cased tag.
- Other fields: trimmed strings.

## Reconciliation (cross-document)

Values for the same canonical field are grouped across documents. The **canonical value** is
the highest-authority source per [source-map.md](source-map.md) (SOV for TIV, loss run for
loss ratio, ACORD for application data). Status:

| Status | Meaning |
| ------ | ------- |
| `single_source` | Only one document reported the field |
| `match` | Multiple documents agree (within `reconcile_tolerance`) |
| `mismatch` | Documents disagree — **all** sources cited; the underwriter resolves it |
| `unparseable` | Multiple documents reported a numeric field but none carried a parseable value; the field cannot be reconciled and seeds a gap/follow-up |

## Gap detection & follow-ups

Required fields absent from every document become **gaps**. A gap in a **critical** field
(`insured_state`, `class_code`, `effective_date`, `total_insured_value`) blocks appetite
triage (band `Incomplete`). Each gap seeds a **drafted** broker follow-up request (draft
only — a human sends it).

## Appetite rules (default config; each cites evidence)

| Rule | `pass` | `refer` | `out` |
| ---- | ------ | ------- | ----- |
| `state_in_appetite` | state ∈ `appetite_states` | — | state ∉ `appetite_states` |
| `class_in_appetite` | class ∉ `excluded_classes` | — | class ∈ `excluded_classes` |
| `tiv_within_capacity` | TIV ≤ `refer_tiv_threshold` | `refer_tiv_threshold` < TIV ≤ `max_tiv_ceiling` | TIV > `max_tiv_ceiling` |
| `loss_ratio_within_threshold` | ratio ≤ `loss_ratio_refer` | ratio > `loss_ratio_refer` | — |
| `catastrophe_exposure` | zone ∉ `cat_refer_zones` | zone ∈ `cat_refer_zones` | — |

A rule whose field is unavailable returns `not_evaluable` (and drives a gap/follow-up).
Default config (versioned; overridable per deployment): `appetite_states` = 10 approved
states; `excluded_classes` = `["1389","2911","7996"]`; `refer_tiv_threshold` = 50,000,000;
`max_tiv_ceiling` = 100,000,000; `loss_ratio_refer` = 0.60; `cat_refer_zones` =
`["tier1_wind","high_wildfire","seismic_high"]`.

## Routing recommendation mapping (deterministic, documented)

Precedence, evaluated top-down:

| Band | Rule |
| ---- | ---- |
| **Out-of-appetite (recommend decline — underwriter adjudicates)** | Any appetite rule returned `out` |
| **Incomplete — pending broker information** | No `out`, but a **critical** field is missing |
| **Refer to underwriter** | No `out` and no critical gap, but any rule returned `refer` |
| **In-appetite — route to underwriter for standard handling** | All evaluable rules `pass`, no critical gap |

The band is a **triage recommendation for a human underwriter**. It is **not** an
underwriting decision and it never binds, quotes, prices, declines, issues, or closes the
risk.

## Hard boundaries (fail closed)

- Never state or imply that coverage **is** bound, quoted, priced, declined, denied, or
  issued — describe appetite status factually and attribute the decision to the underwriter.
- Never draft a **premium/price** number.
- Never **close** the submission or tune appetite thresholds to a broker/insured.
- `Out-of-appetite` and `catastrophe_exposure` describe **appetite position**, not an
  underwriting decision or a portfolio-accumulation conclusion.
