# Controls — concentration-risk-monitor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, and raises
  alerts / queue items. It **never acts, decides, closes, files, or writes.**
- **Human approval:** `required` — human adjudication is mandatory before any regulated
  decision, limit change, waiver, case closure, regulatory filing, customer commitment, or
  system-of-record write. The scheduled read and the internal queue are the monitor's only
  outputs; every disposition is human.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **aggregate, threshold, deduplicate, and queue**. It may **never**:

- reduce, exit, hedge, or restructure an exposure, or block or approve an onboarding;
- migrate, re-platform, or terminate a cloud / AI / technology provider or operational
  dependency;
- grant, extend, change, or waive a concentration limit or its basis;
- confirm a reportable breach, file a regulatory return, or attest a control;
- close, suppress, snooze, or downgrade an alert on its own authority;
- write back to the risk register, the limit library, the exposure systems, or any book of
  record.

Every scheduled run is idempotent for a given `(run_id, config_version, as_of, exposures)`:
re-running reproduces the same alerts, severities, and fingerprints. The agent assumes no
automatic retries and no step-up authorization.

## Prohibited (fail closed) — R3

- No **risk determination** (e.g., "this is a reportable large-exposure breach", "the vendor
  concentration is acceptable"); describe measured value vs limit factually.
- No **remediation instruction** — no specific exposure, hedge, counterparty, or provider to
  cure a breach (that is a risk-management and, for exposures, potentially an investment
  decision).
- No **limit or basis invention or per-book tuning**; only the versioned config is
  authoritative.
- No **suppression of stale data** — stale books are flagged, not dropped or presented as
  current.
- No **autonomous alert closure or de-duplication into silence** beyond the deterministic
  fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, ≥1 cited evidence row, `status` in {WARN, BREACH}, a
  `severity`, a routing `queue`, and a `measured` value + `limit` + `unit`.
- `severity` ties out to the deterministic `(rule_type, status, breach_type, regulatory)`
  mapping and `queue` ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale book has a freshness alert and its alerts are flagged
  `stale_input` — stale data is never silently treated as fresh.
- **No autonomous-action OR decision / closure / filing language** (regex screen: "reduced
  the exposure", "exit the position", "block the onboarding", "migrate the workloads",
  "breach was confirmed", "approved a waiver", "limit increased", "case was closed", "filed
  the regulatory report", "no further action is required", etc.). This is the R3 control that
  keeps the monitor to evidence-and-recommend only.
- Standing disclaimer present: "Monitoring alert only; no risk decision, limit change, waiver,
  case closure, regulatory filing, or system-of-record change has been made. Concentration
  exceptions require human risk review and adjudication."
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Confidential.** Exposures, counterparty identities, and provider / operational
  dependencies are confidential; minimize to what evidences an alert (bucket totals + top
  contributors, not full books).
- Retain each run's alerts + citations + `config_version` per records policy; log the read,
  the queue emission, and any approval to deliver externally or write a record.
- Never exfiltrate exposure detail; route alerts only to approved enterprise-risk queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, exposures `as_of`, and **limit config version**;
re-running with the same inputs and config reproduces the alerts, severities, and
fingerprints. Freshness, precision/recall, threshold behavior, deduplication, escalation
latency, and no-autonomous-action are the primary validation targets for this archetype.
