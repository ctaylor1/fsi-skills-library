# Domain Rules — underwriting-workbench-assistant

Orientation references: the carrier's underwriting guidelines, appetite statement, delegated
binding-authority schedule, and catastrophe-management standard. These, plus the approved
**underwriting rules / appetite / authority config**, are versioned contracts and take
precedence. Thresholds below are documented **defaults**; deployment config overrides them,
and the `config_version` is recorded on every compiled profile.

## Required risk sections (completeness)

A complete profile needs all seven sections, each present with a `source_ref` and `as_of`:
`entity`, `property`, `exposure`, `loss_history`, `catastrophe`, `financial`, `third_party`.
Any missing section → `needs-data`. Data is never guessed to fill a gap.

## Source freshness SLAs (default)

| Section | Max age (days) | Critical? |
| ------- | -------------- | --------- |
| entity | 365 | no |
| property | 180 | yes |
| exposure | 180 | yes |
| loss_history | 400 | no |
| catastrophe | 120 | yes |
| financial | 365 | no |
| third_party | 90 | no |

Age is measured against the review `as_of_date`. A **stale critical** section → `needs-data`.
A stale non-critical section → `UW-FRESHNESS` exception (route to underwriter).

## Approved underwriting rules (deterministic, documented)

| Rule ID | Condition (default) | Severity | Route |
| ------- | ------------------- | -------- | ----- |
| `UW-AUTH-TIV` | TIV above the underwriter's binding-authority TIV | referral | senior underwriter |
| `UW-CAPACITY` | Requested limit above binding-authority limit | referral | `reinsurance-treaty-interpreter` |
| `UW-APPETITE-CLASS` | Occupancy class not in the approved appetite list | referral | senior underwriter |
| `UW-LOSS-RATIO` | 3-year loss ratio above `0.70` | referral | senior underwriter |
| `UW-CAT-ACCUM` | Catastrophe accumulation at/above `0.80` | referral | `catastrophe-exposure-monitor` |
| `UW-THIRD-PARTY` | Adverse third-party risk flag present | referral | referral authority / financial-crime specialist |
| `UW-FIN-STRENGTH` | Financial-strength score below `50` | exception | underwriter |
| `UW-FRESHNESS` | Non-critical section past its freshness SLA | exception | underwriter |

Rules are applied **only to present data**; they surface findings for a human, never a
decision. The rule set is a triage/exception aid, not an autonomous accept/decline engine.

## Disposition logic (advisory only)

1. Any required section missing **or** any critical section stale → `needs-data`.
2. Else any rule finding present → `refer-to-underwriter` (list findings + routes).
3. Else (complete, fresh, no findings) → `ready-for-underwriter-review`.

None of these is an underwriting decision. `human_adjudication` stays `pending` with
`decision: null`; the accept/quote/decline/bind decision is recorded by the human underwriter
outside this skill.

## Hard boundaries (fail closed)

- No **bind / quote / decline / issue** and no final price or terms.
- No **autonomous underwriting decision** and no **system-of-record write**.
- No **unsupported claims** — every assertion cites its source; gaps are listed, not asserted.
- No **guessing** missing/stale-critical data to force a profile to complete.

## Compiled profile — required contents

Durable `workbench_id`; masked insured + occupancy + line of business; completeness map
(present/missing per section); source-freshness table with `as_of`, age, SLA, status; rule
findings with severity, message, evidence, and route; a draft `decision_rationale`
(recommendation framed for underwriter adjudication, applied rule IDs, routes, citations,
empty `unsupported_claims`); a pending `human_adjudication` block; and the standing note.
