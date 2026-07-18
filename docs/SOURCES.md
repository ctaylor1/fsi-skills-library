# Source Register (v2)

Authoritative sources for the portfolio, the implementation model, and the standards this
library is built to.

## Build plan (authoritative)

The definitive plan is the source workbook, maintained outside this repository:

> `amazon-quick-fsi-skills-2026-catalog-and-build-plan-v2.xlsx`
> (worksheets: Executive Summary · Skill Catalog · Build Matrix · Supplemental Review ·
> Plan Updates · Baseline Changes · Build Standards · Skill Template · Sources)

`tools/build_catalog_from_xlsx.py` regenerates `catalog/skills-catalog.json` and `.csv`
from that workbook.

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
