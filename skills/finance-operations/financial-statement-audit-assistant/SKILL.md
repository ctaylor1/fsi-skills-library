---
name: financial-statement-audit-assistant
description: >-
  Draft and package financial-statement audit support working papers: map financial-statement
  captions to the trial balance and tie them out, build documented monetary-unit sampling
  plans, record testing results and exceptions, accumulate misstatements against materiality,
  and track open items — every tie-out, selection, and finding cited, and required approvals
  recorded. Use when an internal or external auditor needs to plan testing, foot and tie a
  caption to the GL/subledgers, select a sample, document evidence, or assemble an audit
  working-paper draft for engagement-team review. HARD BOUNDARY: this skill NEVER forms or
  expresses an audit opinion, concludes on fair presentation, materiality sufficiency, or
  going concern, opines on ICFR/SOX, signs off on behalf of a human, or delivers, files, or
  submits anything. It produces a draft only; the opinion and any external delivery require
  the engagement partner.
license: MIT
compatibility: Amazon Quick Desktop; requires ERP/GL (trial balance), subledger, consolidation/financial-statement, FP&A, regulatory-reporting, and document/spreadsheet MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Internal or external audit / finance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Financial Statement Audit Assistant

## Purpose and outcome
Assemble a controlled **audit support working paper** from approved inputs: tie each
financial-statement caption to the trial balance, build a documented sample, record testing
results and exceptions, accumulate misstatements against materiality, and list open items —
with a citation on every tie-out, selection, and finding. The outcome is an audit-ready
**draft** the engagement team can review and the partner can approve; the audit **opinion**,
any conclusion, and any external delivery remain human decisions this skill never makes.

## Use when
- "Foot and tie this financial-statement caption to the trial balance / GL."
- "Build a sample for AR existence / revenue testing from this population."
- "Document my test results and track the exceptions as findings."
- "Accumulate the misstatements we found and show them against materiality."
- "Draft the working paper / testing memo for engagement-team review."

## Do not use
- **Forming or expressing an audit opinion**, or concluding the statements "present fairly"
  / are "free from material misstatement" → engagement partner / licensed auditor (human).
- **Going-concern** or **materiality-sufficiency** conclusions → the engagement team (human).
- **ICFR / SOX** control-effectiveness opinions → the controls-testing lead.
- **GL-to-subledger reconciliation** → `gl-reconciler`.
- **Substantive analytical / variance investigation** → `fpa-variance-analyzer`.
- **Fair-value / estimate testing** → `valuation-reviewer`.
- **Assembling the redacted evidence file with chain of custody** → `audit-evidence-packager`.
- Any request to **deliver, file, submit, or issue** the paper as final → refuse; route to the
  partner-approved delivery step.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill drafts support working
papers; it consumes reconciled balances and normalized captions upstream and hands cited
evidence to evidence-packaging, analytics, valuation, and reporting skills. Forming the
opinion and approving delivery are **human** roles with no downstream skill.

## Inputs and prerequisites
- A de-identified audit request: `engagement` (entity, period, framework, currency),
  `planning` (overall/performance materiality, clearly-trivial threshold, tolerable
  misstatement, reliability factor, sample seed), `financial_statements` (captions with
  `tb_accounts` and `fs_amount`), `trial_balance`, an optional sampling `population`, any
  `known_misstatements`, and the `approvals` block. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to ERP/GL, subledgers, the consolidation/FS package, FP&A comparatives, and
  client-provided support documents.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **ERP/GL trial balance** is the
tie-out base; the financial-statement package is tested against it. Cite every item as
`{system}:{ref}@{period/version}`. Planning parameters are a **versioned contract** recorded
on the working paper.

## Workflow
1. **Validate** — run `validate_input`; resolve or flag data gaps (unmapped accounts,
   missing population, invalid parameters) as *needs-data*; never guess to make a caption tie.
2. **Tie out (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): sum mapped
   trial-balance accounts per caption, compute the difference, and classify **tie /
   difference / unmapped** against the clearly-trivial threshold. Each tie-out is cited.
3. **Sample (deterministic)** — monetary-unit sampling: interval =
   `tolerable_misstatement / reliability_factor`; 100%-examine key items ≥ interval; make a
   systematic residual selection from a fixed seed; report examined coverage. Or record "not
   performed" with the reason.
4. **Record testing & findings** — each tie-out difference and each carried exception becomes
   a **cited** finding marked *open for auditor evaluation* — evidence, not a conclusion.
5. **Accumulate misstatements** — aggregate factual + projected misstatements above the
   clearly-trivial threshold and present them **against** overall materiality *for auditor
   evaluation only*.
6. **Assemble the draft** — populate the eight sections of
   [assets/output-template.md](assets/output-template.md), carry through recorded approvals,
   and stamp the standing note. Never form an opinion, deliver, or file.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen enforces: all eight template sections present; every tie-out and
finding cited (no unsupported assertion); tie-out arithmetic and status consistent with the
threshold; **no** audit-opinion / assurance / fair-presentation / going-concern language;
**no** deliver/file/submit language (draft-only); `Preparer` and `Reviewer` approvals
recorded; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. Preparer and engagement-reviewer sign-off are **recorded** on the draft;
**partner approval is required before any reliance or external delivery** (issuing to the
client, the file of record, a regulator, or a group/component auditor). The audit **opinion**
and every conclusion are human judgments this skill never makes. This skill drafts and
packages; humans review, conclude, approve, and deliver.

## Failure handling
- **Unmapped accounts / missing support** → status `unmapped`; add an open item; do not force
  a tie.
- **No eligible population or invalid parameters** → sampling `not-performed` with the reason;
  never invent a selection.
- **FS vs. GL vs. filed-return conflict** → cite each figure; raise an open item; route the
  data-quality question to `regulatory-reporting-data-validator`.
- **Aggregate misstatement at/above materiality** → flag `at-or-above-overall-materiality`
  for auditor evaluation; do **not** conclude.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no
  retry and no step-up authorization.

## Output contract
1. **Working-paper draft** — the eight sections of `assets/output-template.md`
   (engagement/scope, planning/materiality, source mapping & tie-outs, sampling approach,
   testing results, misstatement summary, open items, approvals).
2. **Tie-out table** — per caption: fs_amount, tb_sum, difference, status, citations.
3. **Sampling record** — interval, reliability factor, random start, key items, selections,
   examined coverage (or "not performed").
4. **Findings** — each cited and *open for auditor evaluation*.
5. **Misstatement summary** — aggregate vs. overall materiality, *for auditor evaluation only*.
6. **Approvals block** — preparer + reviewer recorded; partner required before delivery.
7. **Machine-readable** — the full working-paper JSON keyed to the engagement.
8. **Standing note** — "Draft audit working papers only. No audit opinion is expressed or
   implied; no conclusion on fair presentation, materiality, or going concern has been
   reached. Requires engagement-team review and partner approval before any reliance or
   external delivery."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential (financial records).** Restrict to the engagement team and minimize any
customer/employee identifiers pulled into support. Retain the draft, cited sources, and the
**planning-parameter version** per the firm's audit-documentation retention policy; log
preparer identity and every source read. The audit file of record is maintained by the
engagement's system, not by this skill.

## Gotchas
- **Draft ≠ opinion.** A complete, tidy working paper is still evidence for a human to
  evaluate — it never becomes a conclusion here.
- **Cite or it fails.** An uncited tie-out or finding is an unsupported assertion and fails
  `validate_output`. Pull the source ref when you pull the number.
- **Materiality is an input, not a verdict.** Showing aggregate misstatement against
  materiality is a comparison for the auditor; it does not decide sufficiency.
- **Sampling parameters are versioned.** Record the reliability factor, interval, and seed so
  the selection reproduces exactly.
- **A tidy tie-out can still be "unmapped".** A missing account mapping is needs-data, not a
  zero difference — never guess the mapping to make it tie.
- **Recorded ≠ manufactured.** Approvals are carried from human sign-off; this skill never
  fabricates a preparer/reviewer/partner approval.
