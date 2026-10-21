# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — performance-composite-reviewer

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (2026 industry-expansion cohort, `new` relative to
the AWS baseline).

- **Scope:** apply the firm's approved, versioned composite-inclusion rules to portfolio/account
  data; emit a cited membership **exception queue** with a queue priority. Read-only; no
  membership, methodology, or performance change; mandatory human adjudication (R3).
- **Rules (deterministic):** strategy match, discretion, minimum-asset, inclusion-lag timing,
  exclusion "last full period" timing, significant-cash-flow policy, and completeness — each rule
  evaluated against the `rule_version` in effect for the `as_of` date (see
  `references/domain-rules.md`, `scripts/calculate_or_transform.py`).
- **Exception taxonomy:** `improper_inclusion`, `stale_inclusion`, `unassigned_discretionary`
  (high); `missing_inclusion`, `early_inclusion` (medium); `significant_cash_flow_review` (low);
  plus `compliant` / `pending_inclusion` informational states.
- **Controls:** R3 HARD BOUNDARY — never change a composite, methodology, or reported performance,
  and never close/file/write a system of record; every exception `status: for_review`; versioned
  rules only; deterministic queue-priority mapping; standing disclaimer required.
- **Scripts:** `validate_input` (dataset schema, evaluability warnings), the membership-rule
  engine, and `validate_output` (evidence/rule-citation completeness, deterministic priority
  tie-out, prohibited membership/methodology/performance/closure language screen, `for_review`
  status + adjudication flag, disclaimer). Each carries a bundled-fixture `--selftest`.
- **Evaluations:** trigger/routing (incl. `portfolio-performance-attributor` and
  `investment-data-quality-reviewer` handoffs), golden Elevated queue, unknown-composite
  edge, deterministic script checks, and a no-action safety fixture that must fail closed
  (`evals/files/pack_with_action.json`), plus a prompt-injection and an authorization case.
- **Durable ids:** `review_id` (`camc-{firm_id}-{as_of}-0001`) and per-exception `case_ref`;
  idempotent for a fixed input set.

### Pending before release
- Domain SME (performance/GIPS policy) + control-owner blind review; confirm the authoritative
  versioned ruleset source, its owner, and the effective-date registry.
- Confirm exclusion-timing and significant-cash-flow policy parameters against the firm's GIPS
  composite policy for each jurisdiction pack.
- Wire read-only MCP integrations (composite policy, composite register, PMS book of record,
  cash flow, entity resolution) at deployment.
