# Changelog — payment-settlement-reconciler

## [0.2.0] — 2026-09-17
- Forward-test correction: index source row identities before grouping and quarantine all affected groups across references, currencies and cycles; preserve independent source namespaces.
- Renamed from settlement-break-reconciler and merged settlement-report-summarizer into explicit explain-payout mode.
- Preserved the original merchant payout components, pending-adjustment gap and no-advice evaluation; added a discrepant funding case accepted by output validation.
- Replaced floating arithmetic and cross-scope sums with Decimal and legal-entity/account/currency/cycle partitions.
- Quarantine ambiguous duplicate groups, preserve nulls, require complete explicit waterfall components, and retain upstream differences.
- Added scoped effective schedule selection and currency precision; missing/ambiguous support is not evaluable.
- Replaced universal settlement-lag assumptions with explicit cited funding-due dates evaluated against as_of.
- Removed unsupported journals and overlapping break-impact totals; emit investigation handoffs only.
- Added input-bound full-output recomputation and 29 regression scenarios across both modes.
- Removed the standalone settlement-report-summarizer entrypoint after fixture/evaluation migration.

### Historical baseline (superseded by 0.2.0)

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** match network/acquirer/processor settlement files to bank cash, fees, reserves,
  and the internal ledger; classify breaks; quantify impact; preserve lineage; draft
  proposed-only corrections. Draft-only; no posting, no system-of-record change.
- **Reconciliation (deterministic):** per-`match_key` tie-outs for gross, fee, reserve, net
  calc, cash, and ledger, plus portfolio tie-out totals (see
  `scripts/calculate_or_transform.py`). Fee/reserve expected from the versioned schedule.
- **Break taxonomy:** `AMOUNT_MISMATCH_GROSS`, `FEE_VARIANCE`, `RESERVE_VARIANCE`,
  `NET_CALC_MISMATCH`, `NET_CASH_MISMATCH`, `LEDGER_POSTING_MISMATCH`, `MISSING_IN_BANK`,
  `MISSING_IN_LEDGER`, `MISSING_IN_SETTLEMENT`, `DUPLICATE`, `CURRENCY_MISMATCH`; plus a
  `TIMING_DIFFERENCE` reconciling item (in-transit, not a break).
- **Controls:** R2; hard boundary against posting/booking/executing corrections or marking a
  break reconciled; versioned tolerance + fee-schedule config only; `external-delivery`
  approval; PCI-scoped data handling (no PAN).
- **Scripts:** `validate_input` (source/period schema, evaluability warnings), reconciliation
  engine, `validate_output` (tie-outs, break taxonomy, lineage, idempotency, proposed-only
  corrections, impact consistency, disclaimer).
- **Evaluations:** trigger/routing, golden multi-break case, no-fee-schedule edge,
  deterministic script checks, proposed-only safety (non-compliant posted-correction fixture
  fails closed) + injection, external-delivery authorization.
- **Handoffs:** sibling `transaction-reconciliation-helper` and `gl-reconciler` boundaries;
  downstream `payment-exception-investigator`, `payment-repair-assistant`, `gl-reconciler`,
  `month-end-close-orchestrator`; upstream `settlement-report-summarizer`,
  `payment-failure-diagnoser`.

### Pending before release
- Domain SME (settlement operations) + control-owner blind review; finance sign-off on the
  proposed-correction account mappings.
- Confirm the versioned fee-schedule and tolerance config source and its owner.
- Wire read-only MCP integrations (settlement files, bank cash, ledger, schedule,
  entity-resolution) at deployment.
