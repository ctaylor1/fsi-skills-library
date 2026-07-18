# Adjacent-Skill Handoffs — customer-onboarding-document-checker

This skill produces a cited **completeness gap report** with a durable `checklist_id` and a
deterministic **readiness status**, then stops. It does not verify identity, screen for
financial crime, adjudicate a match, waive a requirement, approve onboarding, or open an
account.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `kyc-customer-due-diligence-screener` | Documents are complete; substantive identity/risk/PEP/sanctions screening is needed | `checklist_id` + applicant record |
| `enhanced-due-diligence-packager` | Higher-risk customer needs source-of-funds/wealth, ownership, and adverse-media evidence assembled | `checklist_id` + package |
| `beneficial-ownership-verifier` | Business customer — legal/control ownership must be mapped and reconciled to evidence | `checklist_id` + ownership docs |
| `sanctions-match-adjudicator` | An open `watchlist_potential_match` exception needs authorized adjudication | the open exception + evidence |
| `customer-risk-rating-reviewer` | The customer risk rating must be (re)calculated under approved methodology | `checklist_id` + applicant record |
| `credit-application-packager` / `loan-package-completeness-checker` | The package is actually a lending application/closing package, not deposit onboarding | package + product |

## Human / operations handoffs (no catalog skill performs these)

- **Onboarding approval / account opening** and **document-waiver** decisions belong to the
  authorized onboarding specialist or operations approver — this skill only reports gaps.
- **KYC/CIP identity-verification determination** belongs to the BSA/AML compliance officer
  and the CDD/sanctions screening skills above; this skill never asserts identity is
  verified.

## Upstream (may call this skill)

`omnichannel-case-orchestrator` and branch/operations service skills may request a
completeness check before routing a package for approval. A scheduled monitor is **not**
used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes **completeness findings only**; it must not verify identity, screen or
  adjudicate financial-crime risk, decide readiness beyond the deterministic mapping, waive
  a requirement, or take an account action — those belong to the human and the downstream
  skills.
- Downstream skills reuse the `checklist_id` and cited evidence rather than re-inventorying
  the documents.
