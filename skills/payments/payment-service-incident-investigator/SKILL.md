---
name: payment-service-incident-investigator
description: Investigate payment-service incidents using unique payment outcomes, attempts, release/provider/trace
  timelines and entity/currency exposure. Draft hypotheses, bounded containment and reconciliation recovery; retains
  legacy API log diagnostics without executing remediation.
license: MIT
compatibility: Python 3.10+; standard library only. Offline supplied JSON; no connectors or production actions bundled.
metadata:
  aws-fsi-category: Payments
  aws-fsi-skill-type: Analysis and evaluation skills
  aws-fsi-risk-tier: R3
  aws-fsi-archetype: Analyze & review
  aws-fsi-agent-pattern: Interactive decision-support copilot
  aws-fsi-delivery-wave: Payments Phase 3
  aws-fsi-action-mode: Draft-only; no system-of-record change
  aws-fsi-scheduled-agent: 'no'
  aws-fsi-baseline-status: existing-updated
  aws-fsi-human-approval: required
  aws-fsi-data-classification: Confidential; opaque payment identifiers only
  aws-fsi-jurisdictions: Initial US, euro area and UK; scope-specific evidence required
  aws-fsi-owner: Payments service operations and resilience
  aws-fsi-primary-user: Payment incident commanders, support and engineering
  aws-fsi-version: 0.3.0
  aws-fsi-recertification-date: '2027-09-18'
---

# Payment service incident investigation

Use for a service-level payment incident spanning retries, releases, traces and uncertain
customer outcomes. Preserve one-payment repair ownership and distinguish service impact
from acceptance-performance experiments. Read [references/incident-schema.md](references/incident-schema.md)
for the Phase 3 native contract and [references/incident-rules.md](references/incident-rules.md)
for consequence and recovery boundaries.

1. Establish the incident window and eligible unique-payment inventory independently of
   attempt logs. Quarantine conflicting identities; keep unknown outcomes unresolved.
2. Inspect retry chains, authoritative lifecycle outcomes and amount partitions by legal
   entity and currency. Report attempts, customer outcomes and actual loss separately.
3. Build a source-linked release/provider/trace timeline. Record competing hypotheses and
   discriminating tests. Coincidence and frequent error categories do not prove cause.
4. Draft bounded containment and recovery: preserve original identities, status lookup,
   reconciliation, outstanding ownership and support handoff. A timeout cannot justify
   resending with a new key. Retain unresolved payment inventory after technical recovery.
5. Produce [assets/incident-template.md](assets/incident-template.md). Hand off repair and
   release evidence through [references/handoffs.md](references/handoffs.md); neither an
   incident summary nor a supplied pass flag authorizes recovery execution or closure.

Run `python scripts/validate_incident_input.py INPUT.json`,
`python scripts/investigate_incident.py INPUT.json > OUTPUT.json`, and
`python scripts/validate_incident_output.py OUTPUT.json --input INPUT.json`.
Run `python scripts/test_phase3.py` for new regressions.

## Legacy API log diagnostic mode

The original `scripts/validate_input.py`, `scripts/calculate_or_transform.py`, and
`scripts/validate_output.py` remain callable with their original log contract, including
`--selftest`. Read [references/domain-rules.md](references/domain-rules.md) and use
[assets/output-template.md](assets/output-template.md). That mode categorizes supplied
log rows and masks PAN-shaped sequences; it does not reconstruct incident denominators,
retry chains or financial outcome. Run `python scripts/test_phase1.py` to verify its
compatibility. New incident mode accepts opaque identities and redacted evidence only.

Read [references/source-map.md](references/source-map.md), [references/controls.md](references/controls.md)
and [references/payment-contract.md](references/payment-contract.md). All modes remain
read-only or draft-only. No configuration, payment, key or incident state is changed.
