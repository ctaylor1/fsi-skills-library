---
name: claimant-dispute-packager
description: "Prepare a claimant-owned dispute chronology, adverse-reason evidence matrix and concrete requests using the supplied notice and appeal route. Use to organize claimant reconsideration or information requests; no carrier response, legal merits decision, filing or invented deadline."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction and product profiles required; synthetic US-TEST is not a legal profile"
  aws-fsi-owner: "Insurance claimant advocacy"
  aws-fsi-primary-user: "Claimant or authorized claimant representative"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Claimant Dispute Packet

Start from the claimant and actual adverse notice, maintaining the claimant's requested remedy. Preserve each notice reason and cited provision verbatim in structured source fields; label a missing provision as absent-in-notice. Order events by sourced dates and retain actor and factual description. A reason-to-evidence link explicitly explains supporting, contrary or contextual relevance. Keep contrary evidence visible; an apparent document inconsistency is not proof that the carrier erred.

Each adverse reason needs mapped evidence and at least one specific reconsideration, information or correction request. Gaps remain in the packet. Record the notice receipt, destination, appeal route and source-reviewed response date; no standard number of days is built in. Jurisdiction, contract, benefit plan, notice and delivery circumstances determine applicability. An elapsed date prompts human review and does not establish loss of rights.

The output is a draft claimant request packet. It does not change to carrier capacity, draft an institutional complaint response, certify legal sufficiency, submit an appeal or contact anyone. For clinical disputes retain qualified medical evidence rather than having the assistant decide clinical facts.

## Prepare and review

Read [references/schema.md](references/schema.md) to construct native input and [references/source-map.md](references/source-map.md) to bind evidence. Do not invent facts to fill the schema or treat invented fixtures as approved rule profiles. The profile must establish jurisdiction, product, effective dates, method and accountable reviewer.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the output in an authorized location and run `python scripts/validate_output.py OUTPUT.json`. Output validation re-runs the native method from retained source evidence, including when someone has recomputed hashes after altering results. Use [assets/output-template.md](assets/output-template.md) for the human-readable draft, citing the actual source passages.

Read [references/domain-rules.md](references/domain-rules.md), [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md) for limits and ownership. [references/insurance-foundation.md](references/insurance-foundation.md) and [references/insurance-contract.md](references/insurance-contract.md) define retained evidence, inherited unresolved issues and source-bound capacity mappings. A complete draft or consistent content hash proves neither source truth nor professional approval.

Run `python scripts/test_domain.py` and executable cases in [evals/evals.json](evals/evals.json). Planned natural-language evaluations are recorded separately and remain unrun until actually reviewed. Production use still needs domain, control and legal/compliance acceptance and privacy/retention configuration.
