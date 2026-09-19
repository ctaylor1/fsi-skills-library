# Wealth management P2 implementation

> Historical P2 milestone. P3 is now implemented; see [current scope](P3-IMPLEMENTATION.md) and [current validation](P3-VALIDATION.md). Counts and planned priorities below describe the original P2 milestone.

Date: 2026-09-17. P2 implements the four agreed practitioner workflows without removing existing coverage. The catalog now contains **237 packages across 14 categories**, including **25 wealth-management packages**. The router selects eight P0, thirteen P1 and four P2 jobs; investor-side manager diligence remains in Asset Management. Implementation verification is recorded separately in [P2 validation](P2-VALIDATION.md).

## Delivered scope

| Priority | Package | Delivered behavior and method limits |
| --- | --- | --- |
| P2.1 | [Advisor book of business review](../../skills/wealth-management/advisor-book-of-business-reviewer/SKILL.md) | Builds a policy-ranked service queue, household review calendar, dated owner workload and practice measures. Preserves life events, retention concerns and explicit client-requested growth. Reconciles opening-cohort retention, asset bridges and external flows. Unknown population/capacity/economics stays unknown; revenue cannot outrank client service. No CRM update, appointment, reassignment or predictive client score. |
| P2.2 | [Wealth prospect and referral preparation](../../skills/wealth-management/wealth-prospect-referral-preparer/SKILL.md) | Creates a permitted-source brief and service-discussion questions. Separately checks research use, referrer sharing, channel permission, global/channel suppression, incentives/conflicts and attributed specialist reviews. Produces a sourced email or manual-phone draft only when all supplied checks are complete. No scraping, enrichment, prospect qualification, contact or CRM write. |
| P2.3 | [Wealth lending and liquidity review](../../skills/wealth-management/wealth-lending-liquidity-reviewer/SKILL.md) | Compares protected cash, supplied liquidation proceeds and quoted unsecured, property-secured or non-purpose securities-backed facilities. Separates new proceeds from total facility debt, models monthly amortization/interest and fees, and stresses rates, collateral prices and advance rates. Keeps demand repayment and balloon risk visible. No APR calculation, tax inference, product selection, credit decision or borrowing. |
| P2.4 | [Private-market client review](../../skills/wealth-management/private-market-client-reviewer/SKILL.md) | Reconciles commitments, typed capital/distribution notices, linked settlements and forecast calls. Separates remaining commitments, unpaid called reserves and uncalled amounts; projects dated cash by account without assumed transfers or anticipated distributions. Preserves eligibility evidence, stale/unknown NAV and manager-diligence findings. No subscription, eligibility determination, performance calculation, payment or investment selection. |

Each package includes substantive instructions, a documented schema, source and control references, explicit handoffs, an output template, deterministic scripts and positive/adverse/tampering fixtures. New packages are version **0.1.0**, R3, draft-only, Wave 8, with recertification date 2027-09-17. The router is version **0.3.0**. These metadata dates do not attest source freshness or institutional approval.

## Shared evidence and subject scope

The existing `wealth-p0-v1` envelope remains compatible. Its name identifies the envelope version, not the implementation priority. Twenty-four byte-identical copies of [wealth_contract.py](../../shared/wealth-management/wealth_contract.py) now support the selected P0/P1/P2 packages. The three P1 analysis-helper copies remain unchanged.

All four P2 workflows use [wealth_workflow.py](../../shared/wealth-management/wealth_workflow.py) for strict finite Decimal parsing, dated policy applicability, source-linked findings, input preservation, full output reconstruction and command-line handling. Domain rules specify supported precision and rounding. Lending uses monetary inputs at cent precision and rounded monthly interest; other packages document their own rounding conventions. All four helpers are bundled locally so packages do not import sibling skills.

Every P2 request requires an explicit current policy matching engagement capacity and jurisdiction, a source registry with dated review windows, and `upstream_issues`. Each issue retains `{artifact_id, code, message, status, source_ids}`. A resolved record also needs attributed, dated resolution evidence and citations. Empty lists require reviewed scope; omitted lists or an unmapped top-level `unresolved_issues` alias reject. Missing item citations remain findings. A ready label never resolves a concern from an originating artifact.

Book review has a distinct collection scope: `scope_type: advisor-book`, `book_id`, and envelope `household_id: book:<book_id>`. Actual household IDs remain on roster, action and economic records. One professional capacity applies to each run. A downstream household job needs a new, reviewed request for the actual household; the book marker is never a client identity. Unallocated book concerns remain with the practice owner until affected households are determined.

Prospect review may use an explicitly provisional case identifier. It never authenticates a CRM match or treats a referral as contact permission. The affirmative-permission requirement is this package's deliberately bounded workflow, not a universal statement of US marketing law. Only email and manual-phone drafts are implemented.

Lending and private-market financial models are bounded to USD. Lending alternatives are standalone comparisons, never additive cash resources. Private-market obligations retain their actual account funding perimeter; household liquidity does not establish inter-account transfer authority.

## Router and handoffs

The [router](../../skills/wealth-management/wealth-management-router/SKILL.md) adds `book-review`, `prospect-referral`, `lending-liquidity` and `private-markets`. It preserves all earlier intents and the `goal-progress` planning alias. Steps identify book, prospect or household scope; mixed book/household requests surface a separation finding. The router selects requested workflows and executes none of them.

Router inputs use `unresolved_issues` and `upstream_artifact_ids`. Map each concern to the target P2 `upstream_issues` schema with its actual originating artifact ID and status. Merge source identities deliberately; never substitute the router artifact for the financial evidence or discard a concern to satisfy a narrower schema. Validate each target separately.

The private-market skill consumes investor-side manager due diligence and owns client commitment/cash/eligibility records. It does not duplicate manager selection analysis. Lending consumes household budget/reconciliation and separately reviewed liquidation tax assumptions. Book review directs household work; prospect preparation hands off to actual discovery after a documented conversation. Each package's handoff reference defines the exact evidence and boundary.

## Catalog persistence and prior milestones

Four additions carry source `wealth-management-p2-2026-09-17` in [provisional-additions.json](../../catalog/provisional-additions.json). There are **64 provisional additions**: 47 earlier, five P0, eight P1 and four P2. [Approved overrides](../../catalog/approved-overrides.json) preserve the P0 recommendation-review rename, P1 household-planning rename and current router metadata.

`python tools/build_catalog_from_xlsx.py --from-current` regenerates the current JSON/CSV using approved records when the external workbook is unavailable. Regeneration is idempotent. The external workbook has not been changed. `python tools/sync_wealth_contract.py --check` verifies all 24 contract, three analysis and four workflow copies.

[P0 implementation](P0-IMPLEMENTATION.md), [P0 validation](P0-VALIDATION.md), [P1 implementation](P1-IMPLEMENTATION.md) and [P1 validation](P1-VALIDATION.md) preserve the earlier milestone scope and results. P1 regression assertions now permit later catalog growth while continuing to enforce P1 metadata, migrations, financial behavior and destinations; the P2 integration tests assert the exact current totals.

## Remaining priorities and acceptance

| Priority | Planned package | Professional job |
| --- | --- | --- |
| P3 | family-wealth-governance-preparer | Family decision processes, succession and next-generation discussions |
| P3 | trust-administration-reviewer | Governing-document obligations, beneficiary matters, distributions and accounting evidence |

P3 is retained in the plan and is not implemented or cataloged in this milestone. P2 completion means authored packages and the recorded deterministic/independent checks. Wealth-professional and compliance acceptance, real-model evaluation, authenticated sources, institution-specific privacy/records controls and live integration certification remain deployment work. No external account action or client communication was performed.
