# Domain Rules — dispute-operations-assistant

Orientation references: Visa and Mastercard dispute/chargeback rules and dispute-resolution
frameworks (e.g., Visa Claims Resolution, Mastercard dispute reason codes), and — for the
issuer's consumer-facing obligations — Regulation E (EFTA, debit/prepaid error resolution)
and Regulation Z (TILA, credit-card billing-error/chargeback rights). **The current network
rulebook and the firm's dispute procedures take precedence and are versioned contracts.** The
reason codes, windows, and evidence sets below are **illustrative defaults**; a deployment
loads the current catalog from `network-rules-change-tracker`.

## Reason-code registry (versioned; overridable via `rule_registry`)

A reason code is keyed `network:code`. Each maps to a category, a response window (days), and
required-evidence **groups** — a group is satisfied if ANY listed evidence type is present.

| Reason code | Title | Category | Window | Required-evidence groups |
| ----------- | ----- | -------- | ------ | ------------------------ |
| `visa:10.4` | Fraud - Card-Absent | fraud | 30d | auth_record; (avs/cvv/3ds); (prior_undisputed_history / transaction_receipt) |
| `visa:13.1` | Merchandise/Services Not Received | consumer | 30d | (proof_of_delivery/proof_of_service); order_confirmation; terms_of_service |
| `visa:13.3` | Not as Described / Defective | consumer | 30d | item_description_evidence; terms_of_service; proof_no_valid_return |
| `mastercard:4853` | Cardholder Dispute | consumer | 45d | (proof_of_delivery/proof_of_service); order_confirmation; terms_of_service |
| `mastercard:4837` | No Cardholder Authorization | fraud | 45d | auth_record; (avs/cvv/3ds); prior_undisputed_history |

An unknown `network:code` is **needs-data** — never guess the window or evidence set.

## Deadline computation (deterministic)

`response_deadline = dispute_received_date + window_days` (or a per-case
`response_window_days` override). `days_remaining = response_deadline − processing_date`.

| days_remaining | status |
| -------------- | ------ |
| `< 0` | `out-of-time` → **out-of-time-review** (human decides; never auto-accept liability) |
| `0 … 5` | `at-risk` → still draftable, flagged `deadline-at-risk` |
| `> 5` | `on-time` |

## Disposition order (first match wins — decision-support only)

1. **needs-data** — role/identity incomplete, or unknown reason code.
2. **route-specialist** — fraud investigation, merchant-side representment, or ISO 20022
   exception (out of scope; route out).
3. **rule-version-stale** — cited rule version ≠ current effective version (refresh first).
4. **out-of-time-review** — response window elapsed.
5. **evidence-insufficient** — a required-evidence group is missing.
6. **draft-ready-for-review** — all gates hold; assemble a draft case response.

## Hard boundaries (fail closed)

- No **dispute decision**: never accept/deny a chargeback, decide liability, or find fraud.
- No **credit / funds movement**: never issue provisional or final credit, refund, or
  write-off, and never post to a ledger or system of record.
- No **submission / filing / closure**: never submit or file a response to the network,
  acquirer, or issuer, and never close a case. Drafting only; a human authorizes and submits.
- No **outcome guarantees** and no **unsupported claims** — every drafted statement cites a
  bundled exhibit; no predicted result.
- No **personalized legal/financial advice** to a cardholder or merchant.

## Recommendation vocabulary (structured, not a decision)

`represent-defend`, `gather-evidence`, `refresh-rule-version`, `human-review-required`,
`route-to-fraud-investigation`, `route-to-merchant-representment`, `route-to-payment-exception`.
Each is a recommendation for the human adjudicator, never an executed action.

## Draft case-response package — required contents

Durable `case_id`; role + network + reason code (with title/category); transaction identity
(masked card, auth id); computed deadline + status; evidence inventory vs. required groups;
an exhibit-cited draft narrative; a structured recommendation; and the human review &
authorization block (`authorization_status: pending-human-authorization`). See
[../assets/output-template.md](../assets/output-template.md).
