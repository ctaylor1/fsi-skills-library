# Source Map — portfolio-drift-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved risk/analytics system of record** (versioned) | The current and prior characteristic snapshots — active weights, ex-ante tracking error, effective duration, beta, factor exposures | Read-only |
| 2 | **PMS / OMS positions & benchmark** | Underlying holdings and benchmark constituents behind the characteristics (for evidence / look-through) | Read-only |
| 3 | **Market & reference data** | Prices, classifications, factor-model definitions used to produce the characteristics | Read-only |
| 4 | **Mandate / IPS reference** (optional, versioned) | Supplied limit references used ONLY to flag proximity for routing — never adjudicated here | Read-only |
| 5 | **Drift-config** (versioned) | Attention bands and routing buffer | Read-only |

Only **approved** characteristics are compared. Both the current and prior snapshot must
carry an `approval.approved: true` and an `approval.source_ref`; an unapproved or draft
snapshot fails input validation (fail closed). Never compute a characteristic from raw
holdings here — that is the risk/analytics system's job and its output is the record.

## Citation format

`{system}:{ref}#{snapshot}` — e.g. `risksys:portfolio=PF-4471;snapshot=2026-07-15#current`
and `risksys:portfolio=PF-4471;snapshot=2026-06-30#prior`. Every change and exception cites
**both** the current and prior snapshot rows it was computed from. A supplied mandate
reference is cited to its `mandate_reference` value; the authoritative rule text lives with
`mandate-compliance-monitor`, not here.

## Version / effective-date rules

- The **drift-config** (`config_version`) is a versioned contract; the packet records the
  version so a comparison is reproducible. Bands are never tuned to a portfolio.
- Each snapshot carries an **effective date** (`as_of` for current, `prior_as_of` for prior)
  and an approval timestamp. `prior_as_of` must be strictly before `as_of`.
- The mandate reference, when supplied, is a versioned input used only for routing proximity.
  If it is absent, limit-proximity routing is disabled and the packet says so.

## Durable identifiers

- `packet_id = pdm-{portfolio_id}-{as_of}-0001` binds the output to the exact portfolio,
  current effective date, and (via `config_version`) the bands in force. Re-running with the
  same two approved snapshots and the same config reproduces the changes, exceptions, and
  priority. Downstream skills reference this `packet_id`.

## Least-privilege operations (deployment)

- `risksys.snapshot(portfolio_id, as_of)` → the approved characteristic set (paged).
- `pms.holdings(portfolio_id, as_of)` / `benchmark.constituents(benchmark_id, as_of)` →
  underlying evidence and look-through.
- `refdata.resolve(security|sector|factor_model)` → normalized classifications.
- `mandate.reference(mandate_id, config_version)` → limit references for proximity routing.
- `config.get('drift', version)` → attention bands + routing buffer.

All read-only, deterministic, durable `packet_id`, below the fixed timeout; page large
holdings/benchmark reads as resumable stages. The skill writes **nothing** to any book of
record.
