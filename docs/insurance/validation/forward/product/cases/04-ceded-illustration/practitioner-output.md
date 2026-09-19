# Reinsurance layer illustration — DRAFT

Synthetic treaty ****0001, synthetic cedent, calendar 2026, USD. The supplied and reviewed illustration basis is losses occurring; eligibility is a supplied assumption from eligibility-review-v1/row1, not a decision made here.

- Article 1 states a USD 10m per-occurrence layer above USD 5m for eligible 2026 losses (synthetic-treaty:treaty-v1/article-1@2026-01-01).
- Article 2 states an explicit USD 20m annual aggregate (synthetic-treaty:treaty-v1/article-2@2026-01-01).
- Article 3 states one reinstatement restoring erosion pro rata as to amount at 100% of the USD 2m layer premium with no time adjustment (synthetic-treaty:treaty-v1/article-3@2026-01-01).

For the USD 12m synthetic loss dated 2026-07-01 (synthetic-bordereau:loss-bordereau-v1/row1@2026-07-01), the illustrative layer amount is min(12m - 5m, 10m) = 7m. Illustrative ceded recovery is 7m, cumulative ceded 7m, and remaining aggregate 20m - 7m = 13m. The first erosion restores 7m, and the illustrative reinstatement premium is 7m / 10m × 100% × 2m = 1.4m. These are mechanics under the supplied assumptions; no real-claim recoverability, billing or booking decision is made. No structural gap prevents this bounded illustration; source authenticity and professional acceptance have not been established.

Informational interpretation only; not a coverage or recoverability determination, reserving or accounting decision, or legal advice.
