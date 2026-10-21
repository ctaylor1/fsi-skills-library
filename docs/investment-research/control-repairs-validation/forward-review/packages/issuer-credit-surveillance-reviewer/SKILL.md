---
name: issuer-credit-surveillance-reviewer
description: "Compare sourced corporate credit ratios, liquidity, spreads and reported events across comparable periods, flagging defined changes without assigning ratings, changing a thesis or recommending a position."
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
  aws-fsi-owner: "Investment Research methods & evidence"
  aws-fsi-primary-user: "Corporate credit research analyst"
  aws-fsi-version: "0.3.1"
  aws-fsi-recertification-date: "2027-09-20"
---

# Issuer credit surveillance packet

The native method is a supplied-input corporate surveillance assembly. It recomputes gross/net leverage, interest coverage and an EBITDA-minus-capex over interest proxy; compares comparable prior metrics; reports an instrument spread delta and agency rating/outlook changes; and flags supplied covenant changes. It does not establish a complete issuer view, internal rating, investment thesis, funding access, security value, covenant headroom, DSCR, recovery, market-implied credit view, portfolio decision or legal conclusion. Sovereign, public-finance, structured-credit, bank and insurance specialist engines are not supplied by these formulas.

## Workflow

1. Confirm issuer/instrument, requested research use, economic period, source knowledge cutoff where relevant, applicable institutional profile and responsible reviewer. Use only authorized supplied material; the package opens no network connections.
2. Read [schema](references/schema.md) and [method limits](references/domain-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing. Preserve gaps and unsupported scope.
3. Run `python3 -B scripts/calculate_or_transform.py input.json` and retain the exact original input separately. Fixtures illustrate synthetic contracts and are never substitutes for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. The output is immutable native evidence; authored narrative is a separate draft requiring review. Full reconstruction rejects altered/extra/removed fields and mismatched input binding.
5. Hand off the validated native artifact, retained original, source references, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Never promote software validity to professional acceptance, authenticated source truth or action authority.

## Inputs and outputs

Require packet/config versions, `issuer{issuer_id,name,sector,as_of}`, aware intraday `knowledge_cutoff`, source registry, financials, maturity rows, spreads object, ratings/covenant arrays and approval records. Financials and any prior financials require issuer, currency, units, period, accounting basis, a filing/company `source_id`, and numeric EBITDA, gross debt, cash, interest expense, capex and undrawn revolver. Prior currency/units/accounting basis must match. All financial amounts except EBITDA are nonnegative. Registry sources require source ID, type, reference and aware `known_at` no later than cutoff; external eligibility is a boolean assertion. Economic period/as_of remains separate from knowledge time.

Packet sections, metrics, basis, source assertions, tie-outs, changes, source-linked maturity/instrument detail, reported rating object identity, covenant instrument/document/version, flags, approvals and unresolved issues are retained. `support_status` is `PARTIAL` for unresolved data/review gates, otherwise `SUPPLIED_INPUT_REVIEW`. Neither means institutional acceptance. A faithful partial can pass reconstruction while its data/review gates stay held. Action fields remain reported-only / none / unchanged.

## Controls and unavailable behavior

Maturities require instrument ID, legal issuer ID, matching currency, amount, source and exact-date/year consistency. Repeated instrument rows require consolidation in a reviewed adapter. Spreads must reference a market source and identified instrument/issuer, spread type and currency. Agency opinions must reference a rating-agency source and identify issuer vs instrument object; the packet assigns no rating. Covenant flags require instrument/document/version. Source-type mismatches fail before computation. Approval person/role strings are assertions; distinct preparer/reviewer labels do not authenticate people.

The [controls](references/controls.md) distinguish executable guards from institution-owned controls. All work is read-only research/draft preparation. Respect MNPI, confidentiality, information barriers and source licensing; no publication, trade, lender consent, credit approval or system-of-record write is implemented. If sources, access, applicable policy or specialist methods are unavailable, return the useful supported partial, state precisely what is withheld and identify the owner of the next review.

## Validation evidence

The bundled executable eval commands and `tools/test_ir_credit_phase1.py` exercise bounded native behavior, expected arithmetic, mutations and invalid input shapes. Trigger/routing/narrative eval cases remain specifications unless separately executed. They do not establish practitioner, institution, deployment, legal or authority acceptance.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 analytical mode

The explicit `schema_version: ir-phase2/1.0` intake adds the bounded method in [Phase 2 schema](references/phase2-schema.md) and [Phase 2 rules](references/phase2-rules.md). Legacy Phase 1 input remains supported. New analytical results use the source-gated `ir-analysis/2.0` result contract, not the legacy fields. Retain the exact original for full output reconstruction. This mode grants no source authentication, approval, publication, trade or live-model authority.

Analytical financial observations are reported periods ending no later than economic as-of. Spread changes need explicit aware observation times, an institution-supplied current-age policy, ordered matching quotes and source/cutoff eligibility. Missing or stale quote evidence withholds the spread comparison and its alert, preserving supported financial metrics. Read the Phase 2 schema for exact time and policy fields.
