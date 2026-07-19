# Changelog — transaction-monitoring-alert-investigator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled, read-only,
alert-only AML transaction-monitoring alert investigator for the FIU.

- **Scope:** investigate AML alerts escalated from first-line triage; evaluate each escalated
  subject's transactions and KYC/counterparty/geography evidence against versioned typology
  thresholds; classify PASS/WARN/BREACH with cited evidence; build a transaction chronology;
  deduplicate against open cases; check freshness; compute a deterministic recommended
  disposition; queue a severity-ranked evidence bundle. Read-only; **no autonomous disposition,
  closure, SAR filing, account action, or system-of-record write**.
- **Typology engine (deterministic):** structuring (cash deposits below a reporting threshold),
  rapid pass-through (inflow/outflow ratio), high-risk geography, velocity spike vs the customer
  profile, and cash intensity — each explainable, evidenced, and reproducible (see
  `scripts/calculate_or_transform.py`). Per-subject severity tallies drive a recommend-only
  disposition (`recommend_escalate` / `recommend_further_review` / `recommend_monitor`).
- **Controls:** R3 decision-support; scheduled `read-only-monitoring`, alert-only posture; hard
  boundary against closing/dispositioning cases or alerts, deciding/filing SARs, freezing or
  exiting accounts/customers, and writing any system of record; versioned-config thresholds only;
  tipping-off / SAR-confidentiality controls; `required` human FIU adjudication before any
  regulated outcome.
- **Scripts:** `validate_input` (run/subject/rule/transaction schema, evaluability +
  freshness/dedup/escalation warnings), the typology engine, and `validate_output` (indicator
  well-formedness, deterministic severity/queue tie-out, deduplication integrity,
  freshness-handling, chronology ordering, disposition consistency + recommend-only vocabulary,
  no-autonomous-decision/closure/filing screen, disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-subject investigation run (structuring +
  pass-through + geography breaches, dedup, cash-intensity, a clean subject, and a stale subject),
  deterministic script checks, a no-autonomous-action safety fixture (`expect_exit 1`) plus
  injection and tipping-off cases, a no-open-baseline edge, and required-adjudication
  authorization.
- **Handoffs:** upstream from `aml-alert-triager`; downstream to
  `suspicious-activity-report-drafter`, `sanctions-match-adjudicator`,
  `kyc-customer-due-diligence-screener`, `adverse-media-investigator`, and
  `payment-fraud-case-investigator`; disposition, closure, and SAR filing remain human.

### Pending before release
- Domain SME (FIU / BSA officer) + control-owner blind review; model-risk review of the typology
  thresholds and scenario coverage; fairness review of geography and profile-based signals.
- Confirm the versioned typology scenario-library source, its owner, and the `config_version`
  contract with the transaction-monitoring tuning function.
- Wire read-only MCP integrations (transaction-monitoring/case, KYC/CDD, core-banking
  transactions, entity-resolution/network, sanctions & adverse-media screening, prior-case/SAR
  index) at deployment.
- Calibrate typology thresholds, warn buffers, and `max_staleness_days` per jurisdiction pack
  with the FIU.
