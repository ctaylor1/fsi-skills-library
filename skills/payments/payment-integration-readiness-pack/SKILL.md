---
name: payment-integration-readiness-pack
description: >-
  Assemble a go-live readiness packet for a payment integration and deterministically test the
  required readiness items (idempotency, retries, reconciliation, webhook handling, PCI scope,
  monitoring, test coverage) against the approved readiness checklist, flagging every unattested
  or missing item with cited evidence for an implementation manager to review. Use when a manager
  asks to "build the go-live readiness pack", "check we're ready to launch this integration",
  "what's outstanding before go-live", or "score integration readiness". HARD BOUNDARY: R3
  draft/decision-support only — it NEVER approves go-live, clears an integration to launch, or
  declares production-readiness; every disposition is a recommendation an authorized human must
  adjudicate. Routes error diagnosis to payment-api-log-diagnostic-pack.
license: MIT
compatibility: Amazon Quick Desktop; requires integration attestation/config records, approved readiness-checklist config, and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments implementation manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Integration Readiness Pack

## Purpose and outcome
Given an integration's readiness attestations, deterministically test them against the approved
readiness checklist, compute a readiness score, and surface every unattested or missing item with
cited evidence and a suggested review disposition. A successful output lets an implementation
manager review — the go-live decision remains the authorized human's.

## Use when
- "Build the go-live readiness pack", "check we're ready to launch this integration".
- "What's outstanding before go-live", "score integration readiness".
- A reviewer needs a consistent, cited readiness packet.

## Do not use
- The user wants you to **approve go-live or clear the integration to launch** → out of scope; a
  human decides.
- The task is **error diagnosis** from logs → route to `payment-api-log-diagnostic-pack`.
- The task is **fraud-rule impact** → `payment-fraud-rule-impact-analyzer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a readiness packet with a durable
`packet_id`; it does not approve go-live.

## Inputs and prerequisites
- The **integration** context, the **checklist** (required_items with categories), and
  **attestations** (item_id, status, evidence_ref). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Approved readiness-checklist config — a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The attestation/config record is the
system of record; checklist from versioned config. Cite every gap to the item + checklist version.

## Workflow
1. **Validate input** — run `validate_input`; confirm the checklist and attestations are present.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): match each required
   item to its attestation, flag not-attested/missing, note N/A with justification, and compute
   the readiness score by category.
3. **Assemble gaps** — per gap: item, category, expected vs found, citation.
4. **Suggest disposition** — `ready-for-review` or `gaps-for-review` (a triage suggestion, not a
   go-live decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-go-live-approval screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a gap lacks a citation, or the text contains
go-live approval/launch language, **fix or fail closed**.

## Human approval
`required`: no go-live approval or launch clearance without an authorized human. The skill only
evidences readiness gaps.

## Failure handling
- **Missing checklist/config** → fail closed; state what is missing; do not assume readiness.
- **N/A without justification** → treat as a gap; never accept an unjustified exemption.
- **Missing attestation** → flag as a gap, do not assume attested.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — integration (masked), checklist version, readiness score, gap count, disposition.
2. **Gaps** — per gap: item, category, expected vs found, citation.
3. **By-category readiness** and data gaps.
4. **Machine-readable** — checks + gaps + score + `packet_id`.
5. **Standing disclaimer** — "Readiness evidence only; not a go-live approval or a launch
   clearance. No integration has been approved for production."
See [references/controls.md](references/controls.md).

## Privacy and records
Cardholder data + NPI/PII. Mask merchant/account identifiers. Retain packet + citations +
checklist version. Log read + external-delivery approval. Never exfiltrate integration data.

## Gotchas
- **A green score is not an approval.** Full attestation is a review prompt, not a launch.
- **PCI-scope items** are gate items; a missing PCI attestation is always a gap, never waved.
- **N/A must be justified** — an unexplained N/A is a gap.
- **Never declare "production-ready"** — evidence and score only.
