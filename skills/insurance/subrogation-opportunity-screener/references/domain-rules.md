# Domain rules — Subrogation Opportunity Screening

- Recovery availability is available only with explicit waiver:false, prior status:none and source reference. Known waiver or managed/recovered/closed status is unavailable for a new referral. Missing/unsupported status is unknown and cannot fire recovery_not_waived.
- Any recorded not_evaluable condition forces Review, including unknown waiver/prior status, absent limitation/evidence context or incomplete financial inputs. No-Action is a bounded screening result, never a waiver or closure instruction.
- Scenario base = supplied paid + recovery deductible; apply supplied qualifying liability share and configured collectibility factor, then subtract configured cost. Defaults are 2500 floor, 50% share, 750 cost, insured/assets/unknown factors 1/.6/.3. These are explicit scenario assumptions, not collection probabilities or entitlements.
- Unknown paid/deductible/currency/source or responsible-party share yields null economics. Unknown must not become zero paid or zero deductible.
- `paid_to_date` is a required field that accepts null for unknown; `recovery_deductible` may be absent or null. Non-null amounts must be finite numeric values. Unknown amounts retain reviewable nonfinancial signals and force Review with null calculated economics.
- Supported core economics plus evidence and an open supplied limitation window can suggest Refer. Partial signals suggest Review. Deadline distance uses as_of; human counsel establishes the applicable controlling limitation period.
- Consider contrary liability, collectibility, anti-subrogation/made-whole questions and duplicate recovery before any specialist decision.

## Scope limit
Single-party scenario screening from supplied facts, not allocation of multiple tortfeasors, deductible recovery entitlement, recovery ledger reconciliation or legal doctrine application.
