# Payments Phase 2 implementation

Implemented 2026-09-18 against the [agreed roadmap](ROADMAP.md). Ten new packages
complete the core decision and lifecycle authoring scope, bringing Payments to
28 packages; PCI remains in Cybersecurity. All new helpers produce offline review
artifacts. They do not initiate payments or confer operational authority.

## Delivered workflows

| Package | Concrete output and boundary |
| --- | --- |
| [Bank payment workflow designer](../../skills/payments/bank-payment-workflow-designer/SKILL.md) | Rail comparison, access/reach, timing, funding, recovery and control dependencies; no inferred provider access or execution. |
| [Payment initiation control reviewer](../../skills/payments/payment-initiation-control-reviewer/SKILL.md) | Exact individual/batch instructions bound to payer intent, delegation, account/screening evidence, mandate where needed and duplicate checks; authentication is not payment intent. |
| [Payment regulatory applicability reviewer](../../skills/payments/payment-regulatory-applicability-reviewer/SKILL.md) | Entity/activity/funds-flow matrix of candidate obligations and scoped legal questions; no legal clearance or bank-partnership inference. |
| [Merchant acceptance strategy designer](../../skills/payments/merchant-acceptance-strategy-designer/SKILL.md) | Segment/method/provider coverage, operating responsibilities and open decisions; supplied provider claims remain evidence to review. |
| [Card program designer](../../skills/payments/card-program-designer/SKILL.md) | Program blueprint, issuer/sponsor/processor/account responsibilities, custody, controls and operating dependencies; no launch or deposit-protection determination. |
| [Card lifecycle operations assistant](../../skills/payments/card-lifecycle-operations-assistant/SKILL.md) | Separate authorization, holds, presentment, clearing, settlement, issuer posting and merchant funding; no invented balance or funding state. |
| [Payment economics modeler](../../skills/payments/payment-economics-modeler/SKILL.md) | Explicit prospective cost/contribution scenarios, sensitivities and bounded break-even; observed statement-cost analysis remains with merchant-payment-cost-analyzer. |
| [Payment servicing planner](../../skills/payments/payment-servicing-planner/SKILL.md) | Refund/return/cancel/recovery proposals tied to the original payment, prior completed/pending services and independent permissions; no repair authority or guaranteed recovery. |
| [Payment platform architecture reviewer](../../skills/payments/payment-platform-architecture-reviewer/SKILL.md) | Flow, state, identity, idempotency, uncertain-outcome, reconciliation and migration review; declarations and NFR targets are not tested deployment guarantees. |
| [Payment provider evaluator](../../skills/payments/payment-provider-evaluator/SKILL.md) | Mandatory gates, weighted evidence ranges, comparable fee dimensions and shortlist questions; unknown mandatory evidence cannot be offset by a high optional score. |

Each package contains instructions, native schema/domain/source/control/handoff
references, an output template, standalone validators/calculator, fixtures,
executable evaluations and regressions. Catalog additions and overrides survive
regeneration; the external workbook has not been edited.

## Shared profiles and native formats

The additive foundation retains Phase 1 contract version 1.0.0 and bundles local
copies for standalone installation. Requests register source identity and dates;
outputs retain input snapshots/hashes, findings and unresolved upstream issues.
Output validation recomputes the artifact and can compare a separately supplied
original input. These checks establish consistency, not source truth, reviewer
authentication or complete sensitive-data detection.

Ten rail profiles cover initial US ACH/Fedwire/FedNow/RTP, euro-area SCT/SCT Inst/
SDD Core and UK FPS/Bacs/CHAPS. Profiles distinguish timing, access, funding,
finality and recovery and require actual institution/provider evidence. National,
scheme and institution overlays remain necessary; unsupported jurisdictions stay
unsupported. No universal pricing, limits or cutoff defaults are supplied.

Six native message contracts identify exact fields and versions. Executable
parsers cover a bounded ACH 94-character Entry Detail subset and selected
pacs.008.001.08, pain.001.001.09 and pain.008.001.08 XML structures. They reject
unsupported namespaces and unsafe XML constructs. UK FPS and Bacs native formats
have explicit contracts and unsupported raw adapters. This is not complete ACH
file validation, ISO XSD/usage-rule conformance or rail certification.

Four consumer-error reference profiles distinguish US Reg E and Reg Z, EA PSD2
and UK unauthorized-payment review. Public Visa stage orientation is separate
from statutory clocks. The issuer and merchant dispute packages now prepare
case-scoped profiles; specialist review, supplied calendars/trigger dates and
current authorized scheme rules remain required. Preparation does not calculate
legal deadlines or authorize credits/submissions. A prepared issuer profile
cannot be reused for another case. See [source governance](SOURCE-GOVERNANCE.md)
for source dates, near-term changes and recertification limits.

## Routing and composition

The router activates the ten destinations, distinguishes servicing from repair,
and exposes Phase 3/4 gaps. Bank-rail comparison discloses its card-coverage limit.
Orchestration requires participant clarification before selecting merchant
acceptance or bank/issuer platform architecture. Missing context is visible even
when a preliminary destination can be selected.

Merchant, issuer and bank synthetic cases exercise design, exact instruction
controls, separately sourced outcomes and servicing. Handoffs preserve ownership,
source references and unresolved issues. A valid transport envelope can have an
empty target input: native target input must still be assembled and validated.
These are composable workflows, not an automatic pipeline; a planning result
never manufactures a submission, settlement or servicing event.

## Verification and remaining gates

[Validation and retained artifacts](phase2-validation/README.md) separate package
commands, integration methods, independent forward scenarios and natural-language
routing. Independent reviewers found and retested defects beyond the original
fixtures; initial failures are retained alongside corrected outputs.

Phase 2 authoring is complete. Human payments/legal/control-owner acceptance,
trusted-source ingestion, licensed rule packs, real connector integration and
deployment testing remain outstanding. The bounded independent evaluations are
not a broad model benchmark or professional sign-off. Phase 3 performance, fraud,
liquidity, platform/commercial flows and operating depth, and Phase 4 regional and
specialized expansions remain outside this implementation.
