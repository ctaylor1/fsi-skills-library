# Changelog — enterprise-meeting-preparer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Assembles an internal
meeting brief (prep pack) as a controlled, review-ready draft — separated from post-meeting
summarization, distribution/sending, contract review, external research, and task writes
(distinct entitlements and systems of record).

- **Scope:** pull the calendar event, attendees and roles, agenda, background documents and
  contracts, prior decisions, open risks, and outstanding action items, then draft a concise,
  fully source-cited brief from an approved template. Draft-only; no system-of-record change.
- **Controls:** R1; never schedules/sends/distributes/updates anything, never makes/approves/
  authorizes a decision or commitment, never gives investment/legal/tax advice, never states
  anything a cited source does not support; source freshness is screened against a
  `freshness_days` threshold with an explicit acknowledgment path; Confidential data
  minimization.
- **Scripts:** `validate_input` (meeting-intake schema, needs-data / unresolved-attendee /
  unsupported-content warnings), assembly engine (attendee resolution + content-to-source
  integrity + freshness screen + overdue-action flag + template render → status),
  `validate_output` (template fidelity, packageable invariants, scheduling/decision/advice
  language screen, standing disclaimer).
- **Assets:** `assets/output-template.md` meeting-brief template with a citations index,
  reviewer sign-off block, and standing disclaimer.
- **Evaluations:** trigger/routing, golden 6-meeting queue exercising every status,
  deterministic script checks, a non-compliant-brief safety fixture that trips the R1
  guardrail (unsupported content, scheduling/decision/advice language, missing disclaimer),
  and no-send / no-decision-or-advice / no-fabrication refusals plus a distribution
  authorization refusal.
- **Handoffs:** upstream calendar/email, files/contracts, knowledge base, project tracking;
  adjacent `meeting-action-tracker`, `contract-obligation-extractor`,
  `stakeholder-account-researcher`, `task-tracker-updater`; the follow-up/distribution email
  and scheduling are authorized-human actions (no separate skill).

### Pending before release
- Enterprise Functions & Technology owner review; confirm the approved brief template owner,
  version, section order, and the freshness/acknowledgment policy.
- Confirm source classifications and data-minimization rules for pre-read distribution.
- Wire read-only MCP integrations (calendar/email, files/contracts, knowledge base, project
  tracker, templates) at deployment; scheduling, sending, distribution, and task/calendar
  writes remain human actions outside this skill.
