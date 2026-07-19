# Source Map — suitability-reg-bi-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Portfolio-accounting / **OMS** (position of record) | The recommendation, holdings, account type | Read-only |
| 2 | **Disclosures / restrictions** library (versioned) | Form CRS, Reg BI disclosure, product disclosure delivery + version | Read-only |
| 3 | **CRM** | Customer investment profile, objectives, conflicts log, supervision routing | Read-only |
| 4 | **Product data** + **planning engine** | Costs, product attributes, cost/rollover comparisons, approved tax assumptions | Read-only |
| 5 | Suitability/Reg BI **config** (versioned) | Obligation-check parameters and disposition mapping | Read-only |

Never substitute an advisor assertion for the source record. If the customer profile date is
after the recommendation date, or a disclosure version conflicts with the delivered copy, cite
both and flag for the reviewer — do not resolve silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `crm:acct=****4021;profile@2026-07-10`,
`disc:regbi;v2026-01@2026-07-11`, `oms:rec=R-5567@2026-07-14`. Every satisfied check cites the
specific record(s) and delivery/effective date behind it.

## Freshness / effective dates

- The obligation-check parameters and disposition mapping are a **versioned contract**; the
  output records the `config_version` so a review is reproducible.
- Disclosures carry a version and a delivery date; the check confirms delivery **at or before**
  the recommendation date.
- The customer profile carries an as-of date; a profile materially older than the recommendation
  is a data-quality flag for the reviewer.

## Least-privilege operations (deployment)

- `oms.recommendation(account_id, rec_id)` → the proposed action + security + holdings context.
- `disclosures.get(account_id, types[])` → delivery status + version + date for Form CRS, Reg BI
  disclosure, product disclosure.
- `crm.profile(account_id)` → investment profile, objectives, conflicts log, supervision queue.
- `product.costs(security_id)` / `planning.comparison(rec_id)` → costs, alternatives, rollover
  cost/benefit comparison.
- `config.get('regbi', version)` → check parameters + disposition mapping.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long records as
resumable stages. No mutating operation exists in this skill.
