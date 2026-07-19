# Controls — transaction-monitoring-alert-investigator

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule (or on demand for a reviewer),
  reads sources, and raises indicators / evidence bundles / queue items. It **never acts,
  decides, closes, files, or writes.**
- **Human approval:** `required` — human FIU adjudication is mandatory before any regulated
  outcome: an alert disposition, a case closure, a SAR filing decision, a customer/account
  action, or any system-of-record change. The scheduled read and the internal queue are the
  monitor's only outputs.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **resolve entities, threshold typologies, build a chronology, deduplicate, and
queue** an evidence bundle with a recommended disposition. It may **never**:

- close, clear, disposition, snooze, or downgrade an alert or case on its own authority;
- decide, draft-to-file, or file a suspicious activity report, or communicate one to FinCEN;
- make or state an AML determination ("this is money laundering", "not suspicious");
- freeze, block, close, exit, or offboard an account or customer;
- write back to the case system, KYC store, transaction system, or any book of record.

Every scheduled run is idempotent for a given `(run_id, config_version, as_of, subject data)`:
re-running reproduces the same indicators, severities, recommendations, and fingerprints. The
agent assumes no automatic retries and no step-up authorization.

## R3 decision-support boundary (fail closed)

- A **recommended disposition** is a triage suggestion for a human adjudicator, drawn from a
  closed **recommend-only** vocabulary (`recommend_escalate`, `recommend_further_review`,
  `recommend_monitor`). It is never a closure, a clearance, or a filing decision.
- No **threshold invention or per-subject tuning**; only the versioned scenario config is
  authoritative. Report a missing/ambiguous threshold rather than guessing.
- No **suppression of stale data** — stale subjects are flagged, not dropped or presented as
  current.
- No **determination of intent or suspicion** — describe measured value vs threshold factually.
- **Tipping-off / SAR confidentiality:** never expose SAR existence or investigative content to
  the customer or unauthorized parties; route only to entitled FIU queues.

## Required output screens (`scripts/validate_output.py`)

- Every indicator is well-formed: identity, ≥1 cited evidence row, `status` in {WARN, BREACH}, a
  `severity`, and a routing `queue`; threshold indicators carry `measured` and `threshold`.
- `severity` ties out to the deterministic `(rule_type, status)` mapping and `queue` ties out to
  `severity` (typology application; no ad-hoc escalation).
- Deduplication integrity: `new_alerts` and `still_open` partition indicators by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale subject has a freshness indicator and its indicators are
  flagged `stale_input` — stale data is never silently treated as current.
- Chronology integrity: each subject's `chronology` is in non-decreasing date order.
- Disposition consistency: each `recommended_disposition` is in the recommend-only vocabulary and
  ties out to the deterministic mapping from its indicator counts.
- **No autonomous decision / closure / filing language** (regex screen: "case was closed",
  "auto-closed", "SAR was filed", "filed with FinCEN", "determined not suspicious", "no further
  action taken", "froze the account", etc.).
- Standing disclaimer present.
- Escalation packaging ties out: escalation counts sum to the indicator count.

Fail closed on any miss.

## Data classification, privacy, records

- **Restricted (AML/BSA — SAR confidentiality; tipping-off controls).** Customer, transaction,
  and counterparty data is highly sensitive; minimize to what evidences an indicator.
- Retain each run's indicators + evidence bundle + citations + `config_version` per BSA
  records-retention policy; log the read, the queue emission, and any required-approval handoff.
- Never exfiltrate customer or transaction data; route indicators only to approved FIU queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, subject data `as_of`, and **scenario config
version**; re-running with the same inputs and config reproduces the indicators, severities,
recommendations, and fingerprints. Freshness, precision/recall of typology hits, deduplication,
disposition consistency, and escalation latency are the primary validation targets for this
archetype.
