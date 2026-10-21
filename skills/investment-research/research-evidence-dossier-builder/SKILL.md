---
name: research-evidence-dossier-builder
description: >-
  Assemble an internal issuer or security evidence dossier from supplied claims and source metadata. Use to review citations, knowledge timing, permissions, contradictions and coverage gaps before research analysis; does not retrieve or authenticate sources.
license: MIT
compatibility: Offline Python 3.10+ with supplied JSON. Optional enterprise services are separately provisioned; no credentials, licensed data or live connectors are bundled.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "Deployment-specific applicability review required"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Research analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-20"
---

# Research Evidence Dossier Builder

Use this skill before analysis to organize supplied evidence for one issuer or
security. It receives analyst-supplied claims and precise source locations; it does
not extract filings, fetch data or verify source truth. Separate reported facts,
management assertions, vendor normalizations, adjustments, forecasts, scenarios,
interpretations and investment judgments.

Preserve contradictory claims and inherited issues. Withhold claim text from the
output when identity, timing, permission or financial basis fails. Restricted source
text is never copied into the output; retain the original under institution controls.
A well-formed supplied citation does not prove its truth or license.

1. Read [references/schema.md](references/schema.md) and the paired synthetic
   [evals/files/input.json](evals/files/input.json). Collect actual identity, purpose,
   audience and dates. Unknown evidence is a gap; do not manufacture missing facts.
2. Run `python3 -B scripts/validate_input.py INPUT.json`. Resolve structural errors
   before computing. Record semantic gaps; a partial result can be useful.
3. Run `python3 -B scripts/calculate_or_transform.py INPUT.json` and retain the JSON
   as an internal draft. Review eligible and withheld claims, contested evidence, coverage and unresolved issues.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`.
   The complete retained input is mandatory. Missing/extra/tampered output fails.
5. Give the reviewer the draft and unresolved issues. Coverage complete means supplied-inventory-only; it is not a clean research or publication opinion.

Read [references/evidence-standard.md](references/evidence-standard.md),
[references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md) for boundaries. Analytical
views belong to the selected research method; client suitability, transaction work,
publication clearance, legal conclusions and execution retain their separate owners.

No external delivery, approval, trading or system-of-record change is performed.
Successful reconstruction establishes consistency with supplied input only.
Professional acceptance and deployment authorization remain not established.
