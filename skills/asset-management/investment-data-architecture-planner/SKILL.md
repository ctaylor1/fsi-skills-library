---
name: investment-data-architecture-planner
description: "Plan investment data architecture around exact portfolio, security, account, benchmark and time-series grain, licensed purpose, lineage and point-in-time history; review supplied sample resolution and observability using the shared architecture owner."
license: MIT
compatibility: Python 3.10+; portable offline design review. Optional HTTPS reads require an institution-approved gateway, protected policy and credentials.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Institution and data-license specific; no legal determination"
  aws-fsi-owner: "Asset Management investment data and technology"
  aws-fsi-primary-user: "Investment data architect"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Investment data architecture planning

Use for an investment data design or point-in-time history review: for example, combine a security master, portfolio book, custodian account and licensed benchmark feed without erasing source identity or introducing future knowledge. This adapter consumes the actual shared `solution-architecture-planner` review. It adds investment semantics and evidence gates; it does not duplicate that owner's component, interface or cost method.

## Establish the investment data contract

1. Identify the intended research, risk, investment-book or accounting-book use and its accountable owner. Record which source owns each field and date. Keep trade, settlement, valuation and accounting dates distinct; a position in an IBOR is not automatically an ABOR balance. Read [domain rules](references/domain-rules.md) for identity, temporal and benchmark boundaries.
2. Prepare the exact dataset grain and semantic fields from the supplied source dictionary. Declare security/portfolio/account/benchmark/time-series namespaces, currency, units, transformations and versions. Missing identifiers, corporate-action treatment, FX policy and benchmark revisions remain design decisions; do not infer them from names or example fixtures.
3. Obtain the shared architecture owner's original native input and output. Bind the same object, review date, currency and versioned sources. Optional commercial data evidence goes through the shared `data-product-value-evaluator`. Read [schema](references/schema.md) for the native contracts and [handoffs](references/handoffs.md) for adjacent owners.
4. Separate business-valid history from when the institution knew it. Exercise a query before and after a late correction, a validity boundary, an ambiguous overlap and an exact namespace mismatch. Report unresolved samples explicitly. A current restatement must not overwrite a historical research replay.
5. Establish licensed purpose, audience, principal, retention and current permission evidence. Supplied permission records remain unverified. If the user has authorized a read and deployment access exists, use the protected-policy HTTPS client under [gateway contract](references/gateway-contract.md). Never create an approval policy from the request or treat a saved receipt as permission for a new read.
6. Review observed freshness/quality/availability controls separately from proposed targets. Attach the dataset, snapshot, owner, incident route and recovery runbook. Resolve whether replay, stale-data hold or a manual review is appropriate for each dependent investment workflow. Projected test results cannot establish an operating control.

## Produce and verify the draft

Read [source map](references/source-map.md) and [controls](references/controls.md), then run:

```text
python3 -B scripts/validate_input.py REQUEST.json
python3 -B scripts/calculate_or_transform.py REQUEST.json
python3 -B scripts/validate_output.py OUTPUT.json --input REQUEST.json
```

Retain the original request separately. Native output validation reconstructs both the AM result and supplied shared review; it does not authenticate evidence. Use the [output template](assets/output-template.md) to write the architecture decision record separately from immutable JSON. Include each open ownership, license, source, temporal, permission and operational question with an accountable owner.

The local method resolves supplied samples and checks evidence consistency. It does not update reference data, choose an authoritative price, calculate a fund NAV, establish a production book, deploy a platform or certify current access. Production identity matching, richer asset semantics and institution-specific license/legal decisions require their respective owners.
