# Domain Rules — complaint-resolution-assistant

Orientation references: fair-treatment / UDAAP-style conduct expectations, Reg-E error
resolution, Reg-Z fee/APR disclosure, and the firm's complaints-handling policy. The firm's
policy and its **versioned redress/standards/root-cause configuration** take precedence and
are versioned contracts. Assess each complaint against the terms **in force at the time of
the events**, not today's terms.

## Classification & severity (deterministic, documented)

Severity is computed from explainable inputs; the mapping is configuration, not judgment.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Category base (`category_severity`) | mis_selling / unauthorized_transaction / data_privacy 3; fees_charges / accessibility 2; service_delay 1 |
| Vulnerability indicator | +2 |
| Regulatory-reportable | +2 |
| Financial impact | ≥ 1000 +2; ≥ 250 +1 |

Bands: **P1 (Priority)** total ≥ 6; **P2 (Standard)** 3–5; **P3 (Routine)** ≤ 2. Severity is
a handling priority, not an outcome.

## Proposed remediation (the ONLY figures this skill produces)

Redress applies **only where `firm_error` is true** and each loss line is complete
(amount + `loss_date`); goodwill is a discretionary gesture that may appear even when not
upheld, but is capped.

| Component | Rule (default config) |
| --------- | --------------------- |
| Documented financial loss | Sum of `financial_loss_items[].amount` |
| Interest | Per item: `amount × rate × days(loss_date → resolution_date) / basis`; default rate 8% simple, basis 365 |
| Distress & inconvenience | Flat band from `di_bands`: none 0 / low 50 / moderate 150 / substantial 300 / severe 500 |
| Goodwill | `min(goodwill_requested, goodwill_cap)`; default cap 250 |
| **Total** | Sum of the above (ties out in `validate_output`) |

## Proposed outcome (recommendation only, never a decision)

| Condition | `proposed_outcome` |
| --------- | ------------------ |
| `firm_error` true, total redress ≥ `amount_claimed` (or no claim) | `uphold` |
| `firm_error` true, total redress < `amount_claimed` | `partial-uphold` |
| `firm_error` false | `not-upheld` |
| `firm_error` undetermined (null) | `needs-review` (no outcome proposed) |

## Hard boundaries (fail closed)

- No **sending/submitting**, **payment/refund/account change**, **closure**, or **regulatory
  filing**.
- No **binding uphold/reject decision** or **admission of legal liability**.
- No **guarantee/promise** of a specific result and no **legal/financial advice**.
- No **manufactured outcome**: unknown category → `needs-data`; undetermined error →
  `needs-review`.
- **Vulnerability** is a routing flag, never a diagnosis.

## Draft response package — required contents

Durable `complaint_id`; classification (category, severity band, root cause); cited
chronology; applicable standards (cited); proposed remediation breakdown + total; proposed
outcome (labeled DRAFT/pending); the DRAFT response letter with all required sections; the
recorded approvals block (handler review + final approver); routing notes; citations for
every item.
