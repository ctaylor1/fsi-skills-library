---
name: gl-reconciler
description: >-
  Reconcile a general-ledger control account to its subledger or source system: match
  records, classify every disagreement into a fixed break taxonomy (timing, amount
  mismatch, unrecorded-in-GL, unsupported-in-GL, duplicate), trace each break to its source
  rows, tie the breaks out to the GL-vs-subledger difference, and draft PROPOSED correction
  journal entries. Use when an accountant or finance-operations user asks to "reconcile this
  GL account to the subledger", "why doesn't the GL tie to the bank/AP/AR detail", "classify
  the reconciliation breaks", or "propose the correcting entries" for month-end or audit.
  This skill drafts and evidences reconciliations and PROPOSES corrections only; it NEVER
  posts, books, or writes a journal entry, never adjudicates which side is correct, and
  never forces a tie with a plug — posting is a human/authorized-system action.
license: MIT
compatibility: Amazon Quick Desktop; requires ERP/GL, subledger/source-system, consolidation/FP&A, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Accountant / finance operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# GL Reconciler

## Purpose and outcome
Given a GL control account's entries and the supporting **subledger / source-system** detail
for a period, deterministically **match** the two sides, **classify** every disagreement into
a fixed break taxonomy with **lineage** to the source rows, **tie the breaks out** to the
GL-vs-subledger difference, and draft **PROPOSED** correcting journal entries. A successful
output lets an accountant see exactly why the account does not tie, hand documented reconciling
items forward, and give a reviewer a set of proposed corrections to approve and post — the
posting itself stays human/authorized.

## Use when
- "Reconcile GL account 1010 to the bank/AP/AR subledger for June."
- "Why doesn't the GL tie to the subledger? Classify the breaks."
- "Propose the correcting entries for these reconciliation differences."
- A month-end or audit workflow needs a consistent, cited, reproducible account reconciliation.

## Do not use
- You want the correction **posted / booked** to the GL → out of scope. Propose only; an
  authorized human posts in the ERP (see [references/handoffs.md](references/handoffs.md)).
- The gap is an **operating or budget variance to explain**, not a reconciliation break →
  `fpa-variance-analyzer`.
- The break is an **AP subledger exception** needing a resolution workflow →
  `accounts-payable-exception-resolver`.
- **Payment / settlement reconciliation** (cash vs settlement network, nostro/vostro) →
  `settlement-break-reconciler` or `transaction-reconciliation-helper` (Payments).
- The reconciliation is being **packaged as audit evidence** → `audit-evidence-packager` /
  `financial-statement-audit-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a reconciliation with a
durable `reconciliation_id`, a classified break list, lineage, and proposed corrections, then
stops. `month-end-close-orchestrator` may call it as a close task; downstream skills consume
its `reconciliation_id` rather than recomputing the match. It never posts and never approves
its own corrections.

## Inputs and prerequisites
- `entity`, `account`, `as_of` (period cutoff), `config_version`, `currency`.
- **GL entries** and **subledger/source entries**, each row with `entry_id`, `match_key`,
  `account`, `date`, signed `amount`, `currency`, `source_ref`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to ERP/GL and the subledger; approved reconciliation `config` (tolerances,
  materiality, suspense account) — see [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The GL and the subledger are **two
independent positions of record**; a break is a disagreement between them. The skill classifies
and evidences the break — it does not decide which side is right. Cite every break to its GL
and/or subledger source rows.

## Workflow
1. **Scope & validate** — confirm `entity`/`account`/`as_of`; load both sides for the period;
   run [scripts/validate_input.py](scripts/validate_input.py). Fail closed on structural gaps.
2. **Match & classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to group by
   `match_key`, pair rows, and classify each disagreement into the break taxonomy
   (`timing_difference`, `amount_mismatch`, `unrecorded_in_gl`, `unsupported_in_gl`,
   `duplicate`). Each break carries `gl_impact`, a `material` flag, and lineage citations.
3. **Tie out** — confirm the classified breaks fully explain the GL-vs-subledger difference
   (`residual == 0`). If they do not tie, surface the residual; never plug it.
4. **Propose corrections (PROPOSED only)** — for each correctable break, draft a balanced
   correction JE whose adjustment offsets the break; `timing_difference` items are documented
   reconciling items with **no** correction. Every correction is `status: "PROPOSED"`.
5. **Write the pack** — plain-language summary + tie-out + classified breaks with lineage +
   proposed corrections + the standing no-posting disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms tie-outs (residual zero; corrected GL agrees to subledger), the break
taxonomy and lineage, idempotency of the `reconciliation_id`, proposed-only corrections
(balanced, status `PROPOSED`, no posting-completed language), and the disclaimer. Fail closed on
any miss.

## Human approval
`external-delivery`: human review required before the reconciliation or any proposed correction
is delivered externally or written to a system of record. **Posting a correction is always a
separate, authorized human/system action** performed in the ERP under segregation of duties —
never by this skill.

## Failure handling
- **Breaks don't tie** (residual ≠ 0) → report the residual and the unmatched items; do not
  fabricate a plug or force a tie.
- **Missing `match_key`** → items cannot be matched; report them as unmatched and flag the
  data-quality gap rather than guessing a pairing.
- **Ambiguous account/entity or wrong period** → stop and confirm; never reconcile the wrong
  account.
- **Stale / conflicting sources** → cite both the GL and subledger rows; do not silently pick
  a winner.
- **Tool timeout** → return the matches/breaks computed so far with a clear "incomplete" flag;
  no assumed retry.

## Output contract
1. **Summary** — entity, account, `as_of`, GL vs subledger totals, difference, break counts by
   type, material-break count, `reconciliation_id`.
2. **Tie-out** — `difference`, `breaks_total_gl_impact`, `residual` (must be 0),
   `corrected_gl_total`, `ties_out`.
3. **Breaks** — per break: `type`, `match_key`, `gl_impact`, `material`, lineage citations, and
   either a proposed correction or a documented-reconciling-item note (timing).
4. **Proposed corrections** — balanced `PROPOSED` JEs (never posted), each offsetting its break.
5. **Machine-readable** — the full reconciliation JSON + `reconciliation_id` + `input_fingerprint`
   for downstream skills and reproducibility.
6. **Standing disclaimer** — "Reconciliation and proposed corrections only; no journal entry has
   been posted to the general ledger. Proposed corrections require human review and authorized
   posting."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records. GL reconciliation needs no customer NPI; minimize counterparty
detail to what evidences a break. Retain the reconciliation, breaks, lineage, proposed
corrections, and `config_version` per records policy; log the read and any external-delivery
approval.

## Gotchas
- **Propose, never post.** A correction is a proposal; the skill has no posting operation. The
  disclaimer and `status: "PROPOSED"` are load-bearing controls, not decoration.
- **Timing differences are documented, not corrected.** Proposing a JE for an in-transit item
  double-counts it next period — the engine deliberately emits no correction for them.
- **Don't force a tie.** If breaks don't explain the difference, the residual is the finding.
  A plug hides the real break.
- **Sign discipline.** `amount` is signed in the account's natural sign; `gl_impact` is
  GL minus subledger. A sign error breaks the tie-out — trust the deterministic engine over
  hand math.
- **Config is a versioned contract.** Tolerances, materiality, and the suspense account come
  from `config`, never tuned per-reconciliation to make a break disappear.
- **Two positions of record.** The skill never decides the GL or the subledger is "correct";
  it evidences the disagreement for a human.
