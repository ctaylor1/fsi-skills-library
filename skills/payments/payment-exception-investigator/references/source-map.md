# Source Map — payment-exception-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Investigations / case system** | Case + exception state (system of record), `case_id`, linkage | Read-only |
| 2 | **Payment messages & status** | pacs.008/pacs.002/pacs.004/pacs.028, camt.056/camt.029 chronology, status, reason codes | Read-only |
| 3 | **ISO 20022 external code sets** (versioned) | Reason-code -> meaning/family (`AC01`, `AC04`, `RR04`, `DUPL`, …) | Read-only |
| 4 | **Correspondents / counterparties** reference | Debtor/creditor agent (BIC) and party resolution | Read-only |
| 5 | **Screening & repair rules** (versioned config) | Sanctions/regulatory routing, repair eligibility, priority config | Read-only |
| 6 | **Scheme rulebooks** (SEPA, Fedwire, CHIPS, TARGET2, RTP, FPS) | Recall/return windows, permissible next steps | Read-only |

The investigations/case system is authoritative for case state; the payment message store is
authoritative for status and chronology. When the two disagree, cite both and fail closed to
`needs-data` rather than guessing.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `pacs002=STS-3001@2026-07-15`,
`camt056=RCL-3003@2026-07-12`, `invcase=IC-70011`, `config:iso-extcodes@2026.05`.
Every chronology event carries the originating message `msg_ref`; every evidence bundle lists
its citations. Uncited evidence fails `validate_output`.

## Freshness / effective dates

- Case/exception state must be read fresh (avoid working an already-resolved or reassigned case).
- Reason-code meanings and screening/repair/priority rules are **versioned contracts**; the
  `reason_code_set_version` and `config_version` are recorded on every investigation record.
- Recall/return eligibility is time-boxed by scheme rulebook windows; capture the `as_of` date.

## Least-privilege operations (deployment)

- `cases.read(case_id|exception_id)`, `cases.find(uetr|instruction_id)` (linkage) — read-only.
- `messages.read(uetr|instruction_id)` -> pacs/camt set — read-only, bounded.
- `codes.get('iso-ext', version)`, `config.get('pei-screening'|'pei-priority', version)` — read-only.
- `parties.resolve(bic|account_ref)` — read-only.
No mutation from this skill. The camt.029 recall response, any return/repair/resubmission, and
any case-state change are **proposals** routed to the approval broker and to
`payment-repair-assistant`; they execute only after human approval.
