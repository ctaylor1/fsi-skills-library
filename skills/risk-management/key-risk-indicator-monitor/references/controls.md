# Controls — key-risk-indicator-monitor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Scheduled
  read-only; alert only.
- **Scheduled agent:** `read-only-monitoring` — runs on a schedule, reads sources, and raises
  alerts / queue items with cited evidence and escalation commentary. It **never acts, decides,
  closes, or writes.**
- **Human approval:** `required` — mandatory human adjudication before **any** regulated risk
  decision or system-of-record change. The scheduled read and the internal alert queue are the
  monitor's only outputs; every disposition is a human risk decision.

## R3 decision-support boundary

This monitor produces **recommendations and evidence only**, for a human risk manager or
control officer to adjudicate. It must never make or communicate an autonomous regulated
decision. Specifically, the following are **human** actions the monitor may package evidence
for but must never take, recommend, or describe as done:

- accepting a risk, or asserting that a risk has been accepted or is within appetite by
  decision;
- granting, extending, tracking, or drafting a breach **waiver** or exception;
- changing, raising, lowering, or overriding a **limit, threshold, or risk appetite**;
- changing, downgrading, or posting a **risk rating** or **control rating**;
- declaring an **appetite breach** to the board/committee as a determination;
- opening, closing, suppressing, snoozing, or downgrading an **alert, incident, or case**;
- filing or submitting any **regulatory report** or notifying a supervisor;
- writing back to the KRI/risk register, the incident store, or any book of record.

## Scheduled read-only, alert-only posture (archetype control)

This monitor may **evaluate thresholds, detect trends, test seasonality, check data quality
and freshness, deduplicate, and queue** with escalation commentary. It may **never** act,
decide, or close (see the list above). Every scheduled run is idempotent for a given
`(run_id, config_version, as_of, observations)`: re-running reproduces the same alerts,
severities, and fingerprints. The agent assumes no automatic retries and no step-up
authorization.

## Prohibited (fail closed)

- No **risk determination** (e.g., "this is an appetite breach" as a decision, or "the control
  has failed"); describe the measured value vs the threshold factually.
- No **remediation instruction** — no specific limit, waiver, control change, or action to fix
  a breach (that is a risk-governance decision).
- No **threshold invention, re-interpretation, or per-metric tuning**; only the versioned KRI
  library is authoritative. If a band or direction is missing or ambiguous, report the gap —
  never guess a threshold.
- No **suppression of stale or missing data** — a stale observation is flagged, not dropped or
  presented as current; a missing value raises a data-quality alert, not a PASS.
- No **autonomous alert/incident closure or de-duplication into silence** beyond the
  deterministic fingerprint logic (still-open items remain visible as open).

## Required output screens (`scripts/validate_output.py`)

- Every alert is well-formed: identity, ≥1 cited evidence row, `status` in {WARN, BREACH}, a
  `severity`, and a routing `queue`; threshold and seasonal alerts carry `measured` and
  `threshold`.
- `severity` ties out to the deterministic `(breach_type, status, critical)` mapping and
  `queue` ties out to `severity`.
- Deduplication integrity: `new_alerts` and `still_open` partition alerts by fingerprint;
  duplicates route to still-open and are not re-raised as new.
- Freshness handling: every stale KRI has a freshness alert and its alerts are flagged
  `stale_input` — stale observations are never silently treated as current.
- **No autonomous-action / decision language** (regex screen: "accepted the risk", "granted a
  waiver", "raised the limit", "risk rating was downgraded", "auto-closed", "closed the
  incident", "filed the report", "wrote to the register", etc.).
- Standing disclaimer present: "Monitoring alert only; no risk acceptance, breach waiver, limit
  or appetite change, risk- or control-rating change, incident or case closure, regulatory
  filing, or system-of-record change has been made or recommended. KRI exceptions require human
  risk review and adjudication."
- Escalation packaging ties out: escalation counts sum to the alert count.

## Data classification, privacy, records

- **Confidential.** KRI values, loss/incident linkage, and control ratings are confidential
  business information; minimize the pack to what evidences each alert.
- Retain each run's alerts + citations + `config_version` per records policy; log the read, the
  queue emission, and any human adjudication recorded downstream.
- Never exfiltrate register or loss data; route alerts only to approved risk review queues.

## Reproducibility

`run_id` binds the pack to the exact inputs, observation `as_of`, and **threshold config
version**; re-running with the same inputs and config reproduces the alerts, severities, and
fingerprints. Freshness, precision/recall, threshold behavior, deduplication, escalation
latency, and the no-autonomous-action posture are the primary validation targets for this
archetype.
