# Independent payments Phase 2 routing forward pass

Evaluated the 18 original Section 8 requests by independently selecting explicit intents from current skill instructions and the route registry. Did not read evals/evals.json, test_routing.py, or prior evaluation artifacts. No repository files were changed.

All 18 router commands and all 18 native output validations exited 0. Native results: 9 routed and 9 capability-gap. This establishes structured routing consistency only. It does not show target task quality, legal applicability, professional acceptance or production readiness.

Source hashes were unchanged across execution. End-of-adjudication source changes: 3. Full requests, selected intents and rationales, native inputs/outputs, exact commands, stderr, statuses, installed inventory and source hashes are retained beside this report.

## Findings

### F01 — Bank-only rail route does not disclose the requested card comparison gap

The request explicitly names FedNow, RTP, ACH and card rails. The native output routes to bank-payment-workflow-designer, supports only regulatory applicability and economics, and gives no card-specific limitation. Its native profile registry contains bank rails only.

An agent could silently drop the card leg while treating the complete comparison as routed. Lead selection itself is reasonable for the bank rails.

Suggested resolution: Retain the bank lead for the bank-leg comparison, explicitly mark card comparison as separately scoped or unsupported, and add conditional card/merchant acceptance support after the participant and card product are known.

Evidence: skills/payments/payments-router/references/routes.json:120, skills/payments/bank-payment-workflow-designer/SKILL.md:30, skills/payments/bank-payment-workflow-designer/references/rail-profiles.json, /tmp/payments-phase2-routing-forward/case-02/native-output.json

### F02 — Orchestration strategy silently selects a merchant lead for an unknown participant

The original request does not specify merchant, issuer, bank or the orchestration layer. The selected orchestration-strategy intent unconditionally returns merchant-acceptance-strategy-designer with platform architecture as support.

Merchant acceptance/PSP routing and bank/issuer hub orchestration can require different accountable leads. The agent should not treat the merchant assignment as final from this request alone.

Suggested resolution: Ask for participant and orchestration layer, or emit conditional merchant-strategy versus platform-architecture ownership; retain both as alternatives until clarified.

Evidence: skills/payments/payments-router/references/routes.json:247, skills/payments/merchant-acceptance-strategy-designer/SKILL.md:33, skills/payments/payment-platform-architecture-reviewer/SKILL.md:27, /tmp/payments-phase2-routing-forward/case-14/native-output.json

### F03 — The structured missing-context list does not carry evident scope unknowns

All 18 native outputs report missing_context=[] even though no jurisdiction was supplied and most participants are unknown. Some outputs list generic required_inputs and all require target validation.

This does not establish target readiness or infer a supported region, but consumers could misread the empty list as complete context. The independent practitioner judgments retain the omitted scope explicitly.

Suggested resolution: Populate scope-relevant missing_context or distinguish route-selection context from target-input prerequisites; do not invent a region/role to satisfy a target.

Evidence: /tmp/payments-phase2-routing-forward/results.json, skills/payments/payments-router/SKILL.md:27

## Request-level judgments

| # | Original request | Selected intent | Native result | Practitioner judgment |
| --- | --- | --- | --- | --- |
| 1 | Analyze why a merchant's card authorization rate is declining. | authorization-decline | Gap: payment-acceptance-performance-analyzer | Correctly retained a portfolio-performance capability gap. Existing single-payment and error-log tools are support evidence only. |
| 2 | Compare FedNow, RTP, ACH, and card rails for a specific use case. | rail-comparison | bank-payment-workflow-designer | Partial route: bank workflow is a reasonable lead, but card rails are part of the request and absent from its native profiles and the route's support/limitations. Finding F01. |
| 3 | Design an acquiring strategy for a global e-commerce merchant. | global-acquiring | merchant-acceptance-strategy-designer | Reasonable merchant-strategy lead, bounded to currently supported regions. 'Global' still needs country decomposition; no national applicability or global completeness is established. |
| 4 | Model the economics of adding pay-by-bank. | pay-by-bank-economics | payment-economics-modeler | Appropriate prospective-economics lead. Participant perspective, method and baseline assumptions remain missing; no scenario result was attempted. |
| 5 | Analyze interchange and payment acceptance costs. | merchant-cost | merchant-payment-cost-analyzer | Reasonable observed-merchant-cost candidate, conditional on clarifying perspective and incurred versus prospective analysis. The wording alone does not establish either. |
| 6 | Design an embedded-payments strategy for a vertical SaaS company. | vertical-saas-payments | Gap: platform-payment-flow-designer | Correct platform-flow capability gap. Existing commercial, regulatory, economics and architecture packages may contribute bounded artifacts without completing embedded-platform strategy. |
| 7 | Investigate a spike in chargebacks. | chargeback-spike | Gap: payment-acceptance-performance-analyzer | Correct aggregate chargeback-performance gap. No unsupported conversion into single-case representment or issuer error resolution. |
| 8 | Design a fraud strategy for real-time payments. | instant-fraud-strategy | Gap: payment-fraud-control-evaluator | Correct fraud-control-strategy gap. Offline event monitoring and one-predicate backtesting remain supporting evidence, not a complete or inline fraud strategy. |
| 9 | Explain the lifecycle of a card authorization through clearing and settlement. | card-lifecycle | card-lifecycle-operations-assistant | Appropriate card-lifecycle lead. Explain concepts without fabricating an actual payment trace; listed servicing support must not be invoked unless a servicing request appears. |
| 10 | Assess whether a bank should modernize its payment hub. | hub-modernization | payment-platform-architecture-reviewer | Appropriate foundational architecture lead. Modernization business case and later-phase performance/incident/resilience acceptance remain separately scoped. |
| 11 | Compare issuer processors. | issuer-processor-comparison | payment-provider-evaluator | Appropriate provider-diligence lead with optional card-program requirements support. Actual provider evidence, program requirements and territory are still unknown. |
| 12 | Assess cross-border payment options. | cross-border-options | Gap: cross-border-payment-designer | Correct end-to-end cross-border-design gap. Installed domestic-rail profiles or legal orientation do not silently supply corridor, FX or foreign-access capability. |
| 13 | Develop a merchant acquiring architecture. | acquiring-architecture | payment-platform-architecture-reviewer | Appropriate core acquiring architecture lead with commercial requirements support. Actual operator role and territories remain unknown; later-phase resilience is not implied. |
| 14 | Design a payment orchestration strategy. | orchestration-strategy | merchant-acceptance-strategy-designer | Participant ambiguity remains unresolved. Native routing selects merchant acceptance despite no merchant context; platform architecture is also an installed plausible lead. Finding F02. |
| 15 | Analyze a payments company or competitor. | payments-company | Gap: payments-business-model-analyzer | Correct payments-business-model specialization gap. Installed generic company-profile and market-landscape skills can supply research artifacts, not a complete payments-specific competitor analysis. |
| 16 | Assess the opportunity for stablecoin settlement. | stablecoin-opportunity | Gap: stablecoin-settlement-assessor | Correct opportunity-assessment gap. Supplied stablecoin control review is not adoption economics, redemption-access diligence or legal clearance. |
| 17 | Develop an AI strategy for payment operations. | ai-operations-strategy | Gap: payment-operations-improvement-analyzer | Correct payment-operations-strategy gap. Generic AI intake/risk/benchmark packages can support governance but do not provide the missing payments operating-model strategy. |
| 18 | Design payment capabilities for AI-agent-driven commerce. | agent-commerce | Gap: payment-initiation-control-reviewer | Correct advanced agent-commerce gap while acknowledging installed initiation-control core. The native limitation preserves the distinction; no protocol or advanced mandate capability was invented. |

## Interpretation boundaries

- No jurisdiction was supplied or silently converted into US/euro-area/UK clearance. Unknown roles and required target evidence remain in per-case adjudications.
- Support packages are conditional evidence contributors, not an automatically executed pipeline. All target-native validation and domain judgment remain outstanding.
- The global acquiring input's card tag is a provisional acquiring-context interpretation, not a restriction in the original request. Local-method coverage must remain open.
- The agent-commerce gap correctly preserves the distinction between an installed initiation-control core and unimplemented advanced mandate/protocol modules.
- Existing shared company/market research and AI-governance packages can contribute scoped artifacts. They do not erase payments-specific later-phase gaps.
- Generic missing-context disclosure and observed-versus-prospective cost scope need care even where the selected lead is plausible.

## Evidence locations

- results.json: all native results and exact command arrays.
- choices.json: pre-execution selected intents and short practitioner rationales.
- adjudication.json: observed-versus-request judgments and preserved unknowns.
- findings.json: actionable routing findings.
- case-01 through case-18: request, input, decision, native output, stderr, validation logs and record.
- source-hashes-before.json / source-hashes-after.json: execution source lineage.
- source-hashes-at-adjudication.json: changes during adjudication, if any.
- additional-support-source-hashes.json: shared support definitions inspected after routing.
- run_routes.py: reproducible command harness; no target workflows executed.
