# Approved architecture decisions

Decision date: 2026-09-20. User authorized Phase 1 implementation after reviewing these
recommendations. These are library design decisions, not regulatory requirements.

## ADR 1 — first-class investment research

Use `skills/investment-research` for reusable company/issuer/security/industry research,
forecasts, financial models, earnings, credit evidence and analytical valuation.
Use `skills/investment-banking` for M&A, financing, capital raising and transaction
advisory workflows. AM owns applying research to portfolios, mandates and investment
decisions. Shared data utilities live under Data, AI & Model Governance.

Preserve stable skill identifiers when only category changes. Renames and mergers have
explicit aliases and mode mappings. Existing sell-side publication controls remain
explicit; relocation alone does not generalize a workflow or grant access to MNPI.
Research valuation estimates remain distinct from accounting fair-value review,
transaction opinions and household advice.

## ADR 2 — portable artifacts, canonical source

Every released skill is internally complete for its declared local mode and runtime.
Canonical shared helpers/references are bundled with versions, hashes and licenses;
generated copies are never edited independently. Required professional skills and
enterprise engines are declared dependencies, not copied workflows. A router neither
installs nor launches another skill. Missing deployment availability stays unknown.

No required library-wide runtime is introduced. Isolated-installation tests verify
local portability, not institutional acceptance. Shared fixes require deliberate
rebuilds and regression validation rather than silent floating upgrades.

## ADR 3 — transparent calculations and explicit engines

Bounded local methods implement documented, independently testable calculations.
Specialist analytics use explicit engine contracts; an engine may be a local approved
library, institutional service or external provider. Authoritative production NAV,
books and risk come from designated institutional systems. Local challenge calculations
are identified as such. Approval and validation apply to local and external methods.

Every result identifies inputs, method/implementation version, assumptions, dates,
currencies/units, scope, gaps, tolerances and origin. The model explains and organizes;
deterministic code/engines perform arithmetic. No silent simplified fallback when an
engine, licensed data, model or required input is unavailable.
