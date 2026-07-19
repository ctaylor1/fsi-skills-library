# Source Map — stablecoin-payment-controls-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Independent **reserve attestation / audit** report | Backing ratio, asset composition, attestation currency | Read-only |
| 2 | Executed **custody & trust agreements** | Segregation, qualified-custodian, key-management terms | Read-only |
| 3 | **Screening / risk configuration** (gateway, processor, fraud platform) | Wallet sanctions screening, travel-rule, KYC, limits, allowlist | Read-only |
| 4 | **Settlement & reconciliation reports** (ledger + on-chain) | Confirmations/finality, on-chain vs ledger break, mint/burn tie-out | Read-only |
| 5 | Published **customer disclosures** | Redemption terms, reserve reporting cadence | Read-only |
| 6 | **Network rules** and ISO 20022 message context | Rail-specific control expectations, message evidence | Read-only |
| 7 | Versioned **controls config** | Thresholds and the disposition mapping | Read-only |

The reserve attestation and executed agreements are the **position of record**. Never
substitute a program's self-description for the attested figure. If the attestation and a
configuration/report conflict, cite both and flag for the reviewer.

## Citation format

`controls:{source_ref}` where `source_ref` identifies the document/config and its key —
e.g. `controls:reserve-attestation;doc=RS-2026-06;as_of=2026-06-30`. Every finding cites the
specific `source_ref` that evidences (or fails to evidence) the control.

## Freshness / effective dates

- The **controls config** (thresholds, mapping) is a **versioned contract**; the output
  records the `config_version` so a review is reproducible.
- Attestation currency is measured against the review's `as_of`, not "today"; a past-period
  review must use that period's `as_of`.
- Reserve figures are point-in-time; state the attestation date in the output.

## Least-privilege operations (deployment)

- `attestation.get(program, period)` → reserve figures, composition, issue date.
- `agreements.get(program)` → custody/trust segregation and key-management terms.
- `riskcfg.get(program)` → screening, travel-rule, limits, allowlist settings.
- `recon.get(program, date)` → on-chain vs ledger break, mint/burn tie-out.
- `disclosures.get(program)` → redemption terms, reserve-report cadence.
- `config.get('stablecoin-controls', version)` → thresholds + disposition mapping.

All read-only, deterministic, bounded payloads, durable `review_id`, below the fixed
timeout; page long control sets as resumable stages. No mutating or scheduled-agent
operations — this skill is interactive and never writes.
