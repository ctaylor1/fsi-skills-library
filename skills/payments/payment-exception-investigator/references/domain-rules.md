# Domain Rules — payment-exception-investigator

Orientation references: ISO 20022 message definitions (pacs/camt) and the **externalized code
sets** (payment status reason codes), plus the relevant scheme rulebooks (SEPA, Fedwire, CHIPS,
TARGET2, RTP, FPS). The firm's screening/repair rule set and the ISO code-set version are
**versioned contracts** recorded on every investigation record.

## Reason-code mapping (deterministic; `reason_code_set_version`)

The default map lives in `scripts/calculate_or_transform.py` (`DEFAULT_REASON_CODES`) and is
overridable via `reason_code_config`. Meaning drives the *recommended* disposition — never an
executed action.

| Code | Meaning | Family | Default recommendation |
| ---- | ------- | ------ | ---------------------- |
| `AC01` | IncorrectAccountNumber | account | repair-and-resubmit (repairable) |
| `AC04` | ClosedAccountNumber | account | return-to-originator (no repair) |
| `AC06` | BlockedAccount | account | return-to-originator |
| `AM04` | InsufficientFunds | funds | return-to-originator |
| `BE01` | InconsistentWithEndCustomer | party | request-information |
| `RC01` | BankIdentifierIncorrect | agent | repair-and-resubmit |
| `RR04` | RegulatoryReason | regulatory | **route** -> sanctions-match-adjudicator |
| `DUPL` | DuplicatePayment | duplicate | honor-recall (if duplicate evidenced) |
| `TECH` | TechnicalProblem | recall | honor-recall |
| `FRAD` | FraudulentOrigin | fraud | **route** -> payment-fraud-case-investigator |
| `CUST` | RequestedByCustomer | recall | reject-recall (unless consent + funds available) |
| `FOCR` | FollowingCancellationRequest | recall | request-information |
| `MS03` | NotSpecifiedReason | unknown | request-information |

## Precedence (applied in order)

1. **needs-data** — no messages (no chronology) OR no payment identifier -> do not guess.
2. **Routing overrides** — a `fraud_indicator` (or `FRAD`) routes to fraud; a `sanctions_hold`
   (or regulatory family, `RR04`) routes to sanctions. A risk signal is never hidden by dedup
   or a repair recommendation.
3. **possible-duplicate** — a `uetr` / `instruction_id` match to an open case links (never merges).
4. **Recall (camt.056)** — see below.
5. **Reason-code mapping** — for rejected/returned exceptions per the table.
6. **Fallback** — chronology present but no actionable code -> request-information.

## Recall handling (camt.056 -> camt.029 is a human decision)

- `DUPL` (with `duplicate_of` evidence) or `TECH` -> **recommend-honor-recall**.
- `DUPL` without duplicate evidence -> **recommend-request-information**.
- `CUST` -> **recommend-reject-recall**, unless `beneficiary_consent` AND `funds_available` are
  both true, in which case **recommend-honor-recall**.
- Anything else -> **recommend-request-information**.

The camt.029 resolution (positive/negative) is drafted as a recommendation and **issued only by
a human approver** — this skill never sends it.

## Priority scoring (deterministic, documented)

Contributions (default config, overridable via `priority_config`):

| Input | Contribution |
| ----- | ------------ |
| Amount value | ≥ 1,000,000 +3, ≥ 100,000 +2, ≥ 10,000 +1 |
| Scheme criticality | Fedwire/CHIPS/TARGET2/RTP/FPS +2; SEPA/ACH/BACS +1 |
| Aging (first message -> `as_of`) | ≥ 5 days +2, ≥ 2 days +1 |
| Exception severity | recall_requested/returned +2; rejected/nondelivery +1 |
| Fraud/sanctions signal | +3 (also forces a specialist route) |

Bands: **P1 (Critical)** score ≥ 6 or any fraud/sanctions signal; **P2 (Standard)** 3–5;
**P3 (Low)** ≤ 2. Priority is a triage rank for a human, not a decision.

## Hard boundaries (fail closed)

- No fund movement (return/reissue/release/debit/credit/posting) — recommendation only.
- No case closure, determination, exoneration, or filing.
- No camt.029 / pacs.004 / pacs.002 *sent* from this skill.
- No auto-merge; dedup links for human confirmation.
- No sanctions/fraud adjudication; route to the specialist.

## Evidence bundle — required contents

Durable `case_id`; scheme; payment identifiers (uetr/instruction/e2e/txn); parties (masked) with
roles; amount; the cited message **chronology**; last status + reason code/meaning/source; linked
open cases; citations for every item; the deterministic priority band; and a recommendation with
`requires_approval: true`.
