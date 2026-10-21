---
name: proxy-voting-reviewer
description: "Assemble supplied shareholder-meeting evidence in evidence mode or compare a human-proposed vote with supplied effective policy and precedents in policy mode. Preserve human voting authority; never propose, approve, cast or submit a vote."
license: MIT
compatibility: Python 3.10+; portable offline JSON methods. Enterprise source access and execution are not bundled.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Proxy-voting analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Proxy Voting Reviewer

Assemble supplied shareholder-meeting evidence in evidence mode or compare a human-proposed vote with supplied effective policy and precedents in policy mode. Preserve human voting authority; never propose, approve, cast or submit a vote.

## Select the explicit mode

- “Assemble the AGM agenda, entitlement and research evidence” → `evidence`.
- “Check this analyst-proposed ballot against our policy and precedents” → `policy`.

Evidence mode does not create a proposed vote. Policy mode requires the human-proposed instruction and its native policy/precedent inputs. Neither mode decides, changes, casts, approves or submits a vote; entitlement corrections and professional adjudication remain human-owned.

| Mode | Detailed contract | Native example fixture |
| --- | --- | --- |
| `evidence` | [Native workflow](references/evidence-workflow.md), [method](references/evidence-domain-rules.md), [sources](references/evidence-source-map.md) | `meeting_example.json` |
| `policy` | [Native workflow](references/policy-workflow.md), [method](references/policy-domain-rules.md), [sources](references/policy-source-map.md) | `ballot_example.json` |

## Native operation

1. Read only the selected mode's workflow and references. Prepare `{ "mode": "<mode>", "input": <native-input-object> }`. The two schemas are different; no automatic conversion or handoff is supplied.
2. Run `python3 -B scripts/validate_input.py REQUEST.json`. Unknown modes, extra outer fields and invalid native input fail closed. Inspect native warnings as well as errors.
3. Run `python3 -B scripts/calculate_or_transform.py REQUEST.json`. The dispatcher validates the native input and its resulting native output before returning a source-bound `{mode,result,action_taken:false}` object.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input REQUEST.json` against the separately retained original request. This checks native output against the original subinput and exact outer reconstruction. Source hashes establish reproducibility, not source authentication or permissions.
5. Produce any audience-specific narrative separately and apply [controls](references/controls.md) and [handoffs](references/handoffs.md). No source documents are embedded by default.

The flat mode-prefixed scripts remain available for existing native integrations and evaluation cases; they consume their original native schemas. Top-level scripts always require the explicit wrapper. Switching mode requires a separately prepared and validated native request.

## Acceptance and limits

These are bounded offline methods with synthetic fixtures and declared source evidence. Enterprise access, source authentication, professional acceptance, jurisdiction-specific deployment and execution remain separate. Neither package presence nor successful reconstruction certifies the underlying evidence or professional conclusion.
