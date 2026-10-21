# Native structured-credit intake

Use `schema_version: ir-phase4-structured/1.0`. The paired synthetic input under
`evals/files/input.json` is the complete shape. Common context requires request,
purpose/audience, `subject` of type `security` with `issuer_id`, as-of/use dates,
knowledge cutoff, information barrier, versioned sources, precise declared
citations and inherited issues. No raw documents or credentials are embedded.
All public readers reject duplicate JSON keys and non-finite constants.

Nested domain objects require exactly their documented keys. Missing numbers are
rejected, including fees, reserve and arrears; explicit zero is an observation or
assumption, never an inferred replacement for missingness. Every row requiring
citations needs nonempty references that also appear in top-level `evidence_refs`.
Source knowledge must precede row knowledge, which must be known by cutoff and
as-of. Date-only knowledge is not assigned midnight to fit a timestamp cutoff.
Source entitlements/classification/barrier/identity/validity are gated by the
canonical standard. Ineligible evidence withholds results and analytical lineage.

| Object | Fields and constraints |
| --- | --- |
| `financial_basis` | `currency`: uppercase three-letter code; `units`: ones/thousands/millions/billions; `principal_basis`: outstanding-par; `pool_scope`: explicit restricted scope. All monetary amounts share that currency and scale; no FX or unit conversion. |
| `pool` | `pool_id`, `issuer_id` matching subject issuer, `trustee_id`, `snapshot_date` equal as-of, `known_at`, `inventory_complete: true`, `evidence_refs`, `assets`. Snapshot cannot be known before its date. |
| `pool.assets[]` | Unique `asset_id`; nonempty `obligor_id`, `sector`, `jurisdiction`, `vintage`; positive `balance`; explicit boolean `eligible`; `eligibility_reason`; `known_at`; `evidence_refs`. Multiple assets can share an obligor; concentrations aggregate them. |
| `tranches` | `inventory_complete: true`, `known_at`, `evidence_refs`, `notes`. Requested security must appear. |
| `tranches.notes[]` | Unique `security_id`; unique positive integer `seniority` (1 is most senior); positive `opening_principal`; fractional fixed `annual_coupon` in [0,1]; explicit `opening_interest_arrears: 0`. Equal-rank/pro-rata classes and prior arrears are unsupported. Notes cannot exceed opening collateral par. |
| `reviewed_terms` | `profile: single-period-sequential-pay-v1`, `document_id`, `version`, `review_status: supplied-reviewed-profile`, `known_at`, `evidence_refs`, `interest_base: opening-note-principal`, `loss_priority: equity-then-junior-to-senior`, `principal_priority: senior-to-junior`, `reserve_use: fees-then-interest-only`, nonnegative `opening_reserve`, `trigger`. This is a supplied profile review assertion, not authenticated legal interpretation. |
| `reviewed_terms.trigger` | Explicit boolean `enabled`; `test_basis: ending-performing-collateral-before-distributions/post-loss-notes`; `minimum_ratio`: positive when enabled, null otherwise; `breach_operator: strictly-less-than`; `action: divert-excess-interest-to-sequential-principal`. Equality does not breach. Exact rational reconstruction of declared decimal inputs and a cross-product determine the decision; output exposes that basis and exact numerator/denominator, while the displayed ratio is approximate only. Zero note denominator is reported as null ratio and no diversion is required. |
| `scenario` | Nonempty `scenario_id`, `label`; `kind: analyst-scenario`; `known_at`, `evidence_refs`; `period_start` equal opening snapshot; later `period_end` no more than 366 days after the start; `accrual_year_fraction` in (0,1]; nonnegative `interest_collections` and `fees_due`; `recovery_timing: same-period-cash-no-reinstatement`; `assumptions`. Year fraction and interest collections are supplied scenario inputs, not derived market facts. |
| `scenario.assumptions[]` | Exactly one row per supplied asset: `asset_id`, fractional `default_fraction`, `recovery_fraction`, `prepay_fraction` in [0,1]; nonnegative `scheduled_principal` no greater than surviving par after defaults; `known_at`, `evidence_refs`. Rates apply within this period and are not annual CDR/CPR conversions. |
| `research_review` | Nonempty unique `requested_topics` strings and `assessments`. Topic scope is explicit; unprovided requested topics remain visible gaps. |
| `research_review.assessments[]` | Unique `topic_id` in requested topics; `status: supplied-reviewed` or `gap`; nonempty `assessment`; `known_at`; `evidence_refs`. A supplied-reviewed narrative is not an independent judgment or acceptance. |

Output uses the common original-bound `ir-analysis/2.0` contract. Results expose
collateral rows and concentration strata; junior-first principal loss allocation;
trigger observation and timing; segregated principal/interest/reserve waterfall;
per-note opening, write-down, interest, principal-payment and closing balances;
three numerical conservation checks; requested narrative coverage; and explicit
limits. Write-downs, cash shortfalls, breached triggers, ineligible collateral and
requested coverage gaps remain issues with partial status. The retained original
must accompany output validation; self-contained output hashes are insufficient.
