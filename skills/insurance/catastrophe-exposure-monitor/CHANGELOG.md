# Changelog — catastrophe-exposure-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled,
read-only, alert-only catastrophe-exposure monitor.

- **Scope:** per-event zone accumulation, single-location, and event modeled-loss (low/mid/
  high) threshold breaches against versioned config, with source-freshness handling, data-gap
  surfacing, deduplication (new/ongoing/cleared), and a cited alert-queue package with a
  suggested response priority. Scheduled read-only; **no autonomous action**.
- **Metrics (deterministic):** zone accumulation (aggregate exposed limit + TIV),
  single-location limit, event tail modeled loss; each breach carries an `exceedance_ratio`
  and a deterministic severity band (Critical/Elevated/Watch/Informational → P1–P4). See
  `scripts/calculate_or_transform.py` and `references/domain-rules.md`.
- **Controls:** R2; `aws-fsi-scheduled-agent: read-only-monitoring`; hard boundary against
  binding/declining coverage, changing limits/capacity, buying/ceding reinsurance, booking/
  adjusting reserves, issuing/cancelling endorsements, and closing/suppressing alerts;
  versioned-config thresholds only; stale-feed `degraded` confidence; `external-delivery`
  approval before distribution or system-of-record write.
- **Scripts:** `validate_input` (snapshot schema; ungeocoded/unmodeled/stale-valuation
  warnings), accumulation/threshold engine, `validate_output` (freshness handling,
  deduplication + summary tie-out, escalation/queue packaging with deterministic severity/
  priority tie-out, no-autonomous-action screen, disclaimer). Each carries `--selftest`.
- **Evaluations:** trigger/routing, golden Critical run vs `exposure_snapshot.json`,
  stale-feed edge, deterministic script checks, no-autonomous-action safety on a
  non-compliant package, injection/closure-refusal, external-delivery authorization.
- **Handoffs:** downstream to `underwriting-workbench-assistant`, `submission-intake-triager`,
  `reinsurance-treaty-interpreter`, `reserving-analysis-assistant`, `claims-triage-assistant`;
  reinsurance/capacity purchasing routed to the cat-risk committee (human, no skill).

### Pending before release
- Domain SME (cat-risk / actuarial) + control-owner blind review; model-methodology review.
- Confirm the versioned threshold/appetite/staleness config source and its owner.
- Wire read-only MCP integrations (policy admin, event feed, cat model, reference/geocode,
  claims, config) and the scheduler cadence at deployment.
