# Discovery handoffs

Every handoff carries household ID, request/artifact IDs, source registry and unresolved findings.
No handoff is auto-executed. Preserve source versions and never rerun a downstream decision here.

| Job | Route | Boundary |
| --- | --- | --- |
| Account/engagement onboarding package | `wealth-onboarding-packager` | Separately checks required documents, authority and readiness; discovery is not KYC. |
| Reconcile household accounts/assets/liabilities | `household-wealth-data-reconciler` | Discovery records statements; reconciliation resolves data evidence and coverage. |
| Review investment risk profile | `investment-risk-profile-reviewer` | Separate evidence and conflict analysis; no discovery-derived risk score. |
| Recommendation evidence review | `investment-recommendation-evidence-reviewer` | Only after a recommendation workflow exists; intake creates none. |
| Existing household meeting preparation | `client-review-preparer` | Consumes reviewed context and current investment/plan evidence. |
| Post-interview communication/actions | `advisor-follow-up-assistant` | Uses actual documented interview outcomes and communication review. |

KYC/CDD, beneficial-ownership, and sanctions work is shared with compliance-financial-crime.
Legal, tax, estate, and insurance determinations go to the firm's authorized specialists.
The `wealth-management-router` selects an appropriate job when the request spans these boundaries.
