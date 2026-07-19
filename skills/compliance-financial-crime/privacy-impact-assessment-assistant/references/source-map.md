# Source Map — privacy-impact-assessment-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Privacy / DPIA register (case management)** | Assessment state (system of record), durable `assessment_id`, DPIA trigger/scope | Read-only |
| 2 | **Records of Processing (RoPA) / data inventory** | Processing purpose, controller/processor roles, personal-data categories | Read-only |
| 3 | **Data lineage / mapping** | End-to-end personal-data flows, sources, and recipients | Read-only |
| 4 | **Privacy program artifacts** | Legitimate-interest assessment (LIA), transfer risk assessment (TIA), notices, rights runbooks | Read-only |
| 5 | **Regulatory corpus** | GDPR/UK-GDPR/CCPA text, Art 9/10 conditions, transfer mechanisms, high-risk-processing lists | Read-only |
| 6 | **Information security / TPRM** | Technical/organizational measures, vendor assurance (e.g., SOC 2), DPAs | Read-only |
| 7 | **Records archive / document intelligence** | Retention schedule, source documents, charters with page/version citation | Read-only |
| 8 | Approved **output template** + **privacy-risk weighting** (versioned) | Template fidelity + scoring | Read-only |

The underlying financial-crime data estate this category binds to — KYC/AML, sanctions and PEP
data, transaction monitoring, case management, the regulatory corpus, and the records archive —
is consumed **read-only** as a source of processing facts (what personal data exists, where it
flows, how it is retained). Data-flow mapping, third-party risk, and AI risk are **specialist
domains** (see [handoffs.md](handoffs.md)); this skill consumes their read-only outputs as
evidence and routes for corroboration rather than concluding.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `ropa:proc=PROC-4471@2026-07-09`,
`datalineage:flow=FL-3321@2026-07-10`, `privacyreg:lia=LIA-4471@2026-07-11`,
`regcorpus:gdpr-art6-art9@2026-06`, `contracts:dpa=DPA-771@2026-05`. Every asserted evidence
item carries at least one citation; uncited items are downgraded to gaps by
[../scripts/validate_output.py](../scripts/validate_output.py).

## Freshness / effective dates

- Assessment state and the DPIA register must be read **fresh** — a superseded assessment must
  not be re-packaged as current.
- Regulatory text (Art 9/10 conditions, transfer mechanisms, high-risk lists) is read from the
  **versioned** regulatory corpus; the version is recorded on the legal-basis and transfer
  evidence.
- The output template and privacy-risk weighting are **versioned contracts**; their versions
  are recorded on every assessment for reproducibility.

## Least-privilege operations (deployment)

- `dpiareg.read(assessment_id)` → assessment state, trigger, scope (read-only).
- `ropa.read(processing_id)`, `datainv.read(processing_id)`, `datalineage.flow(processing_id)` — read-only.
- `privacyreg.get('lia'|'tia'|'notice'|'retention', ref)` — read-only program artifacts.
- `regcorpus.get('gdpr'|'ccpa'|'transfer-mechanism'|'high-risk-list', version)` — read-only.
- `tprm.vendor(vendor_id)`, `infosec.controls(system_id)` — read-only assurance evidence.
- `docint.fetch(doc_ref)` — read-only source documents with page/version citation.

No mutation from this skill. Assembling the assessment writes **nothing** to a system of
record; the draft is a proposal for the human adjudicator, recorded via the approval broker.
