# Controls — covenant-compliance-monitor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, and raises
  alerts / queue items with an audit-ready evidence trail. It **never acts, decides, closes,
  or writes.**
- **Human approval:** `required` — mandatory human adjudication before **any** regulated
  covenant action or system-of-record change. The scheduled read and the internal alert queue
  are the monitor's only outputs; every disposition is a human credit decision.

## R3 decision-support boundary

This monitor produces **recommendations and evidence only**, for a human credit officer to
adjudicate. It must never make or communicate an autonomous regulated decision. Specifically,
the following are **human** actions the monitor may package evidence for but must never take,
recommend, or describe as done:

- declaring an event of default, or asserting that one has occurred;
- accelerating, calling, or restructuring a facility; charging off a loan;
- granting, recommending, extending, or drafting a covenant **waiver** or **amendment**;
- issuing or sending a reservation-of-rights or default notice to the borrower;
- changing, downgrading, or posting a **risk rating**;
- closing, suppressing, snoozing, or downgrading an alert on its own authority;
- writing back to the covenant library, the servicing system, or any book of record.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **compute covenant tests, reconcile certificates, threshold, deduplicate,
track headroom/trend, and queue**. It may **never** act, decide, or close (see the list
above). Every scheduled run is idempotent for a given
`(run_id, config_version, as_of, spreads)`: re-running reproduces the same alerts,
severities, and fingerprints. The agent assumes no automatic retries and no step-up
authorization.

## Prohibited (fail closed)

- No **credit determination** (e.g., "this is a wilful default" or "the borrower is
  impaired"); describe the measured value vs the covenant threshold factually.
- No **remediation instruction** — no specific waiver terms, amendment language, cure, or
  capital/repayment action to fix a breach (that is a credit and legal decision).
- No **covenant invention, re-interpretation, or per-borrower tuning**; only the versioned
  covenant library is authoritative. If a definition or threshold is missing or ambiguous,
  report the gap — never guess a mechanic or threshold.
- No **suppression of stale data** — a stale spread is flagged, not dropped or presented as
  current.
- No **autonomous alert closure or de-duplication into silence** beyond the deterministic
  fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, ≥1 cited evidence row, `status` in {WARN, BREACH}, a
  `severity`, and a routing `queue`; financial and negative-covenant alerts carry `measured`
  and `threshold`.
- `severity` ties out to the deterministic `(covenant_type, status, breach_type)` mapping and
  `queue` ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale facility has a freshness alert and its alerts are flagged
  `stale_input` — stale spreads are never silently treated as current.
- **No autonomous-action / decision language** (regex screen: "declared an event of default",
  "accelerated the facility", "waiver was granted", "amended the agreement", "reservation of
  rights", "risk rating was downgraded", "notice was sent", "auto-closed", "closed the
  exception", "cured the breach", etc.).
- Standing disclaimer present: "Monitoring alert only; no covenant waiver, amendment,
  reservation of rights, default declaration, risk-rating change, borrower notice, or
  system-of-record change has been made or recommended. Covenant exceptions require human
  credit review and adjudication."
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Borrower financials, spreads, and certificates
  are confidential; minimize the pack to what evidences each alert.
- Retain each run's alerts + citations + `config_version` per records policy; log the read,
  the queue emission, and any human adjudication decision recorded downstream.
- Never exfiltrate borrower financials or covenant positions; route alerts only to approved
  credit review queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, spread `as_of`, and **covenant config version**;
re-running with the same inputs and config reproduces the alerts, severities, and
fingerprints. Clause/formula extraction fidelity, certificate reconciliation, calculation
accuracy, data freshness, threshold behavior, breach precision/recall, and the audit trail
are the primary validation targets for this archetype.
