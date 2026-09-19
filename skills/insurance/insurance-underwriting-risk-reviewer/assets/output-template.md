# Underwriter-Ready Risk Profile — DRAFT (decision support only)

> **DRAFT — no decision made.** This profile is decision support for a licensed human
> underwriter. No coverage has been bound, quoted, declined, or issued, and no system of
> record has been updated. Fill every `{{...}}` from cited sources; never assert an
> uncited claim. Sections below are required — `scripts/validate_output.py` checks they are
> all present.

**Workbench ID:** {{workbench_id}}  |  **Submission:** {{submission_id}}  |  **Config
version:** {{config_version}}  |  **As-of date:** {{as_of_date}}

## Risk Summary

- **Insured (masked):** {{insured_name_masked}}
- **Occupancy class:** {{occupancy_class}}  |  **Line of business:** {{line_of_business}}
- **TIV:** {{tiv}}  |  **Requested limit:** {{requested_limit}}
- **Recommended disposition (advisory):** {{needs-data | refer-to-underwriter |
  ready-for-underwriter-review}}

## Data Completeness

| Section | Status | As-of | Citation |
| ------- | ------ | ----- | -------- |
| entity / property / exposure / loss_history / catastrophe / financial / third_party | present / missing | {{as_of}} | {{source_ref}} |

- **Complete:** {{true|false}}  |  **Missing:** {{list}}

## Source Freshness

| Section | As-of | Age (days) | SLA (days) | Status |
| ------- | ----- | ---------- | ---------- | ------ |
| {{section}} | {{as_of}} | {{age_days}} | {{sla_days}} | fresh / stale |

## Rule Findings & Exceptions

| Rule ID | Severity | Finding | Evidence | Route |
| ------- | -------- | ------- | -------- | ----- |
| {{UW-*}} | referral / exception | {{message}} | {{citation}} | {{skill / human}} |

_Empty when no rule fired. Every finding must carry evidence._

## Draft Decision Rationale

> Recommendation for underwriter adjudication: {{recommendation}}

- **Applied rules:** {{rule IDs}}
- **Routes:** {{adjacent skills / human handoffs}}
- **Citations:** {{source refs}}
- **Unsupported claims:** none (any uncited assertion is a defect and must be removed)

## Human Adjudication

- **Status:** pending
- **Required approver:** {{underwriter | senior underwriter / referral authority}}
- **Underwriter of record:** {{underwriter_id}}
- **Decision:** _(left blank — recorded by the human underwriter outside this skill)_
- **Decided at:** _(blank)_

## Standing Note

Draft underwriting risk profile and decision support only; no coverage has been bound,
quoted, declined, or issued, and no system of record has been updated. The underwriting
decision remains with a licensed human underwriter.
