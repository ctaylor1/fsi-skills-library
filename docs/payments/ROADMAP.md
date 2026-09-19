# Agreed payments implementation roadmap

Recovered from the completed payments architecture review in this conversation.
Phase 1 was authorized on 2026-09-17; Phase 2 was authorized on 2026-09-18.
Phase 3 and then Phase 4 were each authorized on 2026-09-18 by “implement the next phase now.”
The phase definitions below are preserved from that review. Priority labels in the
portfolio proposal are separate from delivery phases.

## 8. Prioritized implementation roadmap

### Phase 1 — Correctness, truthful scope, and shared foundations

**Address first:** lifecycle diagnosis; both reconciliation packages; repair planning; issuer/merchant dispute separation; APP ownership; PCI mapping; FedNow funding language.

**Work**

- Establish the canonical lifecycle, money, evidence, rule-version and handoff contracts.
- Correct the material defects identified above.
- Add the payments router with existing-capability limitations.
- Consolidate payout explanation, separate dispute roles and move PCI.
- Make names, descriptions and risk classifications match actual behavior.
- Inventory authoritative and licensed sources; remove unsupported universal defaults.
- Plan catalog aliases/renames and workbook reconciliation through the existing catalog mechanisms.

**Dependencies:** agreement on the domain contracts, source ownership and package-distribution model.

**Benefit:** existing capabilities become a reliable base for further work.

**Major risks:** cosmetic renaming without behavior changes; losing the simple payout-explanation experience; breaking catalog and handoff references; carrying forward unjustified approval claims.

**Exit criteria**

- No authorization-as-settlement, unlike-currency aggregation, missing-as-zero or unsupported rollback behavior in the corrected paths.
- Exact repair values and unresolved authority are represented.
- Issuer and merchant dispute routes are demonstrably distinct.
- Bundled contracts, names, catalog references and handoffs remain consistent.
- Deterministic checks and behavioral evaluations are reported separately.

### Phase 2 — Complete the core payments decision and lifecycle coverage

**Address first:** bank-payment workflow design; initiation controls; regulatory applicability; merchant acceptance; card programs/lifecycle; economics; routine servicing; platform architecture.

**Work**

- Build the major missing business and operating entrypoints.
- Add provider evaluation and actual-cost/economic-model separation.
- Deliver native rail profiles and message contracts rather than relabelling generic fixtures.
- Establish initial U.S., euro-area and U.K. coverage, with explicit unsupported-region handling.
- Add source-backed consumer-error and scheme-stage profiles.

**Dependencies:** Phase 1 contracts and reliable regional/rule source management.

**Benefit:** the library can address a complete basic payment proposition—from design and provider selection to controls, servicing and financial outcomes.

**Major risks:** overgeneralizing national rules; conflating contractual and statutory obligations; building generic comparison tables without actual decision criteria.

**Exit criteria**

- A merchant, issuer and bank-payment scenario each traverse design, initiation, operating outcomes and servicing with coherent handoffs.
- Normal servicing cannot inherit repair authority, and repair cannot bypass its exception gate.
- Every supported rail/profile states its input contract, limitations and current source basis.
- Foundational examples produce inspectable decisions and artifacts, not generic advice.

### Phase 3 — Performance, platforms, treasury, and modernization

**Implementation checkpoint:** completed 2026-09-18; see [scope](PHASE3-IMPLEMENTATION.md)
and [executed validation](phase3-validation/README.md). Professional and deployment
acceptance remain separate gates.

**Address first:** acceptance performance; credentials/authentication; fraud-control evaluation; liquidity; embedded/platform and commercial payments; incidents/readiness; operations improvement.

**Work**

- Add meaningful cohort analytics, routing experiments and cost/loss tradeoffs.
- Extend card and bank workflows for network tokens, account updater, pay-by-bank and request-for-payment.
- Implement platform splits, payouts, submerchant responsibilities and B2B remittance/ERP integration.
- Add 24×7 funding and operational liquidity analysis.
- Develop architecture and incident modules for hubs, orchestration, cloud/mainframe migration, ledgers and active-active processing.
- Use shared data/AI capabilities for payment-specific automation and model-control designs.

**Dependencies:** complete core lifecycles, dependable data lineage and metric definitions, native event/message profiles.

**Benefit:** the system handles the modern operating and commercial questions that currently fall outside the library.

**Major risks:** mistaking correlation for causation; measuring attempts rather than customer outcomes; double-counting savings; evaluating fraud on immature labels; missing duplicate/lost-payment consequences during failover.

**Exit criteria**

- Performance analyses reconcile their denominators and monetary impact.
- Fraud proposals quantify loss/friction tradeoffs and uncertainty.
- Platform flows preserve legal-entity and account ownership.
- Migration/readiness cases include negative paths, uncertain outcomes, reconciliation, recovery and operational support.
- AI opportunities have task-specific evaluation and human-oversight designs.

### Phase 4 — Regional depth and specialized payment models

**Implementation checkpoint:** authored and bounded agent evaluation completed
2026-09-18; see [scope](PHASE4-IMPLEMENTATION.md) and
[executed validation](phase4-validation/README.md). The relevant human specialist
review in the exit criteria and institution/deployment acceptance remain open.

**Address first according to demand:** additional corridors and local methods; wallet/mobile-money programs; advanced commercial-card and platform arrangements; optional stablecoin settlement.

**Work**

- Expand Pix, UPI, Interac and other justified market profiles.
- Deepen remittance/correspondent, complex marketplace and cross-border liquidity use cases.
- Add stablecoin settlement assessment only where an actual participant use case justifies it.
- Maintain tokenized-deposit, CBDC and programmable-settlement reference modules.
- Add agent-commerce mandate and evidence modules to existing initiation, credential and platform workflows.
- Consider authenticated execution only as a separately designed deployment capability.

**Dependencies:** specialist source access, jurisdiction expertise, realistic data and demand from intended users.

**Benefit:** targeted expansion without turning every rail, vendor or emerging technology into its own skill.

**Major risks:** using pilot announcements as production evidence; confusing deposits and stablecoins; treating vendor protocols as universal standards; distributing licensed material improperly.

**Exit criteria**

- Each expansion has a distinct supported use case, authoritative sources and an accountable owner.
- Regional behavior is tested against realistic cases and reviewed by the relevant specialist.
- Optional modules do not alter core behavior when absent.
- No execution capability is declared ready based on offline planner tests.

### Validation across all phases

Use four separate gates:

1. **Structural/deterministic validation:** schemas, arithmetic, state transitions, deadlines, identifiers, provenance and package integrity.
2. **Model behavior:** natural-language routing, missing/conflicting evidence, unsupported jurisdictions, role boundaries and compositional behavior.
3. **Professional quality:** realistic end-to-end cases reviewed by payment operations, product, risk, legal/compliance and engineering specialists as appropriate.
4. **Deployment acceptance:** connector identity, actual permissions, authentication, idempotency, failure recovery, monitoring and production change control.

The current [self-test runner](../../tools/run_selftests.py) executes command-based cases; it is not a substitute for gates 2–4. The handoff checker also needs to evolve from name-reference checks toward contract compatibility.

The 18 requested routing examples should become a baseline, supplemented by negative and boundary cases. Passing those examples alone would not establish professional or production readiness.

---
