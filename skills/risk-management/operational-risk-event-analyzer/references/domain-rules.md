# Domain Rules — operational-risk-event-analyzer

Deterministic classification, impact, severity, escalation, and remediation rules. Thresholds
and mappings are **configuration** (versioned, owned by Enterprise Risk Management), not
hard-coded judgments, and are never tuned per event. Orientation references: the Basel
operational-risk event-type and business-line taxonomy and the firm's operational-risk
management standard take precedence at deployment.

## Basel Level-1 event types (classification, position of record)

Internal Fraud · External Fraud · Employment Practices and Workplace Safety · Clients, Products
& Business Practices · Damage to Physical Assets · Business Disruption and System Failures ·
Execution, Delivery & Process Management.

**Business lines:** Corporate Finance · Trading & Sales · Retail Banking · Commercial Banking ·
Payment & Settlement · Agency Services · Asset Management · Retail Brokerage.

A `reported_event_type` / `reported_business_line` that is off-taxonomy is reported
`not_evaluable` — the skill never forces a category.

## Impact quantification (deterministic arithmetic)

| Quantity | Formula |
| -------- | ------- |
| Total recoveries | `sum(recoveries[].amount)` |
| Net loss | `max(gross_loss − total_recoveries, 0)` |
| Total impact | `net_loss + indirect_costs` |
| Banding amount | `potential_loss` if near-miss else `total_impact` |

For a near-miss, `gross_loss` is treated as 0 and the **potential loss** drives banding; if
`potential_loss` is absent, materiality is `not_evaluable`.

## Contributing cause → control theme → root cause

| Cause code | Control theme | Root-cause category |
| ---------- | ------------- | ------------------- |
| `PEOPLE-ERR` | Supervision & error prevention | People |
| `PEOPLE-SKILL` | Training & competency | People |
| `PEOPLE-CONDUCT` | Conduct & segregation of duties | People |
| `PROC-DESIGN` | Process & control design | Process |
| `PROC-BREAK` | Control execution & reconciliation | Process |
| `PROC-DOC` | Procedures & documentation | Process |
| `SYS-FAIL` | IT resilience & availability | Systems |
| `SYS-CONFIG` | Change management | Systems |
| `SYS-CAPACITY` | Capacity & performance management | Systems |
| `EXT-VENDOR` | Third-party / vendor oversight | External |
| `EXT-FRAUD` | Fraud prevention controls | External |
| `EXT-EVENT` | Business continuity & resilience | External |

The **primary root cause** is the most frequent category; ties break by the fixed order
Process → People → Systems → External so the result is reproducible. Each control finding cites
the contributing cause's `source_ref`.

## Escalation candidates (flags for human adjudication, never actions)

- **Regulatory-reporting candidate** when `banding_amount ≥ regulatory_reporting_threshold`
  (default 100,000), OR the event type is conduct-sensitive (Internal Fraud; Clients, Products &
  Business Practices) and `banding_amount ≥ sensitive_reporting_factor × threshold`
  (default 0.5).
- **Board-notifiable** when `banding_amount ≥ board_notify_threshold` (default 1,000,000), OR
  `customer_harm` is true and `affected_customers ≥ board_customer_threshold` (default 250).

Both are **candidates**: a human decides whether and how to report or notify. The skill never
files or notifies.

## Severity band (deterministic mapping)

| Band | Rule |
| ---- | ---- |
| **Critical** | `banding_amount ≥ critical_threshold` (default 1,000,000) OR board-notifiable |
| **High** | `banding_amount ≥ high_threshold` (default 250,000) OR regulatory-reporting candidate |
| **Moderate** | `banding_amount ≥ moderate_threshold` (default 25,000) |
| **Low** | otherwise |

When `banding_amount` is not evaluable (near-miss without potential loss), severity rests on the
escalators only: Critical if board-notifiable, else High if a reporting candidate, else Low.
Severity is **decision support for a human adjudicator**; it is not a risk determination and it
never triggers an escalation, filing, or register update.

## Remediation (recommendations only)

Each control theme maps to one recommended remediation action (see `REMEDIATION_MAP` in
`scripts/calculate_or_transform.py`), phrased as a recommendation ("Recommend …"). The skill
proposes remediation to track; it does not open, assign, approve, or close remediation items.

## Hard boundaries (fail closed)

- Never confirm/finalize a loss, **accept residual risk**, or make a "final determination".
- Never **close** the event/case, **file** a report, **post** a journal, or **update the risk
  register** — raise candidates and route to the human adjudicator.
- Never tune thresholds per event; use only the versioned config and record its version.
- Never assign individual blame or infer intent; describe control failures factually.
