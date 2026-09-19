# Wealth management P3 implementation

Date: 2026-09-17. P3 adds the two agreed specialist workflows: family wealth governance preparation and trust administration review. Existing P0/P1/P2 coverage is retained. The completed catalog contains **239 packages across 14 categories**, including **27 wealth-management packages**. The router selects 27 practitioner jobs; investor-side manager diligence remains in Asset Management. See [P3 validation](P3-VALIDATION.md) for the observed checks and acceptance limits.

## Delivered scope

| Priority | Package | Professional job and boundary |
| --- | --- | --- |
| P3.1 | [Family wealth governance preparation](../../skills/wealth-management/family-wealth-governance-preparer/SKILL.md) | Prepare family decision-process, succession and next-generation discussion materials from attributed objectives, participation, governance records and permissions. Preserve dissent, missing authority, unknown readiness evidence and owned follow-up work. Distinguish internal evidence from the audience draft. A family discussion or recorded vote never establishes legal trust/estate authority or permission to disclose another person's records. |
| P3.2 | [Trust administration review](../../skills/wealth-management/trust-administration-reviewer/SKILL.md) | Review one USD trust under a trust-capacity engagement: supplied governing-document obligations, fiduciary/beneficiary evidence, distribution requests and accounting. Reconcile supplied cash, principal/income allocations, internal transfers and asset records without inferring legal classifications. Produce unresolved items and specialist questions. No legal interpretation, entitlement decision, payment approval, certified accounting or record posting. |

Both are new **0.1.0**, R3, draft-only packages in **Wave 9 - wealth management P3**, with recertification date 2027-09-17. They include instructions, schemas, source/control/handoff references, output templates, deterministic scripts and positive/adverse/tampering evaluations. The router is version **0.4.0**. Version and recertification metadata are not institutional approval or proof of evidence freshness.

## Calculation and preparation limits

Family process observations use only the supplied unanimity or majority-of-all-eligible rules and sourced individual positions. They never adopt a decision or manufacture consensus. Succession results describe evidence against supplied criteria, not competence or appointment. Agenda arithmetic sums supplied durations; it does not optimize a calendar or schedule a meeting.

Trust accounting is a USD cash-basis review for one supplied period. Principal and income are classifications of the same cash; reclassifications do not change total cash, and internal transfer legs must reconcile. Gross dated asset totals count cash once and do not subtract liabilities. Accruals, noncash journals, FX and transfers in transit are outside this version. The cash-after-open-requests illustration assumes simultaneous funding after the stated reserve; it excludes unrelated pending expenses and timing optimization, and grants no distribution approval.

## Subject identity and sharing

The existing `wealth-p0-v1` envelope version is retained. Its `household_id` field carries an explicit subject marker for these two specialist scopes:

| Workflow | Required scope | Required marker | Actual client links |
| --- | --- | --- | --- |
| Family governance | `scope_type: family-group`, `family_id` | `family:<family_id>` | Member and actual household identifiers remain on their respective records. |
| Trust administration | `scope_type: trust`, `trust_id` | `trust:<trust_id>` | Trust account, beneficiary and actual household associations remain separately reviewed evidence. |

These subject markers cannot be passed into household discovery, planning, review or servicing as actual client identities. A downstream request needs an explicit reviewed association, the target's own schema and the minimum authorized source material. Unknown associations remain unresolved; relationship alone cannot establish authority, entitlement, participation or sharing permission.

The router adds `family-governance` and `trust-administration`, retains all earlier intents and the `goal-progress` alias, and identifies each target scope. Missing or inconsistent family/trust fields create findings. Reserved book/family/trust markers trigger a separate-subject finding for other targets, even without a scope declaration. Independent review also identified and repaired explicit prospect-case routing to household work: that handoff now requires a separately reviewed subject request. Legacy absence of scope metadata does not authenticate identity.

Family circulation is a separate output concern. Internal snapshots and source registers can contain material that is not authorized for the discussion audience. Use the audience-specific draft and its stated omissions; do not forward the full internal artifact. Neither package sends, schedules, changes records or authenticates consent.

## Evidence and professional decisions

Both packages bundle the canonical [wealth evidence contract](../../shared/wealth-management/wealth_contract.py) and [workflow helper](../../shared/wealth-management/wealth_workflow.py). There are now **26 evidence-contract copies**, **six workflow-helper copies**, and the existing **three P1 analysis-helper copies**. Packages remain self-contained; helpers do not import sibling skills.

Every request has a current source registry, a policy matching the actual engagement capacity/jurisdiction, and an explicit `upstream_issues` inventory. Each issue retains originating artifact ID, code, literal message, unresolved/resolved status and sources. A resolved label requires attributed dated resolution evidence; it does not grant authority. An empty issue list is a reviewed assertion, not an omission default. Unmapped `unresolved_issues` aliases reject.

The router uses `unresolved_issues` plus `upstream_artifact_ids`; map each concern deliberately into the target schema and retain the actual originating evidence. Never substitute the router artifact for a legal interpretation, client instruction or accounting source. Source metadata, hashes and output reconstruction establish consistency, not source truth or authenticated approval.

Family process rules and succession expectations come from supplied attributed records. Trust governing-document precedence, powers, required notices, distribution conditions and principal/income classifications require the actual legal/administrative applicability evidence. Public references orient reviewers; the implementation embeds no universal state trust law, distribution entitlement, family voting rule or legally binding deadline.

## Catalog persistence and prior milestones

Two additions carry source `wealth-management-p3-2026-09-17` in [provisional-additions.json](../../catalog/provisional-additions.json). There are **66 provisional additions**: 47 earlier, five P0, eight P1, four P2 and two P3. [Approved overrides](../../catalog/approved-overrides.json) preserve both earlier renames and current router metadata.

`python tools/build_catalog_from_xlsx.py --from-current` regenerates JSON/CSV from approved current records without the external workbook. The workbook itself remains unchanged. `python tools/sync_wealth_contract.py --check` verifies canonical copies. P0/P1/P2 tests retain earlier workflow and migration checks while permitting later catalog growth; the P3 integration suite asserts exact current totals and metadata.

Earlier milestone scope/results remain in [P0 implementation](P0-IMPLEMENTATION.md), [P1 implementation](P1-IMPLEMENTATION.md), [P2 implementation](P2-IMPLEMENTATION.md) and their linked validation records. P3 completes the agreed P0–P3 authoring priorities without count-driven consolidation.

## Acceptance still required

Implementation completion is separate from institution-specific professional and control-owner acceptance. Real-model evaluation, source-extraction quality, legal/applicability review, authenticated identity/permissions, access and retention controls, live integrations and production release certification remain deployment work. No trust action, payment, investment order, family communication or system-of-record update is performed by this implementation.
