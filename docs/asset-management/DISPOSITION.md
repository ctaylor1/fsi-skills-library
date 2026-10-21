# Original package disposition

Every original AM package has one canonical owner. Legacy names and old paths resolve through `tools/resolve_skill.py`; aliases are metadata, not duplicate workflow packages. Merged aliases return a required mode. Wrap the old native input as `{"mode": "…", "input": {...}}` for the canonical merged entrypoint.

| Original package | Canonical owner / package | Disposition | Mode |
|---|---|---|---|
| due-diligence-questionnaire-responder | Asset Management / [institutional-proposal-responder](../../skills/asset-management/institutional-proposal-responder/SKILL.md) | rename | — |
| fund-commentary-drafter | Asset Management / [investment-commentary-builder](../../skills/asset-management/investment-commentary-builder/SKILL.md) | rename | — |
| fund-fact-sheet-builder | Asset Management / [fund-fact-sheet-builder](../../skills/asset-management/fund-fact-sheet-builder/SKILL.md) | revise | — |
| investment-thesis-monitor | Asset Management / [investment-thesis-monitor](../../skills/asset-management/investment-thesis-monitor/SKILL.md) | revise | — |
| investment-committee-memo-builder | Asset Management / [investment-committee-memo-builder](../../skills/asset-management/investment-committee-memo-builder/SKILL.md) | revise | — |
| investment-manager-due-diligence-reviewer | Asset Management / [investment-manager-due-diligence-reviewer](../../skills/asset-management/investment-manager-due-diligence-reviewer/SKILL.md) | revise | — |
| mandate-compliance-monitor | Asset Management / [investment-mandate-reviewer](../../skills/asset-management/investment-mandate-reviewer/SKILL.md) | rename | — |
| portfolio-drift-monitor | Asset Management / [portfolio-characteristics-change-monitor](../../skills/asset-management/portfolio-characteristics-change-monitor/SKILL.md) | rename | — |
| hedge-analysis-support-packet | Asset Management / [portfolio-hedge-reviewer](../../skills/asset-management/portfolio-hedge-reviewer/SKILL.md) | rename | — |
| portfolio-exposure-analyzer | Asset Management / [portfolio-exposure-analyzer](../../skills/asset-management/portfolio-exposure-analyzer/SKILL.md) | revise | — |
| portfolio-risk-contribution-packet | Asset Management / [portfolio-risk-contribution-analyzer](../../skills/asset-management/portfolio-risk-contribution-analyzer/SKILL.md) | rename | — |
| portfolio-stress-test-runner | Asset Management / [portfolio-stress-test-runner](../../skills/asset-management/portfolio-stress-test-runner/SKILL.md) | revise | — |
| liquidity-stress-analyzer | Asset Management / [fund-liquidity-assessor](../../skills/asset-management/fund-liquidity-assessor/SKILL.md) | rename | — |
| portfolio-cashflow-liquidity-forecaster | Asset Management / [portfolio-cashflow-forecaster](../../skills/asset-management/portfolio-cashflow-forecaster/SKILL.md) | rename | — |
| counterparty-exposure-monitor | Asset Management / [counterparty-exposure-monitor](../../skills/asset-management/counterparty-exposure-monitor/SKILL.md) | revise | — |
| performance-attribution-builder | Asset Management / [portfolio-performance-attributor](../../skills/asset-management/portfolio-performance-attributor/SKILL.md) | rename | — |
| composite-account-membership-checker | Asset Management / [performance-composite-reviewer](../../skills/asset-management/performance-composite-reviewer/SKILL.md) | rename | — |
| valuation-exception-packet | Asset Management / [fund-valuation-oversight-reviewer](../../skills/asset-management/fund-valuation-oversight-reviewer/SKILL.md) | rename | — |
| nav-preparation-tie-out | Asset Management / [fund-nav-control-reviewer](../../skills/asset-management/fund-nav-control-reviewer/SKILL.md) | rename | — |
| position-cash-reconciliation-assistant | Asset Management / [investment-book-reconciler](../../skills/asset-management/investment-book-reconciler/SKILL.md) | rename | — |
| proxy-meeting-evidence-packet | Asset Management / [proxy-voting-reviewer](../../skills/asset-management/proxy-voting-reviewer/SKILL.md) | merge | evidence |
| voting-policy-consistency-checker | Asset Management / [proxy-voting-reviewer](../../skills/asset-management/proxy-voting-reviewer/SKILL.md) | merge | policy |
| engagement-history-brief | Asset Management / [issuer-engagement-reviewer](../../skills/asset-management/issuer-engagement-reviewer/SKILL.md) | rename | — |
| investment-data-quality-exception-detector | Asset Management / [investment-data-quality-reviewer](../../skills/asset-management/investment-data-quality-reviewer/SKILL.md) | merge | data_quality |
| investment-vendor-feed-reconciler | Asset Management / [investment-data-quality-reviewer](../../skills/asset-management/investment-data-quality-reviewer/SKILL.md) | merge | vendor_feed |
| security-master-enricher | Asset Management / [investment-reference-data-reviewer](../../skills/asset-management/investment-reference-data-reviewer/SKILL.md) | rename | — |
| investment-source-ingester | Data, AI & Model Governance / [research-source-indexer](../../skills/data-ai-model-governance/research-source-indexer/SKILL.md) | move-and-rename | — |
| holdings-transaction-normalizer | Data, AI & Model Governance / [investment-record-normalizer](../../skills/data-ai-model-governance/investment-record-normalizer/SKILL.md) | move-and-rename | — |
| credit-terms-covenant-extractor | Investment Research / [credit-document-terms-reviewer](../../skills/investment-research/credit-document-terms-reviewer/SKILL.md) | move-and-rename | — |
| credit-surveillance-packet | Investment Research / [issuer-credit-surveillance-reviewer](../../skills/investment-research/issuer-credit-surveillance-reviewer/SKILL.md) | move-and-rename | — |

The original category migration recorded 25 former Investment Banking & Research packages: 16 moved to Investment Research and nine transaction-specific packages moved to Investment Banking. Two credit capabilities moved from AM made 18 Investment Research packages at that checkpoint. IR Phase 1 subsequently renamed the issuer capital-structure mapper and moved generic document comparison to Data, AI & Model Governance; this registry records the terminal owners. See [current IR support](../investment-research/support-matrix.md) for installed and planned methods.
