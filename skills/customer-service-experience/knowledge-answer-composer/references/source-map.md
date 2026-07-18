# Source Map — knowledge-answer-composer

Every factual statement in a composed answer must cite one of the sources below, ranked.
See the shared platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved knowledge base** (controlled content library) | Policies, procedures, FAQs with an owner and effective/expiry dates | Read-only |
| 2 | **Filed / product terms** (approved-source retrieval) | Product terms, fee schedules, disclosures, contractual language | Read-only |
| 3 | **Procedure library** | Step-by-step "how do I…" procedures for the servicing task | Read-only |
| 4 | **Service-status** feed | Current outage / availability / maintenance status, time-stamped | Read-only |
| 5 | **CRM / case-management & complaint system** | Account/case context that scopes *which* approved article applies (not a source of the answer text itself) | Read-only |
| 6 | User-supplied text | Only when 1–5 are silent; must be labeled unverified and is never a substitute for approved content | Read-only |

Never let a user assertion, a screenshot, or an inbound message override approved content.
If two approved sources conflict, present both with citations and stop for human review.

## Citation format

Each claim carries a citation of the form `{type}:{source_id};{ref}@{effective_date}` — e.g.
`policy:POL-DISP-14;§2.1@2026-01-01`, `product-terms:PT-CHK-03;p4@2025-06-01`, or
`service-status:SS-2026-07-17;dispute-portal@2026-07-17`. The machine-readable output stores
the citation and `source_id` per claim; the narrative repeats the same wording inline so the
[`scripts/validate_output.py`](../scripts/validate_output.py) grounding check can confirm
every claim is present in `answer_text`.

## Freshness / effective dates

- Every source carries an **effective_date**; a source is usable only if
  `effective_date <= as_of_date` and (no `expiry_date` or `expiry_date >= as_of_date`).
- **Service-status** sources are time-sensitive: treat a status older than the configured
  status window (default: same business day) as **stale** and re-fetch before stating it.
- **Draft, pending, expired, or retired** content is never a basis for an answer; it is
  surfaced as a data gap so the human can request a refresh.
- Jurisdiction must match: a source tagged to a jurisdiction other than the request's is
  excluded unless the question is explicitly cross-jurisdiction.

## Least-privilege operations (deployment)

- `knowledge.search(question, jurisdiction, as_of)` → ranked candidate articles with owner,
  status, effective/expiry dates, and citable `ref`.
- `terms.read(product_id, as_of)` → approved product-terms excerpt + citation.
- `status.read(service_id, as_of)` → current service status + timestamp.
- `case.read(case_id)` → account/case context to scope which article applies (read-only).
All read-only, deterministic schemas, durable `answer_id`, below the fixed timeout.
