# Independent private-fund and institutional forward review

Date: 2026-10-04. Reviewer: the agent that authored sustainability, tokenized-fund and jurisdiction-profile workflows, not these three target methods.

The exercise constructs new raw synthetic source records directly from the documented contracts. It does not use target package fixtures or goldens as expected results. It runs actual native calculation and detached-output validation scripts. Source truth, professional acceptance and production integration remain untested.

## Initial observations and repairs

The initial suite passed 12 of 15 cases. Complete initial requests, outputs, report and runner text remain in `initial/`.

1. A proposed subscription draw after the supplied agreement expires, but before facility maturity, produced no issue. The financing method now retains an explicit agreement-effectivity issue for the proposed draw. Two regressions cover expiry and its inclusive boundary.
2. An LP-led sale containing a new continuation-fund commitment silently discarded that field and reported zero new commitment. The restructuring method now rejects GP-only roll/capital fields in LP-led mode. A regression covers each such unsupported field.
3. A GP continuation claimed unchanged economics while imposing a new uncalled commitment without an issue. The existing status-quo comparison now also retains transaction fees, upfront capital and new commitments. Two regressions cover those changes and the unchanged baseline.

No institutional calculation defect was observed. No institutional file was changed. Repairs were limited to the financing/restructuring native methods, their focused tests and method/schema explanations.

## Final verification

All 15 fresh scenarios now pass. Each emitted output passes detached-original reconstruction. Financing has 14 package unit tests and restructuring has 15; all pass. Isolated declared commands pass for financing, restructuring and institutional solutions, including the original institutional interface.

Independent numeric expectations include:

- Subscription and NAV examples: pre-cap credit 120, borrowing base 100, proposed usage 50, draw headroom 50, debt/NAV 0.25 and leverage headroom 30. Period interest 4, undrawn fee 0.55 and upfront fee 1 total 5.55. A sub-display-precision covenant breach remains a breach; incomplete collateral withholds dependent availability.
- LP sale: adjusted whole-interest price 190, cash 90 and retained reference NAV 105. GP continuation: cash 66, rolled capital 109, fees 6, crystallized carry 9 and future commitment 30. No option is selected; future actual-event claims fail.
- Institutional scenario: liability PV 194, parallel-down PV 197, parallel-up PV 191, effective duration 1.546391752577 and convexity 0. Base cash headroom is 10 then 20; delayed real-asset downside produces 0 then 5. Stale valuations and principal exceeding stressed liquidatable value withhold dependent measures; duplicate principal and mismatched dated factors fail.

`report.json` records the latest run. Re-run with `python3 -B docs/asset-management/phase4-validation/review-private-institutional/evaluate.py`.

## Practitioner assessment

The methods separate source-grounded financial arithmetic from lender certification, fairness valuation, actuarial measurement and execution authority. The schemas expose pricing conventions, lender concentration method, dated liabilities, source versions and unresolved assumptions. Per-mode boundaries remain important: retained LP reference NAV is not continuation capital; collateral NAV is not uncalled commitments; future projected inflows are not current cash. The resulting drafts are useful for an owner-reviewed evidence packet but do not establish legal enforceability, eligibility, source completeness or authority to act.
