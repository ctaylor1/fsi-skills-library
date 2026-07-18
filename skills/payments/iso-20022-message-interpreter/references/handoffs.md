# Adjacent-Skill Handoffs — iso-20022-message-interpreter

This skill **interprets and explains** a single ISO 20022 message (or a linked
status/response) and stops. It does not trace a payment end-to-end, build a case, decide a
disposition, or repair/resubmit anything. It hands off by returning its cited
interpretation object (message classification, tie-outs, findings, and per-transaction
citations) keyed by the message identifiers (`MsgId`, `EndToEndId`, `UETR`).

## Downstream (this skill routes to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `payment-failure-diagnoser` | The user wants to know **why a payment failed or is delayed across the whole chain** (initiation → authorization → routing → messaging → screening → clearing → settlement), not just what one message says | Interpretation object + message identifiers |
| `payment-exception-investigator` | A genuine **exception/investigation case** is needed — chronology of parties and statuses, camt.056/029 cancellation-investigation flow (R3, casework) | Interpretation object + identifiers as case evidence |
| `payment-repair-assistant` | A rejected/held payment must be **corrected, validated, approved, and resubmitted** (R4, approval-gated action) | Interpretation object as input evidence only — this skill never repairs |

## Upstream (may call this skill)

`payment-failure-diagnoser` and `payment-exception-investigator` may call this skill to get
an authoritative, cited interpretation of a specific message (field semantics, status/reason
decoding, truncation detection) rather than re-parsing the message themselves.

## Human / specialist handoffs (no catalog skill applies)

- **Sanctions / AML / fraud determination** — a `FRAD` reason, a screening hit, or a
  suspected-fraud pattern is *explained* here and routed to the sanctions/AML/fraud
  operations function and its regulated skills; this skill never adjudicates.
- **Scheme / correspondent dispute or clarification** requiring contact with another bank →
  payments operations / correspondent-banking specialist (external delivery needs approval).
- **Legal or regulatory interpretation** of a message's obligations → licensed specialist.

## Related but distinct (do not absorb)

- Summarizing an already-settled **settlement report** is `settlement-report-summarizer`.
- Reconciling settlement or transaction **records across sources** is
  `settlement-break-reconciler` / `transaction-reconciliation-helper`.

## Duplicate-execution prevention

- This skill **only interprets/explains**; it must not perform end-to-end tracing, casework,
  disposition, or repair — those belong to the skills above.
- Downstream skills must **reuse** this skill's interpretation (keyed by message identifiers)
  rather than re-deriving field semantics and status meanings.
- A rejection or a control-total break is **surfaced and routed**, never resolved here.
