---
name: investment-research-router
description: >-
  Route declared investment-research jobs to bounded native methods, shared owners or explicit capability gaps using a supplied installation inventory. Use to choose research workflows and review dependencies; returns a plan without launching skills.
license: MIT
compatibility: Offline Python 3.10+ with supplied JSON. Optional enterprise services are separately provisioned; no credentials, licensed data or live connectors are bundled.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "Deployment-specific applicability review required"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Research analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-10-20"
---

# Investment Research Router

Use this skill when the research job needs a method/owner selected. Translate the
user's request into explicit intents in [references/routes.json](references/routes.json).
If subject, job or required method profile is unclear, preserve that uncertainty and
clarify it before recommending an analytical method. The local script handles
declared intents; it does not perform general natural-language intent recognition.

The 42-capability roadmap in [references/capabilities.json](references/capabilities.json)
distinguishes bounded installed methods from planned methods. Supply an installation
inventory to distinguish missing packages from unknown deployment state. Inventory
entries are provider-qualified; similarly named external plugins are not assumed
interchangeable. Read [references/handoffs.md](references/handoffs.md) before composition.

1. Read [references/schema.md](references/schema.md) and the paired synthetic
   [evals/files/input.json](evals/files/input.json). Collect actual identity, purpose,
   audience and dates. Unknown evidence is a gap; do not manufacture missing facts.
2. Run `python3 -B scripts/validate_input.py INPUT.json`. Resolve structural errors
   before computing. Record semantic gaps; a partial result can be useful.
3. Run `python3 -B scripts/calculate_or_transform.py INPUT.json` and retain the JSON
   as an internal draft. Review each route's status, profile limits, dependencies and native-only handoff flag.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`.
   The complete retained input is mandatory. Missing/extra/tampered output fails.
5. Give the reviewer the draft and unresolved issues. This plan launches no package; use producer and consumer native validators before an actual handoff.

Read [references/evidence-standard.md](references/evidence-standard.md),
[references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md) for boundaries. Analytical
views belong to the selected research method; client suitability, transaction work,
publication clearance, legal conclusions and execution retain their separate owners.

No external delivery, approval, trading or system-of-record change is performed.
Successful reconstruction establishes consistency with supplied input only.
Professional acceptance and deployment authorization remain not established.

## Reviewed Phase 2 composition

Incoming reviewed adapter plans are listed with their installed dependency status. Read
[adapter registry](references/adapters.json). Use
`python3 -B scripts/review_handoff.py REQUEST.json --library-root LIBRARY_ROOT`
(the library also exposes `tools/review_ir_handoff.py`) only with installed producer/receiver packages
and retained producer original/output plus the proposed receiver input. It validates
both native contracts and computes a source-bound receiver artifact. Validate a saved
handoff using `OUTPUT.json --input REQUEST.json`. This separate library tool does not
ship or launch missing dependencies; routes alone establish no adapter compatibility.

Mapped receiver fields must be empty or exactly equal to the proposed projection.
Conflicting forecasts, maturities, covenant tests or review findings require human
adjudication; adapters never silently discard them. All sources remain supplied and
unverified. The installed full-library path is an explicit offline dependency for
reviewed composition; standalone route planning does not require it.
