# Source Map — financials-normalizer

Adjustment rows require `statement`, `period`, `std_account`, `adj_id`, `type` and finite `amount`; targets must already be mapped reported accounts. Subtotal `components` form an acyclic, same-statement/same-period graph. Complete role/component coverage is needed for normalized identities; otherwise that check remains not evaluable.


## Version 0.2.0 contract

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.


## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Source financial statements & schedules** (issuer/corporate/deal: 10-K/10-Q, audited FS, deal data book, management accounts) via document intelligence | The reported line items, subtotals, and totals being normalized | Read-only |
| 2 | **Controlled chart-of-accounts / mapping library** (versioned) | Standard-account taxonomy and the source-label → std-account mapping | Read-only |
| 3 | **Normalization / adjustment policy library** (versioned) | Which reclass / non-recurring adjustments are permitted and how they must be evidenced | Read-only |
| 4 | **Entity resolution** | Resolve the entity/issuer/deal so the right statements and mapping pack are used | Read-only |
| 5 | **Normalization config** (versioned) | `tie_out_tolerance`, `adjustment_materiality_pct`, `escalate_finding_count` | Read-only |

The **source statement is the position of record**; normalization never overrides a reported
figure. If two extracts (or a statement and a schedule) conflict, cite both and raise the
break for the reviewer — do not resolve it silently or pick a number.

## Citation format

`{system}:{ref}@{date}` — e.g. `fs:IS;row=Net sales;FY2025@2026-07-15` or
`fs:entity=ACME-CORP;line=IS-9;period=FY2025@2026-07-15`. Every mapped account records the
source `line_id`s in its `provenance`, and every fired finding cites the specific source
row(s) it rests on. When a finding is about a *missing* attribute (no `source_ref`, an
unmapped line), the citation points at the source-record position so the gap stays locatable.

## Freshness / effective dates

- The mapping library, normalization policy, and config are **versioned contracts**; the
  output records the `config_version` used so a normalization run is reproducible.
- State the exact `as_of` and the `source_document` in the output; a normalization is only as
  current as the extract it read.
- Re-running with the same extract, mapping, and config reproduces the normalized dataset,
  the tie-outs, and the readiness band exactly.

## Least-privilege operations (deployment)

- `docintel.extract(document_id, as_of)` → bounded, paged line items with source cell refs.
- `entity.resolve(entity_id)` → confirmed entity/issuer/deal + applicable mapping pack.
- `mapping.get('chart-of-accounts', version)` → source-label → std-account mapping.
- `policy.get('normalization', version)` → permitted adjustments + evidence rules.
- `config.get('financials-normalizer', version)` → tolerances and thresholds.

All read-only, deterministic, durable `normalization_id`, below the fixed timeout; page long
statement sets as resumable stages. The skill makes **no** writes and stages nothing for
execution — it never posts a figure to the GL, subledger, or any system of record.
