# Domain Rules — board-committee-pack-builder

Orientation references: the organization's board/committee governance charter, the approved
board-pack template (a versioned contract), and the corporate-secretary drafting standard.
These, not the skill's judgment, define required sections, sourcing, and approval routing.

## Required pack sections (template fidelity)

Every pack must contain all of: **cover, agenda, decisions, metrics, risks, issues,
sources (approved-source register), approvals (register), and page takeaways**. A missing or
empty required section blocks the draft (`scripts/validate_output.py`).

## Sourcing rule (no unsupported assertions)

| Content kind | Sourcing requirement |
| ------------ | -------------------- |
| Decision / resolution | >= 1 citation to the material it rests on |
| Metric / KPI | exactly the source of the value, with its `as_of` date |
| Risk | citation to the risk register / KRI entry |
| Issue / matter arising | citation to the action tracker or prior minutes |

A `source_id` that does not resolve in the approved-source register is an **unsupported
assertion** and is listed in `unsupported_claims`; the pack cannot pass with any present.

## Approval rules (no unapproved claims)

- A decision requiring approval is **`proposed`** by default and appears in the approvals
  register with its approver role and status `pending`.
- A decision may only read **`approved` / `adopted` / `resolved` / `ratified` / `carried`**
  when a **named human approver** and status (`obtained`) are recorded on it. The skill
  never sets these itself.
- Every `requires_approval` decision must be recorded in the approvals register — omitting
  the requirement is a failure, not a convenience.

## Concise page takeaways

Each content page carries one short takeaway (target: a single sentence, <= 40 words). A
takeaway summarizes already-cited content and introduces **no new unsourced claim**;
`validate_input.py` warns when a takeaway runs long.

## Hard boundaries (fail closed)

- No **send / submit / distribute / finalize** of the pack.
- No **self-approval** of any decision or resolution.
- No **unsupported assertion** — every substantive line cites an approved source.
- No **fabricated or silently refreshed figures**; cite the source and its date.
- No **personalized investment / legal / tax advice** and no binding regulated
  determination.

## Assembled pack — required contents

`pack_id`; cover (committee, date, classification, template version); agenda; decisions with
approval routing; metrics with periods; risks with ratings; issues with owners/due dates; a
complete source register; an approvals register; page takeaways; a `source_map` tying each
claim to its citation; `completeness` (present vs. missing); `unsupported_claims` (empty);
and the standing DRAFT note.
