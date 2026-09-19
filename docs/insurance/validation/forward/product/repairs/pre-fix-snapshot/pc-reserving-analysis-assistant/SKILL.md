---
name: pc-reserving-analysis-assistant
description: "Prepare source-linked reserving analyses from loss-development triangles: compute P&C chain-ladder factors, indicated ultimate losses and basis-specific reserve measures by origin period, and severity, frequency, large-loss, and indicative uncertainty analyses, then assemble them into a documented reserve-analysis exhibit with every figure tied to its data and every assumption stated. Use when an actuary or reserving analyst needs to develop a triangle to ultimate, quantify IBNR, analyse severity/frequency or large-loss impact, document reserving assumptions, or build a reserve-review pack for actuarial sign-off. This skill NEVER selects or books a carried reserve, never issues or signs a Statement of Actuarial Opinion, never opines on reserve adequacy or sufficiency, and never files or submits anything — it produces method-indicated estimates as a draft for a qualified (appointed) actuary to review, select, and approve."
license: MIT
compatibility: Python 3.10+; offline structured inputs and supplied source evidence. Expected source systems are not bundled production connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 1"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Insurance actuarial reserving"
  aws-fsi-primary-user: "Actuary / reserving analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Reserving Analysis Assistant

## Implemented scope and evidence contract

This is a P&C loss-development review. Paid triangles emit `paid`, `ultimate`, and `total_unpaid`; incurred triangles emit `reported_incurred`, `ultimate`, and `ibnr`. Paid development is not labeled IBNR without case-outstanding information. Life/annuity valuation, pricing/rate adequacy, and capital models are unavailable here. Preserve the method, development ages, valuation basis and source units. Read [migration and measure definitions](references/reserve-migration.md) when receiving the retired model-run input.

All output artifacts include the portable insurance evidence contract and source snapshot. Missing actor, versioned source, date or upstream context remains explicitly partial. Content hashes detect changes; they do not authenticate sources or grant approval. After authoring narrative, rebuild `artifact` with `build_artifact` from `scripts/insurance_contract.py` before running output validation. A common envelope does not replace the receiver's native input validator.

## Purpose and outcome
Turn raw loss-development triangles into an audit-ready **reserve-analysis exhibit (DRAFT)**:
compute chain-ladder development factors, project ultimate losses and basis-specific reserve measures by
origin period, analyse severity, frequency, and large-loss impact, quantify an indicative
uncertainty range, and document every assumption — with each figure tied back to its source
data. The outcome is a review-ready pack (or a clear, itemized reason a segment cannot be
developed yet) that a qualified (appointed) actuary reviews, selects from, and approves. The
skill computes **method indications only**; it never selects, books, opines on, or files a
reserve.

## Use when
- "Develop these triangles to ultimate and quantify IBNR for the Q2 reserve review."
- "What are the chain-ladder factors and indicated ultimate for Commercial Auto Liability?"
- "Analyse severity, frequency, and large-loss impact for this segment."
- "Build the reserve-analysis exhibit / assumption documentation for actuarial sign-off."

## Do not use
- Individual claim-file evidence/completeness review → `claim-file-quality-reviewer`. Claim-level reserve adequacy/financial evaluation needs a qualified claims specialist; that capability is not implemented here.
- Existing event/feed exposure monitoring → `catastrophe-exposure-monitor`. New catastrophe PML, accumulation modeling or model validation requires an unavailable catastrophe modeling specialist.
- Explain one reinsurance contract → `reinsurance-contract-reviewer`. Cession allocation, recoverability, ceded-reserve mechanics and administration require an unavailable reinsurance specialist; layer terms are not reserve triangles.
- Independent actuarial model/reserve validation → a qualified independent actuary. The financial-asset `valuation-reviewer` is not an insurance liability-validation substitute.
- Package reviewed results for management → `management-reporting-packager`, only after constructing its native input and preserving professional-review status.
- Close preparation → `month-end-close-orchestrator`, with its native input and separate human authorization. No handoff authorizes reserve selection or booking.
- Selection, booking, adequacy opinion or signed filing → the authorized actuary/finance function; this skill supplies a draft only.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is actuarial analysis
drafting only. It consumes triangles from the claims data mart, parameters from the
versioned actuarial parameter set (`dataset_version`), and large-loss/cat context from
adjacent skills; it emits a `segment_id`-keyed draft with `actuarial_review_required` and
`reviewer_signoff_required`. Selection, opinion, booking, and filing belong to the appointed
actuary and finance, not to this skill.

## Inputs and prerequisites
- The reserving dataset: `dataset_version`, `valuation_date`, `currency`/`unit`,
  `large_loss_threshold`, and per-segment triangles (`segment_id`, `line_of_business`,
  `triangle_basis` paid|incurred, cumulative amounts by origin × development period,
  `tail_factor`, optional `factor_method`, `claim_counts`, `earned_exposure`,
  `large_losses`, `source_ref`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the claims/loss-triangle mart, policy administration, underwriting rules,
  actuarial/catastrophe data, and document intelligence.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The claims data mart is the system
of record for losses; policy administration supplies premium/exposure; the actuarial
parameter set supplies methods, tail, and thresholds. Cite every triangle, count, exposure,
and large-loss figure. Methods, tail, and thresholds are a **versioned contract** — record
`dataset_version` and `valuation_date` on every exhibit.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each triangle is well-formed and
   the basis is stated; a triangle with fewer than two development periods is `needs-data`.
2. **Compute deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): age-to-age
   factors, CDFs (with tail), indicated ultimate and basis-specific reserve measures by origin, severity/frequency,
   large-loss summary, and the indicative min-max uncertainty range. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `needs-data` (immature/undefined factor) or `anomaly-flagged` (paid
   runoff decreasing, or incurred dropping > 20% period-over-period) blocks packaging with
   an itemized reason; only a clean, tied-out segment becomes `draft-analysis`.
4. **Draft the exhibit** — for a packageable segment, assemble the analysis from
   [assets/output-template.md](assets/output-template.md): valuation basis, data/source map,
   method and factors, indicated ultimate/reserve measures, severity/frequency/large-loss, uncertainty,
   assumptions/limitations, and the actuarial review/approval block. No figure without a
   source; report indications, never a selected or adequate reserve.
5. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss.
6. **Never select/book/opine** — hand the reviewed draft to the appointed actuary.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces:
template fidelity (all eight sections), required approvals recorded (pending; no
self-approval), approved method, completeness and source mapping, tie-outs (ultimate =
paid + total_unpaid, or reported_incurred + ibnr), and no adequacy/opinion/booking/filing language; standing note present.
See [references/controls.md](references/controls.md). Correct and re-run until it passes or
the segment is flagged not-packageable.

## Human approval
`external-delivery`. A qualified (appointed) actuary must review, select the carried reserve,
and approve before any indication is relied upon, delivered externally, booked, or used in an
opinion. This skill proposes and drafts; it never selects, books, opines, or files. Internal
drafting may be reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Immature triangle** (< 2 development periods, or an undefined factor from a zero
  denominator) → `needs-data`; list what is missing; never project on a guess.
- **Development anomaly** (paid decreasing, incurred dropping > 20%) → `anomaly-flagged`;
  surface the issue for actuarial review; never smooth or delete data.
- **Missing counts/exposure** → omit severity/frequency for that segment and say so; do not
  fabricate a denominator.
- **Large-loss distortion** → flag the claim(s) for the actuary; report, do not smooth.
- **Stale valuation / parameter set** → return partial output with an explicit incomplete
  flag and the `dataset_version`/`valuation_date` used; no retry assumption.

## Output contract
1. **Segment queue** — per segment: `segment_id`, `line_of_business`, status, and
   `packageable`.
2. **Reserve-analysis exhibit** (per packageable segment) — valuation basis, source map,
   method and factors, indicated ultimate/reserve measures by origin with citations, totals,
   severity/frequency, large-loss summary, indicative uncertainty range, assumptions, and
   `reviewer_signoff_required: true` / `actuarial_review_required: true`, following
   [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each `needs-data` / `anomaly-flagged` segment with its itemized reason.
4. **Machine-readable** — the analysis records keyed by `segment_id` with `dataset_version`.
5. **Standing note** — "Draft reserving analysis for qualified actuarial review only; this
   skill computes method-indicated estimates from the supplied data, does not select or book
   carried reserves, does not issue or sign a Statement of Actuarial Opinion, and does not
   opine on reserve adequacy — a qualified actuary must review, select, and approve every
   figure before use."

## Privacy and records
**Highly Confidential — customer NPI/PII.** Work at the aggregate triangle level; include
claim-level identifiers only for flagged large losses, and mask where not needed (data
minimization). Retain the draft exhibit, `dataset_version`, valuation date, citations, and
the actuarial sign-off with the analysis; log every read and every exhibit produced with the
analyst identity. Recertify per the recertification date.

## Gotchas
- **Indication ≠ selection.** The chain-ladder ultimate is a mechanical indication; the
  appointed actuary selects the carried reserve. Never emit "selected", "adequate", or
  "booked" language.
- **Basis matters.** Paid and incurred develop differently; state the basis per segment and
  never mix bases within one triangle.
- **Tail is applied once.** The tail factor multiplies the CDF a single time to reach
  ultimate; double-applying it overstates IBNR.
- **Anomalies are surfaced, not smoothed.** A decreasing paid triangle or a sharp incurred
  drop is flagged for the actuary, not silently adjusted away.
- **Uncertainty is indicative.** The min-max range is a sensitivity, not a confidence
  interval or a reserve-range opinion.
- **Parameter set is a versioned contract.** Record `dataset_version` and `valuation_date`
  on every exhibit so the indication is reproducible and reviewable.

## Evidence and handoff contract

Read [the insurance evidence contract](references/insurance-contract.md) for source
versioning, explicit unknowns, financial/date bases and receiver validation. A
content hash is not source authentication, professional approval or execution authority.
