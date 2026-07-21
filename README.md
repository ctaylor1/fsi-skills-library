# FSI Skills Library

Agent Skills for the Financial Services Industry, built for general-purpose AI agent platforms/agentic AI assistant applications, such as Amazon Quick Desktop, Claude Desktop, ChatGPT Desktop, Microsoft Copilot, Google Gemini, Perplexity, and Amazon Kiro.
It is conformant with the [Agent Skills specification](https://agentskills.io/specification).

This repository implements a governed catalog of **173 skills** across **14 functional categories**,
each authored to a common standards-based lifecycle with explicit risk tiers, action
boundaries, human-approval gates, adjacent-skill handoffs, and evaluation packs.

> **Status:** Under active construction. See [STATUS.md](STATUS.md) for exactly what is
> built and what is queued next. The authoritative plan is the source workbook
> (see [docs/SOURCES.md](docs/SOURCES.md)); the machine-readable catalog derived from it
> lives in [catalog/skills-catalog.json](catalog/skills-catalog.json).

## Repository layout

```
fsi-skills-library/
├── README.md                     # This file
├── STATUS.md                     # Build progress tracker (what is built / what is next)
├── LICENSE                       # MIT license (applies to the whole library)
├── catalog/
│   ├── skills-catalog.json       # Machine-readable catalog of all 173 skills
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

### Categories (14)

`banking` · `capital-markets` · `insurance` · `payments` ·
`investment-banking-research` · `wealth-management` · `asset-management` ·
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

Portfolio KPIs: **8 × R1**, **77 × R2**, **79 × R3**, **9 × R4**; **12** skills are
approved as read-only scheduled-agent monitors. Four skills are unchanged from the AWS
baseline, 16 are updated, and 153 are new.

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
