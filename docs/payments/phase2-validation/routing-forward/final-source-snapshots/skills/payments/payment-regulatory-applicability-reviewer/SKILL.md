---
name: payment-regulatory-applicability-reviewer
description: Map a payment entity, activity, customer model and funds flow to candidate licensing, safeguarding, consumer and operational obligations in the US, euro area and UK. Produce a sourced applicability matrix and specialist-review questions; do not determine legal clearance, permissions or compliance.
license: MIT
compatibility: Python 3.10+; supplied JSON evidence and bundled public-source summaries. No live regulatory register, legal database or payment connector is bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Payments Phase 2"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential; minimize customer identifiers"
  aws-fsi-jurisdictions: "US, euro area and UK initial profiles; national and institutional review required"
  aws-fsi-owner: "Payments product, legal and compliance"
  aws-fsi-primary-user: "Payment product, legal and compliance teams"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment regulatory applicability

Start with the legal entity, actual activity and ownership of funds. A provider
brand, bank partnership, technology label or scheme membership does not establish
permissions. Separate entity licensing, contractual scheme rules, customer rights,
financial crime, safeguarding and operating controls in the resulting matrix.

Use this for a proposed payment proposition or changed operating model. Use the
scheme-change tracker for a known publication change, the issuer dispute reviewer
for a specific consumer error, and shared financial-crime specialists for match
adjudication. This package does not license an entity or interpret every national law.

## Evidence and procedure

Read [references/schema.md](references/schema.md) before constructing the request.
Register supplied sources and keep absent facts explicit. Read
[references/domain-rules.md](references/domain-rules.md) for activity distinctions and
[references/source-map.md](references/source-map.md) for the authority hierarchy.

1. Identify the legal entity, home/operating countries, consumer or business
   customer, exact service and whether funds are held. Map the holder and customer
   claim at each step. Do not infer a technical-service exclusion from a label.
2. Run `python scripts/validate_input.py INPUT.json` and then
   `python scripts/calculate_or_transform.py INPUT.json`.
3. Review each candidate obligation against the actual entity/activity. Resolve
   state scope in the US and national transposition in the euro area. Keep UK
   payment/e-money safeguarding distinct from bank deposits and deposit insurance.
4. Use [references/consumer-error-profiles.json](references/consumer-error-profiles.json)
   for product-specific error-review orientation. Select legal clocks separately
   from [references/scheme-stage-profiles.json](references/scheme-stage-profiles.json).
   These are source summaries, not approved case deadlines or legal opinions.
5. Produce the matrix and open decisions using
   [assets/output-template.md](assets/output-template.md). Run
   `python scripts/validate_output.py OUTPUT.json --input INPUT.json`.
6. Send scoped evidence and unresolved issues through
   [references/handoffs.md](references/handoffs.md). Native target validation remains
   required. A hash or supplied reviewer reference is not an authenticated approval.

## Boundaries and failure handling

Unsupported jurisdictions return `unsupported`; missing, conflicting or stale
scope returns `needs-evidence`. No result is a license, exemption, compliance
certification, customer-liability decision or permission to move funds. National,
product and institution overlays must be reviewed before operational use.

Do not send customer communications, file applications, decide claims or change
systems. Mandatory specialist adjudication and privacy/retention controls are in
[references/controls.md](references/controls.md). Shared monetary, evidence and
handoff semantics are in [references/payment-contract.md](references/payment-contract.md).
Run `python scripts/regression_tests.py` for bounded software checks. These do not
establish professional acceptance or replace real-model evaluations.
