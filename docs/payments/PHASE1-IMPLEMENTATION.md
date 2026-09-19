# Payments Phase 1 implementation

Authorized 2026-09-17 following the comprehensive payments architecture review.
Scope: correctness, truthful capability boundaries, shared contracts, router,
catalog migration, payout-mode consolidation, issuer/merchant dispute separation
and PCI relocation. Phase 2–4 capability creation is not part of this milestone.

## Required outcomes

- [x] Approval, clearing, settlement, funding and posting stay distinct.
- [x] Transaction and settlement reconciliation retain missing data and quarantine
  ambiguous identity/currency/duplicate evidence without invented journals.
- [x] Repair plans bind exact corrections and source/policy context; no runtime
  execution, authenticated approval or guaranteed rollback is claimed.
- [x] Merchant/acquirer representment and issuer consumer-error review have distinct
  owners, evidence and rule profiles; statutory obligations are not scheme clocks.
- [x] APP/scam case ownership remains in payments; cyber is conditional.
- [x] PCI requirement mapping corrected and package moved to cybersecurity.
- [x] FedNow master/correspondent funding is not mislabeled as RTP prefunding.
- [x] Shared money, lifecycle, time, evidence, rule and handoff contracts bundled
  consistently and covered by executable boundary tests.
- [x] Router distinguishes installed skills, ambiguous participant roles,
  action-unavailable requests and later-phase coverage gaps.
- [x] Renames/merge/move reflected in metadata, catalog, active references and
  reproducible workbook regeneration overrides without losing prior work.
- [x] Deterministic, structural and independent behavioral results recorded
  separately from professional and deployment acceptance.

## Architecture and migration

The canonical contract is `shared/payments/payment_contract.py` plus
`shared/payments/payment-contract.md`; selected copies are bundled in each payment
package and the moved PCI package. Run `python tools/sync_payment_contract.py --check`.
Copies keep packages standalone. Hashes support lineage, never authorization.

`catalog/payments-phase1-migrations.json` records aliases and the PCI move. The
former generic dispute alias requires participant-based routing; the payout summary
alias requires explain-payout mode. They are not blind input-compatible redirects.
`catalog/approved-overrides.json` and `catalog/provisional-additions.json` preserve
these authorized changes across `tools/build_catalog_from_xlsx.py` regeneration.
The external workbook is not present/edited; its owner must reconcile the recorded
overrides before removing them. The catalog can be regenerated with --from-current.

Names for broader incident investigation, full merchant-risk lifecycle, fraud-control
strategy, multi-format messaging and stablecoin opportunity assessment are deferred
until those capabilities exist. Current packages state their narrower boundaries.
The only new payment entrypoint in this phase is payments-router.

## Delivered behavior

| Area | Implementation and boundary |
| --- | --- |
| Lifecycle and bank exceptions | Authorization no longer proves settlement or funding. Bank cases require operation-specific finality/eligibility evidence. RR04 does not independently establish sanctions. Local case identifiers do not imply persisted cases. |
| Transaction reconciliation | Decimal arithmetic and entity/account/currency/cycle partitions; all source comparisons retained. Missing values stay unknown. Reused source identities quarantine every affected group, including reuse under different references or currencies. No invented journals or FX allocations. |
| Settlement and payout explanation | Effective, scoped fee/reserve evidence; supplied due dates and as-of context. Report-only `explain-payout` mode preserves component discrepancies without requiring a bank statement or claiming cash receipt. The former payout summarizer is merged here. |
| Repair planning | R3 draft-only proposal with exact before/after values, source snapshot, policy, screening scope and hash binding. Changing a replacement value requires renewed scoped evidence. Hashes are lineage checks, not approval authentication. |
| Merchant and issuer disputes | Separate package ownership. Merchant responses use supplied applicable profiles and cited deadlines; evidence count does not establish compelling-evidence eligibility. Issuer legal clocks remain distinct from scheme recovery clocks, including clocks with unresolved profiles. |
| Fraud, scams and instant monitoring | Payment fraud retains APP/scam ownership; cyber consultation depends on actual cyber evidence. Instant monitoring uses supplied offset-aware windows and currency partitions and distinguishes FedNow funding from RTP prefunding. The existing fraud-rule analyzer remains a bounded single-predicate, supplied-label analysis. |
| Merchant onboarding and cost | Pending sanctions screening does not become a decline; applicable policy and subject coverage are explicit. Observed costs use Decimal arithmetic and preserve unknown fixed fees; unsupported savings, qualification and annualization assumptions are removed. |
| Rules and integration readiness | Supplied rule bulletins remain unverified alerts without trusted source verification. Evidence links alone do not satisfy readiness; declared inspection records are required. Manual reconciliation is not an automatic exemption. |
| Messaging and API diagnostics | ISO package remains normalized JSON interpretation, with classification-only fallback for unsupported families. API diagnostics preserve documented timestamps/windows, redact PANs, and distinguish failure counts from causal or authorization-rate analysis. |
| Stablecoin and PCI controls | Stablecoin review needs an applicable supplied policy and explicit control parameters; missing critical rows become gaps. PCI requirement mapping is corrected, and the evidence-only package moves to cybersecurity without a compliance-certification claim. |
| Routing and packaging | One lead owner, participant clarification, installed-target checks and explicit later-phase gaps. Shared contracts are bundled for standalone installation. Catalog regeneration now replaces whole skill identifiers idempotently. |

All 18 payment packages and the relocated PCI package carry the shared contract.
The catalog remains **239 packages across 14 categories**: the payout merge removes
one package and the router adds one. The payment category has 18 packages and
cybersecurity has 12. Existing wealth-management files were preserved.

## Verification record

**Phase 1 implementation is complete.** On 2026-09-17:

- All **1,101 package command evaluations** passed, including **100 payments/PCI
  evaluations**. Regression methods called by those commands are included within
  this execution evidence, not added to the command count.
- All **239 packages** passed repository structure validation with **0 errors and
  0 warnings**; handoff validation found **0 dangling references**.
- All **13 payments shared-contract and repository integration tests** passed,
  including standalone routing, migration roles, native-input enforcement and
  idempotent catalog regeneration. The full repository suite passed **277 test
  methods**, including these 13; one existing global catalog assertion was updated
  for the added router.
- Payment route/migration checks, shared-contract consistency across **19 packages**,
  scoped E9/F defect lint and whitespace checks passed.
- Two independent evaluator agents exercised **nine bounded synthetic requests plus
  variants** through the actual instructions and native tools. They found three
  defects: API chronology loss, issuer scheme-clock loss, and duplicate source
  identity counting. All three were repaired and independently retested against
  unchanged reproductions. The reconciliation retest also verified settlement and
  cross-currency identity reuse, preserved valid controls, and rejected the old
  false-match output.

See the [validation record](validation/README.md) for commands, retained original
failures, current outputs and interpretation limits. This is bounded forward
evaluation by agents, not a blinded paired benchmark or human specialist acceptance.
The broader natural-language routing cases remain unexecuted model evaluations.
No live connections or payment-changing actions are added.

## Remaining acceptance boundaries

The offline library cannot authenticate human reviews, policy ownership, signatures,
source systems or payment authority. Profile validation checks declared scope/dates;
deployments must verify trusted sources, identities and runtime permissions.
Licensed scheme rulebooks and institution operating policies are not bundled.
Regional legal completeness, specialist acceptance and connector/runtime acceptance
remain separate later gates. The router's natural-language evaluation cases must
not be counted as executed merely because a structured route test passed.
