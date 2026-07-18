# Source Map — policy-renewal-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Policy administration** (position of record for terms) | Expiring + proposed term structure: premium, coverages/limits/deductibles, exposures, forms/endorsements | Read-only |
| 2 | **Claims** (position of record for loss history) | Claims in the review window: incurred/paid, status, cause, dates | Read-only |
| 3 | **Filed/approved forms library** (controlled content) | Resolve `form_id` + `edition`; identify bureau/state vs. manuscript forms | Read-only |
| 4 | **Underwriting rules / config** (versioned) | Change thresholds and the disposition mapping | Read-only |
| 5 | **Actuarial / catastrophe data** | Exposure/rate context, catastrophe accumulation flags (context only) | Read-only |

Never substitute a quote document, producer note, or insured assertion for the policy-administration
record. If a quote/proposal document and the policy-admin record conflict, cite both and flag for the
reviewer — do not resolve silently.

## Citation format

- Term evidence: `pas:{source_ref}@{as_of}` — e.g. `pas:pas=****4021;term=proposed@2026-07-15`.
- Claim evidence: `claims:{source_ref}@{date_of_loss}` — e.g. `claims:claims=****4021;clm=C-2@2025-02-02`.

Every fired finding cites the specific expiring/proposed values (or claim rows) and the
threshold/basis it compared against.

## Freshness / effective dates

- Config (thresholds, disposition mapping) is a **versioned contract**; the output records the
  `config_version` used so a review is reproducible.
- The review window for loss history defaults to 1,095 days (3 years); state the exact window and the
  years used in the loss-ratio basis.
- Compare the expiring term as of its expiration against the proposed term as of its effective date;
  do not mix mid-term endorsements into the expiring baseline unless they are in force at expiration.

## Least-privilege operations (deployment)

- `pas.term(policy_id, which='expiring'|'proposed')` → one term's structure (premium, coverages,
  exposures, forms).
- `claims.history(policy_id, from, to)` → bounded, paged claim rows for the review window.
- `forms.resolve(form_id, edition)` → filed-form metadata (bureau/state/manuscript, effective date).
- `config.get('renewal', version)` → thresholds + disposition mapping.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long loss histories
as resumable stages. No write, bind, notice, or pricing operation is in scope.
