---
name: actuarial-model-run-assistant
description: >-
  Run a documented, reproducible actuarial loss-development calculation (volume-weighted
  chain-ladder) over a cumulative loss triangle and produce a run packet with age-to-age
  factors, cumulative development factors, per-origin ultimate and IBNR indications, and the
  exact assumptions used, for an actuarial analyst to review. Use when an actuary asks to "run
  the chain-ladder", "develop these losses to ultimate", "compute the IBNR indication", or
  "reproduce the loss-development run". HARD BOUNDARY: R2 model-and-calculate — it produces an
  indication for review only; it NEVER books or sets a reserve, never makes a reserving
  decision, and never certifies reserve adequacy; a qualified actuary owns every reserving
  judgment. Routes triangle-data provenance questions to actuarial-data-lineage-checker.
license: MIT
compatibility: Amazon Quick Desktop; requires actuarial reserving-data (loss triangle) and versioned assumption-config MCP integrations (all read-only). Deterministic stdlib-only computation.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Actuarial analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Actuarial Model Run Assistant

## Purpose and outcome
Given a cumulative loss triangle and documented assumptions, deterministically run the
volume-weighted chain-ladder: age-to-age (LDF) factors, cumulative development factors (CDF),
and per-origin ultimate and IBNR indications, with a full assumption trail. A successful output
is a reproducible indication an actuary reviews — the reserve and any reserving decision remain
the qualified actuary's.

## Use when
- "Run the chain-ladder", "develop these losses to ultimate", "compute the IBNR indication".
- "Reproduce the loss-development run with these factors."
- An actuary needs a consistent, assumption-documented development run.

## Do not use
- The user wants you to **book or set a reserve** or make a reserving decision → out of scope; a
  qualified actuary decides.
- The **triangle data provenance/consistency** is in question → route to
  `actuarial-data-lineage-checker`.
- A non-standard method not in the documented config → escalate; do not improvise a method.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a run packet with a durable `run_id`;
it does not book reserves.

## Inputs and prerequisites
- The **triangle**: origin_periods, dev_ages, cumulative_paid (upper triangle filled, rest
  null); and **assumptions** (method, tail_factor, config_version). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Documented **assumption config** — a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The reserving-data triangle is the
system of record; assumptions from versioned config. The run records the exact triangle and
assumptions used.

## Workflow
1. **Validate input** — run `validate_input`; confirm a rectangular triangle with a monotone
   filled upper region and a numeric tail factor.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): volume-weighted LDFs,
   CDFs (with tail), per-origin ultimate and IBNR from the latest diagonal.
3. **Assemble the run** — factors, per-origin results, totals, and the assumption trail.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for the
   ultimate = latest + IBNR tie, total tie-outs, the no-reserving-decision screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a per-origin ultimate does not equal latest
+ IBNR, totals do not tie, or the text contains reserve-setting/booking language, **fix or fail
closed**.

## Human approval
`external-delivery`: the run may be produced for review, but external delivery requires human
sign-off, and no reserve is ever set or booked by this skill.

## Failure handling
- **Missing assumption/config** → fail closed; state what is missing; do not guess a tail factor.
- **Ragged/non-monotone triangle** → flag; do not silently fill or extrapolate.
- **Zero/negative denominator in an LDF** → flag the factor as not-computable; do not divide.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — triangle id/type, method, tail factor, config version, total ultimate & IBNR.
2. **Factors** — LDFs by age transition, CDFs by age.
3. **Per-origin** — latest diagonal, CDF applied, ultimate, IBNR.
4. **Machine-readable** — factors + per-origin + totals + `run_id`.
5. **Standing disclaimer** — "Actuarial indication for review only; not a booked reserve, a
   reserving decision, or a certification of adequacy."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Retain the run + triangle reference + assumptions. Log read + external-delivery
approval. Never exfiltrate reserving data.

## Gotchas
- **An indication is not a reserve.** The chain-ladder ultimate is one method's output; the
  actuary selects and books.
- **Volume-weighted vs simple average**: this skill runs the documented (volume-weighted) method
  only; a different selection is the actuary's, not an improvisation here.
- **Tail factor** is an explicit assumption from config; never invent one.
- **Latest diagonal** must be the most recent filled age per origin — do not read across a null.
