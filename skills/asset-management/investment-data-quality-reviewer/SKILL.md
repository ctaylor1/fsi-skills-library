---
name: investment-data-quality-reviewer
description: "Review investment data in explicit data_quality or vendor_feed mode: screen a supplied instrument snapshot or compare internal/vendor observations without correcting records or choosing a canonical value."
license: MIT
compatibility: Python 3.10+; portable offline JSON methods. Enterprise source access and execution are not bundled.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Investment-data analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Data Quality Reviewer

Review investment data in explicit data_quality or vendor_feed mode: screen a supplied instrument snapshot or compare internal/vendor observations without correcting records or choosing a canonical value.

## Select the explicit mode

- “Screen our holdings snapshot for missing prices and factor coverage” → `data_quality`.
- “Compare internal prices with this vendor file and retain stale/value differences” → `vendor_feed`.

Snapshot screening does not provide the vendor-comparison schema. Reference-data enrichment, pricing adjudication, corporate-action interpretation and fund accounting are separate workflows.

| Mode | Detailed contract | Native example fixture |
| --- | --- | --- |
| `data_quality` | [Native workflow](references/data_quality-workflow.md), [method](references/data_quality-domain-rules.md), [sources](references/data_quality-source-map.md) | `feed_snapshot.json` |
| `vendor_feed` | [Native workflow](references/vendor_feed-workflow.md), [method](references/vendor_feed-domain-rules.md), [sources](references/vendor_feed-source-map.md) | `feed_reconciliation_example.json` |

## Native operation

1. Read only the selected mode's workflow and references. Prepare `{ "mode": "<mode>", "input": <native-input-object> }`. The two schemas are different; no automatic conversion or handoff is supplied.
2. Run `python3 -B scripts/validate_input.py REQUEST.json`. Unknown modes, extra outer fields and invalid native input fail closed. Inspect native warnings as well as errors.
3. Run `python3 -B scripts/calculate_or_transform.py REQUEST.json`. The dispatcher validates the native input and its resulting native output before returning a source-bound `{mode,result,action_taken:false}` object.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input REQUEST.json` against the separately retained original request. This checks native output against the original subinput and exact outer reconstruction. Source hashes establish reproducibility, not source authentication or permissions.
5. Produce any audience-specific narrative separately and apply [controls](references/controls.md) and [handoffs](references/handoffs.md). No source documents are embedded by default.

The flat mode-prefixed scripts remain available for existing native integrations and evaluation cases; they consume their original native schemas. Top-level scripts always require the explicit wrapper. Switching mode requires a separately prepared and validated native request.

## Acceptance and limits

These are bounded offline methods with synthetic fixtures and declared source evidence. Enterprise access, source authentication, professional acceptance, jurisdiction-specific deployment and execution remain separate. Neither package presence nor successful reconstruction certifies the underlying evidence or professional conclusion.
