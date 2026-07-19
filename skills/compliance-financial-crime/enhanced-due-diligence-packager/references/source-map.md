# Source Map — enhanced-due-diligence-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** | Case state (system of record), durable `case_id`, EDD trigger/scope | Read-only |
| 2 | **KYC / AML** | Customer profile, risk rating of record, SoF/SoW, ownership/UBO | Read-only |
| 3 | **Sanctions / PEP / adverse-media screening** | PEP status, sanctions result, adverse-media hits | Read-only |
| 4 | **Transaction monitoring** | Expected-activity corroboration, funding flows | Read-only |
| 5 | **Regulatory corpus** | High-risk-geography lists (e.g., FATF), applicable EDD standards | Read-only |
| 6 | **Records archive / document intelligence** | Source documents, statements, org charts, dossiers with page/version citation | Read-only |
| 7 | Approved **output template** + **residual-risk weighting** (versioned) | Template fidelity + scoring | Read-only |

Screening, monitoring, ownership verification, and adverse-media disposition are **specialist
domains** (see [handoffs.md](handoffs.md)); this skill consumes their read-only outputs as
evidence and routes for corroboration rather than concluding.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `kyc:cust=C-88213@2026-07-10`,
`docint:sof-brokerage-stmt=SOF-7781@2026-07-08`, `screening:pep=PEP-4471@2026-07-11`,
`regcorpus:fatf-high-risk-list@2026-06`, `casemgmt:EDD-2026-0042@intake`. Every asserted
evidence item carries at least one citation; uncited items are downgraded to gaps by
[../scripts/validate_output.py](../scripts/validate_output.py).

## Freshness / effective dates

- Case state and screening must be read **fresh** — a stale sanctions/PEP screen invalidates
  the package.
- High-risk-geography and standards are read from the **versioned** regulatory corpus; the
  version is recorded on the geography evidence.
- The output template and residual-risk weighting are **versioned contracts**; their versions
  are recorded on every package for reproducibility.

## Least-privilege operations (deployment)

- `casemgmt.read(case_id)` → case state, trigger, scope (read-only).
- `kyc.profile(customer_id)`, `kyc.ubo(customer_id)`, `kyc.sof_sow(customer_id)` — read-only.
- `screening.read(customer_id)` → PEP/sanctions/adverse-media results (read-only; no
  adjudication).
- `txnmon.flows(account_ref, window)` — read-only, bounded.
- `regcorpus.get('fatf-high-risk'|'edd-standard', version)` — read-only.
- `docint.fetch(doc_ref)` — read-only source documents with page/version citation.

No mutation from this skill. Assembling the package writes **nothing** to a system of record;
the package is a draft proposal for the human adjudicator, recorded via the approval broker.
