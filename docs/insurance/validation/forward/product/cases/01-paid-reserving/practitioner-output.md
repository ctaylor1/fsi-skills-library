# Reserve Analysis Exhibit — DRAFT

## 1. Cover and valuation basis
Synthetic P&C property segment PROP-PAID; paid-loss basis; valuation 2026-09-18; USD thousands; dataset synthetic-reserve-v1.

## 2. Data sources and reconciliation
The triangle is synthetic triangle-v1: 2024 paid 100 at 12 months and 160 at 24 months; 2025 paid 250 at 12 months. Source: claims-datamart:triangle-v1, synthetic-v1. Paid totals reconcile to 410. No live claim-system reconciliation was supplied. Separate practitioner-context-v1 states case outstanding 80 and reviewer-provided ultimate 400 for 2025 on aligned basis/units; these are contextual inputs outside the native paid-triangle schema.

## 3. Development method and factors
Volume-weighted 12-to-24-month factor = 160 / 100 = 1.6. With the expressly supplied tail 1, CDFs are 1.6 at 12 months and 1.0 at 24 months. Only one observed link ratio supports this example. Source: triangle-v1 and synthetic-reserve-v1.

## 4. Indicated ultimate and reserve measures
| Origin | Paid | CDF | Indicated ultimate | Total unpaid | Source |
| --- | ---: | ---: | ---: | ---: | --- |
| 2024 | 160 | 1.0 | 160 | 0 | triangle-v1 |
| 2025 | 250 | 1.6 | 400 | 150 | triangle-v1 |
| Total | 410 | | 560 | 150 | triangle-v1 |

For 2025, method-indicated total unpaid is 400 - 250 = 150. Total unpaid includes case outstanding; it is not itself IBNR. The separate supplied case outstanding 80 would imply reported incurred 250 + 80 = 330 and a residual 400 - 330 = 70 on the expressly aligned contextual basis (practitioner-context-v1). The native paid-triangle engine does not consume case outstanding or independently validate that reconciliation; the 70 is a transparent supplemental calculation for actuarial review. The supplied ultimate 400 coincides with the mechanical indication; the engine makes no reserve selection.

## 5. Severity, frequency, and large-loss analysis
Severity and frequency are unavailable because no claim counts or exposure were supplied. Large-loss analysis is unavailable because no claim-level large-loss schedule was supplied. The native output's zero count/total and false large-loss flag must not be interpreted as evidence that no large losses exist.

## 6. Uncertainty and sensitivity
The native min/max link-ratio sensitivity is 560 to 560 in aggregate because there is only one observed factor. This zero width supplies no evidence of certainty and is not a statistical interval. The JSON key selected_ultimate represents the method-indicated aggregate 560, not a human reserve selection.

## 7. Assumptions and limitations
The supplied tail 1 assumes no further development after 24 months for this illustration. Origin, valuation, currency and basis alignment must be checked by the reviewing actuary. Aggregate triangles do not establish claim-level large-loss completeness. The paid output table uses total unpaid because the supplied template's generic IBNR heading would mislabel this paid-basis measure.

## 8. Actuarial review and approval
Preparing analyst, qualified actuary and independent peer reviewer sign-offs remain pending. No selection, booking or approval has been performed.

Draft reserving analysis for qualified actuarial review only; this skill computes method-indicated estimates from the supplied data, does not select or book carried reserves, does not issue or sign a Statement of Actuarial Opinion, and does not opine on reserve adequacy - a qualified actuary must review, select, and approve every figure before use.
