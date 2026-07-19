# Source Map — payment-fraud-case-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** | Case/alert state (system of record), chronology, chain of custody, durable `case_id` | Read-only |
| 2 | **Fraud platform** | Device, behavior, network/ring signals; model scores; watchlist proximity | Read-only |
| 3 | **Identity / KYC** | Customer identity, credential/contact-change events, verification status | Read-only |
| 4 | Gateway / processor / **acquirer** | Transaction detail, authorization, MCC, cross-border, network | Read-only |
| 5 | **Beneficiary / directory** | Beneficiary account, age, mule-watchlist proximity | Read-only |
| 6 | **Settlement + ledger** | Cleared/settled amounts, posting status for the disputed items | Read-only |
| 7 | **ISO 20022 parser** | Structured message fields (pacs/pain) for wire/RTP evidence | Read-only |
| 8 | Network rules / **scheme** references + scoring config (versioned) | Rule context and documented signal weights | Read-only |

Case management is the **system of record** for case state and the `case_id`. The fraud
platform provides signals but never a determination. Sanctions/adverse-media and SAR paths
are handled by specialists (see `handoffs.md`), not here.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `casemgmt:alert=PF-3002@2026-07-16`,
`fraudplatform:device=DVC-8842@2026-07-16`, `txns:txnid=T-90021@2026-07-16`,
`benef:acct=****0233@2026-07-16`, `fraudplatform:ring=RNG-77@2026-07-16`. Every evidence
item, chronology event, party, and network link in the bundle carries a citation.

## Freshness / effective dates

- Case/alert state is read **fresh** to avoid working a case another investigator or an
  adjudicator has already actioned.
- Scoring weights and thresholds are a **versioned contract** (`config_version`,
  `rules_version`); the version is recorded on the output so the recommendation is
  reproducible and reviewable.
- Transaction and settlement status can lag; cite the read time and flag pending items
  rather than assuming a final posting.

## Least-privilege operations (deployment)

- `cases.read(case_id|alert_id)`, `cases.chronology(case_id)` — read-only.
- `fraud.signals(entity_id)`, `fraud.network(entity_id)` — read-only signal reads.
- `idv.summary(customer_id)`, `txns.read(account_id, from, to)`,
  `benef.read(beneficiary_ref)`, `iso20022.parse(message)` — read-only, bounded.
- `config.get('pfraud-signals', version)` — read-only versioned contract.

No mutation from this skill. Any case-state change (adjudication, closure, block, filing) is
a **proposal** recorded via the approval broker for the human adjudicator — never executed
here. See `references/controls.md`.
