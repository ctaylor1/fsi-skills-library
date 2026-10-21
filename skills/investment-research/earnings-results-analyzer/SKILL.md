---
name: earnings-results-analyzer
description: "Analyze reported earnings against separately frozen consensus, whisper, guidance and supplied-model baselines with fiscal, basis, scope and vintage checks; factual surprises without ratings or price targets."
license: MIT
compatibility: Python 3.10+ offline supplied-JSON methods; source retrieval, entitlements and authenticated delivery require institution-owned integration.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Institution-supplied applicability; no universal legal default"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Equity research analyst"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Reported earnings comparison

The native method compares reported actuals with one supplied estimate/consensus baseline per distinct metric, classifies prior-to-new guidance direction, and surfaces factual transcript language observations. It supports actual-only partials and valid guidance changes independently of missing consensus. It does not reconcile actuals against house forecast, company guidance and consensus simultaneously, update a financial model or investment thesis, establish accounting normalization, or issue an investment call.

## Workflow

1. Confirm issuer/instrument, requested research use, economic period, source knowledge cutoff where relevant, applicable institutional profile and responsible reviewer. Use only authorized supplied material; the package opens no network connections.
2. Read [schema](references/schema.md) and [method limits](references/domain-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing. Preserve gaps and unsupported scope.
3. Run `python3 -B scripts/calculate_or_transform.py input.json` and retain the exact original input separately. Fixtures illustrate synthetic contracts and are never substitutes for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. The output is immutable native evidence; authored narrative is a separate draft requiring review. Full reconstruction rejects altered/extra/removed fields and mismatched input binding.
5. Hand off the validated native artifact, retained original, source references, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Never promote software validity to professional acceptance, authenticated source truth or action authority.

## Inputs and outputs

Require legal issuer ID, ticker, reporting period, economic as_of, reporting currency, config version, estimate_source label, aware release_at and knowledge_cutoff at/after release, and nonempty metrics. Each metric requires finite actual, cited actual_ref, actual_known_at within the post-release cutoff, unit, period_ref, accounting_basis and allowed direction. Estimate may be null. Evaluable comparisons require estimate_ref, frozen aware estimate_known_at before release, and explicit matching estimate_period/unit/accounting_basis/currency. Duplicate metric names are rejected: the native schema represents one baseline per metric. Tolerances must be finite nonnegative numbers.

Metric findings retain actual evidence even if surprise is withheld, including a not_evaluable reason for absent/zero estimate or missing cited frozen vintage. Guidance and transcript evidence gaps withhold their findings rather than generating references containing None. Current and prior guidance citations survive. Overall_result describes the available headline findings, not a security view. `baseline_scope` explicitly records the one-baseline limitation; reporting currency, issuer and cutoff metadata survive.

## Controls and unavailable behavior

Reported actual timestamps cannot precede the declared release or exceed cutoff. Frozen estimate vintage and prior guidance vintage must precede release. Financial period and source availability are separate. The method rejects basis mismatches and numeric booleans instead of silently converting. Missing current/prior guidance or transcript source references produce explicit omissions. Prior transcript language without a prior reference does not establish a verified change. No source authenticity, consensus completeness or license entitlement is established.

The [controls](references/controls.md) distinguish executable guards from institution-owned controls. All work is read-only research/draft preparation. Respect MNPI, confidentiality, information barriers and source licensing; no publication, trade, lender consent, credit approval or system-of-record write is implemented. If sources, access, applicable policy or specialist methods are unavailable, return the useful supported partial, state precisely what is withheld and identify the owner of the next review.

## Validation evidence

The bundled executable eval commands and `tools/test_ir_credit_phase1.py` exercise bounded native behavior, expected arithmetic, mutations and invalid input shapes. Trigger/routing/narrative eval cases remain specifications unless separately executed. They do not establish practitioner, institution, deployment, legal or authority acceptance.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 analytical mode

The explicit `schema_version: ir-phase2/1.0` intake adds the bounded method in [Phase 2 schema](references/phase2-schema.md) and [Phase 2 rules](references/phase2-rules.md). Legacy Phase 1 input remains supported. New analytical results use the source-gated `ir-analysis/2.0` result contract, not the legacy fields. Retain the exact original for full output reconstruction. This mode grants no source authentication, approval, publication, trade or live-model authority.
