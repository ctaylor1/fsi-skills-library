# Source Map — chargeback-dispute-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Card-network reason-code & deadline reference** (versioned) | Reason-code title, required-evidence groups, representment window, compelling-evidence rules | Read-only |
| 2 | **Acquirer / gateway records** | The chargeback record, ARN/auth code, dispute amount, chargeback date, disputed transaction | Read-only |
| 3 | **Merchant order / fulfillment (OMS)** | Order confirmation, proof of delivery/service, terms accepted, refund history | Read-only |
| 4 | **Controlled template & content library** | Approved rebuttal template, exhibit-index format, standing disclaimer | Read-only |
| 5 | **Case portal** | Case/dispute identifiers, prior correspondence, current dispute state | Read-only |

The reason-code catalog and representment windows are a **versioned contract**
(`ruleset_version`). Never hard-code a deadline or evidence list that contradicts the
current network ruleset; record the version on every package.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `network-rules:VISA-13.1@cardnetwork-2026.07`,
`acquirer:arn=ARN0001;cb=CB-1001@2026-06-20`, `evidence:EX-1:carrier=UPS;tracking=1Z-AAA`,
`oms:order=ORD-771@2026-05-20`.

## Freshness / effective dates

- The reason code and its window are read from the **current** ruleset; a superseded
  bulletin can change both the required evidence and the deadline (see
  `network-rules-change-tracker`).
- The chargeback date drives the representment deadline. Compute against a stated
  `as_of_date`; if none is supplied the system date is used and the package must say so.

## Least-privilege operations (deployment)

- `network_rules.get(reason_code, version)` → title, required-evidence groups, window,
  compelling-evidence eligibility — read-only.
- `acquirer.get_chargeback(dispute_id)` / `gateway.get_transaction(txn_id|arn)` — read-only.
- `oms.get_order(order_id)` / `oms.get_fulfillment(txn_id)` — read-only, bounded.
- `templates.get('representment', version)` — read-only controlled content.
No mutation from this skill. Submission to the acquirer/network is **out of scope** — it is
performed by an authorized human via the case portal after review.
