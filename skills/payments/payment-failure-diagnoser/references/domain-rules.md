# Domain Rules — payment-failure-diagnoser

Rail-specific reason-code interpretation, the root-cause taxonomy, and the deterministic
**root-cause → route / retry** mapping. Code sets are **configuration** (versioned, owned by
the payments-strategy / network-rules team), not hard-coded judgments. Where the firm's
payments standard or the current scheme/ISO 20022 external code set differs, those take
precedence and are wired as config at deployment. The bundled dictionary in
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py) is a
representative subset for offline validation.

## Root-cause taxonomy

| Category | Meaning | Typical trigger |
| -------- | ------- | --------------- |
| `settled` | Payment completed; no failure | ISO 8583 `00`, ISO 20022 `ACSC/ACCC` |
| `insufficient_funds` | Payer funds unavailable | card `51`, ACH `R01`, `AM04` |
| `expired_or_restricted` | Instrument expired / limit / restricted | card `54/61/62/65` |
| `authorization_decline` | Issuer/agent declined or forbade | card `05/57`, `AG01` |
| `account_invalid` | Account closed / not found / non-transaction | card `14`, ACH `R02/R03/R20`, `AC04` |
| `format_reference_error` | Fixable data/reference defect | card `12`, ACH `R04`, `AC01/AC02/AG02/BE01/BE04/DT01/RC01/RC03` |
| `duplicate` | Duplicate submission | `AM05` |
| `system_timeout` | Issuer/switch/system unavailable or stuck in flight | card `91/96`, pending terminal |
| `screening_hold` | Blocked / regulatory / security response (NOT a determination) | card `63`, ACH `R16`, `AC06/RR04` |
| `suspected_fraud` | Lost/stolen/suspected-fraud response (NOT a determination) | card `41/43/59` |
| `unauthorized_return` | Customer/corporate advises unauthorized | ACH `R05/R07/R08/R10/R29` |
| `recall_return` | Returned/recalled after acceptance | pacs.004 return / camt.056 recall |
| `message_unparseable` | Message/format cannot be interpreted | `FF01`, `NARR` |
| `unknown` | Unrecognized code | any unmapped code |

Codes are resolved **within the declared rail's code set** — the same digits mean different
things per rail (ACH `R10` ≠ card response `10`).

## Decisive-leg logic (deterministic)

1. If the terminal leg is **settled**, root cause = `settled` (payment completed).
2. Else the decisive leg is the **last leg with a failing category** (anything except
   `settled`/`in_progress`); its category is the root cause.
3. Else, if the terminal leg is **pending / in flight** with no failing code, root cause =
   `system_timeout` (stuck-in-flight).
4. Else root cause = `unknown`.

## Root-cause → route / retry (deterministic, documented)

| Root-cause category | `suggested_route` | `retry_eligible` |
| ------------------- | ----------------- | ---------------- |
| `settled` | `none` | false |
| `insufficient_funds` | `customer-remediation` | true |
| `expired_or_restricted` | `customer-remediation` | true |
| `authorization_decline` | `customer-remediation` | true |
| `system_timeout` | `payment-exception-investigator` | true |
| `format_reference_error` | `payment-repair-assistant` | false |
| `account_invalid` | `payment-exception-investigator` | false |
| `duplicate` | `payment-exception-investigator` | false |
| `screening_hold` | `payment-exception-investigator` | false |
| `recall_return` | `payment-exception-investigator` | false |
| `unknown` | `payment-exception-investigator` | false |
| `message_unparseable` | `iso-20022-message-interpreter` | false |
| `suspected_fraud` | `payment-fraud-case-investigator` | false |
| `unauthorized_return` | `dispute-operations-assistant` | false |

`retry_eligible` means the underlying condition *can* clear so a **human or authorized
originating system** may re-present later — it is never an instruction to resubmit, and for
`system_timeout` it is conditional on confirming no prior settlement.

## Required cautions

- `system_timeout`, `duplicate` → "Confirm no prior settlement/credit before any
  re-presentment to avoid a duplicate payment."
- `insufficient_funds`, `expired_or_restricted`, `authorization_decline` → "Re-presentment
  only after the account-holder condition is resolved by the account holder or authorized
  originating system."
- `screening_hold` → "Screening hold is not a sanctions determination; do not release or
  clear the hold — route to investigation."

## Hard boundaries (fail closed)

- Never modify, repair, resubmit, re-present, reverse, release, cancel, return, or refund a
  payment, and never recommend doing so as an instruction — describe options and route.
- Never state or imply a payment **is** fraud or a confirmed sanctions match — describe the
  scheme/bank response factually and route.
- Never invent a meaning for an unrecognized code; keep the raw code and route.
- Never tune the route to the individual; use only the versioned config mapping.
