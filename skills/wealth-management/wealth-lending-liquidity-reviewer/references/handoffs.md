# Handoffs

| Target | Distinct job and evidence to carry |
| --- | --- |
| `household-wealth-data-reconciler` | Resolve ownership, duplicate assets, debts, held-away balances and valuation breaks before treating available resources as reliable |
| `household-financial-planning-assistant` | Reconcile the household cash-flow/debt/goal budget and protected reserves with the proposed facility service |
| `tax-aware-investment-reviewer` | Review supplied liquidation tax lots and tax assumptions; do not infer tax results in the lending model |
| `bank-product-feature-comparator` | Compare current approved banking terms and exclusions without selecting a product |
| `investment-recommendation-evidence-reviewer` | Review applicable recommendation evidence, alternatives and economic conflicts under the correct professional capacity |
| `wealth-account-service-packager` | Prepare separately requested servicing evidence; a financing comparison never grants authority to move funds |
| `client-review-preparer` | Include reviewed scenario tradeoffs, unanswered questions and source lineage in the client meeting pack |

Carry household/request IDs, capacity, as-of date, source registry, artifact ID/hash, terms, calculations and every unresolved finding. Target schemas differ: map P2 `upstream_issues` into the target's documented issue field and validate the target independently. Map P1 tax `unresolved_issues` into attributed status-bearing P2 issue records on return; do not supply an unmapped alias. A ready routing artifact or completed calculation does not close an upstream ownership, tax or funding concern. No automatic pipeline or external action is implemented.
