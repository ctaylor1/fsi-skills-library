---
name: research-publication-preparation-assistant
description: >-
  Prepare a research note for publication by deterministically checking required disclosures,
  rating-scale validity, rating/target-price directional consistency, restricted-list status, and
  the pre-publication compliance checklist — producing a cited pre-publication packet for a
  research associate and supervisory analyst to review. Use when an associate asks to "prep this
  note for publication", "run the pre-pub checks", "are the disclosures complete", or "is this
  ticker on the restricted list". HARD BOUNDARY: R3 draft/decision-support only — it NEVER
  publishes or distributes the note, approves it for publication, or sets/determines the rating or
  target price; it checks and flags for a human. MNPI/information-barrier and research-independence
  controls apply. Routes filing-disclosure change detection to filing-disclosure-change-detector.
license: MIT
compatibility: Amazon Quick Desktop; requires research-note, disclosure-config, restricted-list, and compliance-checklist MCP integrations (all read-only). MNPI-aware.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Research associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Research Publication Preparation Assistant

## Purpose and outcome
Given a research note and the applicable configs, deterministically check required disclosures,
rating-scale validity, rating/target directional consistency, restricted-list status, and the
pre-publication checklist, and surface every gap/flag with citations. A successful output is a
pre-publication packet a research associate and supervisory analyst review; publication, approval,
and the rating/target itself remain the human's.

## Use when
- "Prep this note for publication", "run the pre-pub checks".
- "Are the disclosures complete", "is this ticker on the restricted list".
- A reviewer needs a consistent, cited pre-publication readiness packet.

## Do not use
- The user wants you to **publish/distribute, approve, or set the rating/target** → out of scope;
  the human/supervisory analyst acts.
- The user wants **filing-disclosure change detection** → route to
  `filing-disclosure-change-detector`.
- The user wants a **communications-surveillance review** → `communications-compliance-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a packet with a durable `prep_id`; it
does not publish, approve, or rate.

## Inputs and prerequisites
- The **note** (ticker, rating, prior_rating, target_price, prior_target), **disclosures**
  (required/present), **restricted_list**, **rating_scale**, and **checklist**. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Disclosure/restricted-list/checklist configs are versioned contracts. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The note is the draft; compliance
configs are the authority for disclosures and the restricted list. Cite every gap/flag.

## Workflow
1. **Validate input** — run `validate_input`; confirm the note and configs.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): disclosure
   completeness, rating-scale validity, rating/target directional consistency, restricted-list
   status, and checklist completeness.
3. **Assemble gaps/flags** — per gap/flag: reason, evidence, citation.
4. **Suggest disposition** — `ready-for-compliance-review` or `gaps-for-review` (a triage
   suggestion, not a publication decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-publish/no-approval/no-rating screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a gap/flag lacks a citation, or the text
contains publish/approval/rating-determination language, **fix or fail closed**.

## Human approval
`required`: no publication, distribution, publication approval, or rating/target determination
without the authorized human/supervisory analyst. The skill only checks and flags.

## Failure handling
- **Restricted ticker** → surface a restricted flag and route to compliance; never clear it.
- **Missing disclosure** → gap; never assume a disclosure is present.
- **Rating not in scale** → flag; never coerce to a valid rating.
- **Rating/target directional conflict** → flag (upgrade with a target cut, or vice versa); never
  resolve it.

## Output contract
1. **Summary** — note id, ticker (as permitted), disposition, gap/flag counts.
2. **Checks** — disclosure completeness, rating validity, rating/target consistency,
   restricted-list status, checklist completeness.
3. **Gaps & flags** — each with reason + citation.
4. **Machine-readable** — checks + gaps + flags + `prep_id`.
5. **Standing disclaimer** — "Pre-publication preparation only; not a publication, a distribution,
   a publication approval, or a rating/target determination. Nothing has been published."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential; research independence. Enforce information barriers. Retain packet +
citations + config versions. Log read + external-delivery approval. Never cross the wall.

## Gotchas
- **Prep is not publication.** Passing checks is a review prompt, not a clearance to publish.
- **A restricted ticker is a hard stop** — surface it; compliance decides, not this skill.
- **Rating/target consistency is directional** — it flags conflicts, it does not set the target.
- **Never determine or change the rating** — the analyst owns the call.
