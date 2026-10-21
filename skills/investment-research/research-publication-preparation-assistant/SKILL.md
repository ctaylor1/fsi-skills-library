---
name: research-publication-preparation-assistant
description: "Prepare research publication review by checking supplied applicability profiles, disclosure anchors, restricted-list coverage and source distribution permissions; never approve, publish or distribute research."
license: MIT
compatibility: Python 3.10+ offline supplied-JSON methods; source retrieval, entitlements and authenticated delivery require institution-owned integration.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Institution-supplied applicability; no universal legal default"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Research associate and supervisory reviewer"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Research publication preparation checks

The native method checks supplied disclosure/checklist token sets, a supplied applicable rating scale, supplied rating-direction mapping and target movement, and an explicitly checked ticker restricted list. It supports unrated/debt notes through explicit non-applicability. It is not note-text extraction, full research-quality review, a legal rules engine, license verification, institutional policy certification, rating/target origination, publication approval or distribution.

## Workflow

1. Confirm issuer/instrument, requested research use, economic period, source knowledge cutoff where relevant, applicable institutional profile and responsible reviewer. Use only authorized supplied material; the package opens no network connections.
2. Read [schema](references/schema.md) and [method limits](references/domain-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing. Preserve gaps and unsupported scope.
3. Run `python3 -B scripts/calculate_or_transform.py input.json` and retain the exact original input separately. Fixtures illustrate synthetic contracts and are never substitutes for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. The output is immutable native evidence; authored narrative is a separate draft requiring review. Full reconstruction rejects altered/extra/removed fields and mismatched input binding.
5. Hand off the validated native artifact, retained original, source references, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Never promote software validity to professional acceptance, authenticated source truth or action authority.

## Inputs and outputs

Require note object with note_id and legal issuer_id; disclosures required/present string lists; restricted_list string list; rating_scale string list; and checklist required_items/present_items lists. Explicit rating_applicable and target_applicable are boolean or unknown. Applicable rating requires a nonempty scale and rating; non-applicable notes may have no rating and an empty scale. Targets are finite nonnegative numbers or null. Optional rating_rank values are finite JSON numbers; no universal direction map is inferred. `restricted_list_checked` is boolean or unknown; a ticker is needed for a checked ticker lookup. Context should identify institution, jurisdiction, audience, research_type, profile_id/version, configuration source_ref, applicability_status and rights_status; missing context is an unresolved gap, not clearance.

Cited gaps/flags, check values and applicability status, counts, supplied context, narrow review_scope, not_evaluated items and a review-only disposition. Unknown applicability, unknown/restricted rights, missing configuration version, unclear rating/target applicability or unchecked restricted-list coverage yield gaps-for-review. A restricted ticker yields a hard-stop flag. Even ready-for-compliance-review establishes only completeness of supplied token/configuration checks and still requires compliance/legal/source-rights review.

## Controls and unavailable behavior

Never treat unknown rights or applicability as eligibility. Do not convert an unrated note into a rated note to satisfy a scale check. Configuration tokens do not prove disclosures are in the actual note. Restricted-list checking is ticker-specific, not a complete issuer/instrument/cross-entity control. Any jurisdiction/profile conflict requires the institution’s compliance/legal owner; no universal US or cross-border legal default is installed. Published, approved or distributed states are outside this output contract.

The [controls](references/controls.md) distinguish executable guards from institution-owned controls. All work is read-only research/draft preparation. Respect MNPI, confidentiality, information barriers and source licensing; no publication, trade, lender consent, credit approval or system-of-record write is implemented. If sources, access, applicable policy or specialist methods are unavailable, return the useful supported partial, state precisely what is withheld and identify the owner of the next review.

## Validation evidence

The bundled executable eval commands and `tools/test_ir_credit_phase1.py` exercise bounded native behavior, expected arithmetic, mutations and invalid input shapes. Trigger/routing/narrative eval cases remain specifications unless separately executed. They do not establish practitioner, institution, deployment, legal or authority acceptance.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 analytical mode

The explicit `schema_version: ir-phase2/1.0` intake adds the bounded method in [Phase 2 schema](references/phase2-schema.md) and [Phase 2 rules](references/phase2-rules.md). Legacy Phase 1 input remains supported. New analytical results use the source-gated `ir-analysis/2.0` result contract, not the legacy fields. Retain the exact original for full output reconstruction. This mode grants no source authentication, approval, publication, trade or live-model authority.
