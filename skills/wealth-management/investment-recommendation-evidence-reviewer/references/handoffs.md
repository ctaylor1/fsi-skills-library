# Handoffs — recommendation evidence

| Route | When | Artifact |
| --- | --- | --- |
| `investment-risk-profile-reviewer` | Risk willingness/capacity or constraints need clarification | Household, profile and unresolved dimensions |
| `portfolio-proposal-comparator` | Economic comparison of supplied alternatives is needed | Recommendation and cited proposal snapshots |
| `portfolio-rebalancing-assistant` | Authorized professional requests implementation planning | Selected target, evidence artifact and unresolved findings; never an approval token |
| `conflicts-of-interest-reviewer` | Conflict inventory or mitigation requires deeper review | Conflict sources and findings |
| `senior-investor-protection-screener` | Vulnerability or exploitation concern appears | Concern evidence, restricted to necessary identifiers |
| `regulatory-exam-response-packager` | An authorized evidence collection requests the review | Complete artifact_id/input_hash and source map |
| Authorized advisor/compliance/legal professional | Determine applicability, substantive sufficiency or required approvals | Full review artifact with all findings |

Upstream client-review and advisor follow-up workflows can supply a recommendation packet.
The former name suitability-reg-bi-reviewer is a migration alias, not a second skill.
Reuse the existing artifact rather than independently repeating a comparison or profile assessment.
No route authorizes external delivery or grants an investment/legal decision.

## Carry unresolved upstream concerns
Read and verify the upstream artifact's household, engagement, date, `artifact_id`, `input_hash`,
source registry and complete findings before constructing this request. Merge its relevant sources
without silently overwriting conflicting source IDs. Map every unresolved concern material to the
recommendation to one or more evidence records; retain its original code/message, source IDs and
`upstream_artifact: {skill, artifact_id, input_hash}` under `unresolved_issues`, with
`origin: upstream-artifact`. The receiver supplies source IDs from the cited upstream facts when
an upstream finding has no item-level IDs. Do not claim the finding has resolved by rewording it.

| Upstream concern | Receiving check(s) |
| --- | --- |
| Risk willingness, loss-capacity, liquidity, horizon, experience or constraints conflict | customer_profile and customer_alignment; strategy_review where product/strategy exposure is affected |
| Unresolved comparison cost, service-value or alternative rationale | costs and alternatives; customer_alignment where affected |
| Unresolved conflict inventory or treatment | conflicts |
| Unconfirmed retirement/rollover applicability or comparison | retirement_applicability and rollover_comparison |
| Incomplete professional review or escalation routing | supervision |

Record other concerns under the relevant check instead of dropping them for lack of a named route.
Keep nonempty lists even if the item metadata is documented. When review-ready is sought after
resolution, obtain sourced resolution and new reviewer/date records and re-review the input;
the package does not close an upstream case. An empty list means the source reviewer found no
remaining material issue after that review. Scripts preserve explicit issues; they do not infer
issues from prose, retrieve/authenticate upstream artifacts or prove cross-artifact completeness.
