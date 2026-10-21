# Bounded research method

The native engine demonstrates exactly one supplied reviewed period of at most 366 calendar days. The separately supplied accrual fraction does not permit compressing a multi-year horizon. It does not
infer contractual terms from filing prose or select a standard deal waterfall.
First reconcile the complete opening collateral inventory and all ranked notes
against their dated trustee report and governing terms. Keep historical actual
performance separate from the future scenario. Identify underwriting/vintage,
obligor, sector, geography, eligibility and concentration risks before interpreting
tranche support. Ineligible collateral remains in totals and is flagged; exclusion
would require a newly reviewed inventory and funding reconciliation.

For each asset with opening par B, period default fraction d, recovery fraction r,
scheduled principal S and prepay fraction p:

- Defaulted par = B × d; cash recovery = B × d × r; loss = default minus recovery.
- Surviving par after scheduled principal = B − defaulted par − S.
- Prepayment = surviving par × p; ending performing collateral = surviving par − prepayment.
- Principal cash = scheduled principal + prepayment + cash recovery.

Recovery is counted once as cash. Defaulted par is removed in full, never restored
by recovery. Fractions describe this period; no annualized default/prepay speed or
lagged recovery assumption is inferred. Interest collections and fixed fees are
separately supplied scenario estimates; the engine does not synthesize them from
collateral coupons. All assets are initially performing par for this profile;
prior default balances, impairment carryovers or initial undercollateralization
need a different reviewed engine.

Loss first consumes opening collateral par less total note principal, then writes
down notes from most junior to most senior. The reserve is excluded from this
principal-loss allocation. Coupon due uses opening note principal × fixed coupon
× supplied accrual year fraction, including notes written down within this period
because that is the exact supplied profile. Fee payment precedes note interest,
which follows seniority. Interest cash is used first; reserve draws then cover
fees and note interest. Principal cash cannot be used for interest in this profile.

The optional trigger is observed after collateral flows and note write-downs,
before distributions: ending performing collateral / remaining notes after loss.
Principal collections are deliberately excluded from that numerator. This supplied
profile is neither a universal OC definition nor a legal/regulatory coverage test.
Strictly below the supplied threshold diverts excess interest to senior-sequential
principal. Equality passes. The decision reconstructs the full collateral/default/
recovery/prepayment and note-loss comparison path with exact rational values from
`Fraction(str(original numeric value))`, then compares numerator against threshold
× denominator. No epsilon or rounded display ratio decides a breach. The output
records exact rational numerator/denominator and the float ratio is display only. With no note principal left, ratio is null and excess
cash is residual. Without a breach, excess interest is residual income. Principal
cash plus any diversion pays notes in senior order; excess principal is residual
cash. No reserve top-up, reserve release for principal, reinvestment, PIK,
reinstatement, pro-rata class, floating-rate reset or multi-period state is modeled.

Conservation independently checks opening collateral = ending collateral +
principal collections + collateral loss; collateral loss = equity cushion used +
note write-downs; principal collections + interest collections + opening reserve =
fees paid + interest paid + note principal paid + residual interest + residual
principal + closing reserve. Diverted interest is counted only through principal
payments, not a second cash use. Numerical tolerance is floating-point rounding,
not permission for a material unexplained plug.

Read the requested narrative assessments alongside the cashflow result. Examine
servicer continuity/advances/remittance controls, account-bank and hedge-provider
exposure, replacement triggers, collateral eligibility and representation breaches,
true sale/bankruptcy remoteness/security perfection, priority disputes, extension
and refinancing risk, secondary-market liquidity and source-document amendments.
These require appropriately qualified judgment and the actual terms; this method
preserves supplied assessments and missing topics without pretending to prove them.
Never infer an agency rating, legal enforceability, valuation, market access,
regulatory capital outcome, publication clearance or trade authority.
