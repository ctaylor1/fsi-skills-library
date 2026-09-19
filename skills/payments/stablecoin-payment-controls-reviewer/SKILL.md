---
name: stablecoin-payment-controls-reviewer
description: Review supplied stablecoin control evidence against an explicit active participant/jurisdiction policy profile. Flags missing, unknown or contradictory controls for human review; does not assess settlement adoption, authenticate attestations or determine legal compliance.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. Expected source-system integrations must be supplied by deployment; no connectors or actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments product risk / compliance / treasury"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Stablecoin control evidence review

This package remains a bounded control-evidence review. Use the installed `stablecoin-settlement-assessor` for a concrete use-case comparison against a fiat alternative. This controls package retains its original policy_profile/control API and does not determine whether a merchant using a
stablecoin has an issuer's reserve, mint/burn or custody obligations.

Require a policy_profile identifying source, authority, version, active dates, review
owner/due date, participants, jurisdictions and explicit required_controls. Read
[references/source-map.md](references/source-map.md). Missing/inapplicable/expired
profiles make results not_evaluable and escalated. Missing required controls stay
visible; duplicate control IDs are ambiguous evidence. A supplied attestation is not
independent authentication or proof of effectiveness.

Numeric policy parameters must be supplied explicitly for the affected control.
There is no universal travel-rule threshold, reporting cadence or chain confirmation
count. Travel-rule comparison additionally requires threshold_currency; finality
comparison requires chain_id. Preserve legal instrument distinctions and applicability.
Firm policy cannot override law. The rule list is an evaluation vocabulary, not a
complete legal compliance framework.

Run `python scripts/validate_input.py INPUT.json`,
`python scripts/calculate_or_transform.py INPUT.json`, then
`python scripts/validate_output.py OUTPUT.json`. Explain unresolved evidence and
source limitations using [references/domain-rules.md](references/domain-rules.md).
No launch approval, compliance attestation, filing, waiver or system write occurs.
Use [references/handoffs.md](references/handoffs.md) for specialist work and
[references/payment-contract.md](references/payment-contract.md) for shared semantics.
Run `python scripts/test_phase1.py`.
