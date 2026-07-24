---
name: insurance-rating-quote-worksheet
description: >-
  Produce a rating worksheet that applies the documented rate manual (base rate, rating factors,
  fees, minimum premium) to a risk's characteristics and shows every factor step in the premium
  buildup, per coverage and in total, as an indicated-premium worksheet for an underwriting
  analyst. Use when an analyst asks to "rate this risk", "build the premium worksheet", "show the
  rating factor buildup", or "what's the indicated premium". HARD BOUNDARY: R3 model/
  decision-support only — it computes an INDICATED premium from documented inputs and shows the
  math; it NEVER binds coverage, issues or finalizes a quote, makes an offer, or overrides the
  rate manual; underwriting owns binding and quoting. Routes filing packaging to
  insurance-regulatory-filing-packager.
license: MIT
compatibility: Amazon Quick Desktop; requires rate-manual/rating-factor config and risk-characteristic records plus reference-data MCP integrations (all read-only). Deterministic stdlib-only computation.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Underwriting analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Insurance Rating Quote Worksheet

## Purpose and outcome
Given a documented rate manual and a risk's characteristics, deterministically build the premium
worksheet: per coverage, apply the base rate and each rating factor in order, add fees, enforce
the minimum premium, and total across coverages — showing every step. A successful output is an
indicated-premium worksheet an underwriting analyst reviews; binding and quoting remain
underwriting's.

## Use when
- "Rate this risk", "build the premium worksheet".
- "Show the rating factor buildup", "what's the indicated premium".
- An analyst needs a consistent, auditable premium calculation.

## Do not use
- The user wants to **bind coverage, issue/finalize a quote, or make an offer** → out of scope;
  underwriting acts.
- The user wants to **package a rate filing** → route to `insurance-regulatory-filing-packager`.
- The rate manual itself is in question → escalate; never override the manual.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a worksheet with a durable
`worksheet_id`; it does not bind or issue a quote.

## Inputs and prerequisites
- The **policy** context, the **risk** characteristics, and the **rate_manual** (base rates,
  factors, fees, min_premium) with **coverages**. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The rate manual is a versioned contract; the worksheet applies it, it does not change it. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The rate manual is the authority for
rates/factors; the worksheet records the manual version and every step.

## Workflow
1. **Validate input** — run `validate_input`; confirm base rates, factors, and coverages.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per coverage, base ×
   Π(factors) with an ordered step trail, add fees, enforce min premium; total across coverages +
   policy fees.
3. **Assemble the worksheet** — per-coverage buildup steps, subtotals, fees, indicated total.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for the
   factor-product tie, the total tie, the no-bind/no-quote screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a coverage premium does not equal base ×
Π(factors), the total does not tie, or the text contains bind/quote-issuance language, **fix or
fail closed**.

## Human approval
`required`: no binding, quote issuance/finalization, or offer without underwriting. The skill only
computes the indicated premium.

## Failure handling
- **Missing base rate/factor** → fail closed for that coverage; do not assume a rate.
- **Factor not in the manual** → flag; never invent a factor value.
- **Minimum premium applied** → show it explicitly as a step, not a silent floor.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — policy/risk (masked), manual version, indicated total premium.
2. **Per coverage** — ordered buildup steps (base, each factor, running), premium before fees,
   min-premium application, fees, coverage total.
3. **Totals** — sum of coverages + policy fees = indicated premium.
4. **Machine-readable** — buildup + totals + `worksheet_id`.
5. **Standing disclaimer** — "Indicated-premium worksheet only; not a bound quote, an issued quote,
   or an offer of coverage. Nothing has been bound or quoted."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy/insured identifiers. Retain worksheet + manual version. Log read +
external-delivery approval. Never exfiltrate rating data.

## Gotchas
- **Indicated ≠ quoted.** The worksheet's number is an indication; underwriting quotes and binds.
- **Factor order matters for the trail, not the product** — show the ordered steps for audit.
- **Minimum premium** is shown as an explicit adjustment, never hidden.
- **Never override the manual** — an out-of-manual factor is an exception to escalate.
