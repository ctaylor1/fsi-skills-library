---
name: market-window-readiness-pack
description: >-
  Assemble a deal-launch readiness packet for a capital-markets transaction and deterministically
  test the required readiness items (due diligence, legal documentation, ratings, marketing
  materials, KYC/AML, board approval) against the approved launch checklist, flagging every
  unattested or missing item with cited evidence for a capital-markets analyst to review. Use when
  an analyst asks to "build the launch readiness pack", "what's outstanding before we can go to
  market", "check deal readiness", or "score launch readiness". HARD BOUNDARY: R2 draft/packaging
  — it evidences readiness only; it NEVER decides or approves launch, clears a deal to price, or
  gives market-timing advice (whether the window is open, when to price); a banker owns those
  calls. MNPI/information-barrier controls apply. Routes financing-cost work to
  financing-alternatives-calculator.
license: MIT
compatibility: Amazon Quick Desktop; requires deal attestation/config records, approved launch-checklist config, and reference-data MCP integrations (all read-only). MNPI-aware.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Capital-markets analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Market Window Readiness Pack

## Purpose and outcome
Given a deal's readiness attestations, deterministically test them against the approved launch
checklist, compute a readiness score, and surface every unattested or missing item with cited
evidence and a suggested review disposition. A successful output lets a capital-markets analyst
review — the launch decision and any market-timing call remain the banker's.

## Use when
- "Build the launch readiness pack", "what's outstanding before we can go to market".
- "Check deal readiness", "score launch readiness".
- A reviewer needs a consistent, cited launch-readiness packet.

## Do not use
- The user wants a **launch decision, pricing clearance, or market-timing view** ("is the window
  open", "should we price now") → out of scope; the banker decides.
- The user wants **financing-cost comparison** → route to `financing-alternatives-calculator`.
- The user wants **research pre-publication checks** → `research-publication-preparation-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a readiness packet with a durable
`packet_id`; it does not decide launch or advise on timing.

## Inputs and prerequisites
- The **deal** context, the **checklist** (required_items with categories + gate items), and
  **attestations** (item_id, status, evidence_ref, justification). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Approved launch-checklist config — a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The attestation/config record is the
system of record; checklist from versioned config. Cite every gap to the item + checklist version.

## Workflow
1. **Validate input** — run `validate_input`; confirm the checklist and attestations are present.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): match each required
   item to its attestation, flag not-attested/missing, note justified N/A, enforce gate items,
   and compute the readiness score by category.
3. **Assemble gaps** — per gap: item, category, expected vs found, citation.
4. **Suggest disposition** — `ready-for-review` or `gaps-for-review` (a triage suggestion, not a
   launch decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-launch/no-timing screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a gap lacks a citation, or the text contains
launch-decision or market-timing language, **fix or fail closed**.

## Human approval
`external-delivery`: the pack may be produced, but external delivery requires human sign-off; no
launch decision or timing advice is ever made by this skill.

## Failure handling
- **Missing checklist/config** → fail closed; state what is missing; do not assume readiness.
- **N/A without justification** → treat as a gap; never accept an unjustified exemption.
- **Gate item not attested** (e.g., due diligence, board approval) → always a gap.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — deal (masked), checklist version, readiness score, gap count, disposition.
2. **Gaps** — per gap: item, category, expected vs found, citation.
3. **By-category readiness** and data gaps.
4. **Machine-readable** — checks + gaps + score + `packet_id`.
5. **Standing disclaimer** — "Readiness evidence only; not a launch decision, a pricing clearance,
   or market-timing advice. No deal has been approved for launch."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Enforce information barriers; deal-team only. Retain packet +
citations + checklist version. Log read + external-delivery approval. Never cross the wall.

## Gotchas
- **A full score is not a launch.** Complete attestation is a review prompt, not a go-decision.
- **Never opine on the window.** Whether conditions favor launch is a banker judgment, never this
  skill's.
- **Gate items** (due diligence, board approval) are never waived.
- **N/A must be justified** — an unexplained N/A is a gap.
