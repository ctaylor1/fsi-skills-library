---
name: coverage-initiation-researcher
description: >-
  Develop an initiating-coverage research draft on an equity — business model, industry,
  competitive position, forecasts, catalysts, risks, valuation triangulation, and a cited
  investment thesis — assembled from filings, market data, the research corpus, and linked
  model outputs. Use when an equity-research analyst says "initiate coverage on X", "build
  the initiating-coverage draft/thesis", "pull the business, industry, forecast, and
  valuation together to start coverage", or needs a reviewer-ready, fully cited draft with a
  deterministic readiness check. HARD BOUNDARY: produces a DRAFT only — it never issues an
  approved rating or price target, never gives personalized investment advice, never uses
  guarantee/certainty language, never admits MNPI, and never publishes or delivers. Rating,
  price-target, Reg AC certification, and publication are supervisory analyst and research
  committee decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings, research-corpus, model-artifact, and versioned-config MCP integrations (all read-only); no research-portal or client-delivery write.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Equity-research analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Coverage Initiation Researcher

## Purpose and outcome
Guide an equity-research analyst through the multi-step procedure of assembling an
**initiating-coverage draft**: business model, industry, competitive position, forecast,
catalysts, risks, valuation, and a cited investment thesis. The skill grades section
completeness and evidence coverage, checks the forecast for internal consistency,
triangulates a **draft valuation range** from linked model outputs, and maps the result to a
deterministic **readiness band**. A successful output is a fully cited, reproducible draft a
supervisory analyst can review — the rating, price target, and decision to publish remain
human/committee actions.

## Use when
- "Initiate coverage on X" / "build the initiating-coverage draft or thesis."
- "Pull the business, industry, forecast, catalysts, risks, and valuation together to start
  coverage" on a company.
- The analyst needs a consistent, cited, reviewer-ready draft with a readiness check before
  handing it to a supervisory analyst.

## Do not use
- The user wants **personalized investment advice** ("should I buy this?") or a **guaranteed
  return** → out of scope; the skill drafts evidence, not advice.
- The user wants an **approved rating, price target, or a published note** → those are
  supervisory analyst + research committee decisions; the skill produces a draft only.
- The task is a single component, not the whole draft: build the DCF → `dcf-modeler`; trading
  comps → `comps-analysis-builder`; the operating model → `three-statement-model-builder`;
  post-earnings beat/miss → `earnings-results-analyzer`; industry map → `market-landscape-researcher`.
- Any input carries **MNPI** or wall-crossed data → stop; research operates on public /
  approved-internal sources only.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill **cites** model outputs
(DCF, comps, three-statement) rather than recomputing them, and emits a durable `coverage_id`.
Rating approval, price-target sign-off, Reg AC certification, and publication route to the
supervisory analyst and research committee (human actions, not skills).

## Inputs and prerequisites
- Ticker + company name, `as_of` date, analyst id, and `config_version`.
- A **coverage dossier**: the eight required sections each with cited claims; a `forecast`
  block (years, revenue, ebit_margin, citations); a `valuation` block (method values +
  weights + citations); a proposed rating label; and an `mnpi_attestation`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filings, market data, the research corpus, and linked model artifacts; the
  versioned coverage config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filed disclosures are the position
of record; market data and company disclosure add point-in-time context; model outputs feed
the forecast and valuation. A management assertion never overrides a filed figure. **MNPI must
never enter the draft.** Cite every claim, series, and valuation input to a source.

## Workflow
1. **Scope & attest** — confirm the ticker, `as_of`, and config version; confirm the
   `mnpi_attestation`; validate the dossier with `validate_input`.
2. **Grade sections (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to score each
   required section present/evidenced and compute evidence coverage.
3. **Check the forecast** — recompute revenue growth, tie out any supplied growth, and bound
   margins; blocking errors surface rather than being smoothed over.
4. **Triangulate valuation (draft only)** — assemble a `draft_value_range` and, when weights
   are valid, a blended midpoint from the linked DCF/comps outputs. This is an analytical
   range, **not** a price target.
5. **Map readiness** — map completeness + consistency + evidence to Not ready / Analyst
   review / Ready for supervisory review per the documented mapping.
6. **Write the draft** — plain-language, fully cited sections + the forecast + the draft
   valuation range + the proposed (draft-unapproved) rating + the DRAFT banner + disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every required section is present and evidenced; readiness
ties out deterministically; valuation is complete; the proposed rating stays draft-unapproved;
MNPI is attested; there is no advice/decision or approved rating/price-target language; and
the DRAFT banner + disclaimer are present. **Fail closed on any miss.**

## Human approval
`external-delivery`: supervisory analyst and research committee approval is required before
the draft is published, sent to a client, or written to the research system of record. No
approval is needed for the analyst's own read. The skill never issues an approved rating or
price target and never delivers.

## Failure handling
- **Missing / unevidenced section** → readiness is Not ready; list the gaps; never fabricate
  a section to clear the gate.
- **Forecast inconsistency** (growth mismatch, out-of-bounds margin, non-ascending years) →
  blocking error; surface it, do not silently "fix" the numbers.
- **Incomplete valuation** (uncited method, weights ≠ 1) → no blended midpoint; report the
  range only and mark Not ready.
- **MNPI attestation false / suspected MNPI** → stop; do not proceed to delivery.
- **Stale/conflicting sources** → cite both; flag for the analyst; do not resolve silently.
- **Tool timeout** → return the sections graded so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — company/ticker, `as_of`, evidence coverage, readiness band, proposed
   (draft-unapproved) rating.
2. **Sections** — each required section, plain-language, with cited claims; missing/unevidenced
   sections listed explicitly.
3. **Forecast** — the series with recomputed growth and any consistency findings.
4. **Valuation** — the `draft_value_range` and blended midpoint (draft range, not a price
   target), each method cited.
5. **Machine-readable** — the coverage pack + `coverage_id` for downstream use.
6. **DRAFT banner + standing disclaimer** — "DRAFT — not approved for distribution." and the
   research disclaimer.
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Enforce the information wall; keep MNPI out
of the draft. Retain the draft + citations + `config_version` per records policy; log the read
and any external-delivery approval. Never exfiltrate client-confidential or wall-crossed data.

## Gotchas
- **A readiness band is not a decision.** "Ready for supervisory review" means the draft is
  complete and cited — not that the thesis is right, the rating approved, or delivery cleared.
- **The valuation range is not a price target.** A triangulated draft range is analytical;
  the price target is an approved house call the committee owns.
- **Independence over the mandate.** Do not tilt the thesis to win or protect banking
  business; present downside as fully as upside.
- **Cite the model, don't rebuild it.** Reference the DCF/comps/three-statement artifacts;
  recomputing them here breaks lineage and duplicates work.
- **MNPI is a hard wall.** If in doubt about a figure's provenance, leave it out and flag it.
