---
name: fund-commentary-drafter
description: >-
  Draft monthly or quarterly fund commentary from reconciled performance and attribution,
  holdings and positioning, flows, market context, and the approved messaging library — with
  every figure tied out and every claim bound to a source citation. Use when an
  asset-management product, investor-relations, or portfolio team needs to assemble a periodic
  fund-commentary draft, substantiate its claims, reconcile performance and attribution to
  source, flag unsupported statements, and route the draft for product and compliance sign-off.
  HARD BOUNDARY: draft-only — it never sends, files, publishes, or distributes; it never
  asserts an unsupported or unapproved claim, never uses return guarantees or other prohibited
  marketing language, never drafts un-reconciled numbers, and requires recorded product AND
  compliance approval before any external delivery.
license: MIT
compatibility: Amazon Quick Desktop; requires reconciled-performance, attribution, holdings/positioning, flows, market-data, controlled-content (approved messaging + disclosures/templates), and prior-commentary MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Asset-management product / investor relations / portfolio team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Fund Commentary Drafter

## Purpose and outcome
Assemble a periodic (monthly / quarterly) **fund-commentary draft** from reconciled sources
and the approved messaging library, producing a controlled deliverable a human can review
and deliver. The output is a draft package with a **claim ledger** (every statement bound to
a citation), **tie-out evidence** (performance and attribution reconcile), the required
**disclosures**, and a **product + compliance sign-off block**. A successful output lets
reviewers approve and deliver quickly because each claim is traceable and each number ties
out — the skill itself never sends, files, or publishes.

## Use when
- "Draft the Q2 commentary for the Global Equity Fund."
- "Write this month's fund commentary from the reconciled performance and attribution."
- "Turn the attribution and positioning into commentary and flag anything unsupported."
- "Prepare the commentary and route it for product and compliance sign-off."

## Do not use
- **Attribution / exposure analytics** themselves → `performance-attribution-builder`,
  `portfolio-exposure-analyzer` (this skill *consumes* their cited outputs).
- A **fund fact sheet** (data card) → `fund-fact-sheet-builder`.
- An **investment-committee memo** → `investment-committee-memo-builder`.
- **RFP / DDQ** responses → `due-diligence-questionnaire-responder`.
- Any request to **send, publish, file, or distribute** the commentary, to **self-approve**,
  or to draft **personalized investment advice** → refuse; route to the human approvers.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream analytics
(`performance-attribution-builder`, `portfolio-exposure-analyzer`,
`liquidity-stress-analyzer`) feed cited inputs; downstream, the drafted package goes to
`communications-compliance-reviewer` and to human product/compliance approvers. This skill
emits a draft package and must not perform the upstream analytics or the downstream review.

## Inputs and prerequisites
- A commentary-inputs file: fund/share-class/benchmark/currency, period, **reconciled**
  performance, **reconciled** attribution (effects), positioning, flows, market context,
  **approved** messaging, required disclosures, template version, prior-commentary ref, and
  any proposed `draft_claims`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to performance, attribution, holdings, flows, market data, and the controlled
  content library (messaging + disclosures + template).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Reconciled performance and
attribution are the systems of record for the numbers; the approved messaging library and
disclosure set are **versioned contracts**. Forward/thematic language comes **only** from
approved messaging. Cite every claim.

## Workflow
1. **Validate inputs** — run `validate_input`; resolve tie-out and data-quality warnings
   (un-reconciled numbers, missing disclosures, non-approved messaging) before drafting.
2. **Tie out the numbers (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): confirm
   `excess == fund − benchmark` and `sum(attribution effects) == total_excess == excess`.
   Un-reconciled figures are not drafted.
3. **Assemble the claim ledger** — build each section's claims from the reconciled data and
   **approved** messaging; every claim carries a citation and the commentary period label.
4. **Substantiate proposed narrative** — resolve any free-text `draft_claims` against known
   sources / approved messaging; **flag and exclude** anything that cannot be tied to a
   source. Nothing unsupported is asserted.
5. **Apply the template** — fill the required sections
   ([assets/output-template.md](assets/output-template.md)); attach the tie-out block and the
   required disclosures.
6. **Route for sign-off** — leave product and compliance approvals **pending**; the draft is
   not for delivery until both are recorded. Never send/publish/file.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output gate enforces: all required sections present; performance and attribution
tie-outs `ok`; every claim supported and period-consistent with none unsupported; no
prohibited/misleading marketing language; required disclosures present; product **and**
compliance approvals recorded; `delivery_status` not sent/distributed; standing note
present. Fail closed on any miss.

## Human approval
`external-delivery`. **Product** approves messaging and positioning consistency;
**compliance** approves disclosures and the prohibited-claim screen. Both must be recorded
(approver + date) before external delivery or any system-of-record change. This skill drafts
and packages; humans approve and deliver. It never self-approves and never delivers.

## Failure handling
- **Un-reconciled / mismatched numbers** → do not draft; return for reconciliation with the
  specific tie-out that failed.
- **Missing / non-approved messaging** → omit the forward/thematic claim; do not invent one.
- **Unsupported proposed claim** → flag and exclude; never assert to fill a gap.
- **Missing required disclosure** → block release; list the missing disclosure IDs.
- **Missing an approval** → keep `draft`; surface which sign-off is outstanding.
- **Tool timeout / partial data** → return a partial draft with an explicit incomplete flag;
  assume no automatic retry.

## Output contract
1. **Draft package** — header, the seven required sections, and the claim ledger (each claim:
   text, `source_refs`, `supported`, `period_label`).
2. **Tie-out block** — performance and attribution reconciliations with detail.
3. **Disclosures** — the required disclosure IDs for the fund/jurisdiction.
4. **Sign-off block** — product and compliance status (pending until recorded by humans).
5. **Unsupported-claims list** — anything flagged and excluded, with the reason.
6. **Machine-readable** — the package JSON keyed to the template version.
7. **Standing note** — "Draft only - not for distribution until product and compliance
   approvals are recorded; this skill does not send, file, or publish."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Treat holdings, flows, and unpublished
performance as material non-public until the commentary is published. Retain the draft, the
claim ledger with citations, tie-out evidence, template/messaging/disclosure versions, and
both sign-offs per the marketing-records retention period; log drafter and approver
identities.

## Gotchas
- **Substantiation, not fluency.** A well-written sentence with no citation is still an
  unsupported claim — it is flagged and excluded, not smoothed over.
- **Outlook is library-bound.** Forward/thematic text must come from **approved** messaging;
  paraphrasing into a new promise is not allowed.
- **Numbers must tie before prose.** Excess must equal fund − benchmark and attribution must
  sum to it; a plausible-looking number that does not reconcile is not drafted.
- **Draft ≠ delivery.** Product and compliance sign-off are separate, human, and required;
  this skill never sets a sent/distributed status.
- **Disclosures are excluded from the language screen.** Standard "past performance is not a
  guarantee…" boilerplate lives in the disclosures block, not the claim narrative, so it is
  not mistaken for a prohibited guarantee.
