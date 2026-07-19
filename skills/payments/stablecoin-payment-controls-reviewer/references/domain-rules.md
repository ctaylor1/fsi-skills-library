# Domain Rules — stablecoin-payment-controls-reviewer

Explainable control **findings** and how they map to a **review disposition**. Thresholds are
configuration (versioned, owned by the payments risk/compliance team), not hard-coded
judgments, and never tuned to an individual program. Orientation references: the US GENIUS
Act (payment-stablecoin reserve/attestation/disclosure regime), EU MiCA (e-money/asset-
referenced tokens), NYDFS stablecoin guidance, and FATF Recommendation 16 (travel rule).
These orient the control set; the firm's approved, jurisdiction-specific policy governs and
takes precedence.

## Control catalog and rules (default config)

Each control is evaluated to `pass`, `fail`, `gap` (required but not evidenced /
`attested: false`), or `not_evaluable` (insufficient metrics). Evidence is the control's
`source_ref`.

| Control id | Category | Requirement | Fires (default) |
| ---------- | -------- | ----------- | --------------- |
| `reserve_backing_ratio` | reserve | Reserves fully back outstanding tokens (≥ 1:1) | `fail` if `reserve_market_value / (outstanding_tokens × par_value)` < `min_backing_ratio` (1.0) |
| `reserve_asset_quality` | reserve | Permitted high-quality liquid assets | `fail` if `eligible_pct` < `min_eligible_pct` (100.0) |
| `reserve_attestation_current` | reserve | Attestation within cadence | `fail` if age(`last_attestation_date` → `as_of`) > `max_attestation_age_days` (31) |
| `reserve_segregation` | reserve | Reserves segregated from operating funds | `fail` if `segregated` is false |
| `custody_qualified_custodian` | custody | Assets at a qualified custodian | `fail` if `qualified` is false |
| `key_management` | custody | Quorum-based MPC/HSM signing keys | `fail` if scheme not MPC/HSM/threshold or no `quorum` |
| `sanctions_wallet_screening` | screening | Wallet screening vs sanctions lists | `fail` if `enabled` is false |
| `travel_rule` | screening | FATF travel-rule data capture | `fail` if not `enabled`; `gap` if `threshold` > `required_travel_rule_max` (1000) |
| `kyc_program` | screening | KYC on originator/beneficiary | `fail` if `enabled` is false |
| `txn_limits` | transaction | Per-txn and daily value limits | `gap` if limits absent; `fail` if a limit is 0 |
| `finality_confirmations` | transaction | Min confirmations before credit | `fail` if `min_confirmations` < `required_min_confirmations` (12) |
| `address_allowlist` | transaction | Address allow/blocklist enforced | `fail` if `enforced` is false |
| `incident_response` | operational | Runbook for key compromise/depeg/halt | `fail` if `runbook` is false |
| `reorg_handling` | operational | Chain reorg/fork handling policy | `fail` if `policy` is false |
| `onchain_ledger_recon` | reconciliation | On-chain balances tie to ledger | `fail` if `break_bps` > `tolerance_bps` (5.0) |
| `mint_burn_recon` | reconciliation | Mint/burn tie to reserve movements | `fail` if `reconciled` is false |
| `redemption_disclosure` | disclosure | Redemption rights/timing disclosed | `fail` if `disclosed` is false |
| `reserve_reporting` | disclosure | Reserve composition reported on cadence | `fail` if `cadence_days` > `required_report_cadence_days` (31) |

Any control with `attested: false` is reported as a `gap`. A control missing the metric it
needs is `not_evaluable` (never silently a pass). Findings are **independent and evidenced**;
there is no opaque composite "controls score".

## Critical controls

`reserve_backing_ratio`, `reserve_asset_quality`, `reserve_attestation_current`,
`custody_qualified_custodian`, `sanctions_wallet_screening`, `travel_rule`,
`onchain_ledger_recon`. A `fail`, `gap`, **or** `not_evaluable` on any critical control
escalates (fail-closed: an un-evaluable critical control is treated as a defect).

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Controls Evidenced** | No fail/gap findings and no un-evaluable critical control |
| **Findings - Remediation Recommended** | ≥1 fail/gap finding, none in a critical control, and fewer than `escalate_fail_count` (3) fails |
| **Material Gaps - Escalate** | Any critical-control defect (fail/gap/not_evaluable) OR ≥ `escalate_fail_count` (3) fails |

Disposition is a **triage suggestion for a human adjudicator**. It is never a compliance
determination, launch approval, attestation, or program action.

## Hard boundaries (fail closed)

- Never state or imply **approval, compliance, or attestation** — describe the control state
  factually and attribute the decision to the human adjudicator.
- Never assert a **sanctions violation or hit disposition**; report the screening control
  state and route matches to `sanctions-match-adjudicator`.
- Never **close, waive, file, or write a system of record**.
- Never tune thresholds to the program; use only the versioned config.

## Config (versioned contract)

`min_backing_ratio`, `min_eligible_pct`, `max_attestation_age_days`, `par_value`,
`required_travel_rule_max`, `required_min_confirmations`, `recon_break_tolerance_bps`,
`required_report_cadence_days`, `escalate_fail_count`. Record `config_version` in the output
so the review reproduces. Jurisdiction packs may override these (e.g., MiCA vs GENIUS Act
reserve composition and reporting cadence) without changing the engine.
