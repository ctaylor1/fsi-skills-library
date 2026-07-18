# Source Map — merchant-onboarding-risk-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **KYB / registry** (entity resolution) | Legal entity, incorporation/registration, status; beneficial-ownership tree | Read-only |
| 2 | **Sanctions & watchlist screening** (approved-source retrieval) | OFAC/EU/UN + PEP screening result for entity and each owner | Read-only |
| 3 | **Adverse-media screening** | Negative-news categories and resolution status | Read-only |
| 4 | **Merchant application** (system of intake) | DBA, MCC, business model, expected activity, requested limit, website | Read-only |
| 5 | **Website / product review** (document intelligence) | Confirm products/claims; detect prohibited/undisclosed goods | Read-only |
| 6 | **Fraud & credit data** | Credit assessment, prior-processing/fraud history | Read-only |
| 7 | **Network & prohibited-use rules** (controlled content, versioned) | Prohibited/restricted MCC lists, high-risk geographies, thresholds | Read-only |

The KYB registry is the position of record for entity and ownership. Never substitute an
applicant assertion for the registry record; if the application and the registry conflict,
cite both and flag for the reviewer. Screening results are provided by the screening
services — this skill consumes their status, it does not adjudicate a sanctions hit
(that is `sanctions-match-adjudicator`).

## Citation format

`{system}:{ref}@{date}` — e.g. `ubo:kyb=NB-LLC;ubo=UBO-2`, `adverse_media:am=AM-33417@2026-07-13`.
Every fired finding cites the specific evidence rows (screening record, registry ref,
application field) behind it.

## Freshness / effective dates

- Prohibited/restricted lists, high-risk geographies, and thresholds are a **versioned
  contract** (`config_version`); the output records the version used so a review is
  reproducible.
- Screening results (sanctions, adverse media) carry their own as-of date; a stale screen
  is a data gap, not a clearance — surface it rather than assuming "cleared".
- `as_of` on the review is the application review date.

## Least-privilege operations (deployment)

- `kyb.resolve(entity_id)` → legal entity + ownership tree.
- `screening.get(entity_id|owner_id, kind)` → sanctions/adverse-media status + source_ref.
- `application.get(case_id)` → intake fields (MCC, expected activity, website, limit).
- `webreview.get(case_id)` → website/product review evidence.
- `creditfraud.get(entity_id)` → credit assessment + prior history.
- `config.get('merchant-risk', version)` → prohibited/restricted lists, geographies, thresholds.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
ownership trees or screening batches as resumable stages. No write, board, decline, or
filing operation is bound by this skill.
