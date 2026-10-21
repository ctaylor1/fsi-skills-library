# Migration and handoff boundaries

Phase 1 renames capital-structure-maturity-mapper to issuer-capital-structure-mapper,
and moves/renames financial-document-version-comparator to the shared Data, AI &
Model Governance owner as document-version-comparator. There is one active package
per method. Registered names and historic Asset Management paths resolve to terminal
targets; aliases do not duplicate packages or launch work.

Phase 2 retires model-roll-forward-auditor after exact continuity parity and
reconstruction checks. Its name and historical paths resolve to
research-financial-model-reviewer with mode legacy-roll-forward. Wrap the original
as {"mode":"legacy-roll-forward","input": ORIGINAL}; legacy_result retains the exact
old artifact. The original source is preserved unchanged in
phase2-validation/legacy-auditor. The independent-review mode is separate and does
not infer model approval from continuity.

Old output packets remain artifacts of their original version. Resolve identifiers,
then supply inputs to the new documented contract; do not relabel historical results
or claim schema compatibility. Newly required fields are documented in each updated
native schema and changelog. Keep original JSON for output validation.

Financials normalization stays in Finance & Operations. Generic comparison belongs
to Data, AI & Model Governance. Architecture and automation assessments stay with
shared technology owners. Portfolio decisions, personal advice and transactions keep
their respective Asset Management, Wealth and Investment Banking owners.

The IR router accepts explicit intent IDs, typed subjects, purpose/audience, dates,
profiles and a caller-supplied provider-qualified installed-skill inventory. It returns
a plan only. Installation, native computation, cross-skill compatibility, authenticated
services and professional acceptance are distinct states. Dependencies are advisory;
no skill is launched. Router output validation binds the request plus its bundled
capability/route registry versions. Research views can be drafted internally by the
appropriate analyst method; publication, client advice and execution need their own
owners and independently administered approvals.

Rebuild local discovery with the approved additions/overrides and --from-current
only when the workbook is unavailable. This verifies local reproducibility, not
agreement with the external authoritative workbook. Source-byte preservation uses
the pre-edit baseline, not the already-dirty Git diff.

Phase 2 adds five explicit reviewed mappings in the canonical adapter registry.
They validate actual producer/consumer code and originals, preserve issues and
rights/timing/basis context, and reject conflicting populated receiver fields.
The router lists dependency status; actual mapping needs the separate local
review_handoff.py command and an installed library. Other pairs retain native-only
status. See phase2-implementation.md for supported scope and exact commands.


Phase 3 creates three packages without additional renames or retirements. Its two
model-update mappings require the exact staged candidate and run actual corporate
three-statement/DCF contracts. Event-impact-to-quality maps only the declared bridge
and review scope; human findings remain open. The canonical registry now declares
eight pairings, while other combinations retain native-only status. See
[Phase 3 implementation](phase3-implementation.md) and the router's handoff reference
for exact scope requirements. Existing source-bound artifacts and historical
validation records remain attached to their original versions.


Phase 4 creates five specialist packages without renames or retirements, completing
all 42 target packages. Each retains explicit profile and source/instrument scope;
package completion is distinct from universal analytical coverage. The ninth
reviewed pairing maps an explicit subset of macro-selected observations into theme
research with the same economy/time/purpose context. It preserves original release,
vintage and basis and does not create shocks, causal relationships or allocations.
Other specialist pairs remain native-only. See [Phase 4 implementation](phase4-implementation.md)
and the router's handoff reference. Earlier implementation/validation evidence and
exact legacy auditor compatibility remain preserved.

The subsequent [control repair checkpoint](control-repairs-implementation.md)
updates issuer credit to 0.1.1, surveillance to 0.3.1 and routing to 0.4.1. Reported
credit periods must end by both economic as-of and cutoff dates; repeated EBITDA
adjustment IDs reject before calculation. Spread comparisons now require actual
aware observation/source timestamps and an explicit current-age policy; old
undated intake remains partial with the spread change/alert withheld. The router
uses each method's exact profile selector: surveillance uses `issuer_profile`,
and structured credit uses `structured_credit_profile=single-period-sequential-pay-v1`.
Other corrected subject/profile declarations are recorded in the native parity
audit. This changes current contracts and discovery without relabeling historical
packets or editing any earlier phase evidence.

The [evidence reconciliation checkpoint](evidence-reconciliation-implementation.md)
updates issuer credit to 0.2.0 and surveillance to 0.4.0. Issuer adjustments now
select source-bound canonical economic events/components. Debt-dependent metrics
require explicit instrument inclusion/exclusion and an exact principal-to-carrying-
value reconciliation. Spread comparisons select structured market evidence and a
dated security/issuer mapping. The common envelope remains `ir-phase2/1.0`; legacy
intake lacking these records is partial with dependent metrics withheld. Supply
actual evidence and contexts rather than renaming IDs or inferring a ledger.
Original packets remain attached to their original versions. All earlier phase
and repair implementation/validation records remain unchanged.

The [remaining findings repair checkpoint](remaining-findings-repairs-implementation.md)
updates issuer credit to 0.2.1, surveillance to 0.4.1 and routing to 0.4.2.
Live surveillance entrypoints now require the explicit `ir-phase2/1.0` contract;
legacy requests and legacy output packets reject with a migration-required error.
Supply and review the actual current evidence fields rather than relabeling an old
packet. Frozen historical source and outputs remain available for historical
reconstruction. Issuer credit treats omitted/null nullable inputs consistently,
withholds dependent metrics and reports partial coverage. Current canonical and
bundled capability versions must match installed native metadata. Earlier phase,
control-repair and evidence-reconciliation checkpoints remain byte unchanged.
