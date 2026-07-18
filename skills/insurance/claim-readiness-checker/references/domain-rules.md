# Domain Rules — claim-readiness-checker

Explainable readiness **checks** and how their **gap profile** maps to a readiness status
band. Required-item catalogs, deadline dates, and thresholds are **configuration**
(versioned, owned by underwriting/claims standards, keyed by claim type and jurisdiction),
not hard-coded judgments, and are never tuned to an individual claim. The controlling policy
and the firm's claims-handling standard take precedence over any default here.

## Check taxonomy

| Check | Gap fires when | Evidence attached |
| ----- | -------------- | ----------------- |
| `required_documents_present` | A required document type for the claim type is not present (status `missing` / `illegible` / `pending` / absent) | Present required docs (cited); missing types listed as gaps |
| `required_forms_valid` | A required form is absent, **unsigned**, or on a **non-accepted version** | Valid forms (cited); each invalid/absent form as a gap |
| `required_fields_complete` | A required claim field (claimant, loss description, amount, …) is missing/empty | Missing field names as gaps |
| `chronology_consistent` | `date_of_loss` outside the policy period, OR loss after reported, OR reported after prepared | The conflicting dates as gaps |
| `deadlines_status` | A **hard** deadline is past `as_of` (missed), or any deadline is due within the `at_risk_days` window | Per-deadline `days_remaining` table (cited) |

Each gap records `blocking` (true/false). **Blocking** gaps: a missing/invalid *required*
(blocking) document or form, any missing required field, any chronology conflict, and any
missed **hard** deadline. **Non-blocking** gaps: missing recommended documents, at-risk (not
yet passed) deadlines, and passed **soft** deadlines. Checks that cannot run for lack of data
(no policy dates, no deadlines, no timestamps) are reported as `not_evaluable`, not as passes.

## Readiness mapping (deterministic, documented)

| Status | Rule |
| ------ | ---- |
| **Ready** | No gaps of any kind |
| **Ready with minor gaps** | One or more gaps, but **none blocking** |
| **Not ready** | **Any** blocking gap |

Readiness is a **completeness/timeliness triage suggestion for a human**. It is not a
coverage, eligibility, settlement, or fraud determination and it never adjudicates,
approves, denies, prices, or pays the claim.

## Hard boundaries (fail closed)

- Never state or imply a loss **is / is not covered**, that an **exclusion applies**, or that
  the claim is **eligible / ineligible** — coverage is the adjuster's/insurer's decision.
- Never **approve, deny, close, settle, price, or pay** a claim, or recommend those as
  decisions; never state a **settlement/payout amount** or reserve.
- Never assert a claim is **fraudulent**; potential-fraud handling is a separate human-led
  referral.
- Never tune required-item sets, deadline dates, or thresholds to the individual claim; use
  only the versioned config catalog.

## Considerations (always include when any gap exists)

Readiness ≠ coverage; a coverage/eligibility/settlement determination is the adjuster's;
confirm the policy is in force and check endorsements/limits/deductibles against the system
of record; obtain or re-request missing/illegible required items before submission; verify
each deadline against the controlling policy and jurisdiction rather than this list alone.
