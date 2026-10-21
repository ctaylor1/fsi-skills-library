---
name: customer-conduct-outcomes-reviewer
description: >-
  Assess thematic product and customer cohort outcomes from supplied denominators, harm indicators, value and support barriers, segmentation and vulnerable-customer evidence. Calculate observed rates and coverage gaps without resolving individual complaints or declaring whole-population good outcomes.
license: MIT
compatibility: Offline Python 3.10+ standard-library helpers and supplied evidence; no live connector is bundled.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 — regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted; source-specific confidentiality and audience limits"
  aws-fsi-jurisdictions: "Supplied reviewed jurisdiction and institution profile; no universal legal default"
  aws-fsi-owner: "Conduct Risk / Product Governance / Customer Outcomes"
  aws-fsi-primary-user: "Mandated compliance analyst and accountable professional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Customer Conduct Outcomes Reviewer

Assess thematic product and customer cohort outcomes from supplied denominators, harm indicators, value and support barriers, segmentation and vulnerable-customer evidence. Calculate observed rates and coverage gaps without resolving individual complaints or declaring whole-population good outcomes.

Read [domain rules](references/domain-rules.md) and [input schema](references/input-schema.md)
for the native method. Read [source map](references/source-map.md), [controls](references/controls.md)
and [handoffs](references/handoffs.md) before using evidence or transferring a draft.

## Method

Define product/distribution role, observation window, metric and population grain before aggregating. Keep cohort and vulnerable-customer segmentation explicit, including expected but missing groups. Reconcile eligible population, observed denominator and harmful outcomes; a missing or zero denominator yields no rate, while zero observed harms with a valid denominator is an observed zero. Retain missingness, support/value barriers and selection bias. Compare only to supplied review thresholds and avoid extrapolating from a partial sample to all customers.

Separate intake/triage from substantive review: route malformed requests to intake correction;
retain unsupported legal profiles and substantive unknowns in the draft. Require a durable
case ID, review date/cutoff, authorized purpose/audience and source-specific classification.
Supplied source facts, profile assertions and authority records remain unverified. An evidence
registry alone never supports a claim; map each consequential field to an exact source fact.

## Deliverable and verification

Cohort metric table, numerator/denominator rates, population and observation coverage, missing-group register, vulnerable-customer comparisons, value/support barriers and targeted review actions. Use the [output template](assets/output-template.md) for human narrative;
keep it separate from the immutable native result. Source-bound native calculations have no
professional adjudication or action capability.

```sh
python3 -B scripts/validate_input.py INPUT.json
python3 -B scripts/calculate_or_transform.py INPUT.json > OUTPUT.json
python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python3 -B scripts/test_phase2.py
python3 -B scripts/run_evals.py
```

Retain the original input separately and require exact detached-output reconstruction before
presenting a native result. Invalid structural input stops calculation; null, conflicted,
restricted, stale or unsupported facts withhold dependent conclusions. Unknown is never zero,
pass, innocent, approved or closed. Added narrative or edited native fields fail validation.

## Professional boundary

The accountable owner is **Conduct Risk / Product Governance / Customer Outcomes**. This is internal read-only decision support.
Legal interpretation, authentication, human acceptance, regulated decisions, privilege,
HR action, approval, filing, closure and external delivery stay with authorized professionals.
No token or asserted user approval enables live execution. No system-of-record mutation,
access grant, list change, witness contact, payment, publication or customer communication is
implemented. Synthetic checks prove bounded behavior only; source truth, professional
acceptance and production readiness remain unestablished.

Shared [foundation contract](references/foundation-contract.md), [evidence contract](references/evidence-contract.md)
and [source governance](references/source-governance.md) govern provenance, scope, detached validation and handoff limits.

## Typed count units and supported metric

Supply source-bound `review.population_unit`, `review.numerator_unit` and
`review.denominator_unit` claims. The bounded method supports binary affected-customer
proportions with all three equal to `unique-customers`. Repeated event counts are not
affected customer counts; event/customer, account/customer and other unit combinations
are unsupported and withhold rates and thresholds. Missing units remain a valid
partial intake with unknown metrics; never infer units from prose. Threshold comparison
uses the exact count ratio against the supplied decimal threshold; displayed rounding
does not turn an exception into acceptance.

Decimal `threshold_rate` values must be source-bound decimal strings (for example,
`"0.05"` or `"0.33333333333333333334"`), with the same string in the cited source
fact. The string contains digits with an optional decimal point, is at most 256
characters and lies in [0, 1]. Integer 0/1 thresholds are also exact. JSON fractional
numeric thresholds remain valid partial intake, but their original decimal precision
cannot be established after floating-point parsing; criterion comparison is withheld
and the output requests exact decimal evidence. Displayed rates do not determine
acceptance.
