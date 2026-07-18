# Board / Committee Pack — DRAFT

> DRAFT board/committee pack assembled for human review; nothing has been sent, submitted,
> distributed, or finalized, and no decision has been approved by this skill.

**Pack ID:** `{pack_id}` · **Committee:** {committee} · **Meeting date:** {meeting_date}
**Template:** `{template_version}` · **Classification:** {classification}

The pack MUST contain every section below (the output validator enforces presence).
Each substantive line MUST carry a citation `{system}:{ref}@{as_of}` to an approved source.

---

## 1. Cover
Committee, meeting date, classification, template version, and the corporate-secretary
owner. No content claims here.

## 2. Agenda
Ordered agenda items for the meeting.

## 3. Decisions and resolutions
For each decision requiring approval, one row:

| ID | Decision | Status | Requires approval | Approver (role) | Approval status | Sources |
| -- | -------- | ------ | ----------------- | --------------- | --------------- | ------- |

- `status` is `proposed` until a **named human** approves it. This skill never sets a
  decision to `approved`/`adopted`/`resolved` — that value, with the approver, comes from a
  human and is recorded, not generated.
- Every decision requiring approval appears in the **Approvals register** (§8).

## 4. Metrics / KPI dashboard
Each metric: name, value, period, and citation. No metric without a source.

## 5. Risks
Each risk: title, rating (e.g. Red/Amber/Green), and citation to the risk register / KRI.

## 6. Issues and matters arising
Open items / actions: title, owner, due date, and citation to the action tracker or minutes.

## 7. Sources (approved-source register)
Every source used: `source_id`, system, ref, as-of date, owner. This is the citation
backbone; a claim whose `source_id` is not here is an **unsupported assertion** and blocks
the pack.

## 8. Approvals register
Every decision requiring approval, with approver role, approver identity, status
(`pending` / `obtained`), and date. Required approvals must be **recorded** here.

## 9. Page takeaways
One concise takeaway per content page (keep to a single sentence). Takeaways summarize
cited content; they add no new unsourced claims.

---

## Completeness and sourcing footer (machine-checked)
- **Completeness:** required sections present vs. missing.
- **Unsupported claims:** MUST be empty.
- **Standing note:** the DRAFT banner above MUST be present verbatim.
