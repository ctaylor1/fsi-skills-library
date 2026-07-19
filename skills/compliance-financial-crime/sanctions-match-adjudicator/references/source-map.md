# Source Map — sanctions-match-adjudicator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Sanctions / PEP list data** (OFAC SDN/SSI, EU CFSP, UN, HMT/OFSI, PEP) | The matched listed entity: names/AKAs, identifiers, DOB, nationality, POB, addresses, program, effective/updated dates | Read-only |
| 2 | **Screening engine / filter** | The hit itself, the vendor match score, and the durable `screening_run_id` provenance | Read-only |
| 3 | **KYC / customer** | The subject record: name/aliases, identifiers, DOB, nationality, POB, addresses, ownership | Read-only |
| 4 | **Transactions** | Payment context: parties, countries, amount, value date (jurisdiction nexus) | Read-only |
| 5 | **Case management** | Prior/open adjudications (dedup), durable `case_id` | Read-only |
| 6 | **Regulatory corpus** (OFAC 50% Rule, program guidance) + match-factor/band **config** (versioned) | Ownership treatment, factor weights, disposition bands | Read-only |

The sanctions list data is authoritative for the *listed entity*; KYC for the *subject*; the
screening engine for the *hit*. The subject is never treated as a match on the strength of the
vendor score alone — the deterministic factors and human adjudication govern.

## Citation format

`{system}:{ref}@{version/date}` — e.g.
`sanctions-list:OFAC-SDN/OFAC-12345@2021-03-01`, `screening:hit=SCR-3001@RUN-2026-07-14-0912`,
`kyc:subject=CUST-100@2026-07-10`, `txns:payment=PMT-88120@2026-07-14`,
`casemgmt:prior=SANC-SCR-8000`. Every chronology event, match factor, and party carries at
least one citation; the bundle exposes a de-duplicated citation list.

## Freshness / effective dates

- The **list entry** must be read at its current version; record `list_effective_date` (and
  `list_updated_date` where present) so a stale-list adjudication is visible.
- The **screening run** timestamp anchors the chronology and evidences provenance.
- Match-factor weights and disposition bands are **versioned config**; the version travels on
  every bundle for reproducibility and review.

## Least-privilege operations (deployment)

- `sanctions.get(list_ref, version)`, `sanctions.ownership(entity_id)` — read-only list lookup.
- `screening.get(alert_id | run_id)` — read-only hit + provenance; no re-scoring.
- `kyc.subject(subject_id)` — read-only subject record.
- `txns.read(payment_id)` — read-only, bounded to the flagged payment.
- `cases.find(subject_id, list_ref)` (dedup), `config.get('sanctions-factors'|'sanctions-bands', version)` — read-only.

No mutation from this skill. A disposition is a **proposed** case-state transition recorded via
the approval broker for the sanctions officer; the block/reject/release/unblock and any
blocking/OFAC report are the officer's actions, not this skill's.
