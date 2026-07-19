# Source Map — regulatory-exam-response-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** (exam/inquiry workspace) | Request list, item state, issue/MRA status, durable `exam_id` | Read-only |
| 2 | **Records archive / document intelligence** | Policies, minutes, audit reports, evidence documents + provenance | Read-only |
| 3 | **Regulatory corpus** (controlled retrieval) | The examining regulator's request definitions and applicable rules | Read-only |
| 4 | **KYC / AML, sanctions & PEP, transaction monitoring** | Underlying evidence feeding a response (aggregate/desensitized) | Read-only |
| 5 | **Controlled content library** | Approved narrative templates, owners, effective dates, stale-language blocking | Read-only |
| 6 | **Approval broker** | Records the human approvals/sign-offs (never a substitute for them) | Read-only |
| 7 | Response **package template + config** (versioned) | Section contract, required approver roles | Read-only |

Case management is the system of record for exam/item **state**; the records archive is the
system of record for the **evidence** cited. Cite every assertion and every evidence item.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `casemgmt:exam=EXAM-2026-OCC-014@2026-07-16`,
`records:doc=POL-7742@v7.2`, `records:policy=BSA-AML-v7.2@2026-02-10`,
`config:exam-resp-tmpl@2026.07`.

## Freshness / effective dates

- Read the request list and item state fresh (a stale list may miss added requests or a
  changed due date).
- Evidence carries an effective date/version; a superseded document must not back a current
  assertion.
- The template + required-approver config is a **versioned contract**; the version is recorded
  on the assembled package for reproducibility and review.

## Least-privilege operations (deployment)

- `exam.read(exam_id)`, `requests.list(exam_id)`, `items.state(exam_id)` — read-only.
- `records.get(doc_id)`, `records.provenance(doc_id)` — read-only, bounded to cited items.
- `corpus.get(regulator, request_ref)` — read-only.
- `approvals.read(exam_id, item_id)` — read-only; the broker records human sign-offs.
No mutation from this skill. The assembled package is a **draft artifact**; any submission to
the regulator and any exam-item state change is performed by an authorized human, not here.
