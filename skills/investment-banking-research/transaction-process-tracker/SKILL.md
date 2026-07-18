---
name: transaction-process-tracker
description: >-
  Maintain a source-linked deal-process tracker across outreach, NDA, data-room access,
  diligence, bid, approval, and deadline workstreams: record each counterparty's stage and
  status, compute overdue and due-soon reminders, apply process-control gates (executed NDA
  before access, granted access before diligence), diff a prior snapshot into an auditable
  change log, and capture recorded and outstanding approvals. Use when a deal-team analyst or
  process manager asks to update the tracker, check which NDAs or deadlines are overdue or
  due soon, see what changed since last week, or surface open items and control exceptions
  for an M&A or capital-markets process. HARD BOUNDARY: draft-only — never selects a winning
  bid, ranks or recommends counterparties, awards exclusivity, gives investment advice, sends
  outreach, executes an NDA, grants access, submits a bid, or delivers the tracker; external
  delivery and any system-of-record change require the named human owner's approval.
license: MIT
compatibility: Amazon Quick Desktop; requires deal/process-CRM, contract/NDA management (DMS/e-signature), virtual data room (VDR), governance/approvals, and entity-resolution MCP integrations (all read-only). Bundled scripts are Python stdlib-only.
metadata:
  aws-fsi-category: "Investment Banking & Research"
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
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Deal-team analyst / process manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Transaction Process Tracker

## Purpose and outcome
Keep a live M&A or capital-markets deal process organized without deciding or acting on it.
From a de-identified deal-process intake bundle (counterparties, stages, NDA / data-room /
bid status, milestones, prior snapshot, approvals), assemble a **draft, source-linked
tracker**: per-party stage and status, overdue and due-soon reminders, an auditable change
log, recorded and outstanding approvals, and an open-items list with any control exceptions.
The outcome is a review-ready status pack a deal-team analyst or process manager can act on —
the tracker organizes facts and surfaces exceptions; it never picks a winner, recommends a
counterparty, or executes a process step.

## Use when
- "Update the deal process tracker — outreach, NDA, access, diligence, bid status."
- "What NDA or milestone deadlines are overdue or due this week?"
- "What changed on the process since last week?" (auditable change log)
- "Show open items, control exceptions, and outstanding approvals for Project X."

## Do not use
- **Selecting a bid / recommending a counterparty / awarding exclusivity** → human deal-team
  decision (deal team lead / managing director). This skill never ranks or picks.
- **Valuing a target or a bid** → `lbo-model-builder`, `merger-model-builder`, `dcf-modeler`.
- **Building the counterparty universe** → `buyer-investor-list-builder`.
- **Assembling diligence / data-room content** → `due-diligence-packager`.
- **Sending outreach, executing NDAs, granting access, submitting bids, delivering** →
  legal, the data-room administrator, and the deal team (operational actions), never here.
- **Investment/legal/tax advice** → refuse; out of scope.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream, `buyer-investor-list-builder`
and `investment-banking-pitch-builder` set up the universe and mandate; downstream,
`due-diligence-packager` and the valuation model builders consume a durable `process_id` and
a bid *reference*. Bid selection, access grants, NDA execution, and delivery are human /
operational handoffs. This skill emits a draft tracker snapshot; it must not decide or act.

## Inputs and prerequisites
- The deal-process intake bundle: `process_id`, `as_of_date`, `config_version`,
  `stage_order`, `required_approvals`, `reminder_lookahead_days`; `parties[]` (id, name,
  type, engagement, stage, `nda_status`, `access_status`, optional `bid`, `milestones[]`,
  `source_ref`); `approvals[]`; and a `prior_snapshot` for the change log. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the process CRM, DMS/NDA, VDR, and governance/approvals systems. Every hard
  fact (NDA executed, access granted, bid received, approval recorded) must be cited.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The process CRM is the system of
record for process state; DMS/VDR/governance own the facts they issue (NDA execution, access
grants, approvals). Cite every party, bid, reminder, and approval. `stage_order`,
`required_approvals`, and the reminder window are a **versioned config contract**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm required fields, ISO dates,
   milestone citations, and surface data gaps (undated open milestones, missing prior
   snapshot) and control-gate warnings. Do not guess status.
2. **Assemble the tracker (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per-party stage /
   NDA / access / bid with citations; apply the process-control gates
   (`nda-not-executed`, `access-not-granted`); compute overdue and due-soon reminders against
   `as_of_date`; diff vs. the prior snapshot for the change log; capture recorded and
   outstanding approvals; compile open items and a de-duplicated source index.
3. **Surface exceptions, never resolve them** — each control breach and overdue milestone
   becomes an open item escalated to the deal team; the party is not advanced.
4. **Render the draft** — populate [assets/output-template.md](assets/output-template.md);
   stamp `tracker_status` draft-tracker; keep every hard fact cited.
5. **Never decide or act** — no bid selection, recommendation, exclusivity, send, grant,
   execute, or deliver.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen enforces: all required sections present; no unsupported claims
(every party entry and bid cited); control-gate consistency (an access-granted /
NDA-not-executed active party must carry the matching exception); required approvals recorded
and delivery approval flagged; no decision/recommendation or send/grant/deliver language;
`tracker_status` draft-tracker; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. The tracker is a **draft**: a named human owner (deal team lead /
process manager) must review and approve before it is delivered externally or any system of
record is changed. Bid selection, exclusivity, NDA execution, access grants, and approvals
are human/operational actions the skill only *records*. It proposes and organizes; humans
decide and act.

## Failure handling
- **Missing/undated data** → surface as a data gap; an open milestone with no valid
  `due_date` yields no reminder rather than a guessed one.
- **Control-gate breach** (access before executed NDA, diligence before granted access) →
  flag as a control exception, escalate, do not advance the party.
- **Conflicting sources** (CRM vs. DMS/VDR) → cite both and flag; do not silently reconcile.
- **Missing prior snapshot** → change log limited (parties shown as `added`); note it.
- **Missing required approval** → list as outstanding; block external delivery.
- **Tool timeout** → return the partial tracker with an explicit incomplete flag; assume no
  automatic retry.

## Output contract
1. **Process summary** — counts by stage, engagement, reminders (overdue / due-soon), control
   exceptions, open items, approvals recorded / outstanding.
2. **Party tracker** — per party: stage, `nda_status`, `access_status`, bid summary,
   exceptions, citation.
3. **Approvals** — recorded (type/role/approver/date/citation) and outstanding.
4. **Reminders** — overdue and due-soon milestones with citations.
5. **Change log** — diff vs. prior snapshot on stage / `nda_status` / `access_status`.
6. **Open items** — control exceptions and overdue milestones with escalation actions.
7. **Source index** — de-duplicated citations.
8. **Machine-readable** — the full manifest keyed by `process_id`, `tracker_status`
   draft-tracker.
9. **Standing note** — draft-only; nothing decided, sent, granted, or delivered.
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential — MNPI / client-confidential.** The counterparty list, bids, and deal
status are material non-public information: enforce need-to-know and any ethical wall /
wall-cross list, and mask identifiers to what the tracker requires. Retain each snapshot, its
change log, citations, and `config_version` for reproducibility; log the analyst identity and
the approver on delivery.

## Gotchas
- **Tracking ≠ deciding.** Recording that a bid was received is fine; naming a winner or
  recommending a counterparty is prohibited.
- **Status is observed, not asserted.** Never mark an NDA executed or access granted without
  a cited source; a gap is a data gap, not a default.
- **Gates surface, never self-heal.** A control exception is escalated and the party held —
  the skill does not "fix" the sequence by advancing or back-dating.
- **Reminders need dates.** Undated open milestones cannot be reminded; surface them rather
  than inventing a due date.
- **Config is versioned.** Record `config_version` and the prior-snapshot `as_of_date` so
  every reminder and change-log entry is reproducible.
- **Draft-only means draft-only.** The tracker is never the act of sending, granting, or
  delivering; those stay with humans and operations.
