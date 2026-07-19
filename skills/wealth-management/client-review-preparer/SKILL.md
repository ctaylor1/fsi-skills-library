---
name: client-review-preparer
description: >-
  Assemble a wealth client-review pack from approved sources: resolve the household and its
  accounts, then draft a fully source-cited brief, meeting agenda, and deck outline covering
  goals, holdings and a portfolio summary (with per-account and household value tie-outs),
  performance, plan items, prior meeting notes, service history, life events, open actions, a
  discussion agenda, and required disclosures, from an approved template. Use when a wealth
  advisor, client-service associate, or financial planner needs to prepare an annual or periodic
  client review, a review brief or deck, or a pre-meeting household view. HARD
  BOUNDARY: NEVER makes a recommendation, suitability determination, or trade (recommendations
  route to suitability-reg-bi-reviewer and a licensed human); NEVER closes, files, or writes any
  CRM or system of record; NEVER sends or delivers the pack; gives NO investment, legal, or tax
  advice; states nothing a cited source does not support — it drafts a pack for mandatory human
  adjudication.
license: MIT
compatibility: Amazon Quick Desktop; requires wealth-CRM, portfolio-accounting/custody, performance, planning-engine, and product/disclosure MCP integrations (all read-only; drafting only — no recommendation, trade, delivery, or system-of-record write).
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Wealth advisor / client-service associate / financial planner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Client Review Preparer

## Purpose and outcome
Turn a household's approved wealth data into an audit-ready **client-review pack**: resolve the
household and its accounts, then draft a concise, **fully source-cited** brief, meeting agenda,
and deck outline covering goals, holdings and a portfolio summary (with per-account and
household value tie-outs), performance, financial-plan items, prior meeting notes, service
history, life events, open actions (with overdue flags), a discussion agenda, and the required
disclosures — from an approved template. The outcome is a review-ready pre-read (or a clear,
itemized reason it cannot be assembled yet) that a **licensed human adjudicates**, verifies,
and — if they choose — uses in the meeting. The skill never recommends, decides suitability,
trades, delivers, or writes a system of record, and states nothing a cited source does not
support.

## Use when
- "Prepare my client-review pack for the annual meeting with this household."
- "Build a review brief and agenda: goals, holdings, performance, and open actions."
- "Pull together a pre-meeting deck outline across accounts with source dates."
- "Give me a consolidated household view for the periodic review, with disclosures."

## Do not use
- **Reviewing recommendation evidence / suitability / Reg BI** → `suitability-reg-bi-reviewer`.
- **Measuring goal progress** with scenarios and cash flows → `financial-goal-progress-analyzer`.
- **Modeling retirement income / withdrawals** → `retirement-income-scenario-modeler`.
- **Drafting or refreshing the IPS** → `investment-policy-statement-builder`.
- **Comparing portfolio proposals** → `portfolio-proposal-comparator`.
- **Preparing a rebalance / trade list** (R4, authorization) → `portfolio-rebalancing-assistant`.
- **Screening senior-investor / vulnerability concerns** → `senior-investor-protection-screener`.
- **Post-meeting follow-up** (notes, actions, comms, CRM updates) → `advisor-follow-up-assistant`.
- Any request to **recommend, decide suitability, trade, deliver, write the CRM, close, file,
  or advise** → refuse; draft only and route to the skill above or a licensed human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is **pre-meeting drafting
only**. It consumes read-only context from the CRM, portfolio accounting/custody, performance,
planning engine, and disclosure library, and emits a `client_id`-keyed review pack with
`reviewer_signoff_required` and a recorded `approvals` block. Recommendation/suitability review,
goal analysis, retirement modeling, IPS drafting, proposal comparison, rebalancing/trades,
senior-investor screening, delivery, CRM writes, and post-meeting follow-up belong to the
routes above or to an authorized human. Routing flags are **surfaced**, never auto-actioned.

## Inputs and prerequisites
- The household record: `client_id`, `household_name`, `advisor`, `review_type`
  (`annual`|`semiannual`|`ad-hoc`), `entity_resolved`, `accounts` (id, type, registration,
  reported_value), a per-review **source inventory**, and the content lists — `holdings`,
  `performance`, `goals`, `plan_items`, `prior_notes`, `service_history`, `life_events`,
  `open_actions`, `discussion_questions`, and `disclosures`. Every content item cites a
  `source_id` in the inventory. Optional `flags` drive routing. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- An `as_of_date` (drives freshness and overdue-action calculations), a `freshness_days`
  threshold, a tighter `critical_freshness_days` for holdings/performance, and a
  `disclosure_config` (required disclosures per review type).
- Read access to CRM, portfolio accounting/custody, performance, planning, and the disclosure
  library. No write, trade, send, or delivery capability is used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The wealth CRM is the system of record
for household identity, advisor, notes, service, life events, and actions; portfolio
accounting/custody for accounts, reported values, and holdings; performance for returns;
planning for goals and plan items; the disclosure library for required disclosures. **Cite every
item** with `{system}:{ref}@{date}`. Nothing enters the pack without a source; the approved
template and disclosure config are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each review is structurally complete
   and every content item cites a source in the inventory; flag gaps as warnings.
2. **Assemble deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): confirm required
   inputs, confirm the entity is resolved, confirm every holding/performance/account references a
   known account, check content-to-source integrity, screen source freshness (tighter for
   holdings/performance), tie out holdings to reported account values and accounts to the
   household total, confirm required-disclosure coverage, flag overdue actions, and surface
   routing flags. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `needs-data`, `unresolved-entity`, `account-identity-gap`,
   `unsupported-content`, `stale-source`, `tieout-break`, or `disclosure-gap` blocks assembly
   with an itemized reason; only a clean record becomes `draft-review`.
4. **Draft the pack** — for a packageable review, assemble the pack from
   [assets/output-template.md](assets/output-template.md): identity, portfolio summary (tie-out),
   performance, goals, plan items, prior notes, service history, life events, open actions,
   discussion agenda, disclosures, routing, a citations index, and the recorded approvals +
   reviewer sign-off block. No statement without a cited source.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any miss (template fidelity, unsupported claims, identity, tie-out, disclosure
   coverage, recorded approvals, recommendation/decision/closure/filing/delivery/advice screen,
   standing note).
6. **Never act** — hand the draft to a licensed human, who adjudicates, and — if authorized —
   uses or delivers it and performs any recommendation, suitability decision, trade, CRM write,
   or delivery.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: template
fidelity (required sections, no unfilled placeholders); a packageable record is entity-resolved
and fully source-cited; client/account identity present; holdings tie out per account and to the
household total; required disclosures present; approvals recorded (`reviewer_signoff_required` +
`approvals`); no recommendation/suitability/trade, no decision/closure/filing/CRM-write, no
send/deliver, and no investment/legal/tax advice language; standing note present. See
[references/controls.md](references/controls.md). Correct and re-run until it passes or the
record is flagged not-packageable.

## Human approval
`required`. A licensed human must adjudicate before the pack is used in a client meeting, before
any recommendation or suitability decision, and before any delivery or CRM write; where a
recommendation is contemplated, suitability/Reg BI review is required and recorded in the
approvals block. This skill proposes and drafts; it never recommends, decides, trades, delivers,
writes, closes, files, or advises. Internal drafting may be reviewer-sampled per
[references/controls.md](references/controls.md).

## Failure handling
- **Missing required input** (no advisor, accounts, or goals) → `needs-data`; list exactly what
  is missing; do not invent a household, account, or goal.
- **Unresolved entity** → `unresolved-entity`; a human confirms the household; never guess
  identity.
- **Unknown account reference** (holding/performance/account) → `account-identity-gap`; resolve
  the account; never attach a position to a guessed account.
- **Content cites an unknown source** → `unsupported-content`; drop or substantiate the item;
  never fabricate a holding, return, note, or disclosure to fill the pack.
- **Stale critical source** (holdings/performance older than `critical_freshness_days`,
  unacknowledged) → `stale-source`; refresh or acknowledge; never present stale positions as
  current.
- **Tie-out break** (holdings ≠ reported value, or accounts ≠ household total) → `tieout-break`;
  reconcile at source; values are reported, never projected.
- **Missing required disclosure** → `disclosure-gap`; obtain the disclosure; a review is not
  packageable without its required disclosures.
- **Tool timeout / partial context** → return partial output with an explicit incomplete flag
  and the sources used; no retry assumption.

## Output contract
1. **Review queue** — per review: `client_id`, household, `review_type`, status, `packageable`,
   and a one-line reason.
2. **Review pack** (per packageable review) — identity, portfolio summary (tie-out), performance,
   goals, plan items, prior notes, service history, life events, open actions (overdue flags),
   discussion agenda, disclosures, routing flags, a citations list, `reviewer_signoff_required:
   true`, and a recorded `approvals` block, following
   [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable review with its itemized reason(s).
4. **Machine-readable** — the review records keyed by `client_id` with `as_of_date` and
   `config_version`.
5. **Standing note** — "Client-review preparation draft for internal advisor use only; this
   skill does not make or communicate any investment recommendation, suitability decision, trade,
   closure, or filing, does not send, submit, or deliver the pack, and does not write any CRM or
   system of record; it gives no investment, legal, or tax advice; every item must be verified
   against its cited source and adjudicated by a licensed human before use."

## Privacy and records
**Highly Confidential (customer NPI/PII).** Include only the relationship context the review
needs (data minimization); do not pull unrelated customer data into a pack, and do not elevate
restricted content into a wider-distribution deck. Retain the draft pack, the `as_of_date`,
template/config version, and source citations with the client record; log every read and every
pack produced with the preparer identity. Delivery and any CRM write are human actions outside
this skill.

## Gotchas
- **Preparing ≠ recommending.** The pack surfaces sourced discussion points and options-to-
  consider; it never recommends, decides suitability, trades, or advises. A contemplated change
  routes to `suitability-reg-bi-reviewer` and a licensed human.
- **Preparing ≠ delivering or filing.** Never emit "pack sent / CRM updated / review filed /
  marked complete" language or imply anything was delivered, written, closed, or filed.
- **Every line needs a source.** A confident figure with no citation is an unsupported claim and
  is stripped by the output screen — no holding, return, goal, note, event, action, or
  disclosure without a `source_id`.
- **Holdings tie out.** Per-account holdings must equal the reported value and accounts must sum
  to the household total; a mismatch fails closed. Values are reported, not projected.
- **Critical freshness is tighter.** Holdings/performance sources go stale in
  `critical_freshness_days` (default 7); a stale critical source blocks unless acknowledged.
- **Disclosures are coverage, not decoration.** A review is not packageable until every required
  disclosure for its review type is present and cited.
- **Life events and drift are flags, not verdicts.** Surface and route them; never conclude a
  goal, suitability, or trade outcome here.
