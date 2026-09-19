---
name: payment-scheme-change-tracker
description: Review supplied payment-scheme bulletins and structured obligations for unmapped impacts, missing owners and implementation timing. Produces read-only alerts; does not retrieve or authenticate publications, extract obligations, adopt rules or update systems.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. Expected source-system integrations must be supplied by deployment; no connectors or actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments compliance / product / operations"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Payment scheme change tracking

Use for an internal impact/readiness review of supplied structured scheme bulletins.
Collect source/version, effective dates, obligation IDs, affected products/processes/
controls/contracts/systems, owner registry and prior alert fingerprints. Load
[references/source-map.md](references/source-map.md) for the exact input shape.

Run input validation, calculation and output validation using the matching scripts.
The engine checks declared publisher/version data and consumes supplied obligations;
it does not authenticate signatures, fetch publications or extract source text.
Every supplied bulletin remains unverified-source until the deployment performs its
own external verification. The legacy authenticity alert category means a provenance
review is required, not that a publication has been proved fraudulent.

Use [references/domain-rules.md](references/domain-rules.md) for readiness bands and
deduplication. Future-effective obligations can generate planning alerts but are not
current law. Preserve each source's scheme, participant, jurisdiction and status;
applicability interpretation requires responsible review. Never adopt, waive, close,
file or record a rule implementation through this read-only workflow.

The supplied source snapshot supports recomputation and lineage, not authentication.
Use [references/handoffs.md](references/handoffs.md) for regulatory impact, policy gaps
or contract extraction. Read [references/payment-contract.md](references/payment-contract.md).
Run `python scripts/test_phase1.py`; command evaluations and natural-language cases
remain separate in [evals/evals.json](evals/evals.json).
