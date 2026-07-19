# Changelog - network-rules-change-tracker

## [0.1.0] - 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled, read-only,
alert-only monitor for card-network and payment-scheme rule changes.

- **Scope:** ingest card-network / payment-scheme bulletins; check authenticity and version;
  extract obligations and effective dates; map obligations to products, procedures, controls,
  contracts, systems, and owners; score implementation readiness against effective dates;
  deduplicate against open items; check feed freshness; queue severity-ranked exceptions.
  Read-only; **no autonomous action, decision, closure, filing, or implementation**.
- **Check engine (deterministic):** `authenticity` (untrusted publisher / unverified signature /
  missing version-source), `mapping` completeness (`unmapped_domain`) and applicability
  (`dangling_reference`), `ownership` (`no_owner` / `unknown_owner`), and `readiness`
  (`overdue` / `critical` / `high` / `medium` days-to-effective bands) - each explainable,
  evidenced, and reproducible (see `scripts/calculate_or_transform.py`). Unauthenticated
  bulletins flag derived alerts `unverified_source`; a stale feed flags `stale_input`.
- **Controls:** R3; scheduled `read-only-monitoring`, alert-only posture; hard boundary against
  adopting rules, accepting/closing/filing/attesting obligations, changing
  procedures/controls/contracts/systems, marking changes done, granting waivers, and
  closing/suppressing alerts; versioned-config bands/networks/owners only; `required` human
  approval before any decision, filing, delivery, or system-of-record change.
- **Scripts:** `validate_input` (run/bulletin/obligation schema, mapping/owner/authenticity/
  freshness/dedup warnings), the check engine, and `validate_output` (alert well-formedness,
  deterministic severity/queue tie-out, readiness/authenticity payloads, deduplication integrity,
  freshness + unverified-source handling, no-autonomous-action/decision/closure/filing screen,
  disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-bulletin change run (authenticity failure,
  mapping completeness + dangling reference, missing/unknown owner, overdue/critical/high/medium
  readiness, deduplication, and a fully-clean bulletin), deterministic script checks, a
  no-autonomous-action safety fixture (`expect_exit 1`) plus an injection case, a no-open-baseline
  edge, and required-approval authorization.
- **Handoffs:** downstream to `regulatory-change-impact-analyzer`, `policy-procedure-gap-analyzer`,
  `contract-obligation-extractor`, `audit-evidence-packager`, and
  `regulatory-exam-response-packager`; adjudication and implementation remain human.

### Pending before release
- Domain SME (payments compliance / product / operations) + control-owner blind review.
- Confirm the versioned rule/change taxonomy source, its owner, and the `config_version` contract
  (trusted networks, readiness bands, lead times).
- Wire read-only MCP integrations (bulletin feed, taxonomy, inventories, owner registry,
  implementation tracker, prior-alert store) at deployment.
- Calibrate `readiness_bands`, `min_lead_days`, and `max_feed_staleness_days` per network with
  payments operations and risk.
