# Source Register (v2)

Authoritative sources for the portfolio, the implementation model, and the standards this
library is built to.

## Build plan (authoritative)

The definitive plan is the source workbook, maintained outside this repository:

> `amazon-quick-fsi-skills-2026-catalog-and-build-plan-v2.xlsx`
> (worksheets: Executive Summary · Skill Catalog · Build Matrix · Supplemental Review ·
> Plan Updates · Baseline Changes · Build Standards · Skill Template · Sources)

`tools/build_catalog_from_xlsx.py` regenerates `catalog/skills-catalog.json` and `.csv`
from that workbook, then applies approved repository additions and overrides.

The 2026 industry expansion contributes 47 provisional additions. The user-approved
wealth-management implementation contributes five P0 additions (2026-09-16), eight P1,
four P2 and two P3 additions (2026-09-17), for 66 total in
`catalog/provisional-additions.json`. Renames and revised metadata are maintained in
`catalog/approved-overrides.json` and applied after additions, so workbook regeneration
does not resurrect the old recommendation-review or goal-progress names. The workbook itself was not
changed in this implementation. `--from-current` refreshes the catalog from these approved
changes when the external workbook is unavailable. See
[wealth P0 scope](wealth-management/P0-IMPLEMENTATION.md), [P1 scope](wealth-management/P1-IMPLEMENTATION.md), [P2 scope](wealth-management/P2-IMPLEMENTATION.md), and [P3 scope](wealth-management/P3-IMPLEMENTATION.md).

## Specification & authoring standard

| Source | URL | Use |
| ------ | --- | --- |
| Agent Skills normative specification | https://agentskills.io/specification | Required directory and SKILL.md format, naming, metadata, progressive disclosure, file references, and validation. |
| Agent Skills authoring best practices | https://agentskills.io/skill-creation/best-practices | Coherent scope, real expertise, progressive disclosure, gotchas, templates, validation loops, plan-validate-execute. |
| Agent Skills official repository | https://github.com/agentskills/agentskills | Reference implementation, examples, `skills-ref` validator, open format. |

## Platform (Amazon Quick Desktop)

| Source | URL | Use |
| ------ | --- | --- |
| Amazon Quick skills and agents | https://docs.aws.amazon.com/quick/latest/userguide/skills-and-agents-desktop.html | Skill creation, attached tools/files, auto-selection, scheduled agents, local execution constraints. |
| Amazon Quick MCP integration | https://docs.aws.amazon.com/quick/latest/userguide/mcp-integration.html | Remote MCP actions, authentication, fixed timeout, static tool lists, failure handling, authorization limits. |
| Amazon Quick desktop security | https://docs.aws.amazon.com/quick/latest/userguide/desktop-security.html | Local data handling, folder controls, system-tool permission model, privacy controls. |

## Regulatory & risk references (per-skill `references/domain-rules.md` cites these)

| Source | URL |
| ------ | --- |
| 2026 FINRA Annual Regulatory Oversight Report | https://www.finra.org/rules-guidance/guidance/reports/2026-finra-annual-regulatory-oversight-report |
| Bank of England / FCA — AI in UK financial services 2024 | https://www.bankofengland.co.uk/report/2024/artificial-intelligence-in-uk-financial-services-2024 |
| FSB — monitoring AI adoption and vulnerabilities | https://www.fsb.org/2025/10/monitoring-adoption-of-artificial-intelligence-and-related-vulnerabilities-in-the-financial-sector/ |
| EIOPA Opinion on AI governance and risk management | https://www.eiopa.europa.eu/eiopa-publishes-opinion-ai-governance-and-risk-management-2025-08-06_en |
| NAIC 2026 strategic priorities | https://content.naic.org/article/naic-spring-national-meeting-advance-modernization-resilience-and-consumer-protection |
| Swift ISO 20022 implementation FAQ | https://www.swift.com/standards/iso-20022/iso-20022-faqs/implementation |
| PCI DSS v4.0.1 publication | https://blog.pcisecuritystandards.org/just-published-pci-dss-v4-0-1 |
| World Economic Forum — Future of Jobs 2025 | https://www.weforum.org/publications/the-future-of-jobs-report-2025/in-full/4-workforce-strategies/ |
| NIST AI Risk Management Framework | https://www.nist.gov/itl/ai-risk-management-framework |

> These are **orientation references** for authoring, not a substitute for the firm's own
> approved, jurisdiction-specific policy and rule sources. Each skill's source hierarchy
> requires the firm's controlled sources to take precedence, with citations, effective
> dates, versions, and owners.

## Payments Phase 1 — 2026-09-17

The user-approved implementation adds payment-specific aliases/merge/move records in [catalog/payments-phase1-migrations.json](../catalog/payments-phase1-migrations.json), durable overrides in approved-overrides.json and the router in provisional-additions.json. External workbook reconciliation remains pending; regeneration retains these approved changes. [Payments source governance](payments/SOURCE-GOVERNANCE.md) distinguishes orientation sources, current rule profiles, licensed distribution and deployment verification.

## Payments Phase 2 — 2026-09-18

Ten user-authorized packages are recorded in provisional-additions.json under
Payments Phase 2. Router/dispute metadata changes are preserved by catalog additions
and overrides. The external workbook is unchanged. Initial native rail/message and
consumer-error/scheme profiles retain explicit scope, current source references,
review intervals and unsupported adapters; see [source governance](payments/SOURCE-GOVERNANCE.md)
and [implementation](payments/PHASE2-IMPLEMENTATION.md).

## Insurance Phase 1 — 2026-09-18

The user-approved implementation records 15 legacy aliases and two mergers in
[insurance migrations](../catalog/insurance-phase1-migrations.json). The resulting
23 packages include the new router. Approved overrides preserve names, scope and
metadata when the catalog is regenerated; provisional additions include the router.
These are repository-approved changes, not edits to the external workbook.
[Insurance source governance](insurance/SOURCE-GOVERNANCE.md) separates primary
orientation references, supplied source assertions, applicable institutional rules,
licensed resources and professional acceptance. The common insurance artifact
contract is an engineering convention, not a regulatory standard or authentication
mechanism. See [implementation](insurance/PHASE1-IMPLEMENTATION.md) and
[validation evidence](insurance/validation/README.md).

## Payments Phase 3 — 2026-09-18

Six additions, two expanded renames and existing module metadata are preserved in
provisional additions/approved overrides and [migration records](../catalog/payments-phase3-migrations.json).
The source workbook is unchanged; approved catalog regeneration is tested. Public
FedNow orientation was refreshed to April 2026 v3.6 in the rail and native-message
registries. Credential and operating references are documented in package source
maps and [source governance](payments/SOURCE-GOVERNANCE.md). See
[implementation](payments/PHASE3-IMPLEMENTATION.md) and [validation](payments/phase3-validation/README.md)
for scope, retained evidence, corrected findings and outstanding acceptance gates.

## Insurance Phase 2 — 2026-09-18

Seventeen user-authorized operating foundations are recorded in
[the phase manifest](../catalog/insurance-phase2-capabilities.json) and provisional
additions; the router's Phase 2 metadata is preserved on catalog regeneration. The
external workbook is unchanged. Native source profiles, shared context mappings,
synthetic forward evaluation and remaining source/professional acceptance are
separated in [source governance](insurance/SOURCE-GOVERNANCE.md),
[implementation](insurance/PHASE2-IMPLEMENTATION.md) and
[validation evidence](insurance/phase2-validation/README.md).

## Payments Phase 4 — 2026-09-18

Four new provisional additions and approved metadata overrides preserve the
regional/corridor, wallet, stablecoin and business-model scope through catalog
regeneration. Seven optional modules extend six installed packages without a
rename or a source-workbook edit. The singular business-model package replaces an
uninstalled proposal label only. Primary operator/regulator/protocol references
and explicit review limits are recorded in [source governance](payments/SOURCE-GOVERNANCE.md)
and the package source maps. Public references do not prove institution access,
provider authorization or conformance. See [scope](payments/PHASE4-IMPLEMENTATION.md)
and [validation](payments/phase4-validation/README.md).

## Insurance Phase 3 — 2026-09-18

Twenty-one user-authorized specialist packages are recorded in
[the phase manifest](../catalog/insurance-phase3-capabilities.json) and provisional
additions. Router metadata and four existing-package guide/version updates are
preserved by approved overrides. The source workbook is unchanged. Source-bound
native methods, independent synthetic evaluations, corrected interface/benefit
findings and separate professional acceptance gates are recorded in
[implementation](insurance/PHASE3-IMPLEMENTATION.md),
[validation](insurance/phase3-validation/README.md) and
[source governance](insurance/SOURCE-GOVERNANCE.md).
