---
name: claim-settlement-authority-packet
description: >-
  Assemble a settlement-authority request packet for a claim — claim summary, the adjuster's
  evaluated exposure (indemnity + expense from provided inputs), the required authority tier and
  approver from the authority matrix, and a supporting-evidence index — and check completeness
  against the packet checklist, for a senior adjuster to route for approval. Use when an adjuster
  asks to "build the settlement authority request", "which authority level is needed to settle
  this", "package the settlement approval request", or "who signs off on this settlement amount".
  HARD BOUNDARY: R3 draft/decision-support only — it NEVER approves a settlement, grants or
  exercises authority, authorizes payment, or sets the settlement amount; it looks up the required
  tier deterministically and packages the request for a human approver. Routes evidence mapping to
  liability-evidence-matrix-builder.
license: MIT
compatibility: Amazon Quick Desktop; requires claim/evaluation records, authority-matrix config, and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Senior adjuster"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claim Settlement Authority Packet

## Purpose and outcome
Given a claim's evaluated exposure and the authority matrix, deterministically compute total
exposure, look up the required authority tier and approver, index the supporting evidence, and
check the packet against the checklist. A successful output is a routed authority *request* a
senior adjuster reviews; the settlement approval and authority grant remain the authorized
approver's.

## Use when
- "Build the settlement authority request", "which authority level is needed to settle this".
- "Package the settlement approval request", "who signs off on this settlement amount".
- A reviewer needs a consistent, cited authority-request packet.

## Do not use
- The user wants you to **approve the settlement, grant authority, or authorize payment** → out of
  scope; the human approver acts.
- The user wants **evidence mapping / liability** → route to `liability-evidence-matrix-builder`.
- The user wants **damage-document comparison** → `claim-damage-evaluation-comparator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a request packet with a durable
`packet_id`; it does not approve or grant authority.

## Inputs and prerequisites
- The **claim**, the **evaluation** (indemnity_estimate, expense_estimate, basis_note), the
  **authority_matrix** (tiers), **evidence_refs**, and the **checklist**. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The authority matrix is a versioned contract; the packet looks up, it does not decide. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The claim/evaluation record is the
system of record; the matrix from versioned config. Cite the tier and each item to its source.

## Workflow
1. **Validate input** — run `validate_input`; confirm evaluation figures and the matrix.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): total = indemnity +
   expense; select the smallest tier whose cap ≥ total; record the approver; check completeness.
3. **Assemble the packet** — exposure, required tier/approver, evidence index, gaps.
4. **Suggest disposition** — `packet-ready` or `gaps-for-review` (a triage suggestion, not an
   approval).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-approval/no-authority-grant screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a gap lacks a citation, or the text contains
approval/authority-grant/payment language, **fix or fail closed**.

## Human approval
`required`: no settlement approval, authority grant, payment authorization, or amount-setting
without the authorized approver. The skill only packages the request.

## Failure handling
- **Exposure exceeds the top tier** → flag `exceeds_matrix`; route to the highest tier + escalate;
  never approve.
- **Missing evaluation figure** → fail closed on the total; do not assume a number.
- **Missing checklist item** → completeness gap; do not fabricate the content.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — claim (masked), total exposure, required authority tier + approver, disposition.
2. **Exposure** — indemnity, expense, total, basis note.
3. **Evidence index** and completeness gaps (each cited).
4. **Machine-readable** — exposure + tier + gaps + `packet_id`.
5. **Standing disclaimer** — "Authority-request packet only; not a settlement approval, a grant or
   exercise of authority, or a payment authorization. No settlement has been approved."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask claimant identifiers. Retain packet + citations + matrix version. Log read
+ external-delivery approval. Never exfiltrate claim data.

## Gotchas
- **The tier is a lookup, not an approval.** Identifying the required approver is not granting
  authority.
- **Exceeds-matrix** exposure is escalated, never approved at the top tier by default.
- **Total exposure** is indemnity + expense from the provided evaluation — never re-estimate the
  claim value here.
- **Never authorize payment or state the settlement is approved.**
