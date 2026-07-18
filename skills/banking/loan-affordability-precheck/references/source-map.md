# Source Map — loan-affordability-precheck

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Product terms / credit-policy config** (versioned) | DTI/residual thresholds, stress parameters, band mapping | Read-only |
| 2 | Core-banking / **loan origination-servicing** | Applicant income, obligations, existing housing/debt, requested loan terms | Read-only |
| 3 | **Document intelligence** | Income/expense figures extracted from pay stubs, statements, tax forms (with citations) | Read-only |
| 4 | **CRM** | Applicant relationship context, disclosed intent, prior prechecks | Read-only |
| 5 | **Approved calculation service** | Amortization / DTI computation (mirrored deterministically in `scripts/`) | Read-only |

Disclosed figures are inputs to an **indicative** estimate; they are not verified underwriting data.
If a document source and a disclosed figure conflict, cite both and flag for the reviewer — never
silently pick one. The affordability precheck never substitutes for income/asset verification.

## Citation format

`{system}:{ref}@{date}` — e.g. `los:applicant=****4321;field=gross_monthly@2026-07-15` or
`docintel:paystub=PS-2026-06;field=net_pay@2026-07-01`. Record the `config_version` for every
threshold used so the band is reproducible.

## Freshness / effective dates

- Threshold/stress config is a **versioned contract**; the output records the `config_version` used.
- Rates and product terms are time-sensitive; state the `as_of` date and the assumed `annual_rate_pct`
  explicitly (a precheck is not a rate lock or an offer).
- Disclosed income/expense figures should carry their own effective date; stale figures make the
  estimate indicative.

## Least-privilege operations (deployment)

- `los.applicant_profile(applicant_id)` → income, obligations, existing housing/debt (read-only).
- `los.loan_request(applicant_id)` → requested principal, rate, term, product type.
- `docintel.extract(document_id, fields)` → cited income/expense figures.
- `config.get('affordability', version)` → thresholds + stress parameters + band mapping.
- `calc.amortize(principal, rate, term)` → payment (mirrored by `scripts/calculate_or_transform.py`).

All read-only, deterministic, durable `precheck_id`, below the fixed timeout. No writes to the
loan-origination system, no decision recorded, no applicant-facing decision sent from this skill.
