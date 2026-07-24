# Source Map — valuation-exception-packet

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Pricing / IBOR** (system of record) | Carried price, holdings, prior price, as-of, `case_id` context | Read-only |
| 2 | **Approved pricing vendors** | Evaluated prices, vendor as-of/EOD stamps (observed inputs) | Read-only |
| 3 | **Broker-quote capture** | Executable (firm) and indicative quotes | Read-only |
| 4 | **Trade blotter / OMS** | Executed trade prints (size, time) for the name | Read-only |
| 5 | **Corporate actions** | Splits, dividends, factor/terms context for move validation | Read-only |
| 6 | **Valuation policy / tolerance config** (versioned) | Staleness days, outlier bands, dispute tolerance, pricing hierarchy | Read-only |

The **carried price** (pricing/IBOR) is the system of record for what the fund currently holds
the security at. It is context, **not** the answer — the packet compiles evidence about whether
that carried price is stale/disputed/off-market and hands the decision to the committee. This
skill never writes back to pricing/IBOR.

## Observed vs hypothesis (by `source_type`)

| `source_type` | Class | Notes |
| ------------- | ----- | ----- |
| `exchange_close` | **observation** | Official close in an active market (Level 1). |
| `vendor_evaluated` | **observation** | Approved-vendor evaluated price with an as-of stamp. |
| `executable_quote` | **observation** | Firm/executable broker quote (`firm: true`). |
| `trade_print` | **observation** | Arm's-length executed trade of sufficient size. |
| `indicative_quote` | **hypothesis** | Non-firm broker indication. |
| `matrix_price` | **hypothesis** | Matrix/spread-based estimate. |
| `model_price` | **hypothesis** | Model / comparable-based estimate (unobservable inputs, Level 3). |
| `carry_forward` | **hypothesis** | Prior-day price carried forward (stale by construction). |

A hypothesis is **evidence**, never an observed price. See
[domain-rules.md](domain-rules.md) for the full pricing hierarchy and thresholds.

## Citation format

`{system}:{ref}@{as_of/version}` — e.g.
`pricing:secid=US1234@2026-07-17`,
`vendor:IDC;secid=US1234@2026-07-17EOD`,
`broker:GS;secid=US1234@2026-07-17T15:02Z`,
`trace:print=TP-9931@2026-07-17T14:32Z`,
`config:valuation-tolerances@v2026.07`.

## Freshness / effective dates

- Every candidate price carries an **as-of** time/date; staleness is measured in **business
  days** against the valuation date (`as_of`).
- Tolerance config and the pricing hierarchy are **versioned contracts**; the version is
  recorded on every case for reproducibility. If the config is unversioned or stale, fail
  closed and flag it (do not assess against an unknown rule set).

## Least-privilege operations (deployment)

- `pricing.read(book, as_of)`, `pricing.prior(secid, as_of)` — read-only carried/prior price.
- `vendor.prices(secid, as_of)`, `broker.quotes(secid, as_of)`, `trades.prints(secid, from,to)`
  — read-only observed inputs.
- `corpactions.read(secid, window)` — read-only move context.
- `config.get('valuation-tolerances'|'pricing-hierarchy', version)` — read-only.

No mutation from this skill. It reads sources and emits a packet; the price decision and NAV
striking are separate, human-approved actions in other systems/skills.
