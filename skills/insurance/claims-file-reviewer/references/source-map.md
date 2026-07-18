# Source Map — claims-file-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Claims system** (claim file, notes, reserves, payments, decisions) | Position of record for the claim | Read-only |
| 2 | **Policy & endorsements** (filed/approved forms) | Coverage grants, limits, deductibles, exclusions, policy period | Read-only |
| 3 | **Evidence** (medical / repair / adjuster reports, photos, correspondence) | Support for severity, reserves, and decisions | Read-only |
| 4 | **Payments / reserves ledger** | Paid and outstanding amounts, authority references | Read-only |
| 5 | **Legal & recovery data** (litigation, subrogation, salvage) | Open issues, recovery potential | Read-only |
| 6 | **Review config** (versioned) | Required-document sets, thresholds, tolerances | Read-only |

The claims system is the position of record. Where a policy form and a claim note conflict
(e.g., a note asserts a coverage the form does not grant), cite both and raise a finding for
the adjuster — never resolve the conflict as a coverage conclusion.

## Citation format

`{system}:{ref}@{date}` — e.g. `claims:claim=CLM-2026-0442;doc=DOC-EST@2026-06-20`,
`policy:PA-2026-778812;form=CA-0001;COLL@2026-01-01`, or `config:{version};required_documents.auto_collision.photos`.
Every finding cites the specific record, form clause, or config rule it derives from.

## Freshness / effective dates

- The **review config** (required-doc sets, thresholds, tolerances) is a versioned
  contract; the output records the `config_version` so a review is reproducible.
- Cite the **policy version in force on the loss date**; endorsements change coverage by
  effective date. The reviewer flags a loss outside the policy period; it does not decide
  whether coverage was in force.
- The chronology is built from dated events; state `as_of` and surface gaps rather than
  inferring unrecorded activity.

## Least-privilege operations (deployment)

- `claims.read(claim_id)` → claim header, documents, events, reserves, payments, decisions.
- `policy.read(policy_number, as_of)` → coverages, endorsements, period (form-cited).
- `evidence.read(claim_id)` → bounded document metadata + amounts (not raw PII beyond what
  evidences a finding).
- `config.get('claims-review', version)` → required-doc sets, thresholds, tolerances.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long claim
histories as resumable stages. No write, reserve-change, payment, or closure operation is
bound to this skill.
