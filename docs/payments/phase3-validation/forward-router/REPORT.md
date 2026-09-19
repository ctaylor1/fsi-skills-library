# Independent Phase 3 routing forward review

Reviewed 2026-09-18. Read the public router SKILL, registry and script interface. Recovered the original 18 request texts from the agreed architecture plan; that plan also contains conceptual architecture destinations. No router eval specifications, expected test outcomes, fixtures, golden outputs or previous routing results were read. Authored practitioner routing decisions and rationales from requested work products, current implemented scope and role/context boundaries, then mapped them to the public explicit-intent schema.

The native script does not classify natural language. This exercise is agent intent selection plus deterministic routing and public-contract validation, not a blinded NLP benchmark or proof of full task delivery.

## Result

**37 cases (18 original requests + 19 supplementary), 74 native CLI calls, 198 assertions passed.** All four router implementation/source hashes remained unchanged during the final execution. The original requests produced **13 preliminary routed destinations, 1 role clarification, and 4 retained capability gaps**. Every output withheld authority and required target-native validation.

| Original request | Final interpretation |
| --- | --- |
| Analyze why a merchant’s card authorization rate is declining. | Acceptance performance; jurisdiction remains missing. Unique order/attempt cohorts, not individual diagnosis. |
| Compare FedNow, RTP, ACH and cards for a use case. | Bank workflow leads; explicitly partial: a combined bank/card ranking is not implemented. Card contracts and economics need separate evidence. |
| Design acquiring for a global e-commerce merchant. | Merchant acceptance strategy; initial regional scope and national overlays are disclosed. |
| Model adding pay-by-bank. | Payment economics; prospective adoption/displacement, not incurred-fee analysis. |
| Analyze interchange and acceptance costs. | Merchant cost; clarify cost_basis and jurisdiction before native input. |
| Design embedded payments for vertical SaaS. | Platform payment flow and actual seller/contract/funds-flow ownership. |
| Investigate a spike in chargebacks. | Acceptance performance, with case packaging/fraud support when needed; no single case package as lead. |
| Design a real-time-payment fraud strategy. | Fraud control evaluator, native strategy-only mode; historical replay is not mandatory. |
| Explain card authorization through clearing and settlement. | Card lifecycle operations, preserving stage distinctions. |
| Assess payment-hub modernization. | Payment platform architecture; cutover and deployment acceptance remain separate. |
| Compare issuer processors. | Provider evaluator, with issuer/card-program requirements. |
| Assess cross-border options. | Capability gap: corridor-specific cross-border design remains later-phase scope. |
| Develop merchant acquiring architecture. | Payment platform architecture with commercial acceptance support. |
| Design payment orchestration strategy. | Needs participant clarification. Merchant/acquirer versus bank/issuer/processor changes the lead. |
| Analyze a payments company or competitor. | Capability gap: payments business-model analysis remains later-phase scope. |
| Assess stablecoin settlement. | Capability gap: adoption/settlement assessment is distinct from existing control-evidence review. |
| Develop an AI strategy for payment operations. | Operations improvement analysis and supervised experiments. |
| Design payments for AI-agent commerce. | Capability gap: core initiation exists, but advanced mandate/protocol design is not implemented. |

No jurisdiction was invented for the original requests. The merchant/issuer role was included only where clear from the wording. Missing context stays visible; a routed destination is preliminary, not a ready native request.

## Finding closed during review

Initial source inspection found `instant-fraud-strategy` emitting `target_mode: strategy-and-portfolio-replay`. The fraud native schema supports `strategy`, `portfolio` and `strategy-and-portfolio`; a new threat/control strategy does not require a historical replay sample. This was reported before running the retained final cases. The root agent corrected the route to `strategy` and added an integration assertion.

The unchanged natural request “Design a real-time-payment fraud strategy.” now returns the appropriate lead and `target_mode: strategy`. The retained final original-08 input/output and independent mode compatibility assertion passed. The initial observation was a source-interface finding, not a failed CLI run; no fabricated failing execution is claimed. No remaining issue was identified in this review.

## Supplementary coverage

The 19 additional cases distinguish merchant from bank orchestration, missing/incorrect dispute roles, legacy predicate replay from a new fraud strategy, legacy API log categorization from service-incident investigation, credential review, commercial ERP workflows, weekend liquidity, routing experiments, request-for-payment and pay-by-bank collection, resilience design and readiness, execution refusal, absent installed targets, stablecoin evidence-only scope and prose without a supported explicit intent.

Legacy modes remain explicit and narrow. New service/collection/resilience modes do not inherit live execution authority. A requested deployment returns action-unavailable. An absent analytics package returns target-unavailable. No lead is repeated as its own collaborator. All outputs validate against the retained request and current registry; target input schemas still need their own validation.

## Retained evidence

- `original-requests.json`: exact original 18 texts.
- `cases-and-expectations.json`: independently authored request interpretation, structured input, expected status/lead/mode and rationale.
- `run_forward.py`: complete invocation and assertion logic.
- `*-input.json`, `*-output.json`, stdout/stderr and validation files: exact native artifacts.
- `commands.json`: all 74 argv lists and exit codes.
- `assertions.json`, `summary.json`: all assertions and aggregates.
- `initial-mode-finding.json`: initial source observation and correction, clearly distinguished from an execution failure.
- `code-hashes-before.json`, `code-hashes-after.json`: final registry, SKILL, route script and bundled contract hashes.
