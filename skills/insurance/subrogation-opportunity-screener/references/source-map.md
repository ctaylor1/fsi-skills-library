# Source Map — subrogation-opportunity-screener

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Claims system** (system of record) | Claim financials (paid, reserve, deductible), status, loss facts, party roster | Read-only |
| 2 | **Policy administration** | Line of business, coverage, waiver-of-subrogation endorsements, made-whole/anti-subrogation conditions | Read-only |
| 3 | **Liability & correspondence** | Loss-cause narrative, adverse-insurer admissions, police/expert reports, negotiation history | Read-only |
| 4 | **Payments & recovery ledger** | Amounts paid to date, deductible reimbursed, prior recovery/salvage credits | Read-only |
| 5 | **Limitation-rules pack** (versioned) + **limitation calendar** | Controlling statute-of-limitation / notice period by jurisdiction and claim type; the diaried date | Read-only |
| 6 | **Party / external records** | Responsible-party resolution, insurer identity, collectibility (assets/coverage known) | Read-only |
| 7 | Recovery-strategy **config** (versioned) | Referral floor, liability-share floor, collectibility factors, limitation buffers | Read-only |

Never substitute a claim handler's assertion for the recorded claim financials or the diaried
limitation date. If the limitation-rules pack and the diaried date conflict, cite both and flag
for the recovery specialist — do not silently pick one.

## Citation format

`{system}:{ref}@{date}` — e.g. `claims:claim=CLM-556677;party=TP-1@2026-07-15`. Every fired
signal cites the specific evidence rows (party, financial line, evidence document, limitation
entry) behind it.

## Freshness / effective dates

- The **limitation date** is time-critical and jurisdiction-specific; the output records the
  diaried date, days remaining, and the config version so the screen is reproducible. A missing
  limitation date makes `limitation_window_open` **not evaluable** — resolve before reliance.
- Config (floors, factors, buffers) is a **versioned contract**; the output records the config
  version used so a screening is reproducible.
- Recovery economics use amounts **as of** the screening date; late payments change the base.

## Least-privilege operations (deployment)

- `claims.read(claim_id)` → financials, status, loss facts, party roster.
- `policy.read(policy_id)` → LOB, waiver/anti-subrogation endorsements, made-whole conditions.
- `recovery.ledger(claim_id)` → paid, deductible, prior recovery/salvage.
- `limitation.resolve(jurisdiction, claim_type)` + `limitation.calendar(claim_id)` → controlling
  date + diaried date.
- `party.resolve(party_id)` → insurer identity, collectibility indicators.
- `config.get('subrogation', version)` → floors, factors, buffers.

All read-only, deterministic, durable `screening_id`, below the fixed timeout; page a large
book of claims as resumable stages.
