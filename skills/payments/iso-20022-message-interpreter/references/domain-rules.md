# Domain Rules — iso-20022-message-interpreter

Authoritative field semantics, code interpretations, integrity rules, and truncation
thresholds this skill applies. These encode market practice; the registered schema and the
applicable usage guideline (see [source-map.md](source-map.md)) are the governing sources
and win on any conflict. All rules are **descriptive** — none of them repairs, resubmits,
or dispositions a payment.

## 1. Message identity and structure

- `message_type` is `<family>.<NNN>.<VVV>.<NN>` (e.g. pacs.008.001.08). The **variant/version**
  (`.VVV.NN`) is significant; interpret against that version's code lists and element set.
- Every message has a **Group Header** (`GrpHdr`): `MsgId`, `CreDtTm`, and — for initiation
  and clearing messages — `NbOfTxs` and optional `CtrlSum`.
- Transaction identifiers and their scope:
  - `MsgId` — message level, sender-assigned, not guaranteed unique end-to-end.
  - `PmtInfId` / `InstrId` — batch / instruction level.
  - `EndToEndId` — assigned by the originator, **must be carried unchanged** the length of
    the chain; the literal `NOTPROVIDED` means the originator supplied none.
  - `TxId` — assigned by the first agent; identifies the interbank transaction.
  - `UETR` — Unique End-to-end Transaction Reference, a **UUIDv4** in `<UETR>`; the SWIFT
    gpi tracking key. Recommended/expected on pacs.008 and pacs.009.

## 2. Integrity / business rules (surface, never silently correct)

- **NbOfTxs** must equal the count of transactions present. A mismatch is a control-total
  break.
- **CtrlSum**, when present, must equal the sum of the instructed amounts. A mismatch is a
  control-total break.
- **Currency** must be a valid ISO 4217 code; the amount's decimal places must not exceed
  the currency's minor units (e.g. JPY 0, most 2, BHD/KWD/OMR 3).
- **IBAN** (when the account is IBAN-shaped) must pass the ISO 13616 mod-97 check digit.
- **BIC** must be ISO 9362 shaped: 8 or 11 characters (`AAAABBCC[XXX]`).
- **Charge bearer** (`ChrgBr`) is one of DEBT, CRED, SHAR, SLEV.
- A **rejection/return status** without an accompanying reason code or text cannot be
  explained — flag it; do not infer a cause.

## 3. Truncation and character-set risk

ISO 20022 is richer than the legacy MT / FIN world and than some scheme profiles. When a
message is (or will be) mapped down, information is lost. Detect and flag:

- **Length truncation**: identifier fields are `Max35Text`; name and unstructured
  remittance lines commonly map to MT `4*35` (≈140 characters). Any unstructured remittance
  line or party name **> 140 characters** is a truncation risk on down-mapping to MT `:70:`
  / `:59:` fields.
- **Character-set loss**: cross-border FIN uses the **SWIFT-x** character set
  (`a–z A–Z 0–9 / - ? : ( ) . , ' +` and space). Characters outside this set (accents,
  ampersand, symbols) are replaced or cause rejection. Flag any non-permitted character.
- **Structured→unstructured collapse**: structured remittance (`Strd`) that is flattened to
  unstructured text can lose reference/reconciliation data. Note it when it applies.

## 4. Status and reason interpretation (pacs.002 / pain.002)

Transaction/group status (`TxSts` / `GrpSts`), decoded to a category and plain meaning:

| Code | Category | Meaning (short) |
| ---- | -------- | --------------- |
| ACSC / ACCC | accepted | Accepted, settlement completed. |
| ACSP | accepted | Accepted, settlement in process. |
| ACCP / ACTC | accepted | Accepted after customer / technical validation. |
| ACWP | accepted | Accepted without posting yet. |
| ACWC | accepted-with-change | Accepted after a modification. |
| PDNG | pending | Not yet processed; awaiting action/information. |
| RCVD | received | Received, not yet processed. |
| PART | partial | Partially accepted; inspect each transaction. |
| RJCT | rejected | Rejected; a reason code should accompany. |

Common status/return **reason codes** (External Status Reason / Return Reason; decode
against the referenced version). A reason is data carried in the message — an assertion by
a party, not a determination by this skill:

| Code | Meaning |
| ---- | ------- |
| AC01 | Incorrect account number. |
| AC02 / AC03 | Invalid debtor / creditor account number. |
| AC04 | Closed account number. |
| AC06 | Blocked account. |
| AG01 / AG02 | Transaction forbidden / invalid operation code. |
| AM04 | Insufficient funds. |
| AM05 / DUPL | Duplication / duplicate payment. |
| BE01 | Name and account inconsistent with end customer. |
| RC01 | Bank identifier (BIC/routing) incorrect. |
| RR01–RR04 | Missing/insufficient regulatory party information. |
| TM01 | Received after cut-off time. |
| CUST / MS02 / MS03 | Requested by customer / reason not specified. |
| FRAD | Fraudulent-origin reason **asserted by a party** — carried, not adjudicated here. |
| NARR | See accompanying free-text narrative. |

An unlisted code is reported as **unknown**, with a pointer to the governing code list.

## 5. Purpose and category-purpose

- `Purp/Cd` (external purpose) and `CtgyPurp/Cd` (category purpose, e.g. SALA, SUPP, TAXS,
  INTC) explain the payment's stated intent and can drive scheme routing/handling. Decode
  from the external code list; do not infer intent beyond the coded value.

## 6. Interpretation boundaries (what the rules never conclude)

- Never conclude a payment **is/isn't fraudulent**, **is/isn't sanctioned**, or **is
  compliant** — those are regulated determinations for the monitoring/investigation and
  compliance functions.
- Never conclude a payment **will settle** or is **safe to release**.
- Never emit a **repair, correction, resubmission, cancellation, or fund-movement**
  instruction. A `FRAD` reason or a `RJCT` status is *explained and routed*, not acted on.
