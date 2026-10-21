---
name: earnings-preview-packet-builder
description: "Prepare pre-event earnings evidence and frozen consensus, whisper, guidance and supplied-model comparisons with fiscal and basis alignment; no invented forecast, actual surprise or investment recommendation."
license: MIT
compatibility: Python 3.10+ offline supplied-JSON methods; source retrieval, entitlements and authenticated delivery require institution-owned integration.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Institution-supplied applicability; no universal legal default"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Research associate"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Earnings preview packet

The native method assembles a versioned preview template and performs descriptive consensus-versus-guidance midpoint arithmetic and fiscal QoQ/YoY KPI deltas. It accepts supplied research components; it does not retrieve sources, originate house forecasts, scenarios, ratings, targets or trade views, or publish/distribute. The supported native review profile uses explicit supervisory-analyst, research-compliance and legal-disclaimer role assertions. Other institutional profiles require separate reviewed configuration; buy-side applicability is not inferred.

## Workflow

1. Confirm issuer/instrument, requested research use, economic period, source knowledge cutoff where relevant, applicable institutional profile and responsible reviewer. Use only authorized supplied material; the package opens no network connections.
2. Read [schema](references/schema.md) and [method limits](references/domain-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing. Preserve gaps and unsupported scope.
3. Run `python3 -B scripts/calculate_or_transform.py input.json` and retain the exact original input separately. Fixtures illustrate synthetic contracts and are never substitutes for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. The output is immutable native evidence; authored narrative is a separate draft requiring review. Full reconstruction rejects altered/extra/removed fields and mismatched input binding.
5. Hand off the validated native artifact, retained original, source references, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Never promote software validity to professional acceptance, authenticated source truth or action authority.

## Inputs and outputs

Require packet ID, preparer ID, review profile ID/version, issuer ID/name/ticker, economic as_of_date, aware `knowledge_cutoff`, event fiscal period/report date/comparable period and aware `event.release_at`. Cutoff must precede release, including within the same day. Require a versioned template, required sections, required review-role list and nonempty items. Item source bundles require aware `known_at` no later than cutoff; data-point vintages, when supplied, must also qualify. Numeric metric values are finite JSON numbers or null, with unit/fiscal-period/accounting-basis labels; any supplied consensus/guidance value requires a source and aware known_at. Economic forecast periods may lie in the future if their source vintage is eligible.

Ordered items retain source bundles/vintages, data points, supplied content-review records, readiness reasons, template coverage, consensus-versus-guidance table, explicit fiscal KPI comparators, role-assertion rollup and draft notices. `ready-for-control-review` means supplied content/role assertions are complete for further human control review. Incomplete sources, sections or role records yield `hold-for-approval`. Neither status authenticates an approver, proves entitlement or clears distribution.

## Controls and unavailable behavior

Date-only cutoffs or naive timestamps fail. Preparer labels may not equal an asserted independent approval label; duplicate roles fail. Required roles are fixed to the explicitly supplied sell-side profile, not silently reduced to a sole preparer. Source `approved` flags express eligibility assertions only. Forward-looking facts require third-party attribution; prohibited originated-view kinds fail. Missing evidence remains a held partial instead of an invented figure or source.

The [controls](references/controls.md) distinguish executable guards from institution-owned controls. All work is read-only research/draft preparation. Respect MNPI, confidentiality, information barriers and source licensing; no publication, trade, lender consent, credit approval or system-of-record write is implemented. If sources, access, applicable policy or specialist methods are unavailable, return the useful supported partial, state precisely what is withheld and identify the owner of the next review.

## Validation evidence

The bundled executable eval commands and `tools/test_ir_credit_phase1.py` exercise bounded native behavior, expected arithmetic, mutations and invalid input shapes. Trigger/routing/narrative eval cases remain specifications unless separately executed. They do not establish practitioner, institution, deployment, legal or authority acceptance.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 analytical mode

The explicit `schema_version: ir-phase2/1.0` intake adds the bounded method in [Phase 2 schema](references/phase2-schema.md) and [Phase 2 rules](references/phase2-rules.md). Legacy Phase 1 input remains supported. New analytical results use the source-gated `ir-analysis/2.0` result contract, not the legacy fields. Retain the exact original for full output reconstruction. This mode grants no source authentication, approval, publication, trade or live-model authority.
