# Source Map — suspicious-activity-report-drafter

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** | Case state (system of record), durable `case_id`, the approving investigation reference and its SAR-drafting approval | Read-only |
| 2 | **Transaction-monitoring / investigation** | Concluded investigation findings, rationale, and the fact set the narrative draws on | Read-only |
| 3 | **Transactions** | Individual transactions, amounts, dates, instruments, counterparties (for chronology + tie-outs) | Read-only |
| 4 | **KYC / AML** | Subject/party identity, expected activity, relationships | Read-only |
| 5 | **Sanctions / PEP / adverse-media screening** | Screening context surfaced during drafting (route to specialist; do not conclude) | Read-only |
| 6 | **Typology library** (versioned) | Approved typology codes and their required indicators | Read-only |
| 7 | **Records archive / document intelligence** | Source documents with page/version citation | Read-only |
| 8 | Approved **output template** + **narrative/quality checklist** (versioned) | Template fidelity + quality screens | Read-only |

The suspicion determination is made **upstream** by the human-adjudicated investigation; this
skill drafts from that concluded, approved case and never re-adjudicates it. Screening,
ownership, and adverse-media disposition are **specialist domains** (see
[handoffs.md](handoffs.md)); this skill consumes their read-only outputs as evidence and routes
for corroboration rather than concluding.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `casemgmt:SAR-2026-0100@intake`,
`tmcase:TM-CASE-5521;findings@2026-06-12`, `txns:acct=****3300;txnid=T6@2026-06-01`,
`kyc:cust=SUBJ-1;expected-activity@2026-06-11`, `config:typology-library=sar-2026.07`. Every
asserted fact carries at least one citation; uncited facts, chronology events, or rationale
are downgraded to gaps by [../scripts/validate_output.py](../scripts/validate_output.py).

## Freshness / effective dates

- Case state and the SAR-drafting approval must be read **fresh** — a draft is only produced
  from a case currently approved/adjudicated for SAR drafting.
- Transactions, amounts, and dates are read from the transactions system of record and must
  **tie out** to the declared activity summary; a break forces `needs-evidence`.
- The typology library, output template, and quality checklist are **versioned contracts**;
  their versions are recorded on every package for reproducibility.

## Least-privilege operations (deployment)

- `casemgmt.read(case_id)` → case state, approving investigation, SAR-drafting approval (read-only).
- `tmcase.read(investigation_id)` → concluded findings and rationale (read-only).
- `txns.read(account_ref, from, to)` → transactions for chronology + tie-outs (read-only, bounded).
- `kyc.profile(subject_id)`, `kyc.expected_activity(subject_id)` — read-only.
- `screening.read(subject_id)` → PEP/sanctions/adverse-media context (read-only; no adjudication).
- `config.get('typology-library'|'sar-template'|'sar-quality-checklist', version)` — read-only.
- `docint.fetch(doc_ref)` — read-only source documents with page/version citation.

No mutation from this skill. Assembling the package writes **nothing** to a system of record;
the package is a draft proposal for the human quality reviewer and the MLRO/BSA Officer, and
any filing is a separate authorized human action. There is no `file`, `submit`, or `close`
operation in this skill's surface.
