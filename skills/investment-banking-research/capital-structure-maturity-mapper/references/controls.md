# Controls — capital-structure-maturity-mapper

- **Risk tier:** R2 — analytical/packaging support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — external delivery requires human sign-off; no advice
  or recommendation is ever made.

## Prohibited (fail closed)
- No **financing advice** or **recommendation** (refinance, issue, tender, optimal structure).
- No **ranking/labelling** a structure as good/bad/optimal.
- No **summing mixed currencies** without a supplied FX basis; no imputed principal/maturity.

## Required output screen (`scripts/validate_output.py`)
- `Σ by_seniority == total_debt` and `Σ maturity_wall == total_debt` (single-currency) within
  tolerance.
- No advice/recommendation language (regex: we recommend/should refinance/should issue/optimal
  capital structure/you should raise/advise…to issue).
- Standing disclaimer present.

## Segregation of duties
The mapper/analyst is not the advising banker; the map supports, never replaces, banker judgment
and advice.

## Data classification, privacy, records
- **Highly Confidential (MNPI / client-confidential).** Enforce information barriers; deal-team
  only.
- Retain map + source lines + as_of; log read + external-delivery approval.

## Reproducibility
`map_id` binds output to the exact debt schedule and as_of; computation is deterministic and
stdlib-only.
