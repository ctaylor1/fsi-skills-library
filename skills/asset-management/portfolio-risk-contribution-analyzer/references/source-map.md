# Source Map — portfolio-risk-contribution-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved risk engine** (official risk outputs) | The reported ex-ante total risk that the packet **reconciles to** (`approved_engine.total_risk`) | Read-only |
| 2 | **Approved risk model** (covariance + methodology, versioned) | The annualized covariance `matrix` and the methodology `name`/`version` used to compute contributions | Read-only |
| 3 | **PMS/OMS holdings** | Position of record for the portfolio **weights** and grouping labels (issuer/sector/asset class) | Read-only |
| 4 | **Prior approved risk-contribution packet** (packet store) | Baseline (`total_risk`, per-position `pcr`/`trc`) for the **material-change** comparison | Read-only |
| 5 | **Versioned riskcontrib config** | Reconciliation tolerance, materiality thresholds, grouping dimension, rounding | Read-only |

The **approved risk engine total is the reconciliation anchor**: the packet reconciles its
computed total to it and **never overwrites it**. The **covariance and methodology come from
the approved, versioned risk model**; **weights come from PMS/OMS**. Every weight, the
covariance, the methodology, the engine total, and the prior-review reference must resolve to
one of the above with a dated citation. When a source conflicts (e.g. weights differ between a
draft blotter and PMS/OMS), keep the **position of record** and record the other as a sourced
note; do not silently choose.

## Citation format

`{source}:{ref}@{date}` — e.g. `pms:holdings FUND-ORION-EQ@2026-07-15`,
`riskmdl:annualized position covariance FUND-ORION-EQ@2026-07-15`,
`riskmdl:approved methodology v2026.06@2026-06-30`,
`riskengine:official ex-ante volatility FUND-ORION-EQ@2026-07-15`,
`packet:riskcontrib-FUND-ORION-EQ-2026-04-15@2026-04-15`. Each entry in the packet's
`assumptions_register` carries `provenance` (the source class) and `citation` (the specific
ref + date). `scripts/validate_output.py` rejects any assumption missing either, and requires
the methodology `name` and `version`.

## Freshness / effective dates

- The **`as_of`** anchors both the weights and the covariance; do not mix dates within one
  packet. A covariance from a different date than the holdings is a data-quality break.
- **methodology `version`** and **`config_version`** are **versioned contracts**; the packet
  records both so a result is reproducible and a change in method is never mistaken for a
  change in the book.
- The **prior-review `as_of`** and `packet_id` bind the material-change comparison to a
  specific baseline; both are recorded.
- The **`inputs_hash`** binds the packet to the exact numeric inputs used; re-running the same
  inputs reproduces the same `packet_id` and the same numbers.

## Durable identifiers

- `packet_id = riskcontrib-{portfolio_id}-{as_of}-{inputs_hash}` — the durable job ID for this
  packet; downstream skills reference it rather than recomputing.
- `inputs_hash` — sha256 (16 hex chars) over weights, covariance, methodology version,
  grouping, engine total, materiality/tolerance config, and the prior packet id.
- `prior_packet_id` — the durable ID of the baseline packet the material-change section
  compares against.

## Least-privilege operations (deployment)

- `holdings.read(portfolio_id, as_of)` → positions with weights and grouping labels.
- `riskmodel.get(portfolio_id, as_of, version)` → covariance matrix + methodology metadata.
- `riskengine.total(portfolio_id, as_of)` → official ex-ante total risk (reconciliation anchor).
- `packetstore.read(prior_packet_id)` → prior decomposition baseline.
- `config.get('riskcontrib', version)` → tolerance, materiality thresholds, grouping, rounding.

All read-only, deterministic, durable `packet_id`, below the fixed timeout. This skill makes
**no writes**; delivery to a committee, client, or report is a separate, human-approved step.

## Executable input additions

Use [phase1-contract.md](phase1-contract.md) for the current required fields, scope and detached-original validation. The service calls above are integration contracts; the bundled scripts do not implement those connectors. Source binding proves reproducibility against supplied records, not their authenticity.
