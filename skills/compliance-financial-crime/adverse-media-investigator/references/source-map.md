# Source Map — adverse-media-investigator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** | Durable `case_id`, prior adverse-media cases, evidence bundle, chain of custody | Read-only |
| 2 | **KYC / customer due diligence** | Subject identity, DOB, nationality, ownership, known identifiers (entity resolution) | Read-only |
| 3 | **Sanctions & PEP data** | List proximity for a subject (route to specialist; do **not** adjudicate) | Read-only |
| 4 | **Regulatory / court / official corpus** | Tier-1 primary sources: enforcement actions, judgments, gazettes | Read-only |
| 5 | **Adverse-media / news retrieval** | Candidate media hits with source, date, headline, excerpt | Read-only |
| 6 | **Transaction monitoring** | Corroborating activity context for a case (amounts, counterparties) | Read-only |
| 7 | **Records archive** | Historical filings, prior dispositions, retention records | Read-only |
| 8 | Scoring config (source tiers, category weights, materiality bands) — **versioned** | Entity resolution + materiality | Read-only |

## Source tiers (reliability, used in materiality)

- **Tier 1** — official / primary: regulator enforcement, court records, government gazettes,
  official sanctions lists. Highest weight.
- **Tier 2** — established media: reputable, editorially-governed outlets.
- **Tier 3** — low reliability: aggregators, blogs, anonymous or unverified posts. A Tier-3
  hit alone cannot make a case material; it needs Tier-1/Tier-2 corroboration.

## Citation format

`{source}:{source_ref}@{published_date}` — e.g. `regulator:enf=2025-0115@2025-03-02`,
`media:art=fin-times-2022-3391@2022-09-10`, `sanctions_list:list=OFAC;entry=SDN-33119@2026-01-05`.
The screening baseline is cited as `screening:{config_version}@{as_of_date}`.

## Freshness / effective dates

- Recency is scored relative to the batch `as_of_date`; every hit records its `published_date`.
- Sanctions/PEP list proximity must be read fresh and routed — never adjudicated on a stale
  snapshot.
- Source tiers, category weights, and materiality bands are a **versioned** scoring config;
  the `config_version` is recorded on every case for reproducibility and review.

## Least-privilege operations (deployment)

- `cases.get(subject_id)` / `cases.find(prior adverse-media)` — read-only, durable `case_id`.
- `kyc.summary(subject_id)` — read-only identity + identifiers for entity resolution.
- `flags.read(subject_id)` → sanctions/PEP proximity (boolean + source), **no adjudication**.
- `corpus.get(ref)` / `media.search(subject)` — read-only Tier-1/2/3 retrieval.
- `config.get('ami-scoring', version)` — read-only versioned scoring contract.

No mutation from this skill. Any escalation, EDD assembly, sanctions adjudication, rating
change, or SAR is a **proposal/handoff** recorded via the approval broker for a human owner.
