# Payments Phase 3 implementation

Phase 3 was authorized on 2026-09-18 through “implement the next phase now,” following
the completed Phase 2 checkpoint. This implements the [agreed Phase 3 scope](ROADMAP.md):
performance, credentials, fraud controls, platform/commercial flows, payment liquidity,
incidents/resilience and operating improvement. Six new packages and two expanded
renames bring Payments to 34 packages. PCI remains in Cybersecurity.

## Package and module map

| Workflow | Implemented behavior | Main limit |
| --- | --- | --- |
| [Acceptance performance](../../skills/payments/payment-acceptance-performance-analyzer/SKILL.md), new | Order-versus-attempt funnels, cohort and currency partitions, retries, mature chargebacks, costs and routing-experiment guardrails | Descriptive comparisons and supplied assignments do not prove causal uplift or statistical significance. |
| [Fraud controls](../../skills/payments/payment-fraud-control-evaluator/SKILL.md), renamed and expanded | Journey/threat/control strategy plus interacting-rule portfolio replay, mature/unknown labels, exposure and friction scenarios | No actual block/allow decision, rule deployment or causal avoided-loss estimate. Original predicate replay remains a separate legacy contract. |
| [Credentials/authentication](../../skills/payments/payment-credential-authentication-reviewer/SKILL.md), new | Token domains, provisioning, current state, account-updater consent and exact authentication binding | Opaque references only; no token operation, cryptographic verification, SCA or liability-shift determination. |
| [Platform flows](../../skills/payments/platform-payment-flow-designer/SKILL.md), new | Seller and account ownership, PayFac/MoR responsibilities, allocations, reserves, refunds and payout capacity | Legal entity/currency ownership is preserved; no automatic permission or funds movement. |
| [Commercial workflows](../../skills/payments/commercial-payment-workflow-designer/SKILL.md), new | Supplier enablement, invoice/credit/payment allocations and remittance/ERP linkage | Payments design and reconciliation inputs, not replacement of procurement, invoice approval or exact initiation controls. |
| [Liquidity/funding](../../skills/payments/payment-liquidity-and-funding-analyzer/SKILL.md), new | Entity/account/currency time paths, reservations, funding availability, forecast exclusions and stress shortfalls | No cross-entity pooling, implicit FX, institutional ALM or treasury execution. |
| [Service incidents](../../skills/payments/payment-service-incident-investigator/SKILL.md), renamed and expanded | UTC chronology, attempts and unique-payment impact, release hypotheses, uncertain financial outcomes and recovery evidence | Legacy log diagnostics remain available; no causal conclusion from temporal correlation or automatic retry. |
| [Operations improvement](../../skills/payments/payment-operations-improvement-analyzer/SKILL.md), new | Completed-window and backlog workloads, STP/rework, constrained capacity/cash scenarios and task-specific automation/AI evaluation | Capacity released is distinct from cash saved; overlapping opportunities are not additive. No autonomous operational action. |
| [Bank workflows](../../skills/payments/bank-payment-workflow-designer/SKILL.md), additive collection module | Normalized request-for-payment and pay-by-bank request/response review with an independent initiation handoff | Request acceptance is neither submission nor settlement. RFP supports bounded US FedNow/RTP orientation; no pain.013 parser or UK/SEPA request-to-pay adapter. |
| [Platform architecture](../../skills/payments/payment-platform-architecture-reviewer/SKILL.md), additive resilience module | Hub/orchestration and cloud/mainframe/ledger/active-active operating designs, ownership, idempotency, reconciliation and fault-scenario evidence | Design declarations and supplied test reviews do not establish deployed resilience or authorize cutover. |
| [Integration readiness](../../skills/payments/payment-integration-readiness-reviewer/SKILL.md), additive resilience module | Version/scope-bound negative-path, recovery, uncertain-outcome, reconciliation and operational-support evidence review | Missing, failed or mismatched evidence remains unresolved; no go-live approval. |

The router activates these workflows and selected native modes. Observed merchant
costs remain distinct from prospective economics. Corridor expansion, additional
regional depth, stablecoin adoption and advanced agent commerce remain visible gaps.
The payment-business-model specialization is also still unimplemented; priority
labels in the architecture proposal are not delivery-phase commitments.

## Contracts and compatibility

New native helpers use the existing source-bound foundation and contract 1.0.0.
No global envelope change was needed. Each package is independently distributable;
copies are verified by the synchronization tools. Original architecture/readiness
CLIs continue to use their prior schemas; resilience has separate CLIs. Bank rail
comparison likewise keeps its native contract alongside the collection module.

The renamed incident package retains its original log diagnostic CLIs. The fraud
package preserves predicate replay under `scripts/legacy/`; those inputs are not
accepted as portfolio inputs. [Migration records](../../catalog/payments-phase3-migrations.json)
and approved catalog overrides preserve both renamed destinations across catalog
regeneration. Active handoffs point to installed packages. Historical validation
records retain the names and evidence applicable at their checkpoint.

Sources and unresolved issues survive handoffs; each recipient still needs its
native input assembled and validated. An empty target input is deliberately not a
complete adapter or an approval. No package silently creates a payment, posting,
new consent, retry, rule deployment or cutover from another package's draft.

## Source refresh

Primary-source verification found the Phase 2 FedNow February 2026 pointer had been
superseded by April 2026 v3.6. The shared rail profile, native-message registry and their bundles now point to
the applicable public version. The documented funding and nonvalue-RFP distinctions
remain; private participant implementation material is still required. Historical
Phase 2 records were not rewritten. [Source governance](SOURCE-GOVERNANCE.md)
records this correction and the new credential/engineering references.

## Acceptance

[Phase 3 validation](phase3-validation/README.md) records executed package checks,
portable/native integration checks, independent forward scenarios, findings and
retests. These are separate from professional and deployment gates. Test counts
are bounded to their execution unit and are not measures of source truth or model
reliability. Human domain/control-owner review, trusted-source ingestion, current
licensed institution rules, live connectors and production acceptance remain open.
Phase 4 was not implemented.
