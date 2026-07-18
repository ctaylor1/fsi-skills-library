# Next-Best-Action Package (DRAFT) — {{customer_ref}}

> Draft-only. Nothing in this package has been sent to the customer or written to a system
> of record. A human agent must review, record the required approvals, and read the
> applicable disclosures before acting. Package template: `nba-package-v1`.

## Customer Context Snapshot
Segment, tenure, products, open complaint status, and the interaction/context sources this
package is grounded in. Cite CRM / transcript / case references with dates.

## Recommended Next Best Actions
Ranked, eligibility-gated, and cited. One row per action.

| Rank | Action ID | Type | Recommendation | Why (rationale) | Eligibility basis | Citations | Required disclosures | Specialist referral? |
| ---- | --------- | ---- | -------------- | --------------- | ----------------- | --------- | -------------------- | -------------------- |
| 1 | … | education / service / retention / cross-sell / referral | … | … | … | source refs | … | none / licensed specialist |

Every recommended action must (a) come from the approved action catalog, (b) carry at least
one citation, and (c) be non-binding. No guarantees, no approvals, no personalized
investment/credit/claim decisions.

## Consent & Eligibility Checks
Do-not-contact status, vulnerability flag, and per-channel marketing consent. Any outbound
action requires the matching channel consent and no do-not-contact flag.

## Excluded or Routed to Specialist
Actions that were **not** recommended, with reason:
- Ineligible (product / tenure / signal not met).
- Consent-gated (channel consent missing or do-not-contact set).
- Vulnerability-suppressed (retention/cross-sell not offered → route to specialist support).
- Prohibited binding decision (credit / claim / investment/suitability) → route to a
  licensed specialist. NBA refers; it never decides.

## Required Disclosures
The union of disclosures attached to the recommended actions. The agent must read the
applicable disclosures verbatim before offering the action.

## Approvals & Handling
- Required approvals (record each with approver + timestamp): servicing supervisor / QA
  reviewer before external delivery; licensed specialist sign-off before any referral is
  acted on.
- Approval status: `pending` until recorded. External delivery stays disabled until status
  is `approved`.

## Sources
All context references and action citations used, with dates/versions.

---
Standing note: Draft recommendations only. No action here is a binding credit, claims, or
investment decision; nothing has been delivered to the customer or written to any system of
record.
