# Adjacent-Skill Handoffs — financial-spreading-assistant

This skill produces a source-linked, reproducible **spread** (`spread_id`) — classified
statements, ratios, cash-flow proxy, an as-reported/normalized pair, and tie-outs — then stops.
It does not decide credit, draft the memo, test covenants, or write a system of record.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `credit-memo-drafter` | The analyst needs the credit write-up / memo built from the completed spread | `spread_id` + spread |
| `covenant-compliance-monitor` | The ratios must be tested against covenant thresholds | `spread_id` + ratios |
| `cashflow-forecaster` | The user wants a forward cash-flow projection, not a historical spread | history + statements |
| `loan-affordability-precheck` | A quick affordability / serviceability screen is wanted from the figures | `spread_id` + ratios |
| `credit-application-packager` | The spread is one artifact in a larger application package | `spread_id` |
| `loan-package-completeness-checker` | Confirm the credit file (including the spread) is complete | `spread_id` |

## Upstream (may call this skill)

`customer-onboarding-document-checker` or a document-intake step may deliver the borrower's
statements/tax returns; `bank-statement-analyzer` may summarize activity before a spread is built.
A scheduled agent is **not** used here (`aws-fsi-scheduled-agent: no`); the skill is interactive.

## Boundary with the credit decision

- This skill **spreads and calculates**; it never states the borrower is creditworthy, qualifies,
  or is approved/declined, and it never recommends or prices a facility. Those are underwriting
  activities that require a **human credit officer** (and the authorized decision system) — route
  to them with the `spread_id`.
- For **corporate-entity financials normalization outside a lending context**, use
  `financials-normalizer`; this skill is the lending/credit spread.

## Duplicate-execution prevention

- The skill classifies, spreads, and ties out **once** and emits a durable `spread_id`; downstream
  memo/covenant/packaging skills reuse that artifact rather than re-spreading.
- Ambiguous mappings are escalated here and resolved by a human before downstream use — downstream
  skills must not re-classify or override the flagged lines silently.
