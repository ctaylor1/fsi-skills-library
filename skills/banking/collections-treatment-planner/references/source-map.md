# Source Map — collections-treatment-planner

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Core-banking / **loan servicing** (system of record) | Balance, minimum due, past-due amount, days-past-due, product | Read-only |
| 2 | **CRM** / case management | Contact history, consent & suppression flags, disclosed hardship/vulnerability context, preferences | Read-only |
| 3 | **Product terms** & document intelligence | Product-specific treatment terms, hardship program terms, disclosures | Read-only |
| 4 | Collections **policy config** (versioned) | Delinquency bands, treatment eligibility rules, contact caps | Read-only |
| 5 | Approved **calculation service** | Indicative affordability (income − expenses) — never a credit/affordability decision | Read-only |

The **servicing system of record** is authoritative for delinquency figures. Never
substitute a verbal balance or a CRM note for the servicing record; if they conflict, cite
both and flag for the specialist. Suppression/consent flags are authoritative from CRM and
must be honored even when other data invites outreach.

## Citation format

- Case evidence: `case:acct=****4521;as_of=2026-07-15`.
- Policy rule: `policy:{rule_id}@{config_version}` — e.g. `policy:TRT-ARR-03@collections-cfg-2026.07`.
- Contact history: `crm:acct=****4521;ci=CI-520`.

Every eligible treatment cites the delinquency basis, any supporting case fact, and the
policy rule that makes it eligible.

## Freshness / effective dates

- Policy config (bands, eligibility rules, contact caps) is a **versioned contract**; the
  output records the `config_version` used so a plan is reproducible.
- Delinquency figures are taken as of `as_of`; state the exact date in the output.
- Contact-frequency screen counts phone attempts in the trailing `call_cap_window_days`
  (default 7) relative to `as_of`.

## Least-privilege operations (deployment)

- `servicing.read(account_id)` → balance, DPD, product, past-due amount.
- `crm.read(account_id)` → contact history, suppression/consent flags, disclosed context,
  preferences (only what a treatment decision requires).
- `product.terms(product_type)` → treatment terms, hardship program terms.
- `config.get('collections', version)` → bands, eligibility rules, contact caps.
- `calc.affordability(income, expenses)` → indicative surplus only.

All read-only, deterministic, durable `plan_id`, below the fixed timeout. This skill never
calls a write/execute operation; staging and executing an approved treatment belong to the
human and to `loan-servicing-exception-resolver`.
