# Domain Rules — suitability-reg-bi-reviewer

The obligation-check set and how it maps to a **review-disposition band**. Check parameters are
configuration (versioned, owned by the Wealth Management advisory & compliance function), not
hard-coded judgments, and are never relaxed for an individual. Orientation references: **SEC
Regulation Best Interest (Reg BI, 17 CFR 240.15l-1)** and **FINRA Rule 2111 (Suitability)**; the
firm's supervisory procedures and any configured jurisdiction pack take precedence. This is
**decision support**: the skill evidences obligations; a human supervisor/principal makes the
best-interest / suitability determination.

## Reg BI component obligations (retail customers)

1. **Disclosure Obligation** — deliver Form CRS and the Reg BI disclosure (capacity, fees/costs,
   conflicts, material limitations) and product-level disclosure, at or before the recommendation.
2. **Care Obligation** — three prongs: **reasonable-basis** (understand the product's risks,
   rewards, costs), **customer-specific** (aligned to *this* customer's investment profile), and
   **quantitative** (a series of recommendations is not excessive); reasonably-available
   **alternatives** must be considered and **cost** must be a factor (not dispositive).
3. **Conflict of Interest Obligation** — identify, disclose, and mitigate/eliminate conflicts
   (e.g., proprietary products, third-party compensation, sales incentives).
4. **Compliance Obligation** — supervisory procedures and documentation; the recommendation is
   routed for principal review.

For **institutional / non-retail** accounts, the retail disclosure checks are `not_applicable`
and the **FINRA Rule 2111** suitability path applies (reasonable-basis, customer-specific,
quantitative).

## Check taxonomy

| Check | Obligation | Satisfied when | Blocking |
| ----- | ---------- | -------------- | -------- |
| `disclosure_form_crs` | Disclosure | Form CRS delivered at/before the recommendation (retail) | yes |
| `disclosure_reg_bi` | Disclosure | Reg BI disclosure delivered (retail) | yes |
| `disclosure_product` | Disclosure | Product-level disclosure (prospectus/fee) delivered | no |
| `care_profile_complete` | Care | All required investment-profile fields present | yes |
| `care_reasonable_basis` | Care | Product-level due diligence documented | no |
| `care_cost_considered` | Care | Costs captured **and** a cost comparison documented | no |
| `care_alternatives_considered` | Care | ≥ `min_alternatives` alternatives documented with rationale | no |
| `care_rollover_comparison` | Care | (Rollover only) plan-vs-IRA comparison documented | no |
| `care_quantitative_series` | Care | (Switch/exchange only) rationale addressing excessive trading | no |
| `conflict_disclosed` | Conflict | Every identified conflict marked disclosed | no |
| `conflict_proprietary_comp` | Conflict | (Proprietary / third-party comp) conflict disclosed **and** mitigated | no |
| `supervision_routed` | Compliance | Recommendation routed for principal review (routed, **not** approved) | no |

Each check returns `satisfied` / `gap` / `not_evaluable` / `not_applicable`. Satisfied checks
carry cited evidence; gaps and not-evaluable items state exactly what is missing. Checks are
independent findings — there is no opaque composite "suitability score".

## Disposition mapping (deterministic, documented)

| Band | Rule |
| ---- | ---- |
| **Insufficient-evidence** | Any **blocking** obligation is `not_evaluable` (a required evidence category is absent). Fail closed. |
| **Gaps-identified** | No blocking gap, but ≥ 1 check is a `gap`. |
| **Evidence-complete** | Every applicable check is `satisfied`. Evidence is ready for the principal's determination. |

`not_applicable` checks are ignored in the mapping. The disposition is a **review-readiness
triage for a human**. **Evidence-complete is not an approval and not a best-interest
determination** — it means the record is complete enough for a supervisor/principal to
adjudicate.

## Hard boundaries (fail closed)

- Never state or imply the recommendation **is suitable**, **is in the customer's best interest**,
  or **meets/satisfies the best-interest standard** — attribute the determination to the human.
- Never **approve, clear, reject, close, or file**; never place a trade or sign off.
- Never provide the skill's own **personalized investment advice**.
- Never relax a required disclosure or the profile-completeness bar for an individual; use the
  versioned config and the rule.

## Open-item prompts (always include when not Evidence-complete)

For each gap/not-evaluable check: name the missing evidence (e.g., "document reasonably-available
alternatives and their costs", "attach the plan-vs-IRA rollover comparison", "confirm Form CRS
delivery date", "disclose and mitigate the proprietary-product conflict"), so the advisor/compliance
analyst can remediate before the principal adjudicates.
