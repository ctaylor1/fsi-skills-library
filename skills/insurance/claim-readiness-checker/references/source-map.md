# Source Map — claim-readiness-checker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Policy administration** (position of record) | Policy in force, period, insured, endorsements, limits, deductibles, and the required-item / deadline schedule for the claim type | Read-only |
| 2 | **Claims** system | Claim record, reported dates, loss facts, submitted documents and forms, claim fields | Read-only |
| 3 | **Document intelligence** | Presence, type, legibility, signature, form version, and page/field citation for each document | Read-only |
| 4 | **Underwriting-rules / claims-standards config** (versioned) | Required-document, required-form, required-field catalogs and deadline/at-risk thresholds per claim type and jurisdiction | Read-only |
| 5 | **Actuarial / catastrophe & producer systems** | Event/CAT context and producer-supplied documents, when the claim references them | Read-only |

Never substitute a claimant assertion for the policy or claims record. If the policy record
and a submitted document conflict (e.g., stated policy period vs. document date), cite both
and flag for the reviewer — do not resolve it silently, and never infer coverage from it.

## Citation format

`{system}:{ref}` — e.g. a document is `dms:claim=CLM-2026-88421;doc=D-2`; a deadline traces
to `policy:deadline=proof_of_loss@2026-08-19`. Every inspected document, form, and deadline
evidence row carries a citation so a reviewer can open the exact source.

## Freshness / effective dates

- The required-item catalog, deadline schedule, and thresholds are a **versioned contract**
  (owned by underwriting/claims standards); the output records the `config_version` used so a
  readiness check is reproducible.
- Deadlines are computed against `as_of`; the output states `as_of` and each deadline's
  `days_remaining`. Deadline dates must be verified against the controlling policy and
  jurisdiction — this check surfaces timeliness, it does not set the legal deadline.
- Chronology uses the policy period and the loss/reported/prepared dates; state each date used.

## Least-privilege operations (deployment)

- `policy.get(policy_number, as_of)` → status, period, endorsements, limits, deductibles,
  required-item and deadline schedule for the claim type/jurisdiction.
- `claims.get(claim_id)` → claim fields, reported dates, document/form manifest.
- `docintel.inspect(doc_id)` → type, status/legibility, signed flag, form version, citation.
- `config.get('claim-readiness', version)` → required-item catalog + thresholds.
All read-only, deterministic, durable `readiness_id`, below the fixed timeout; page long
document manifests as resumable stages.
