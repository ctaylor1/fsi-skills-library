# Controls — real-time-payment-risk-monitor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, and raises
  alerts / queue items. It **never acts, decides, files, closes, or writes.**
- **Human approval:** `required` — human adjudication is required before any regulated
  decision or action (fraud/AML/mule/sanctions determination, account block/freeze, payment
  hold/release/return/reversal/repair, SAR/regulatory filing, case closure, or system-of-record
  write). The scheduled read and the internal alert queue are the monitor's only outputs.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **enrich, threshold, deduplicate, and queue**. It may **never**:

- block, hold, release, return, reverse, cancel, recall, or repair a payment or transfer;
- block, freeze, suspend, or close an account;
- make or communicate a fraud, AML, mule, or sanctions **determination** (a watchlist hit is a
  candidate for adjudication, not a confirmed match);
- file a SAR / CTR or any regulatory report, or report a customer to an authority;
- close, suppress, snooze, or downgrade an alert or case on its own authority;
- write back to the gateway/processor, fraud platform, settlement, ledger, watchlists, or any
  book of record.

Every scheduled run is idempotent for a given `(run_id, config_version, as_of, flow)`:
re-running reproduces the same alerts, severities, and fingerprints. The agent assumes no
automatic retries and no step-up authorization.

## Prohibited (fail closed)

- No **regulated decision** (fraud/AML/sanctions finding, account decision) or statement that
  one was taken; describe measured value vs limit and cited watchlist membership factually.
- No **action instruction stated as performed** — no "we blocked/held/reversed/filed/closed".
  A recommendation to a human to review is permitted; asserting the monitor acted is not.
- No **limit invention or per-account tuning**; only the versioned config is authoritative.
- No **suppression of stale data** — stale feeds are flagged, not dropped or presented as
  current.
- No **autonomous alert/case closure or de-duplication into silence** beyond the deterministic
  fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, ≥1 cited evidence row, `status` in {WARN, BREACH}, a
  `severity`, and a routing `queue`; measured rule types carry `measured_value` and `limit`.
- `severity` ties out to the deterministic `(rule_type, status, breach_type)` mapping and
  `queue` ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale entity has a freshness alert and its alerts are flagged
  `stale_input` — stale flow is never silently treated as fresh.
- **No autonomous-action / decision / filing / closure language** (regex screen: "blocked the
  account", "reversed the payment", "held the payment", "confirmed fraud", "filed a SAR",
  "closed the alert/case", "auto-closed", "override the limit", etc.). This is the R3
  fail-closed screen: decision/closure/filing language forces exit 1.
- Standing disclaimer present (alert-only, human-adjudication statement).
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Minimize to what evidences an
  alert; never embed full PANs or unnecessary personal data in the pack.
- Retain each run's alerts + citations + `config_version` per records policy; log the read, the
  queue emission, and any human adjudication.
- Never exfiltrate flows, counterparties, or watchlist contents; route alerts only to approved
  payments-risk queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, feed `as_of`, and **rule config version**;
re-running with the same inputs and config reproduces the alerts, severities, and fingerprints.
Freshness, precision/recall, threshold behavior, deduplication, escalation latency, and the
no-autonomous-action screen are the primary validation targets for this archetype.
