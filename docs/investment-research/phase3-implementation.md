# Phase 3 implementation — Investment Research

Implemented 2026-10-20: controlled model-update preparation, corporate-event
mechanics and research quality review. The library now contains 37 installed IR
target methods and five planned Phase 4 methods; global installed/catalog inventory
is 390. [Validation evidence](phase3-validation/README.md) records bounded software
checks, independent fresh-case reviews and their limits.

| New package | Implemented behavior |
|---|---|
| financial-model-update-preparer | Immutable native-model original, supplied current version/hash conflict checks, exact declared update coverage, scalar-field allowlists, before/after ledger, explicit snapshot advancement and atomic staged candidate. |
| corporate-event-impact-reviewer | Single-event equity raises, repurchases, acquisitions, refinancing and asset disposals; cash/debt/net-debt/share bridges, fees, funding, tranche interest and explicit proposed/announced/supplied-completed status. |
| research-quality-reviewer | Explicit review requirements, structured claim/source timing and identity, missing coverage, independent declared arithmetic, basis comparability, contradictions, risks, disclosures and open adjudication findings. |

## Controlled proposals and actual model validation

Model preparation supports the existing corporate three-statement and annual indexed
DCF input contracts. It preserves original source metadata and financial identity,
requires observed-current hash/version equality, and rejects overlapping, omitted,
undeclared, no-op and out-of-scope patches. Advancement of economic, knowledge and
use dates is explicit and cannot regress or change precision. Necessary generated
context changes have a separate audit trail. Arbitrary private metadata cannot be
copied into the released native candidate.

Evidence must have been eligible under the original snapshot's own cutoff; later
knowledge cannot retrospectively rehabilitate an invalid original. Such a packet
requires separate rebasing/adjudication rather than a clean update claim.

The preparer does not execute the model. Native semantic checks and financial effects
are established only by the separately invoked reviewed handoff or actual native
engine. Two new adapters, model-update-to-three-statement and model-update-to-dcf,
require receiver input equal to the complete staged candidate, validate the producer
against its retained original, then run the actual receiver input validator,
calculation and original-bound output validator. Supplied current observations do
not constitute a live lock. No workbook, live model or system of record is changed.

The updater supports replacement of existing scalar inputs, including supplied
historical/forecast periods, rather than row insertion/deletion, workbook formulas,
arbitrary sectors or automated accounting roll-forward. The analyst must declare
all required changes; hidden omissions outside that inventory are not discoverable.

## Corporate events and independent research review

Event mechanics preserve security/share class, share-count basis, date and explicit
monetary/share scales. Missing terms are rejected; they do not become zero. Pending
terms remain conditional scenarios. Completed status is supplied evidence and does
not authenticate legal closing. Funding, market reaction, purchase accounting,
weighted-average EPS and multi-event interactions require separate review.

Funding checks distinguish upfront cash needs from closing cash. Acquired cash or
retained proceeds cannot silently finance a preceding cash-funded leg. Separately
reported upfront and ending shortfalls retain the conservative settlement assumption;
the larger requirement is reported without double-counting overlapping gaps. A
different settlement sequence or bridge facility needs separate supplied evidence.

The event-impact-to-quality adapter constructs twelve bridge claims with their
original baseline/effective dates and explicit forecast assumptions, plus funding
risk and conditionality review items. It independently recomputes net debt in each
state without pretending that different dates are directly comparable. The receiver
must explicitly request all seven checks, the mapped claims, arithmetic, section,
risk and disclosure requirements. Conflicting populated packets are rejected;
additional caller requirements remain visible as missing coverage. Human judgment
findings and inherited issues remain open.

The generic QA method can also review independently supplied structured packets.
Arithmetic consistency does not establish textual entailment, economic soundness or
full research coverage. Its SKILL instructions require source-text review where
available. Supplied resolutions remain pending separate adjudication. An empty or
incomplete inventory cannot establish the requested readiness.

## Integration and controls

The reviewed registry now contains eight explicit pairings: the five Phase 2
mappings plus three Phase 3 mappings. Actual installed package file inventories and
manifest digests must agree; unpinned additional code is rejected. The router only
plans, preserving native support, installation and reviewed dependency states.

The canonical evidence standard is version 1.1.0 and the reviewed handoff method
1.2.0. Existing analytical engines, fixtures and historical validation evidence are
preserved. Existing packages receive only the updated evidence reference and its
manifest pin. New packages, current capability/routes/indexes, portable manifests
and approved local catalog additions are synchronized. No additional aliases or
retirements are introduced; exact legacy auditor compatibility remains unchanged.

Regenerate local catalog files with approved additions/overrides and --from-current
when the external workbook is unavailable. This proves saved-catalog reproducibility,
not reconciliation with the external authoritative workbook. A source-byte audit
uses the pre-edit 18,625-file baseline to separate this phase from the already dirty
checkout.

## Remaining work

Phase 4 retains macroeconomic, cross-asset-theme, sovereign-credit, public-finance-credit
and structured-credit research as explicit planned capabilities. Professional model,
research, legal/compliance and institutional acceptance; authenticated/licensed sources;
production integration and live authorization remain separately administered.
