---
name: asset-management-router
description: >-
  Route investment-manager and asset-owner requests to portfolio, fund, research,
  operations, product, risk, reporting and technology capabilities. Identify bounded
  implementations and missing methods before preparing source-bound handoffs. Route
  household planning, corporate transactions and IT asset inventory to their owners.
license: MIT
compatibility: Requires Python 3.10+ for offline routing and validators; receiver skills must be separately installed. No market-data connector, enterprise engine, scheduler or execution service is bundled.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - platform controls"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Routing metadata only; no implemented legal applicability packs"
  aws-fsi-owner: "Asset Management architecture and investment operations"
  aws-fsi-primary-user: "Investment manager / asset-owner team / investment operations"
  aws-fsi-version: "0.4.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Asset management router

## Purpose and use

Identify the professional job and its actual subject before selecting a skill. A
manager's fee revenue, a fund's NAV, an investor's capital account and the market value
of the manager's listed stock are different subjects. Route multi-job requests as
explicit cooperating workflows. The router returns a plan; it installs or launches nothing.

Read [routes](references/routes.json) for 42 representative investment requests and
four exclusions. Read [capabilities](references/capabilities.json) to distinguish
bounded current methods from planned capabilities. Read [migrations](references/migrations.json)
only to resolve former identifiers/paths; legacy names are not duplicate implementations.

## Workflow

1. Interpret the user's request into one or more declared `intents`, a real subject
   `type`/`id`, `request_id`, `as_of`, and requested action. Do not invent missing scope.
   Ambiguous jobs need clarification; the deterministic router does not claim general
   natural-language understanding.
2. Run [input validation](scripts/validate_input.py), then
   [routing](scripts/calculate_or_transform.py). `available_skills` is an optional
   deployment inventory of canonical package names. Absence means installation is unknown.
   An empty list means no listed package is installed. Use the containing package name
   for an installed mode; a former mode/package name does not establish installation.
3. Explain the primary job, supporting jobs, missing data/methods and relevant overlays.
   A planned capability is a gap even if a similarly named folder exists. In particular,
   institutional manager diligence requires `institutional` mode, RFP requires `rfp` mode, NAV controls do not calculate NAV,
   and current liquidity/attribution methods are deliberately bounded.
4. For a real handoff, read [the contract](references/handoff-contract.md). Retain
   detached originals, validate the native result, bind scope and method, and use
   [artifact assembly](scripts/build_artifact.py). Map actual receiver-native fields;
   do not treat a prose link or a common envelope as schema compatibility.
5. Run [handoff validation](scripts/validate_handoff.py) against the explicitly installed
   producer and receiver, supplying the detached original producer request. Both native
   validators run again; envelope integrity alone is insufficient. Unresolved source
   issues remain open. Source references, hashes and reviewer
   strings do not authenticate evidence, approve an investment or authorize action.
6. Validate the route result with [output validation](scripts/validate_output.py)
   and the original request using `--input`. Report a review plan, not completion
   of the selected professional workflow.

## Inputs and output

Routing needs declared intent identifiers from `routes.json`, subject type/id, request
date and optional installation inventory. It returns route status, exact current scope,
supporting dependencies and unresolved issues. See [template](assets/output-template.md).
Unknown intent or contradictory subject scope must not be guessed into a valid route.
Unknown intents fail validation. A declared intent with an incompatible subject produces
`needs_scope_clarification`; it does not establish a usable workflow. See the full
59-intent examples and status rules in [domain rules](references/domain-rules.md).

For calculations, read [engine contract](references/engine-contract.md). All live
systems and licensed sources are deployment dependencies; the native scripts only
operate on supplied evidence. See [source map](references/source-map.md),
[controls](references/controls.md), [domain rules](references/domain-rules.md) and
[handoffs](references/handoffs.md) when preparing a scoped workflow.

## Authority and acceptance

No trade, fund accounting posting, portfolio modification, vote, distribution, filing,
payment or external communication occurs. Keep route selection, numerical validation,
professional review, approval and execution separate. The router is tested with
synthetic requests and native validators; institutional source authentication and
professional/deployment acceptance remain separate.

Run the executable [eval cases](evals/evals.json) from this package directory. The
independent route assertions check all 59 declared intents and installation/action
boundaries; stored route goldens are additionally validated against detached inputs.

## Specialist routes

Phase 4 adds staged transitions, securities/private-fund financing, restructuring, sustainability and token-register controls, plus explicit specialist attribution, walk-forward, basket, liability and jurisdiction extensions. Read `native_extension` when present and pass that exact extension into the receiving native contract. Derivatives implementation routes to the hedge reviewer; staged portfolio transitions have a distinct route. Availability and approval remain caller-supplied, never inferred.
