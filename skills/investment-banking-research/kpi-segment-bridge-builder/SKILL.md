---
name: kpi-segment-bridge-builder
description: >-
  Extract disclosed operational KPIs and build source-linked revenue, margin, volume-price,
  and segment bridges that decompose the change between two reported periods, with every
  component tied to a disclosure and reconciled to the reported totals. Use when a research
  associate asks to "build a revenue or segment bridge", "decompose the change in revenue or
  margin", "split growth into volume vs price vs FX vs M&A", or "reconcile disclosed KPIs to
  the reported total". This skill decomposes DISCLOSED, historical results only: it NEVER
  forecasts or projects any KPI, segment, margin, volume, or price, and it NEVER normalizes
  accounting judgment beyond approved, versioned mappings (no ad-hoc reclassification,
  non-GAAP adjustment, or restatement). It issues no investment recommendation, price target,
  or advice; forecasting routes to the model skills and normalization to financials-normalizer.
license: MIT
compatibility: Amazon Quick Desktop; requires filing-intelligence, disclosed-KPI/MD&A, approved-mapping-registry (versioned), bridge-config (versioned), and entity-resolution MCP integrations (all read-only). Python stdlib only; no network.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Research associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# KPI / Segment Bridge Builder

## Purpose and outcome
Given a company's **disclosed operational KPIs** for two closed, reported periods, extract them
and build a **deterministic, source-linked set of bridges** - revenue, margin, volume-price, and
segment - that decompose the change between the periods, tie every component to its disclosure,
and reconcile the walk to the reported totals. A successful output lets a research associate show
*exactly* what moved a KPI and where each number came from, defensible line by line to a reviewer
or deal team, and hands a reproducible pack (`pack_id`) to downstream forecasting, memo, and
review skills. This is a **historical decomposition only**: the skill **never forecasts** and
**never normalizes accounting judgment beyond approved mappings** - those belong to other skills
and to licensed/accounting humans.

## Use when
- "Build a revenue bridge from FY2024 to FY2025 / decompose the change in revenue."
- "Split the growth into volume vs price vs FX vs M&A/scope, tied to the disclosures."
- "Build a segment bridge that reconciles the segments to the reported total."
- "Bridge the margin change into its disclosed drivers, with a citation on each."
- A research associate needs a tied-out, reproducible KPI decomposition with sources.

## Do not use
- The user wants to **forecast/project** a KPI, segment, margin, volume, or price forward
  (HARD BOUNDARY) -> build the historical bridge, then route the forward work to `dcf-modeler`,
  `three-statement-model-builder`, or `scenario-sensitivity-generator` (see
  [references/handoffs.md](references/handoffs.md)).
- The user wants **accounting normalization/reclassification beyond approved mappings**
  (non-GAAP recasts, restatements, a "cleaner" basis than disclosed) (HARD BOUNDARY) ->
  `financials-normalizer` / accounting policy approves the mapping first.
- The user wants a **recommendation, price target, or valuation verdict** -> licensed-human /
  investment-committee matter; **personalized investment, legal, or tax advice** is likewise.
- The statements are on **inconsistent bases** and need standardizing first -> `financials-normalizer`.
- Full **beat/miss earnings note** with guidance and thesis -> `earnings-results-analyzer`.
- Independent **review** of the finished bridges -> `valuation-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills standardize and supply the
disclosed statements and KPIs; this skill emits a tied-out bridge pack with a durable `pack_id`,
`inputs_hash`, `config_version`, and `mapping_version`; downstream forecasting/memo/review skills
consume it without re-extracting the KPIs. It must not duplicate their forecasting,
normalization, delivery, or review steps.

## Inputs and prerequisites
- **Company identifier** (masked as needed) and **prior/current period** labels and end dates -
  both must be **closed, reported** periods.
- **Reported totals** (the disclosed anchors to reconcile to) as `{value, provenance, citation,
  source_type}`.
- **Bridges** to build - each a `walk` (disclosed signed components: volume, price, FX,
  M&A/scope, mix, or per-segment deltas) or a `volume_price` (disclosed units + price for a
  two-factor decomposition). Every component carries `{amount, provenance, citation,
  source_type, derivation, mapping_id?}`.
- **Approved mappings** (`mapping_version`) for any reclassified/re-mapped component, and the
  **bridge config** (`config_version`) for the decomposition convention and tolerance.
- Read access to filing-intelligence, disclosed-KPI/MD&A, the approved mapping registry, and the
  versioned config (see [references/source-map.md](references/source-map.md)). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filed financials are the anchor; the
disclosed KPI supplement / MD&A supplies the bridge components; the approved mapping registry is
the **only** admissible source of reclassification; versioned config supplies the convention and
tolerance. Every anchor and component resolves to one of these with a dated citation. A filed
total outranks a disclosed component; the walk must still reconcile to the filed total.
**Nothing forward-looking enters a bridge.**

## Workflow
1. **Scope** - confirm company, the prior and current reported periods, currency/units, which
   bridges to build, `config_version`, and `mapping_version`; load the disclosed totals and KPIs.
2. **Validate input** - run [scripts/validate_input.py](scripts/validate_input.py); it **fails
   closed** on a forward-looking `source_type` (never forecast) and on structural gaps, and warns
   on missing provenance, an unapproved `mapping_id`, or a walk that will not tie out.
3. **Build the bridges (deterministic)** - run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): for each `walk`,
   reconcile the disclosed components and compute contributions; for each `volume_price`,
   decompose the delta into volume/price/mix from disclosed units and price under the documented
   convention; reconcile each bridge to the reported totals.
4. **Read the checks** - confirm every bridge ties out and reconciles, every mapping used is
   approved, and every component is in the register with provenance + citation.
5. **Write the pack** - a plain-language narrative of what moved each KPI and why, with the
   component amounts, contributions, and sources - and the standing disclaimer. No forecast, no
   normalization beyond mappings, no recommendation.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check independently re-derives every tie-out (walk sums, volume/price/mix from
factors, contribution sums), re-checks reconciliation to the disclosed totals, rejects any
forward-looking `source_type` and any unapproved mapping, requires provenance + citation on every
register entry plus `config_version`/`mapping_version`/`pack_id`/`inputs_hash`, screens the
narrative for forecast and advice/recommendation language, and requires the disclaimer.
**Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the pack is delivered to a
client, deal team, data room, CRM, or written to a model of record. No approval is needed for the
associate's own read. The skill takes **no action**, makes **no forecast**, and makes **no
accounting-normalization or investment decision**.

## Failure handling
- **Forward-looking input** (`source_type` forecast/guidance/projection/...) -> `validate_input`
  **errors**; the skill never forecasts. Route the forward work to the model skills.
- **Unapproved mapping** (`mapping_id` missing / not approved / not effective) -> warned on input,
  **rejected** on output; route the reclassification to `financials-normalizer` / accounting policy.
- **Walk does not tie out** / does not reconcile to the disclosed total -> fail closed; do not
  present an untied bridge. Re-check the disclosed components and the reported total.
- **Unsourced component** -> warned on input, **rejected** on output; every number needs a source.
- **Conflicting sources** -> keep the filed total as the anchor, record the disclosed component
  as a sourced item, cite both; the walk must still reconcile.
- **Tool timeout** -> return the bridges built so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** - company (masked as needed), the two reported periods, currency/units, and the
   list of bridges with their total change and whether each ties out and reconciles.
2. **Bridges** - per bridge: `beginning`, `ending`, `total_change`, each component's `amount`,
   `contribution`, `derivation`, `source_type`, and `mapping_id`; for `volume_price`, the
   disclosed factors and the volume/price/mix split under the stated convention.
3. **Assumptions register** - every disclosed input (anchors, components, factors, reported
   totals) with `source_type`, `provenance`, and `citation`.
4. **Mapping register** - every `mapping_id` used, with its `status` and `effective_date`.
5. **Model checks** - tie-outs, reconciliation, and mappings-all-approved.
6. **Machine-readable** - the full pack JSON with `pack_id`, `job_id`, `inputs_hash`,
   `config_version`, and `mapping_version` for downstream skills.
7. **Standing disclaimer** - "Historical, source-linked KPI/segment bridge for analytical
   purposes only; a decomposition of disclosed, reported results. It is not a forecast, not
   normalized accounting, not investment advice, and not a recommendation. Every figure ties to a
   disclosed source, and a qualified human must review it before any use."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. KPI extraction and bridges can embed material non-public information
(pre-release results, deal context) - treat the pack, its inputs, `pack_id`, and `job_id` as
need-to-know and respect information barriers / wall-crossing. Retain the pack, its assumptions
and mapping registers, `config_version`, and `mapping_version` per records policy; log the read
and any external-delivery approval. Never exfiltrate MNPI.

## Gotchas
- **A bridge is history, not a forecast.** It explains what already happened between two reported
  periods; the moment a number is forward-looking it is out of scope - route it to the model skills.
- **Only approved mappings normalize.** A "cleaner" segment basis or a non-GAAP recast that is
  not in the approved `mapping_version` is a control failure, not a convenience - get it approved
  first.
- **The walk must reconcile to the disclosed total,** not just internally. Components that sum to
  a made-up ending are not a bridge; reconcile to the filed figure.
- **The volume/price split depends on the convention.** This skill uses base-period weighting
  with an explicit joint (mix) term, stated in the pack; do not silently switch weighting to move
  a component.
- **Contributions can exceed 100% or go negative** (e.g. an FX drag against organic growth) -
  that is correct; the signed components must still sum to the total change.
- **Do not tune to a number.** Convention, tolerance, and the approved mapping set come from
  versioned config; never bend them to reach a wanted decomposition.
