---
name: liability-evidence-matrix-builder
description: >-
  Build a claim liability-evidence matrix that maps each alleged fact to its supporting and
  contradicting evidence items with citations, assigns a deterministic coverage status
  (supported / contested / unsupported), and flags evidence gaps — as a casework bundle for a
  claims adjuster to review. Use when an adjuster asks to "map the evidence to the facts", "build
  the liability evidence matrix", "which allegations are unsupported", or "what evidence do we
  have for each fact". HARD BOUNDARY: R3 investigation/decision-support only — it NEVER determines
  liability, fault, or negligence, never apportions responsibility, and never decides the claim;
  every status is an evidence observation an adjuster must adjudicate. Routes damage-document
  comparison to claim-damage-evaluation-comparator.
license: MIT
compatibility: Amazon Quick Desktop; requires claim fact/evidence records and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Claims adjuster"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Liability Evidence Matrix Builder

## Purpose and outcome
Given a claim's alleged facts and evidence items, deterministically map each fact to its
supporting and contradicting evidence, assign a coverage status (supported / contested /
unsupported), and flag evidence gaps — each with citations. A successful output is an
evidence-mapped casework bundle an adjuster reviews; the liability/fault determination remains
the adjuster's.

## Use when
- "Map the evidence to the facts", "build the liability evidence matrix".
- "Which allegations are unsupported", "what evidence do we have for each fact".
- A reviewer needs a consistent, cited fact→evidence matrix.

## Do not use
- The user wants a **liability, fault, or negligence determination** → out of scope; the adjuster
  decides.
- The user wants **damage-document comparison** → route to `claim-damage-evaluation-comparator`.
- The user wants a **settlement-authority packet** → `claim-settlement-authority-packet`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a matrix with a durable `matrix_id`;
it does not determine liability.

## Inputs and prerequisites
- The **claim**, the **facts** (fact_id, statement, party), and the **evidence** (evidence_id,
  type, source_ref, supports[], contradicts[]). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Status thresholds are documented. See [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The claim file is the system of record.
Cite every matrix cell to the specific evidence items.

## Workflow
1. **Validate input** — run `validate_input`; confirm facts and evidence with references.
2. **Build (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): for each fact, collect
   supporting and contradicting evidence, assign status, and flag unsupported facts as gaps.
3. **Assemble the matrix** — per fact: supporting[], contradicting[], status, citations.
4. **Suggest disposition** — `matrix-complete` or `gaps-for-review` (a triage suggestion, not a
   liability finding).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-liability screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a matrix cell lacks evidence citations, or
the text contains liability/fault language, **fix or fail closed**.

## Human approval
`required`: no liability, fault, negligence, or apportionment determination without the adjuster.
The skill only maps evidence.

## Failure handling
- **Evidence referencing an unknown fact** → flag as a dangling reference; never silently drop.
- **A fact with no evidence** → `unsupported` + a gap; never infer support.
- **Contradicting evidence** → status `contested`; never resolve the conflict.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — claim (masked), fact count, status counts, disposition.
2. **Matrix** — per fact: statement, party, supporting/contradicting evidence, status, citations.
3. **Gaps** — unsupported facts and dangling references.
4. **Machine-readable** — matrix + `matrix_id`.
5. **Standing disclaimer** — "Evidence mapping only; not a liability, fault, or negligence
   determination and not a claim decision. No responsibility has been apportioned."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII (may include injury/medical). Mask claimant identifiers. Retain matrix +
citations. Log read + external-delivery approval. Never exfiltrate claim data.

## Gotchas
- **A status is not a verdict.** `supported` means evidence exists, not that the fact is true or
  that anyone is liable.
- **Contested ≠ resolved** — surface both sides; the adjuster weighs them.
- **Never apportion fault or use liability language** — evidence only.
- **Dangling evidence** (points to a missing fact) is a data-quality flag, not a finding.
