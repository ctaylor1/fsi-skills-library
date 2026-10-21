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
  aws-fsi-version: "0.4.1"
  aws-fsi-recertification-date: "2027-09-20"
---

# Issuer credit surveillance evidence

Compare sourced reported corporate financial ratios, liquidity, spreads and reported events across comparable periods. The supported intake is explicitly `schema_version: ir-phase2/1.0`; legacy requests and packets require migration and are rejected by all live entrypoints. The method does not establish a complete issuer view, rating, thesis, covenant compliance, DSCR, security value or portfolio decision. Bank, insurer and other specialist profiles are unsupported.

## Workflow

1. Confirm issuer/security, research use, economic as-of, source knowledge cutoff, supplied profile and responsible reviewer. Use authorized supplied material; this package opens no network connections.
2. Read [schema and migration](references/schema.md), [analytical schema](references/phase2-schema.md) and [method limits](references/phase2-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing.
3. Run `python3 -B scripts/calculate_or_transform.py input.json`. Retain the exact original separately. Fixtures are synthetic contracts and never substitute for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. Every output field is reconstructed from the retained original. Authored narrative is a separate reviewed draft.
5. Hand off the original and immutable output with evidence, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Software validity does not establish practitioner acceptance, source authenticity or action authority.

## Inputs and outputs

Require the common research context, source registry, citations and comparable `prior`/`current` reported financial observations, including explicit period, currency, unit, accounting basis and consolidation scope. Financial periods cannot end after economic as-of or the knowledge-cutoff date. Null financial values withhold dependent metrics. Supplied thresholds determine disclosure alerts. See [the full schema](references/phase2-schema.md) for exact fields.

Spread comparisons additionally require uniquely selected structured market observations, a dated source-bound security/issuer/currency mapping, exact requested-subject binding, aware observation times, an explicit current-age policy and eligible source blocks. Assertions must reconcile to the selected records, registry version and precise registered locator. Missing, stale, conflicting, unrelated or wrong-role evidence withholds the spread delta and widening alert while preserving supported financial metrics, subject to the common whole-projection source gate. A copied assertion is not independent source evidence.

The result contract is `ir-analysis/2.0`: `status`, `results`, `unresolved_issues`, source context, lineage and `input_hash` bind the complete original. `partial` faithfully records unresolved coverage; `complete-for-supplied-scope` means only the bounded supplied-input computation completed. Neither means institutional acceptance. Action fields remain reported-only / none / unchanged; authority and action remain false.

## Controls and migration

The [controls](references/controls.md) distinguish executable guards from institutional responsibilities. Legacy inputs without the exact live schema and legacy outputs are rejected with `legacy surveillance migration required`; no compatibility flag or automatic adapter is supplied. Migration requires a reviewed new request containing real supporting evidence, not added schema labels or inferred dates. Frozen historical source/artifacts remain the basis for reproducing earlier phase evidence; current validators do not recertify those legacy outputs.

All work remains read-only research and draft preparation. Respect MNPI, confidentiality, information barriers and source licensing. No publication, trade, lender consent, credit approval, live-model update or system-of-record write is implemented. Missing source access, policy or specialist methods must remain explicit coverage gaps.

## Validation evidence

Bundled executable eval commands exercise current input/output and calculation behavior, plus deliberate legacy rejection. `tools/test_ir_surveillance_legacy_gate.py` covers both dispatch paths and public commands; the active credit, control-repair and evidence-reconciliation suites cover numerical/adverse behavior. Trigger, routing and narrative cases are specifications unless separately executed. These checks do not establish professional or deployment acceptance.

Read [the evidence and control standard](references/evidence-standard.md) for identity, knowledge timing, permission use, detached source binding and professional acceptance boundaries.
