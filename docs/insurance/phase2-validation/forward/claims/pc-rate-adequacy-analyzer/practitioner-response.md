# CP-NY-2025 — internal draft rate indication

The supplied single-cohort method produces an indicated increase of approximately **8.0330%**, from **$1,377.343750** adjusted premium per location-year to **$1,487.986111** indicated premium per location-year. This is a reproduced indication using the supplied assumptions; no rate has been selected or filed.

Prepared for fictional Harbor Mutual actuarial pricing by an internal insurer analyst; US-NY commercial property; review date 18 September 2026; synthetic reviewed profile version 1. EXPERIENCE covers 1 January–31 December 2025, with earned premium $4,875,000, reviewed ultimate non-catastrophe loss plus LAE $2,940,000, and 3,900 earned location-years. PRICING-MEMO supplies the prospective assumptions and explicit alignment/no-double-counting review.

| Bridge | Calculation | Result per location-year |
|---|---|---:|
| Adjusted premium | 4,875,000 × 1.075 × 1.025 ÷ 3,900 | $1,377.343750 |
| Prospective experience loss+LAE | 2,940,000 × 1.09 ÷ 3,900 | $821.692308 |
| Credibility blend | 65% × unrounded experience + 35% × 875 | $840.350000 |
| Fixed expense, catastrophe, reinsurance net cost | 128 + 62 + 41 | $231.000000 |
| Indicated premium | (840.35 + 231) ÷ (1 − 0.235 − 0.045) | $1,487.986111 |
| Indicated change | Unrounded indicated premium ÷ 1,377.343750 − 1 | 8.0330% |

Independent decimal arithmetic from the raw source numbers agrees with every native amount at the helper's six-decimal presentation precision. The output ratio is 0.080330; conversion to percentage multiplies that ratio by 100. No rounded intermediate was fed back into the computation.

The packet is complete and evaluable for this bounded arithmetic and marked `ready-for-review`. The pricing actuary retains responsibility for suitability of development, trend, credibility, catastrophe/reinsurance treatment, expense selections, coverage/mix changes, sensitivity and applicable filing requirements. The reviewed assumptions are supplied assertions, not independently authenticated evidence or proof of adequacy.

Sources: synthetic EXPERIENCE, PRICING-MEMO and REVIEW-PROFILE, all version 1, retained in `raw_sources/`. Human professional review remains pending. No individual quote, rate selection, approval or filing occurred.
