# Domain rules — investment recommendation evidence

The check set is a **library evidence-availability taxonomy**, not a codification of every
legal obligation. The human-owned profile supplies capacity, jurisdiction, current basis,
retirement context and a policy-sourced disclosure deadline. It must identify owner, version,
reviewer, review date, rationale and sources. Brokerage may select `brokerage_reg_bi`,
`brokerage_2111` or `human_policy`; advisory may select `advisory_fiduciary` or `human_policy`;
private-bank/trust currently require `human_policy`. These are routes for expert review, not
legal determinations. Capacity and jurisdiction must match the engagement. A rollover always
requires a retirement applicability review.

| Check | Required item categories | Applicability |
| --- | --- | --- |
| customer_profile | investment_profile | Core |
| strategy_review | risks, features, costs | Core; may describe account/strategy rather than security |
| costs | cost_components, cost_comparison | Core |
| alternatives | available_alternatives, rationale | Core |
| customer_alignment | objective_alignment, risk_alignment, liquidity_alignment | Core |
| trading_series | series_review | Core; does not assume buy/sell/hold is exempt from review |
| disclosures | disclosure_delivery | Core; event and deadline selected by controlled profile |
| conflicts | conflict_inventory, treatment | Core; a documented none-identified inventory is evidence |
| supervision | review_routing | Core; evidence of the applicable firm process, not universal principal approval |
| rollover_comparison | plan_and_destination_comparison | Rollover action |
| retirement_applicability | current_legal_basis | Retirement context or rollover action |

Missing records become `missing`. Incomplete source metadata, reviewer record, item inventory,
subject linkage or dates become `incomplete`. Otherwise status is `documented`; this means the
record is present and internally consistent, not that its rationale is adequate. Only the two
conditional checks may become `not-applicable`, based on action/context. No caller-configurable
minimum-count or disable-check parameter exists. Every issue appears in `findings`; any finding
forces `needs-data`. Empty evidence cannot become `review-ready`.
Each supplied record must explicitly list `unresolved_issues`. Any listed substantive concern
makes the check incomplete, including a documented assessment or otherwise conditional check.
Issue provenance is retained in the result; source gaps generate additional findings. Empty lists
are a source-review representation, not machine proof of substantive sufficiency. Narrative text
is deliberately not classified with keyword/regex rules; the professional encodes its concerns.

Disclosure items require identity/version and a delivered date at/before the profile's stated
deadline. Other evidence records cannot be dated after the review. The script does not infer
that one arbitrary disclosure satisfies every product, account or jurisdiction requirement;
the source reviewer must list the relevant events and the applicability policy must be current.
The output validator recomputes the complete deterministic artifact, rather than accepting
counts, status, citations or claimed decisions supplied independently.

## Regulatory orientation, reviewed 2026-09-16
- [SEC staff bulletin on care obligations](https://www.sec.gov/about/divisions-offices/division-trading-markets/broker-dealers/staff-bulletin-standards-conduct-broker-dealers-investment-advisers-care-obligations): orientation on considering the investor and reasonably available alternatives in the applicable capacity.
- [FINRA Rule 2111](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2111): read the applicability and institutional provisions, including Supplementary Material .08; do not stack Rule 2111 automatically onto recommendations subject to Reg BI.
- [DOL March 18, 2026 notice](https://www.dol.gov/newsroom/releases/ebsa/ebsa20260318?lang=en): the 2024 retirement fiduciary rule was vacated; the restored five-part test and applicable exemptions require current legal review.

These public references orient source review. They do not authenticate the supplied profile,
replace current controlled procedures or establish legal sufficiency. Human legal/compliance
acceptance remains pending for deployment.
