# Domain Rules — cyber-incident-response-coordinator

How the coordinator normalizes an incident record and derives a **suggested** severity band
and **notification reminders**. Thresholds and role lists are configuration (versioned, owned
by the CISO / operational-resilience function), not hard-coded judgments. Orientation
references: NIST SP 800-61 incident-handling lifecycle, the firm's IR standard, and — where the
incident touches critical services — the applicable operational-resilience regime
(e.g., DORA, FCA/PRA operational resilience). The firm's standard takes precedence.

## Coordination record sections

| Section | What the coordinator maintains |
| ------- | ------------------------------ |
| **Chronology** | Time-ordered, source-linked entries by phase (detection, triage, declaration, containment, eradication, recovery, communication, decision). |
| **Roles** | Coverage of mandatory IR roles vs. those unfilled (a coordination gap, not a decision). |
| **Tasks** | Containment/eradication/recovery/evidence actions with owner, status, due; open and **overdue** are surfaced. |
| **Evidence** | Register with source_ref, hash, and custody; chain-of-custody completeness is flagged. |
| **Decisions** | Decision log with the human **adjudicator**, a recommendation, and status; pending vs. human-adjudicated. |
| **Communications** | Stakeholder updates with audience, channel, approver, source. |
| **Dependencies** | Affected services, criticality, impact tolerance, upstream dependencies. |
| **Notification reminders** | Deterministic reminders that clocks/obligations MAY apply, routed to named humans. |
| **Post-incident actions** | Proposed lessons-learned / remediation items (proposals only). |

## Suggested severity band (deterministic, documented)

Computed from the `impact` block against the versioned `major_breach_records` threshold. It is
a **triage suggestion for the incident commander**, never a binding classification.

| Band | Rule (first match wins) |
| ---- | ----------------------- |
| **SEV1 (Critical)** | `impact_tolerance_breached`, OR `scope == enterprise`, OR (`confirmed_data_exposure` AND `regulated_data` AND `records_exposed >= major_breach_records`). |
| **SEV2 (High)** | `critical_service_affected`, OR `confirmed_data_exposure`, OR `scope == multi-system`. |
| **SEV3 (Moderate)** | `records_exposed > 0`, OR `suspected_compromise`, OR `scope == single-system`. |
| **SEV4 (Low)** | No material impact flags set. |

The pack records the basis (which conditions fired). The incident commander confirms or
overrides; the coordinator never sets an official severity.

## Notification reminders (reminders, not determinations)

| Trigger | Reminder routed to | Never |
| ------- | ------------------ | ----- |
| Confirmed regulated/customer-data exposure | Legal/privacy counsel (human) + `operational-resilience-reporter` for drafting | Determine that notification IS/IS NOT required; file anything |
| Impact tolerance breached | Operational-resilience owner (human) + `operational-resilience-reporter` | Decide the regulatory-reporting question; submit a report |
| Critical service affected | Business-continuity owner + comms lead (human) | Send a customer/stakeholder communication |

Every reminder states obligations **MAY** apply and names the human/skill that owns the actual
decision and any filing.

## Hard boundaries (fail closed)

- Never **make or state a regulated decision**: official severity, notification-required
  finding, root-cause attribution as fact, or any customer/regulator commitment.
- Never **close, resolve-final, or file**: the record stays `open` / `in-coordination`; closure
  and any regulatory/breach/SAR filing are human/authorized-system actions.
- Never mark a decision **adjudicated** unless a human `decided_by` is recorded; the coordinator
  only proposes recommendations.
- Never **take or stage a response action** (revoke, isolate, block, patch, restore) — those are
  the technical team's actions via their own entitled tools; the coordinator tracks them.
- Never present threat-intel attribution or root cause as established fact.

## Reproducibility

`coordination_id` binds the pack to the exact inputs, `as_of`, and **config version**; re-running
with the same inputs and config reproduces the chronology ordering, task/overdue computation,
suggested severity, and reminders.
