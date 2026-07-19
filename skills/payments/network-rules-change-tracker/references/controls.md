# Controls - network-rules-change-tracker

- **Risk tier:** R3 - regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` - runs on a schedule, reads sources, and raises
  alerts / queue items. It **never acts, decides, closes, files, or writes.**
- **Human approval:** `required` - required before any regulated decision, filing, attestation,
  network/customer commitment, case closure, control attestation, or system-of-record change, and
  before an alert pack is delivered outside the payments compliance / product / operations
  function. The scheduled read and the internal queue are the monitor's only outputs;
  adjudication and implementation are human.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **enrich, threshold, deduplicate, and queue**. It may **never**:

- adopt a network rule, or accept, close, file, or attest an obligation;
- change, add, or remove a product, procedure, control, contract, or system;
- mark a change implemented / compliant / done, or set an implementation status;
- grant, extend, or waive a deadline, obligation, or requirement;
- close, suppress, snooze, or downgrade an alert on its own authority;
- write back to the bulletin feed, the taxonomy, the inventories, the tracker, or any book of
  record.

Every scheduled run is idempotent for a given `(run_id, config_version, as_of, bulletins,
inventories)`: re-running reproduces the same alerts, severities, and fingerprints. The agent
assumes no automatic retries and no step-up authorization.

## Prohibited (fail closed)

- No **regulated / compliance determination** (e.g., "we are compliant", "this obligation does
  not apply"); describe measured value vs band / mapping factually and leave adjudication to a
  human.
- No **implementation instruction** - no specific procedure edit, control change, contract
  amendment, or system change to satisfy an obligation (that is a product/ops decision).
- No **band or lead-time invention or per-bulletin tuning**; only the versioned config is
  authoritative. If a band, network, or owner is missing/ambiguous, report the gap.
- No **suppression of stale or unauthenticated inputs** - a stale feed is flagged
  (`stale_input`), an unauthenticated bulletin is flagged (`unverified_source`); neither is
  dropped or presented as current/in-force.
- No **autonomous alert closure or de-duplication into silence** beyond the deterministic
  fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, >=1 cited evidence row, `status` in {WARN, BREACH}, a
  `severity`, and a routing `queue`; readiness alerts carry `days_to_effective` +
  `effective_date`; authenticity alerts carry a `reason`.
- `severity` ties out to the deterministic `(category, status, breach_type)` mapping and `queue`
  ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: a stale feed has a freshness alert and every derived alert is flagged
  `stale_input`.
- Authenticity handling: every alert from an `unauthentic_bulletins` entry is flagged
  `unverified_source`.
- **No autonomous-action / decision / closure / filing language** (regex screen: "auto-closed",
  "closed the obligation", "filed the attestation", "attested", "approved the change", "granted a
  waiver", "marked implemented", "updated the control/procedure/contract/system", "no reviewer
  action is required", etc.).
- Standing disclaimer present (see SKILL.md Output contract).
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Inventories can reference
  customer-data and cardholder-data systems; bulletins are publisher-confidential. Minimize to
  what evidences an alert; never embed cardholder data in the pack.
- Retain each run's alerts + citations + `config_version` per records policy; log the read, the
  queue emission, and any required approval.
- Never redistribute a bulletin or inventory outside entitled payments reviewers; route alerts
  only to approved payments queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, `feed_as_of`, and **taxonomy config version**;
re-running with the same inputs and config reproduces the alerts, severities, and fingerprints.
Freshness, authenticity precision, mapping completeness, deduplication, and escalation latency are
the primary validation targets for this archetype.
