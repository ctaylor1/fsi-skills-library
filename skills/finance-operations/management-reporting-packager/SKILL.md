---
name: management-reporting-packager
description: >-
  Assemble a controlled, source-cited management report package from approved finance inputs:
  compute actual-to-budget and actual-to-prior KPI variances, attach cited driver commentary,
  summarize subledger-to-GL reconciliation tie-outs, build source lineage, flag exceptions and
  data gaps, record the required preparer/reviewer approvals, and write executive takeaways — as
  a DRAFT for human review. Use when a controller, FP&A, or business-finance user says "assemble
  / draft the monthly management or board finance pack", "package these KPIs and variance
  commentary", or needs a review-ready pack with citations and reconciliation tie-outs. This
  skill NEVER delivers, submits, distributes, emails, or posts the pack, NEVER marks a figure
  final / board-approved or records the delivery approval, and NEVER includes an unsupported
  claim, an unreconciled break, or forward-looking guarantees / investment advice — delivery,
  posting, and sign-off are human / operations actions.
license: MIT
compatibility: Amazon Quick Desktop; requires consolidation/ERP-GL, subledger, FP&A, regulatory-reporting, controlled-template library, and approval-broker MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Controller / FP&A / business finance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Management Reporting Packager

## Purpose and outcome
Take approved finance inputs — KPI figures with baselines, driver commentary, subledger-to-GL
reconciliations, exceptions, and sign-off records — and assemble a **controlled DRAFT
management report package** against the approved template: computed variances, cited
commentary, tie-out summary, source lineage, exception flags, recorded approvals, and
executive takeaways. The outcome is a review-ready, fully cited pack a controller/FP&A owner
can review and route for delivery. Every figure and claim traces to a source; delivery,
posting, and final sign-off remain human.

## Use when
- "Assemble / draft the monthly management (or board) finance pack."
- "Package these KPIs and variance commentary into a controlled report with citations."
- "Build the exec pack from the close outputs, with reconciliation tie-outs and exception flags."
- "Put together the review-ready management report with source lineage and takeaways."

## Do not use
- The user wants to **send, email, submit, distribute, or post** the pack (to the board, a
  committee, a regulator, or the GL) → out of scope; draft-only. Delivery/posting is a
  human/operations action after approval.
- **Explaining** an actual-to-budget/forecast variance by driver (not just packaging a cited
  result) → `fpa-variance-analyzer`.
- **Reconciling** a subledger to the GL or proposing journal corrections for a break →
  `gl-reconciler`.
- **Certifying the close** or posting sign-offs/journals (a gated write) →
  `month-end-close-orchestrator`.
- An **audit evidence bundle** with chain of custody → `audit-evidence-packager`; forming an
  audit **opinion** → `financial-statement-audit-assistant`.
- **Personalized investment advice**, a price target, or a forward-looking guarantee → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill packages the **cited results**
of upstream analysis and emits a durable `package_id`; it never re-derives a variance, re-runs
a reconciliation, certifies the close, or delivers the pack. Missing or uncited inputs route
back upstream rather than being invented.

## Inputs and prerequisites
- The **period, entity/scope, and config version**; the **KPIs** (id, name, value, unit,
  `source_ref`, plus budget/prior baselines and cited commentary); the **reconciliations**
  (ledger vs subledger balances, tolerance, source); **exceptions**; and the **approval**
  records (preparer, reviewer; delivery stays pending). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to consolidation/ERP-GL, subledgers, FP&A, the controlled template library, and
  the versioned reporting config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). GL/consolidation is authoritative for
a KPI value; the subledger for its tie-out; FP&A for baselines and driver commentary. The
report template and reporting config are **versioned contracts**. Cite every figure, commentary
line, reconciliation, and exception; when a reported value and its subledger conflict, record
both and flag the break — never pick one.

## Workflow
1. **Validate & scope** — confirm entity/period/cut-off; run `validate_input`; note any data
   gaps (missing baselines, uncited commentary, missing reconciliations/approvals) that will
   block the pack.
2. **Assemble (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes vs-budget
   and vs-prior variances, tags each KPI `supported`/`unsupported` from its citations, evaluates
   each reconciliation tie-out against tolerance, aggregates exceptions, records approvals, and
   computes `package_status` from explicit blocking reasons. `delivery_status` is always `draft`.
3. **Render to template** — populate all eight sections of
   [assets/output-template.md](assets/output-template.md) from the assembled package, keeping
   every figure and claim tied to its citation.
4. **Executive takeaways** — write 3–6 cited, factual takeaways (no guarantees, no advice);
   surface exceptions and any unresolved break plainly.
5. **Block or ready** — if any unsupported claim, break, or missing approval remains, the pack
   is `blocked`: list the blocking reasons and route to the relevant upstream skill/human. Only
   an all-clear pack is `ready-for-review`.
6. **Never deliver** — stop at a draft; delivery, posting, and delivery sign-off are human.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all eight template sections present; `delivery_status: draft` with no
send/submit/post language; every KPI cited and no `unsupported` KPI in a `ready-for-review` pack;
`package_status` consistent with unsupported claims/breaks/missing approvals; preparer + reviewer
recorded and delivery not recorded; no final-approval or forward-looking/advice language; standing
note present. Fail closed on any miss.

## Human approval
`external-delivery`. Human approval is required before the pack is delivered externally or posted
to any system of record; the reviewer's own read needs none. Preparer and reviewer sign-offs are
**recorded from source**; the **delivery** approval is a human/operations action this skill never
performs or records. The skill drafts and packages; humans deliver.

## Failure handling
- **Uncited figure or commentary** → mark the KPI `unsupported`; block the pack; do not
  paraphrase a number the sources do not contain.
- **Reconciliation break beyond tolerance** → record it as unresolved, block the pack, route to
  `gl-reconciler`; never net or explain it away.
- **Missing baseline** (no budget/prior) → report variance `not-computable`; still require a
  citation for the figure.
- **Missing required approval** → block; do not record it yourself.
- **Mixed close cut-offs / stale plan version** → treat as a data gap and block; do not blend.
- **Tool timeout** → return the partial pack with an explicit `blocked` / incomplete flag; no
  retry assumption.

## Output contract
1. **Package header** — `package_id`, entity, period, `config_version`, `package_status`,
   `delivery_status: draft`.
2. **Rendered pack** — the eight template sections (cover/scope, executive takeaways, KPI
   scorecard & commentary, reconciliation & tie-out, source lineage, exceptions & data gaps,
   approvals & sign-off, standing note), each cited.
3. **Blocking reasons** — for a `blocked` pack, the explicit list and the route for each.
4. **Machine-readable** — the assembled package JSON keyed by `package_id`.
5. **Standing note** — "DRAFT management report package for human review only. No pack has been
   delivered, submitted, distributed, or posted to a system of record, and no figure has been
   approved as final."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential financial records** — may include pre-release, price-sensitive results. Minimize
data to what the report requires; mask individual approver identities. Retain the assembled
package, its citations, and the `config_version` per records policy; log the read and any
external-delivery approval obtained downstream. Treat the draft as need-to-know until human
delivery occurs outside this skill.

## Gotchas
- **A draft is not a delivery.** The pack is assembled for review; sending, posting, or filing
  it is a separate human/operations action this skill never performs.
- **Commentary is a claim.** A cited figure with uncited narrative is still `unsupported` — the
  narrative needs its own `commentary_source_ref`.
- **A break blocks; it is not explained away.** An out-of-tolerance reconciliation is recorded
  as unresolved and routed, never netted or narrated into a tie.
- **No forward-looking guarantees, no advice.** Report cited facts and variances; never "will
  beat budget", "guaranteed", or "a buy".
- **Delivery approval stays pending.** Preparer/reviewer are recorded from source; recording the
  delivery sign-off here is a control breach.
- **Config is a versioned contract.** Tolerances, required approvals, and KPI definitions come
  from the approved `config_version` stamped on the pack — not from what would make it pass.
