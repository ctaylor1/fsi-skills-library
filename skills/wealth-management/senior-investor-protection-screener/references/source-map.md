# Source Map — senior-investor-protection-screener

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Portfolio accounting / OMS **transactions** (position of record) | Focal disbursement + baseline history | Read-only |
| 2 | **CRM** client context | Age/DOB, trusted-contact status, beneficiary/registration/address changes, structured observation notes, known payees | Read-only |
| 3 | **Planning engine / product data** | Whether a disbursement matches a documented plan (RMD, withdrawal strategy, gifting) | Read-only |
| 4 | **Reference data** | Payee/counterparty resolution, channel taxonomy | Read-only |
| 5 | Senior-protection **config** (versioned) | Signal thresholds and disposition mapping | Read-only |

Never substitute a client assertion, a caregiver's statement, or a third party's request for
the transaction/CRM record. If a record and a note conflict, cite both and flag for the
reviewer. Observation flags (third-party present, urgency, confusion, etc.) are **structured
inputs supplied by a trained human**, not conclusions the skill infers on its own.

## Citation format

`{system}:{ref}@{date}` — e.g. `txns:acct=****4521;txnid=D-90001@2026-07-14T09:40:00`,
`crm:crm=****4521;chg=C-3301@2026-07-01`, `crm:crm=****4521;note=N-5567`. Every fired signal
cites the specific evidence rows (transactions, change records, observation refs) it rests on.

## Freshness / effective dates

- Config (thresholds, disposition mapping) is a **versioned contract**; the output records the
  config version used so a screening is reproducible.
- Baseline lookback default 365 days; state the exact window in the output.
- The specified-adult age threshold (default 65) and the "specified adult" impairment
  criterion are jurisdiction/config-driven (FINRA Rule 2165 / NASAA Model Act); configure per
  deployment. US is the default jurisdiction pack.

## Least-privilege operations (deployment)

- `txns.read(account_id, from, to)` → bounded, paged transaction rows.
- `crm.context(client_id)` → age, trusted-contact status, recent changes, structured
  observation flags (no free-text PII beyond what evidences a signal).
- `planning.get(client_id)` → documented plan events (RMD, gifting, withdrawal schedule).
- `refdata.resolve(counterparty|channel)` → normalized values.
- `config.get('senior-protection', version)` → thresholds + disposition mapping.

All read-only, deterministic, durable `screening_id`, below the fixed timeout; page long
histories as resumable stages. No write, hold, notification, filing, or case-closure operation
is bound to this skill.
