# Wealth management P0 implementation

Historical P0 milestone. Current scope and verification are in [P1 implementation](P1-IMPLEMENTATION.md) and [P1 validation](P1-VALIDATION.md). Counts and behavior below describe P0 at its completion.

Date: 2026-09-16. Scope: the eight prioritized practitioner workflows plus a routing entrypoint. Five packages were added and four revised; the recommendation reviewer was renamed. No skills were removed to reduce the portfolio size. The catalog now contains 225 packages, including 14 wealth-management packages.

## Delivered scope

| Priority | Workflow | Package | Change |
| --- | --- | --- | --- |
| P0.1 | Client discovery | `wealth-client-discovery-assistant` | New: cited household facts, goals, constraints and missing discovery evidence |
| P0.2 | Household data reconciliation | `household-wealth-data-reconciler` | New: account inventory, ownership shares, held-away coverage, conflicts and partial totals |
| P0.3 | Onboarding | `wealth-onboarding-packager` | New: relationship/account documentation and external review evidence under firm policy |
| P0.4 | Risk profile | `investment-risk-profile-reviewer` | New: separate willingness, capacity, liquidity, horizon, experience and constraints |
| P0.5 | Recommendation evidence | `investment-recommendation-evidence-reviewer` | Renamed/rebuilt: complete evidence inventory, applicability, costs, alternatives, disclosures and conflicts |
| P0.6 | Investor protection | `senior-investor-protection-screener` | Revised: unknown observations, bounded history, contextual applicability and substantive output validation |
| P0.7 | Client review | `client-review-preparer` | Revised: dated sources, review-type/disclosure applicability, substantive pack and bound lineage |
| P0.8 | Advisor follow-up | `advisor-follow-up-assistant` | Revised: sourced meeting facts, usable correspondence, task details and communication review handoff |
| Support | Workflow selection | `wealth-management-router` | New: eight explicit routes, preserved engagement context, visible unsupported intents |

P0 means implementation priority, not production certification. All nine packages produce analysis or drafts with required human review. There are no new trading, transfer, account-opening, sending or record-writing integrations.

## Evidence and handoffs

The canonical helper is [wealth_contract.py](../../shared/wealth-management/wealth_contract.py). Identical copies are bundled in seven packages so they remain installable independently. Use `python tools/sync_wealth_contract.py --check` to detect drift; change the canonical file and rebundle deliberately when revising the contract.

The common `wealth-p0-v1` envelope requires a request, household, professional capacity, jurisdiction, as-of date and source registry. Source owners, dates and review validity are mandatory. Domain evidence retains item citations and explicit missingness. Malformed envelopes fail validation; incomplete domain evidence remains needs-data or the package's documented blocked state.

Each substantive artifact retains structured input evidence and an input-bound identifier, then checks output content against that input. Hashes detect inconsistent edits and support lineage; they are not authentication, professional approval or proof that the underlying sources are true. A consistently fabricated input and output can pass structural checks. The application must enforce source access, reviewer identity and approval authenticity.

Client-review and follow-up retain their existing schemas with stricter requirements. The router documents field mapping and target validation; it does not provide an automatic pipeline or universal adapter. Recommendation evidence now requires a structured unresolved-issues list for every evidence record; upstream risk concerns carry citations and artifact references and cannot be cleared by a documented label. A shared envelope or review-ready flag does not make an artifact valid input for another workflow. All handoffs must retain unresolved findings, source lineage and minimum necessary context.

## Migration

- `suitability-reg-bi-reviewer` becomes `investment-recommendation-evidence-reviewer`. Update installed skill directories, manifests, saved prompts and external handoffs. There is no runtime redirect or duplicate legacy package.
- Recommendation, protection, client-review and follow-up are version 0.2.0 with stricter, potentially breaking input/output contracts. Regenerate artifacts from source using each current schema and validator; old outputs cannot be assumed compatible.
- New packages are version 0.1.0. Fixtures are synthetic and configuration examples are illustrative, not approved firm policies.
- [approved-overrides.json](../../catalog/approved-overrides.json) persists renames and revised metadata across workbook regeneration. Five additions are recorded in [provisional-additions.json](../../catalog/provisional-additions.json), alongside the prior 47 additions. `build_catalog_from_xlsx.py --from-current` applies these approved changes without the external workbook; normal workbook regeneration applies the same merge.
- External handoff names were updated throughout the library. Those reference edits do not certify or otherwise harden the receiving packages.

## Quality gates and verification

Use an environment with Python 3.10+, PyYAML and Ruff; openpyxl is additionally needed only for workbook import. The package validator now fails if PyYAML is unavailable instead of reporting an unvalidated pass.

```sh
python tools/validate_skills.py
python tools/check_handoffs.py
python tools/sync_wealth_contract.py --check
python tools/test_wealth_p0.py
python tools/run_selftests.py
ruff check --select E4,E7,E9,F --ignore E401,E702,E731,E741 tools shared skills
```

The explicit lint selection retains this repository's existing error rules across Ruff versions. `temp/` is unrelated untracked reference material and is excluded from this implementation's checks.

Verification results and independent forward-test observations are recorded in [P0-VALIDATION.md](P0-VALIDATION.md). Executable fixture and regression checks establish deterministic behavior under tested inputs. Natural-language cases in `evals.json` are specifications, not automatically executed model evaluations. Independent agent scenarios are a limited additional check; they are not wealth-professional acceptance or a production benchmark.

## Remaining release gates

Before institutional deployment, obtain wealth-domain and compliance acceptance of realistic cases for each professional capacity; install authenticated read-only sources and firm-controlled applicability/policy profiles; integrate reviewer identity, retention, access control and audit records; and run deployment-specific agent selection and output-quality evaluation. The scripts cannot establish those controls by checking strings in JSON.

At this milestone, P1 remained separate and the five other wealth packages retained their earlier implementations. The subsequent [P1 implementation](P1-IMPLEMENTATION.md) revises those packages and delivers all thirteen agreed P1 workflows, including replacement of the earlier rebalancing approval/execution design with a draft-only transition model.
