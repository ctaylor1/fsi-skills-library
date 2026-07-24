---
name: capital-structure-maturity-mapper
description: >-
  Build a descriptive capital-structure and maturity-wall map from a company's debt schedule —
  totals by instrument type and seniority, secured vs unsecured split, the maturity wall by year,
  weighted-average maturity and coupon, and near-term maturities — as a source-linked packet for
  a debt-capital-markets analyst. Use when an analyst asks to "map the capital structure",
  "build the maturity wall", "summarize the debt stack by seniority", or "what's maturing in the
  next two years". HARD BOUNDARY: R2 draft/packaging — it is descriptive only; it NEVER gives
  financing advice, recommends refinancing/issuance, opines on the "optimal" structure, or
  suggests a transaction; a banker owns all advice. MNPI/information-barrier controls apply.
  Routes financing-cost comparison to financing-alternatives-calculator.
license: MIT
compatibility: Amazon Quick Desktop; requires debt-schedule/reference-data MCP integrations (all read-only). Deterministic stdlib-only computation. MNPI-aware.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Debt-capital-markets analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Capital Structure & Maturity Mapper

## Purpose and outcome
Given a company's debt schedule, deterministically build a descriptive capital-structure and
maturity-wall map: totals by instrument type and seniority, secured/unsecured split, the maturity
wall by year, weighted-average maturity and coupon, and near-term maturities — each tied to source
lines. A successful output is a factual map an analyst uses; all financing advice remains the
banker's.

## Use when
- "Map the capital structure", "build the maturity wall", "summarize the debt stack by seniority".
- "What's maturing in the next two years", "what's the weighted-average maturity".
- An analyst needs a consistent, cited capital-structure summary.

## Do not use
- The user wants **financing advice / a recommendation** (refinance, issue, optimal structure) →
  out of scope; the banker advises.
- The user wants **cost comparison across financing alternatives** → route to
  `financing-alternatives-calculator`.
- The user wants **covenant terms** extracted → `credit-terms-covenant-extractor`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a map packet with a durable `map_id`;
it does not advise or recommend.

## Inputs and prerequisites
- The **company** (id, name, as_of) and **instruments** (type, seniority, principal, currency,
  coupon_pct, maturity_date, secured). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Single reporting currency assumed; mixed currency is flagged. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The debt schedule is the system of
record; cite every total to the contributing instrument lines.

## Workflow
1. **Validate input** — run `validate_input`; confirm instruments with principal and maturity.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): totals by type and
   seniority, secured/unsecured, maturity wall by year, WAM, WAC, near-term maturities.
3. **Assemble the map** — buckets, weighted averages, near-term wall, source lines.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   total tie-outs, the no-advice screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If the seniority/maturity buckets do not sum to
total debt, or the text contains advice/recommendation language, **fix or fail closed**.

## Human approval
`external-delivery`: the map may be produced, but external delivery requires human sign-off; no
advice or recommendation is ever made by this skill.

## Failure handling
- **Mixed currencies** → do not sum across currencies; group by currency and flag; never apply an
  FX rate that was not supplied.
- **Missing maturity/principal** → exclude from the affected metric and flag; never impute.
- **Undated perpetual/other** → bucket as `undated`, not forced into a year.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — company (masked as needed), as_of, total debt, WAM, WAC.
2. **By seniority / by type / secured-unsecured** — totals.
3. **Maturity wall** — by year, plus near-term (≤24m) total.
4. **Machine-readable** — buckets + weighted averages + `map_id` + source lines.
5. **Standing disclaimer** — "Descriptive capital-structure map only; not financing advice, a
   recommendation, or a view on the optimal structure. No transaction is suggested."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Enforce information barriers; restrict to the deal team. Retain map +
source lines + as_of. Log read + external-delivery approval. Never cross the wall.

## Gotchas
- **Description is not advice.** A large near-term wall is a fact to present, never a "should
  refinance".
- **Weighted-average maturity** is principal-weighted years-to-maturity from as_of — state the
  as_of.
- **Currency**: never sum mixed currencies without a supplied FX basis; group and flag instead.
- **Never rank or label a structure as good/bad/optimal.**
