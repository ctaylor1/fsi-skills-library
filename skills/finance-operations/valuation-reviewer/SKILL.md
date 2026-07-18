---
name: valuation-reviewer
description: >-
  Review a valuation for correctness and control: check fair-value-hierarchy classification
  against input observability, input freshness and traceability, comparables, valuation
  adjustments and reserves, Level 3 uncertainty disclosure, manual overrides, and
  independent-price-verification (IPV) evidence — surfacing findings with cited evidence and
  a suggested review disposition. Use when a valuation, product-control, or finance analyst
  asks "review this mark/valuation", "is the fair-value level supported", "is there IPV and
  does it tie out", "are these adjustments/overrides justified", or needs a review-ready
  evidence pack for the valuation committee or audit. This skill evidences findings and
  suggests a disposition; it NEVER signs off a valuation, approves an override or adjustment,
  posts/books a value to the ledger, or makes a fair-value determination — those are
  human/authorized-committee actions.
license: MIT
compatibility: Amazon Quick Desktop; requires pricing/market-data (IPV), valuation-record (ERP/GL, subledger, product-control), controlled valuation-policy library, config, and document-intelligence MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Valuation / product-control / finance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Valuation Reviewer

## Purpose and outcome
Given a valuation record for an instrument or position, apply a set of **explainable review
checks** to the method, fair-value-hierarchy classification, inputs, comparables,
adjustments, overrides, and independent-price-verification (IPV) evidence; explain in plain
language why each finding fired, attach cited evidence, and produce a review-ready pack with
a **suggested review disposition**. A successful output lets a valuation / product-control
reviewer or the valuation committee decide what to do next — the sign-off, any override or
adjustment approval, the hierarchy determination, and any posting remain human.

## Use when
- "Review this mark / valuation and tell me what's wrong or unsupported."
- "Is the Level 2/3 fair-value classification supported by the inputs?"
- "Is there IPV on this mark, and does the independent price tie out within tolerance?"
- "Are these valuation adjustments / model reserves / overrides justified and approved?"
- A reviewer needs a consistent, cited valuation write-up to attach to a committee or audit
  file.

## Do not use
- The user wants a **sign-off**, an **override/adjustment approval**, a **posting** to the
  GL/system of record, or a final **fair-value determination** → out of scope. Provide review
  evidence and route to the authorized approver / Valuation Control Committee.
- Deep **fixed-income pricing** review (marks, spreads, liquidity adjustments) →
  `fixed-income-pricing-reviewer`.
- The concern is the **pricing model itself** (conceptual soundness, performance) →
  `model-validation-assistant`; documentation pack → `model-risk-documenter`.
- The carrying value **doesn't tie** to the subledger (a reconciliation break, not a
  valuation question) → `gl-reconciler`.
- **Personalized investment advice** or a price target → out of scope entirely.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a review pack with a
durable `review_id`; downstream pricing/model/audit skills consume it. It must not duplicate
their sign-off, validation, or posting steps.

## Inputs and prerequisites
- **Instrument/position identifier** and the **valuation record** for the `as_of` date:
  method (market / income / cost), declared fair-value level (1/2/3), reported value and
  currency, and the **inputs** (each with observability, value, source_ref, source_date).
- Optional but expected by level/method: **comparables** (market approach), **adjustments**
  (with rationale/source/approver), **IPV** block (performed, independent value, tolerance,
  source), **overrides** (with approver/rationale), and a Level 3 **uncertainty range**.
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to pricing/market-data, the valuation record, the valuation-policy library, and
  the versioned review **config** (thresholds — see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **independent price** and the
**valuation record** are the authorities; policy and config are versioned contracts; document
intelligence supplies approval/override evidence. Never substitute a desk/trader assertion
for the independent price. Cite every finding's evidence to a source row.

## Workflow
1. **Scope & validate** — confirm the instrument and `as_of`; load the valuation record and
   config; run `validate_input`. Note which checks are evaluable given method/level.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to apply the
   configured checks (hierarchy consistency, input staleness/traceability, IPV missing/breach,
   unexplained/material adjustments, comparable sufficiency, Level 3 uncertainty, unapproved
   overrides). Each check returns a finding with its evidence and citations. Findings are
   **explainable**, not a black-box score.
3. **Assemble evidence** — for each fired finding, attach the specific record rows (input,
   adjustment, IPV, override) and the threshold it breached, with citations.
4. **Suggest disposition** — map the fired-finding profile to a disposition band
   (Pass with observations / Findings raised / Escalate) per the documented mapping. This is a
   triage suggestion for a human, explicitly **not** a sign-off or fair-value determination.
5. **Write the pack** — plain-language finding-by-finding explanation + evidence + the
   suggested disposition + explicit review considerations (benign explanations to weigh) and
   the checks reported `not_evaluable`.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has evidence + citation, no sign-off /
approval / posting / fair-value-determination language is present, the disposition maps
deterministically from the findings, the standing disclaimer is present, and review
considerations are included. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is delivered to the valuation
committee, the audit file, or any system of record. No approval is needed for the reviewer's
own read. The skill never signs off, approves, posts, or determines fair value.

## Failure handling
- **Missing IPV / independent price** → report `ipv_missing` (Level 2/3) or mark IPV checks
  `not_evaluable`; never restate the desk mark as independently verified.
- **Ambiguous instrument/position** → stop and confirm; never review the wrong record.
- **Method/level-specific gaps** (e.g., no comparables for a market mark) → run only the
  checks the data supports; report the rest as `not_evaluable`.
- **Stale/conflicting sources** (reported vs independent) → cite both; do not resolve silently
  or declare the mark correct.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — instrument, `as_of`, method/level, count of fired findings, suggested
   disposition.
2. **Findings** — per fired finding: check name, plain-language reason, severity, evidence
   rows (cited), and the threshold/context it breached.
3. **Review considerations** — explicit benign explanations (approved exception, thin market,
   immaterial magnitude, refreshed input, approved tolerance, delegated override) so the
   reviewer weighs both sides.
4. **Not-evaluable checks** — with the reason each could not run.
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Valuation review evidence only; not a valuation sign-off,
   override approval, or fair-value determination. No value has been posted or approved."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records; may include position-level and issuer-confidential data.
Minimize data in the output to what evidences a fired finding. Retain the review + citations +
`config_version` per records policy; log the read and any external-delivery approval. Never
exfiltrate valuation or position data.

## Gotchas
- **A finding is not a decision.** Fired findings justify a *review disposition*, never a
  sign-off, an override approval, or a fair-value conclusion.
- **Independence**: the desk/trader mark is the thing under review, not the answer. When
  reported and independent prices conflict, evidence both — do not adopt the desk number.
- **Under-classification risk**: an unobservable significant input forces at least Level 3;
  a lower declared level is a high-severity finding, not a rounding choice.
- **Stale IPV is not IPV**: an independent price older than the review window does not verify
  today's mark; check the IPV `source_date`, not just that a value exists.
- **Adjustments describe amounts, not intent**: flag an unexplained or material reserve
  factually; never assert the desk "mismarked to hit P&L" — that is an investigation
  conclusion.
- **Do not tune thresholds to a desk**: thresholds come from the approved, versioned config,
  not from what would make this mark pass.
