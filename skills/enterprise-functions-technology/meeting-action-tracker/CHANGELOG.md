# Changelog — meeting-action-tracker

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Turns a meeting record
into a controlled, review-ready action package — separated from narrative minutes, polished
stakeholder comms, and any actual tracker/message/calendar change (distinct entitlements and
systems of record).

- **Scope:** extract decisions, action items (owner + due date), dependencies, open questions,
  and risks; resolve owners against the roster; normalize due dates; resolve dependencies;
  detect possible duplicates against an existing task list (read-only); and draft a recap plus
  per-owner reminders from an approved template. Draft-only; no system-of-record change.
- **Controls:** R1; never creates/assigns/closes tasks, never sends messages, never schedules
  invites, never writes any system of record, never fabricates an owner or due date, and never
  asserts an item the meeting record does not support; every item is cited to a `segment_id`;
  the recap/reminder template is a versioned contract (`template_version`).
- **Scripts:** `validate_input` (meeting/item schema, unsupported/needs-confirmation/blocked
  warnings), register builder (citation requirement + owner resolution + due normalization +
  dependency/cycle resolution + duplicate detection + status precedence + draft comms),
  `validate_output` (citation/traceability, ready-discipline, committed-set integrity, draft-
  comms delivery/approval, silent system-change and advice language screen, standing note).
- **Assets:** `assets/output-template.md` action-package template with a decision log, action
  register, open questions/risks, follow-ups, draft recap/reminders, and a reviewer sign-off
  block with the standing disclaimer.
- **Evaluations:** trigger/routing, golden 8-item meeting exercising every status (ready,
  needs-confirmation, blocked, unsupported, possible-duplicate), deterministic script checks, a
  non-compliant-package safety fixture that trips the R1 guardrail (uncited "ready" items,
  sent/unapproved draft comms, system-change and advice language, missing disclaimer), and
  no-send / no-fabrication / no-tracker-write refusals.
- **Handoffs:** upstream meeting transcript/recording, roster, project-tracking (read-only),
  templates; adjacent `meeting-minutes-summarizer`, `stakeholder-update-composer`,
  `project-tracker-updater` (approval-gated, human).

### Pending before release
- Enterprise-functions control-owner review; confirm the recap/reminder template owner,
  version, and effective dates.
- Confirm item-extraction conventions (owner resolution, due-date phrasing, dependency syntax)
  with the meeting-operations owner and jurisdiction/data-classification packs.
- Wire read-only MCP integrations (transcript/recording, roster/calendar, project-tracking,
  templates) at deployment; task creation, messaging, and calendar changes remain human actions
  outside this skill.
