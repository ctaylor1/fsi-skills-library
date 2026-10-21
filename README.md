# FSI Skills Library

Agent Skills for the Financial Services Industry, built for general-purpose AI agent platforms/agentic AI assistant applications, such as Amazon Quick Desktop, Claude Desktop, ChatGPT Desktop, Microsoft Copilot, Google Gemini, Perplexity, and Amazon Kiro.
It is conformant with the [Agent Skills specification](https://agentskills.io/specification).

This repository implements a governed catalog of **395 skills** across **15 functional categories**,
each authored to a common standards-based lifecycle with explicit risk tiers, action
boundaries, human-approval gates, adjacent-skill handoffs, and evaluation packs.

> **Status:** Under active construction. See [STATUS.md](STATUS.md) for exactly what is
> built and what is queued next. The source workbook plus approved additions and overrides
> (see [docs/SOURCES.md](docs/SOURCES.md)) define the catalog in
> [catalog/skills-catalog.json](catalog/skills-catalog.json). Package presence and passing
> deterministic checks are separate from institutional deployment acceptance.

Compliance & Financial Crime Phase 3 adds screening-control evaluation, monitoring
scenario design/effectiveness and case QA, bringing the domain to **38 packages including
its router**. All **36 target workflows** have bounded native methods, with **41 declared
router intents** and two scoped review projections. Existing data, architecture,
AI/model, privacy, vendor and automation owners retain their jobs. Source authentication,
professional/institutional acceptance and production use remain open; Phase4 is pending.
See [Phase3 implementation](docs/compliance-financial-crime/PHASE3-IMPLEMENTATION.md),
[composition](docs/compliance-financial-crime/MODERNIZATION-COMPOSITION.md) and
[validation](docs/compliance-financial-crime/phase3-validation/README.md).

The wealth-management work includes all eight P0, thirteen P1, four P2 and two P3 practitioner
workflows, plus the router. P3 adds family wealth governance preparation and trust administration
review, completing the agreed implementation priorities. See [P3 scope and handoffs](docs/wealth-management/P3-IMPLEMENTATION.md)
and [P3 validation evidence](docs/wealth-management/P3-VALIDATION.md) for delivered behavior. [P4 quality validation](docs/wealth-management/P4-VALIDATION.md) now retains 30 real-model runs across 12 synthetic advisor cases, separate-agent reviews and 20 executable handoff tests. Initial with-skill responses passed 105/111 rubric items, but only 6/12 met every item. Source-fidelity and internal-audience packaging findings remain open; this is not professional or production acceptance.

Payments Phase 1 adds a router and common evidence/lifecycle contracts, corrects operational
calculations and authority boundaries, merges payout explanation into settlement reconciliation,
and moves PCI evidence to cybersecurity. That checkpoint had **18 payment packages** and 239
catalog entries. See [implementation and validation](docs/payments/PHASE1-IMPLEMENTATION.md)
and [source governance](docs/payments/SOURCE-GOVERNANCE.md) for its scope and acceptance evidence.

Payments Phase 2 adds ten core workflows, bringing the domain to **28 packages**: bank
workflow design, initiation controls, regulatory applicability, merchant acceptance, card
programs/lifecycle, economics, routine servicing, architecture and provider evaluation.
Initial US, euro-area and UK profiles include bounded native message inspection and
case-scoped consumer-error/scheme preparation. See [Phase 2 implementation](docs/payments/PHASE2-IMPLEMENTATION.md)
and [validation evidence](docs/payments/phase2-validation/README.md). That checkpoint left
Phase 3/4 capabilities as explicit gaps.

Payments Phase 3 adds six packages and expands two renamed packages, bringing the domain
to **34 packages**. It covers acceptance analytics, fraud controls, credentials, platform
and commercial flows, liquidity, incidents, resilience and operations improvement.
Card/bank workflows gain credential and collection handoffs. See [Phase 3 implementation](docs/payments/PHASE3-IMPLEMENTATION.md)
and [validation evidence](docs/payments/phase3-validation/README.md). That checkpoint
left regional expansion and advanced payment models for Phase 4.

Payments Phase 4 adds four packages, bringing the domain to **38**, and seven optional
modules across six existing packages. It covers regional Pix/UPI/Interac design,
cross-border corridors and liquidity, wallet/mobile money, advanced platform and
commercial cards, stablecoin settlement assessment, company economics and optional
agent-commerce controls. See [Phase 4 implementation](docs/payments/PHASE4-IMPLEMENTATION.md)
and [validation evidence](docs/payments/phase4-validation/README.md). All four agreed
implementation phases are authored; human specialist review, institutional sources
and deployment acceptance remain open. No payment execution capability is added.

Insurance Phase 1 established 23 packages through two workflow mergers and a new router.
Phase 2 added 17 operating foundations. Insurance Phase 3 adds **21 specialist
workflows**, bringing the domain to **61 packages**: strategy/economics, portfolio and
actuarial analysis, claims/recovery/disputes, fraud/SIU, reinsurance, exposure/CAT,
finance/capital/ORSA and market conduct. Native handoffs retain sources, unresolved
issues and professional ownership. See [Phase 3 implementation](docs/insurance/PHASE3-IMPLEMENTATION.md),
[validation evidence](docs/insurance/phase3-validation/README.md) and
[remaining phases](docs/insurance/IMPLEMENTATION-PLAN.md). These offline methods do
not establish professional or deployment acceptance.

Insurance Phase 4 adds **three Insurance and four shared skills**, bringing Insurance
to **64 packages**. Workflow/data/core design, solution architecture, paired automation
assessment, data-product value and queue performance now have native methods and
routes. See [Phase 4 implementation](docs/insurance/PHASE4-IMPLEMENTATION.md) and
[validation, retained findings and acceptance gates](docs/insurance/phase4-validation/README.md).
These are offline draft reviews; source authentication and professional/deployment
acceptance remain separate.

Insurance Phase 5 adds **five specialist review skills**, bringing Insurance to
**69 packages**: parametric triggers and health-payer pricing, utilization, coded-claim
payment and provider networks. Each requires source-bound rules and scoped ownership;
none grants clinical, coverage, payment or network authority. See
[Phase 5 implementation](docs/insurance/PHASE5-IMPLEMENTATION.md) and
[validation evidence](docs/insurance/phase5-validation/README.md).

Insurance Phase 6 adds **acceptance evidence tooling** for the 69 Insurance skills
and four shared dependencies. Portable checks, exact package snapshots and
institution-scoped review records feed a readable dossier; successful software
checks never grant professional or deployment approval. See the
[review guide](docs/insurance/acceptance/README.md) and
[current dossier](docs/insurance/phase6-validation/reviewed-dossier/report.md).

Asset Management Phase 1 establishes **25 AM packages**, a dedicated Investment
Research category with **18 packages**, and Investment Banking with **nine packages**.
It adds declared-intent routing, explicit capability gaps, portable shared resources,
source-bound native validation and reviewed handoff mappings. Two shared investment
data utilities live under Data, AI & Model Governance. See the
[Phase 1 implementation](docs/asset-management/PHASE1-IMPLEMENTATION.md),
[support matrix](docs/asset-management/SUPPORT-MATRIX.md) and
[validation evidence](docs/asset-management/phase1-validation/README.md).
Asset Management Phase 2 adds **29 foundations**, bringing AM to **54 packages**, and
expands institutional proposals, manager diligence and committee modes. It includes
bounded business, portfolio, performance, fund-accounting, ETF/index and private-market
methods, source-linked evidence and portable native validators. See
[Phase 2 implementation](docs/asset-management/PHASE2-IMPLEMENTATION.md) and
[validation evidence](docs/asset-management/phase2-validation/README.md).
At that checkpoint ten capabilities remained planned. Phase 3 added **four modernization
adapters**, bringing AM to **58 packages** at that checkpoint: data architecture, platform modernization,
operating models and AI workflows. They reuse pinned shared methods and include an optional
read-only approved-gateway client, historical data controls, migration/recovery rehearsals
and supplied AI evaluation accounting. See [Phase 3 implementation](docs/asset-management/PHASE3-IMPLEMENTATION.md)
and [validation](docs/asset-management/phase3-validation/README.md). Six specialized
Phase 4 capabilities were still planned at that checkpoint; live gateway, professional and institutional
acceptance remain separate work.


Asset Management Phase 4 adds **six specialist packages** and expands six existing methods, bringing AM to **64 packages**. It covers transitions, financing, private-fund restructuring, sustainability, token-register controls, specialist attribution, supplied-engine derivatives, walk-forward research, ETF baskets, institutional liabilities/real assets and reviewed jurisdiction profiles. Earlier schemas remain supported. See [Phase 4 delivery](docs/asset-management/PHASE4-IMPLEMENTATION.md) and [validation](docs/asset-management/phase4-validation/README.md). Complex models remain supplied engine dependencies; source truth and institutional acceptance remain separate.

Investment Research Phase 1 adds a declared-intent router and supplied-evidence dossier,
repairs native evidence and method controls, renames the issuer capital-structure mapper,
and moves generic document comparison to Data, AI & Model Governance. IR has **19 installed
packages**, including its retained legacy model auditor. The **42-capability roadmap**
has 18 bounded native target methods and 24 planned methods. Source authentication,
reviewed cross-skill expansion and institutional acceptance remain separate. See
[implementation](docs/investment-research/phase1-implementation.md),
[support matrix](docs/investment-research/support-matrix.md) and
[validation](docs/investment-research/phase1-validation/README.md).

Investment Research Phase 2 creates **16 analytical packages** and expands **16 existing
methods**, bringing IR to **34 installed target methods** with eight Phase 3/4 methods
still planned. It retires the legacy model auditor after exact continuity parity,
adds independent formula/economic review, corporate forecast-to-DCF, equity valuation
alternatives, credit/earnings analysis and **five reviewed native adapters**. Passing
software checks does not establish practitioner, institutional or deployment acceptance.
See [Phase 2 implementation](docs/investment-research/phase2-implementation.md) and
[validation](docs/investment-research/phase2-validation/README.md).

Investment Research Phase 3 adds **three controlled research methods**, bringing IR
to **37 installed target methods** with five Phase 4 methods planned. Staged model
updates preserve originals and version observations, corporate-event analysis keeps
conditional terms explicit, and research QA checks requested coverage and declared
arithmetic. Three new reviewed native handoffs bring the total to eight. See
[Phase 3 implementation](docs/investment-research/phase3-implementation.md) and
[validation](docs/investment-research/phase3-validation/README.md).

Investment Research Phase 4 adds **five specialist research methods**, completing
the **42 target packages**: macroeconomic, cross-asset theme, sovereign-credit,
public-finance-credit and structured-credit research. Vintage-aware evidence and
explicit specialist profiles preserve scope and model limits. A ninth reviewed
handoff transfers selected macro observations into theme research without inferring
shocks or causality. See [Phase 4 implementation](docs/investment-research/phase4-implementation.md)
and [validation](docs/investment-research/phase4-validation/README.md). Institutional
acceptance and live integration remain separate.

## Repository layout

```
fsi-skills-library/
├── README.md                     # This file
├── STATUS.md                     # Build progress tracker (what is built / what is next)
├── LICENSE                       # MIT license (applies to the whole library)
├── catalog/
│   ├── skills-catalog.json       # Machine-readable catalog of all 395 skills
│   └── skills-catalog.csv        # Same, spreadsheet-friendly
├── docs/
│   ├── BUILD-STANDARDS.md        # Delivery lifecycle + release gates
│   ├── SKILL-TEMPLATE.md         # Reusable SKILL.md template + section guidance
│   ├── RISK-TIERS.md             # R1–R4 definitions, action modes, approval mapping
│   ├── ARCHETYPES.md             # The 9 build archetypes and their package shapes
│   ├── SHARED-SERVICES.md        # Reusable platform services + MCP/Quick design rules
│   ├── METADATA-SCHEMA.md        # The aws-fsi-* frontmatter metadata contract
│   └── SOURCES.md                # Authoritative source register
├── tools/
│   ├── build_catalog_from_xlsx.py  # Regenerate catalog/ from the source workbook
│   ├── validate_skills.py          # Validate skill packages against spec + standards
│   └── status_report.py            # Recompute STATUS coverage from the filesystem
└── skills/
    └── <category>/<skill-name>/    # One directory per skill (see below)
        ├── SKILL.md                # Required: frontmatter + concise instructions
        ├── references/             # Domain rules, source map, controls, handoffs
        ├── scripts/                # Deterministic validators / transformers
        ├── evals/                  # evals.json + de-identified fixtures
        └── CHANGELOG.md            # Versioned scope/control/tool/data/behavior changes
```

### Categories (15)

`banking` · `capital-markets` · `insurance` · `payments` ·
`investment-research` · `investment-banking` · `wealth-management` · `asset-management` ·
`risk-management` · `compliance-financial-crime` · `finance-operations` ·
`cybersecurity-operational-resilience` · `customer-service-experience` ·
`data-ai-model-governance` · `enterprise-functions-technology`

Skills are grouped by category for navigability, but each skill directory is named
**exactly** as the skill's `name` field (the immediate parent of `SKILL.md`), which is
what the Agent Skills spec requires. The category folder is a grandparent and does not
affect spec validation.

## How the library is governed

Every skill is classified along the dimensions the portfolio plan defines:

- **Risk tier** — `R1` informational · `R2` analytical/drafting · `R3` regulated/control
  decision support · `R4` approval-gated action. See [docs/RISK-TIERS.md](docs/RISK-TIERS.md).
- **Build archetype** — one of 9 patterns (Explain & summarize, Analyze & review,
  Model & calculate, Draft & package, Reconcile & validate, Monitor & alert,
  Investigate & casework, Domain workflow, Orchestrate & resolve). See
  [docs/ARCHETYPES.md](docs/ARCHETYPES.md).
- **Action boundary** — read-only, draft-only, scheduled-read-only, or approval-gated
  write. No skill makes a binding regulated decision, closes a case, files, trades,
  pays, posts, or writes a system of record without a human approval gate.
- **Delivery wave** — the rollout order (W1 stabilize/platform/low-risk → W2 analytical
  → W3 regulated casework → W4 gated orchestration).

Current catalog: **7 × R1**, **126 × R2**, **224 × R3**, **7 × R4** across 15 categories. Risk tiers and catalog status are not proof of operational certification. The source workbook remains separately maintained and unreconciled with local provisional additions.

## Design constraints (Amazon Quick Desktop)

Skills are authored against the constraints documented in [docs/SHARED-SERVICES.md](docs/SHARED-SERVICES.md):

- MCP operations are small, deterministic, least-privilege, idempotent, bounded, and
  complete within the fixed execution timeout; long work is split into resumable stages.
- Tools default to **Read Only** or **Ask Each Time**; mutating operations require
  idempotency, validation, verification, and rollback guidance.
- No assumption of automatic retries or step-up authorization.
- Scheduled agents are restricted to read-only monitoring, freshness checks, briefing,
  or queue creation — never autonomous action.

> **Environment note.** The enterprise systems these skills integrate with (core banking,
> OMS/EMS, KYC/AML, claims, ERP/GL, SIEM/SOAR, etc.) are referenced as required MCP
> integrations. Bundled `scripts/` are **deterministic validators and transformers that
> operate on documented JSON schemas and de-identified fixtures**, not live connectors.
> Wiring skills to real source systems is a deployment-time integration step.

## Validating skills

```bash
python tools/validate_skills.py            # validate the whole library
python tools/validate_skills.py skills/banking/account-anomaly-screener
```

The validator checks the spec rules (name↔directory match, name/description constraints,
frontmatter validity, one-level-deep file references) plus this library's metadata
contract. For the official reference validator, see
[`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref).

## Disclaimer

Everything in this repo is provided as open source software to accelerate agent development and FSI adoption of agents. It is offered "as-is" without warranties or service level agreements. Users are responsible for conducting their own security reviews, dependency audits, and testing before deploying in production, and for keeping installations up-to-date. Breaking changes may occur between releases. While community contributions are welcome, there is no guarantee of support response times, and long-term roadmap decisions remain with the maintainers. Organizations with strict compliance or regulatory requirements should evaluate whether the project's licensing and governance model align with their internal policies.

## License

MIT — see [LICENSE](LICENSE). Individual skills declare `license: MIT` in their
frontmatter.
