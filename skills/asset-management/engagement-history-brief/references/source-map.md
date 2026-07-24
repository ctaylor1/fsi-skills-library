# Source Map — engagement-history-brief

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Engagement log / stewardship CRM** | System of record for what was said, committed, and followed up; `engagement_id`, attendees, follow-up state | Read-only |
| 2 | **Issuer disclosures & regulatory filings** (document intelligence) | Authoritative source for **disclosed progress** against a commitment | Read-only |
| 3 | **Meeting notes / engagement letters** (document intelligence) | Contemporaneous record of topics, commitments, and attendees | Read-only |
| 4 | **Entity resolution** (issuer / security master) | Resolve the issuer, ticker, and holding funds | Read-only |
| 5 | **Research-provider inputs** (approved-source retrieval) | Supporting context only; never a substitute for the primary record | Read-only |
| 6 | **Controlled template & config** (`brief_version`, `source_hierarchy_version`) | Template sections + source-ranking version (versioned contracts) | Read-only |

The engagement log ranks above disclosures for *what was committed*; issuer disclosures and
filings rank above notes for *what progress was disclosed*. Research-provider material never
overrides the primary record.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `engagementlog:ENG-2025-05@2025-05-20`,
`docint:DOC-2@2025-05-20`, `filing:RNS-8821@2025-12-03`,
`config:eng-brief@2026.07`. Every engagement, commitment, disclosed-progress, follow-up, and
source-document row carries at least one citation; `validate_output` fails closed on any
uncited item.

## Freshness / effective dates

- Read the engagement log and disclosures **fresh**; a brief is only as current as its
  `as_of_date`, which is stamped on the issuer profile and the provenance block.
- A **disclosed-progress** record is dated to when the issuer disclosed it, independent of the
  engagement date, so late disclosures against old commitments are attributed correctly.
- Commitment status is computed against `as_of_date` (overdue = `due < as_of_date` with no
  disclosed progress). Re-running with a later `as_of_date` may move a commitment into
  `overdue-no-disclosure`; that is expected and reproducible.

## Durable identifiers

- `brief_id` — durable id for the assembled brief (issuer + as_of run); downstream skills and
  the human review reference this id rather than re-assembling.
- `engagement_id`, `commitment_id`, `follow_up_id`, `doc_id` — carried through from the log so
  every brief row is traceable back to the system of record.

## Least-privilege operations (deployment)

- `engagementlog.read(issuer_id, from, to)`, `engagementlog.list_followups(issuer_id)` — read-only.
- `docint.get(doc_id)`, `filings.read(issuer_id, from, to)` — read-only, bounded.
- `entity.resolve(issuer_id|ticker)` — read-only.
- `config.get('eng-brief', version)` — read-only.

No mutation from this skill. The brief is a **draft artifact**; recording an objective, a firm
position, a vote, or any engagement-log write happens outside this skill via the approval
broker and the system of record, under human authorization.
