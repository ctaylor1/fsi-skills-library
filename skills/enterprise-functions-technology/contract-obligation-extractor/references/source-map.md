# Source Map — contract-obligation-extractor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Contract / CLM system** | System of record for the executed contract, `register_id`, contract metadata, recorded reviews | Read-only |
| 2 | **Document intelligence** | The clause text, headings, and clause/page-level citations that back every extraction | Read-only |
| 3 | **Contract taxonomy / obligation-type register** (versioned) | The required obligation categories the register must cover | Read-only |
| 4 | **Procurement / vendor master** | Counterparty identity, contract type, relationship context | Read-only |
| 5 | **Knowledge / policy systems** | Standard clause positions and definitions used only to characterize, not to advise | Read-only |

The executed contract in the CLM system wins on conflict; document intelligence provides the
evidencing clause text and citations. The taxonomy is the authority on what categories the
register must address. This skill reads only — it never writes back an extraction, decision,
interpretation, or delivery.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `clm:contract=K-7788;clause=4.1@2025-07-01`,
`clm:review=RV-1@2026-07-16`, `config:contract-taxonomy@2026.07`. Every `extracted`,
`ambiguous`, or `conflict` entry carries a clause citation; an extraction with no resolvable
clause is `unsourced` and becomes a `needs-source` open item — never an asserted obligation.

## Freshness / effective dates

- Each clause citation records the contract version/date it was read from; work the current
  executed version, not a superseded draft.
- The `taxonomy`, the register template, and the review requirements are **versioned
  contracts**; their versions are recorded on the manifest (`config_version`,
  `template_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `clm.read(contract_id)` → contract metadata, clauses, recorded reviews — read-only.
- `docintel.get(clause_id)` / `docintel.cite(clause_id)` → clause text + citation — read-only.
- `taxonomy.get(version)` → required obligation categories — read-only.
- `vendor.read(counterparty_id)` → counterparty identity/context — read-only.
No mutation from this skill. The assembled register is a **draft**; any delivery, execution,
or system-of-record change is a separate, human-approved step via the approval broker.
