# Insurance Phase 2 — operating foundations

Status: implementation and bounded local verification complete, 2026-09-18.
User-authorized after the completed Phase 1 checkpoint. Professional and deployment
acceptance remain separate.

## Scope and exit criteria

Implement the 17 distinct workflows in
[the Phase 2 manifest](../../catalog/insurance-phase2-capabilities.json), taking the
insurance domain from 23 to 40 packages. These fill the Phase 2 operating areas in
[the roadmap](IMPLEMENTATION-PLAN.md): product and P&C rate adequacy, policy
transactions/billing, distribution/delegated authority, claim coverage/handling/
financial/payment review, life underwriting/service/death benefits, and ceded
reinsurance program/administration.

The new native methods must perform the actual bounded job, not merely count
documents or accept a self-certified readiness flag. Each package requires useful
professional output, explicit applicability and missingness, meaningful arithmetic
or evidence relationships, native input/output validation, source binding, adverse
regressions and portable resources. A shared envelope cannot establish domain
correctness. Routes become active only when their native packages exist and pass.

Exit checks include catalog and metadata correspondence, preserved Phase 1
behavior, versioned shared-resource consistency, real native receiver handoffs,
fresh independent practitioner scenarios, whole-repository checks and retained
validation evidence. Deterministic agreement and agent evaluation remain distinct
from domain specialist and institutional deployment acceptance.

## Deliberate boundaries

- Native tools are offline and draft-only. They do not bind, issue, cancel, deny,
  pay, file, notify, or write a system of record.
- Rule profiles carry explicit jurisdiction, product/line, version, source and
  effective dates. Model guidance does not establish state adoption or a universal
  legal deadline. Supplied evidence is not independently authenticated.
- Life underwriting has its own narrow package. Annuity sales/service, disability,
  long-term care and health-payer workflows do not become interchangeable with it.
- Ceded scenario comparison does not invent CAT model outputs, loss distributions
  or an optimal program. Claim scenarios do not select booked reserves or decide
  coverage. Premium reconciliation does not decide lapse or cancellation rights.
- Phase 3 analytical/specialist depth and Phase 4 architecture/automation remain
  separate. Existing unrelated payments and wealth-management work is preserved.

## Implemented native workflows

| Package | Bounded method and practical output |
| --- | --- |
| `insurance-product-design-reviewer` | Trace product needs to features, wording, customer scenarios and launch evidence; preserve contradictions and missing owners. |
| `pc-rate-adequacy-analyzer` | Single-cohort prospective P&C pure-premium indication from reviewed ultimate losses, trend, credibility, expenses and supplied CAT/reinsurance provisions. No loss-development selection or filing approval. |
| `insurance-policy-transaction-packager` | Version-bound policy change, before/after values, authority, notice/document plan and signed premium effect. No issuance or status change. |
| `insurance-premium-billing-reconciler` | Signed receivable movement bridge, reversals, invoice allocations, aging and unapplied cash; no inferred lapse/cancellation. |
| `insurance-producer-onboarding-reviewer` | Entity/license/appointment/contract evidence matched to actual entity, jurisdiction, line and dates; conflicts remain unresolved. |
| `insurance-placement-packager` | Current quote version, comparable scope/costs, subjectivities and placement evidence; no invented missing premium or binding instruction. |
| `insurance-delegated-authority-reviewer` | Agreement authority, per-risk and aggregate exposure, ledger completeness and independently based report reconciliation/late reporting. |
| `life-annuity-sales-reviewer` | Product-specific needs, liquidity, replacement, alternatives and disclosure evidence for life/annuity sales review; no suitability score or sale. |
| `claim-coverage-reviewer` | Policy clauses and supporting/contrary claim facts form reviewable competing hypotheses; no coverage verdict or rights letter. |
| `claim-handling-plan-builder` | Accountable tasks, explicit supplied deadlines, dependency ordering, overdue service and incomplete evidence; no communication or claim resolution. |
| `claim-financial-evaluation-assistant` | Paid/case stocks and separate future-unpaid scenarios, gross/net bridges and reserve-change illustrations; no selected/booked reserve or settlement decision. |
| `claim-payment-closure-reviewer` | Distinct payment and closure gates, authority, duplicate obligations, settled history, obligations/reserve and owned reopening routes; no payment or closure. |
| `life-underwriting-reviewer` | Identity/consent, disclosed financial support, required evidence and contradictory risk disclosures; no medical/risk-class decision. |
| `life-annuity-contract-service-reviewer` | Contract/service rights and consents plus explicitly supported same-day value scenarios, signed MVA and charges; no transaction/tax decision. |
| `life-benefit-claim-reviewer` | Insured/death evidence, conflicting entitlement, sourced offsets and benefit bridge; no adjudication or allocation through disputed ownership. |
| `reinsurance-program-analyzer` | Supplied deterministic events through ordered quota-share/occurrence layers, participation, aggregate erosion and supplied costs. No CAT distribution, optimization or purchase decision. |
| `reinsurance-contract-administration-reviewer` | Contract notices, premium/claim statements, ledger roll-forwards, claim-level differences and collateral evidence; no inferred legal recoverability or collection. |

Each package has native scripts, schema/method/source references, an output template,
synthetic fixtures and adverse regressions. The shared foundation and evidence
contract are bundled for standalone installation. The router activates these jobs
while preserving participant/line clarification and remaining specialist gaps.
Catalog additions preserve regeneration and exact package metadata.

## Composition and review repairs

Two actual native compositions are tested: coverage findings to handling tasks,
and a selected financial scenario to payment review with separately supplied
payment authority. Their source artifacts and open issues survive receiver input
validation and execution. These examples are explicit reviewed mappings, not a
universal adapter or an automatically orchestrated insurance lifecycle.

Cross-object, party, capacity, line or jurisdiction handoffs now need an exact,
source-bound context mapping. Future upstream evidence and unsupported transitions
keep the result incomplete. Shared hashing establishes content consistency only.

Seventeen independently authored fresh cases exposed three domain-output defects:
unowned reopening routes accepted for closure; a stale requested value used as the
policy table's before value; and a valid report difference suppressed by unrelated
underwriting authority basis. All were repaired and replayed with unchanged inputs.
Schema/topic omissions and the undisclosed same-day servicing valuation requirement
were also corrected; prior-day values remain prior-day evidence, with a precise gap.
Original observations and repaired results are retained separately.

## Validation

Final verification is recorded in [Phase 2 evidence](phase2-validation/README.md).
The 17 new packages contain 258 regression methods; all 40 insurance packages contain
412 package methods. These are invoked within package commands, not additive
independent professional evaluations. Natural-language eval specifications remain
planned unless a separate execution record explicitly identifies them as run.

The repository's established `compatibility` frontmatter field is intentionally
preserved. Generic skill-creator quick validation rejects this preexisting field;
repository-specific structural validation is authoritative for this library's
format. No broader ecosystem compatibility claim is inferred.

Phase 1 validation stays a historical checkpoint. Live source versions, licensed
resources, domain specialist acceptance, broader model evaluation and institutional
deployment controls remain outstanding. Next implementation milestone: Phase 3
analytical and specialist depth in [the roadmap](IMPLEMENTATION-PLAN.md).
