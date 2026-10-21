---
name: issuer-capital-structure-mapper
description: "Map supplied issuer debt, maturities, securities, legal estates, guarantees and explicit priority links by currency and unit; retain unknowns and inventory gaps without legal-priority opinions or financing advice."
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
  aws-fsi-primary-user: "Corporate credit research analyst"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Capital structure and maturity inventory

The native method inventories a supplied corporate debt schedule. It groups known principal by currency, type, supplied seniority, secured status and maturity year; computes eligible principal-weighted coupon and years to maturity; and totals scheduled amounts within two calendar years. It does not establish complete economic or legal capital structure, verify guarantees or structural subordination, convert currencies, price instruments, assess refinancing access, or recommend a transaction.

## Workflow

1. Confirm issuer/instrument, requested research use, economic period, source knowledge cutoff where relevant, applicable institutional profile and responsible reviewer. Use only authorized supplied material; the package opens no network connections.
2. Read [schema](references/schema.md) and [method limits](references/domain-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing. Preserve gaps and unsupported scope.
3. Run `python3 -B scripts/calculate_or_transform.py input.json` and retain the exact original input separately. Fixtures illustrate synthetic contracts and are never substitutes for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. The output is immutable native evidence; authored narrative is a separate draft requiring review. Full reconstruction rejects altered/extra/removed fields and mismatched input binding.
5. Hand off the validated native artifact, retained original, source references, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Never promote software validity to professional acceptance, authenticated source truth or action authority.

## Inputs and outputs

`company{company_id,name,as_of}` uses a calendar economic as-of date. `instruments[]` is nonempty. Each row requires durable `instrument_id`, legal `issuer_id`, explicit three-letter `currency` and `source_ref`. Principal and coupon are finite nonnegative JSON numbers or null. `secured` is boolean or null; `maturity_date` is a valid calendar date or null. Supplied type and seniority are descriptive labels, not a legal determination.

`instruments[]` retains identity, amount, currency, coupon, maturity, security assertion and source reference. `by_currency` holds each currency inventory and coverage flags. A single-currency packet exposes those fields at the top level; mixed-currency top-level totals and averages are null. `total_debt` is null if principal coverage is incomplete; `known_principal` is a labeled subtotal. Unknown maturity uses an `undated` bucket and withholds full WAM and near-term totals. Unknown coupon withholds full WAC; separately labeled known-subset averages retain their own denominators. Missing principal stays in detail and `excluded_instruments`.

## Controls and unavailable behavior

Unknown principal, coupon, maturity and security must remain distinct from zero and unsecured. Currency totals never cross currencies. Validate exact output against the original schedule, including every contributing instrument and all buckets. Entity association and source authenticity remain analyst review responsibilities.

The [controls](references/controls.md) distinguish executable guards from institution-owned controls. All work is read-only research/draft preparation. Respect MNPI, confidentiality, information barriers and source licensing; no publication, trade, lender consent, credit approval or system-of-record write is implemented. If sources, access, applicable policy or specialist methods are unavailable, return the useful supported partial, state precisely what is withheld and identify the owner of the next review.

## Validation evidence

The bundled executable eval commands and `tools/test_ir_credit_phase1.py` exercise bounded native behavior, expected arithmetic, mutations and invalid input shapes. Trigger/routing/narrative eval cases remain specifications unless separately executed. They do not establish practitioner, institution, deployment, legal or authority acceptance.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 analytical mode

The explicit `schema_version: ir-phase2/1.0` intake adds the bounded method in [Phase 2 schema](references/phase2-schema.md) and [Phase 2 rules](references/phase2-rules.md). Legacy Phase 1 input remains supported. New analytical results use the source-gated `ir-analysis/2.0` result contract, not the legacy fields. Retain the exact original for full output reconstruction. This mode grants no source authentication, approval, publication, trade or live-model authority.
