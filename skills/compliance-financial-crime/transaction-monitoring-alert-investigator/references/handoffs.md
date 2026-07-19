# Adjacent-Skill Handoffs — transaction-monitoring-alert-investigator

This skill is a **scheduled, read-only, alert-only** monitor and R3 decision-support. It produces
a cited evidence bundle (`run_id`) with per-indicator `fingerprint`s, a chronology, and a
recommended disposition for each escalated subject — then stops. It does **not** disposition or
close a case, decide or file a SAR, clear an alert, or take any account/customer action. Those are
human FIU decisions, supported by the upstream and downstream skills below.

## Upstream (what escalates into this skill)

| Upstream skill | Hands off | Handoff artifact |
| -------------- | --------- | ---------------- |
| `aml-alert-triager` | First-line triage escalates a transaction-monitoring alert that needs substantive investigation | `alert_id` + triage evidence + risk rating |

This is also a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it may run
on its schedule over the queue of escalated alerts, or on demand for an FIU investigator against a
specific subject.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suspicious-activity-report-drafter` | The investigator decides the case warrants SAR consideration and needs a fact-based narrative + case package drafted for approval and authorized filing | `run_id` + subject evidence bundle + chronology |
| `sanctions-match-adjudicator` | An indicator turns on a potential sanctions match on the subject or a counterparty that needs adjudication | subject/counterparty + screening context |
| `kyc-customer-due-diligence-screener` | The activity reveals a KYC/CDD gap, stale profile, or beneficial-ownership question that must be refreshed | `subject_id` + identified gap |
| `adverse-media-investigator` | A party needs credible adverse-media assessment to weigh relevance and source quality | subject/counterparty identity |
| `payment-fraud-case-investigator` | The pattern is better explained as payment fraud (device/identity/beneficiary) than AML typology | `alert_id` + transaction scope |

Disposition itself — closing the case, deciding and filing a SAR, clearing the alert, or taking an
account/customer action — is performed by the **FIU investigator and their authorized reviewers**
through their entitled systems, never by this monitor.

## Duplicate-execution prevention

- The monitor computes and evidences **indicators and a recommended disposition only**; it must
  not reach a disposition, close a case, decide/file a SAR, or take an account action — those
  belong to the human reviewer and the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_cases`) prevents the same persistent pattern
  on an already-open case from being re-raised every scheduled run; still-open items remain
  visible as open rather than being silently cleared.
- Downstream skills consume the `run_id` / evidence bundle rather than re-deriving thresholds or
  re-screening the whole transaction history.

## Human / operations handoffs (no catalog skill)

- **Scenario / threshold changes** to the versioned typology library are owned by the
  financial-crime tuning and model-risk functions (an operations/model-governance change), not by
  this monitor; report the gap and route to that team rather than adjusting a threshold.
- **Law-enforcement or regulator contact**, and any customer-facing action, are handled by
  authorized compliance officers under legal supervision.
