---
name: adverse-media-investigator
description: >-
  Review supplied media and official-source records for source-side identity evidence, publication/event chronology, reliable relevance and linked matter developments. Produce a scoped review recommendation with unresolved records and search-coverage limits. Use when a financial-crime / negative-news investigator requests evidence review. Human decisions and operational actions remain out of scope.
license: MIT
compatibility: Python 3 standard library for supplied local JSON; live MCP retrieval and system integrations are not implemented.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential customer data; restricted when protected SAR/STR or other restricted material is present"
  aws-fsi-jurisdictions: "Supplied applicable policy profile; no bundled approved legal default"
  aws-fsi-owner: "Negative-news screening and investigation owner"
  aws-fsi-primary-user: "Financial-crime / negative-news investigator"
  aws-fsi-version: "0.1.1"
  aws-fsi-recertification-date: "2027-09-21"
  aws-fsi-review-date: "2026-09-21"
---

# Adverse Media Investigator

Review supplied media and official-source records for source-side identity evidence, publication/event chronology, reliable relevance and linked matter developments. Produce a scoped review recommendation with unresolved records and search-coverage limits.

## Phase 1 scope

No live search, complete corpus certification, source authentication, alias/transliteration inference, independent identity determination or legal culpability determination is implemented. The source category describes reported allegations/findings, not proof of the named crime. Low-reliability reports require reliable independent evidence before material conclusions.

Users: Financial-crime / negative-news investigator. Accountable deployment owner: Negative-news screening and investigation owner; the metadata names an owner function, not an approved appointment or live authorization. Jurisdiction, institution type, policy authority, assessment date and classification must be established for the individual case. No country-specific legal pack is bundled.

## Workflow

1. Confirm the requested evidence review, the case owner, classification/audience and data-access scope. Use supplied records or separately authorized retrieval. Do not infer permission to change systems, contact customers, decide outcomes, send material or file reports.
2. Read [domain rules](references/domain-rules.md), [source/input contract](references/source-map.md), [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md). Use an applicable explicit policy profile; fixtures are test-only.
3. Run `python3 scripts/validate_input.py input.json`. Stop the native computation on structural/policy errors; incomplete substantive evidence must stay unknown or a gap.
4. Run `python3 scripts/calculate_or_transform.py input.json` to produce the bounded native result. Retain the original input separately. Interpret source references as supplied pointers and input hashes as reproducibility controls, not verification of the underlying facts.
5. Validate the complete native result with `python3 scripts/validate_output.py output.json --input input.json`. Added narrative, altered scores, invented evidence or approval claims fail exact reconstruction. Do not weaken this by validating against a rewritten source.
6. Present the scoped result, unknowns and limitations for human review. Use the separate workflow envelope for owner/audience and handoffs; do not append unvalidated prose inside the native result. Consult [controls](references/controls.md) and [handoffs](references/handoffs.md).

## Policy and evidence boundaries

`policy_profile` must carry version, jurisdiction, institution_type, purpose, authority, effective_date, review_due_date, approval_status and approval_ref; version must match the input config/methodology version and dates must cover as_of. `execution_context: review` requires a supplied `approved` status; `test-only` is accepted only with `execution_context: test`. These are asserted metadata and still require the authorized human to verify policy applicability and authority.

Source authenticity, legal applicability, human authorization, fairness, control effectiveness and operational readiness are not established by schema checks or hashes. Missing evidence is never a clean result. Restrict handling according to actual case classification and applicable confidentiality law; routine CDD remediation is not universally prohibited customer contact, but this skill performs no contact.

## Bundled checks

- [Input example](evals/files/screening_batch_example.json) and [bound native result](evals/files/investigation_example.json) are synthetic tests, not approved operational policy.
- `python3 scripts/test_phase1.py` exercises policy, detached-source, adversarial evidence and domain behavior.
- [Evaluation definitions](evals/evals.json) separate executable checks from scenario-only expectations. Passing them is not domain-owner or production acceptance.
