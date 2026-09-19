# Domain rules — separate investment-risk dimensions

Preserve willingness, loss capacity, liquidity, horizon, experience and constraints as six
independent records. Do not infer a classification or combine them into an ordinal risk score.
The taxonomy is a library review convention, not a regulatory questionnaire or suitability standard.

- **Willingness:** recorded client maximum-loss percentage, actual assessment and respondent IDs,
  method/version, and a sourced method-approval owner/reference. These are captured inputs;
  the software does not certify that the method or signature is authentic.
- **Loss capacity:** professionally assessed loss-capacity amount, investable assets, currency,
  assessment reference and basis. The basis should reflect the actual income, spending,
  liabilities and goals analysis; the package does not derive capacity from wealth alone.
- **Liquidity:** sourced available liquid resources and required amount within a stated number
  of months. No settlement or withdrawal recommendation is made.
- **Horizon:** the relevant goal ID and months; this is not substituted for liquidity.
- **Experience:** cited experience level per instrument type (none, limited, experienced).
- **Constraints:** individually cited restrictions or a sourced explicit none-identified record.

## Deterministic calculations
capacity_loss_pct = assessed_loss_capacity_amount / investable_assets * 100 (positive denominator).
willingness_loss_amount = investable_assets * maximum_loss_pct / 100.
liquidity_shortfall = max(required_amount - available_liquid_amount, 0).
Percentages round to six decimal places; amounts round to two. These diagnostic arithmetic outputs
are not an approved financial model, a loss forecast or a selected risk rating.

Flag willingness amount above assessed capacity; capacity above stated investable assets; inadequate
liquid resources; exposure scenario loss above willingness or capacity; lockup beyond goal horizon;
lockup beyond an underfunded liquidity need; missing/no experience in a proposed instrument; and
contradictory constraints. Do not compare different currencies or invent an FX rate. There are no
regulatory numerical thresholds: comparisons use the supplied documented facts.

Missing applicable data or any inconsistency produces findings and needs-data. Missing metrics stay
null; the output preserves every dimension. Complete consistent evidence becomes review-ready for a
human, with assigned_risk_rating=null and rating_decision=not-made. Conflicts require professional
reconciliation, not a mechanical minimum/maximum score rule.

## Regulatory orientation, reviewed 2026-09-16
- [SEC staff bulletin on care obligations](https://www.sec.gov/about/divisions-offices/division-trading-markets/broker-dealers/staff-bulletin-standards-conduct-broker-dealers-investment-advisers-care-obligations): orientation on considering the investor and reasonably available alternatives in the applicable capacity.
- [FINRA Rule 2111](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2111): read the applicability and institutional provisions, including Supplementary Material .08; do not stack Rule 2111 automatically onto recommendations subject to Reg BI.
- [DOL March 18, 2026 notice](https://www.dol.gov/newsroom/releases/ebsa/ebsa20260318?lang=en): the 2024 retirement fiduciary rule was vacated; the restored five-part test and applicable exemptions require current legal review.

Apply the current capacity-specific, human-owned procedure at deployment. The public references
support orientation; they neither approve this questionnaire nor substitute for professional review.
