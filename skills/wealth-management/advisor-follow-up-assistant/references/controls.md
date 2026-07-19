# Controls — advisor-follow-up-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft package for human adjudication, never an action.
- **Human approval:** `required` — the advisor owns the content and the recommendation; a
  supervisory principal owns the communication and supervision sign-off (FINRA Rule 2210 / 3110).
  This skill records those approvals as `pending`; it does not grant, simulate, or bypass them.

## Prohibited (fail closed)

- **Sending / delivering** the client communication — any "sent," "emailed," "delivered to the
  client," "message has been sent" language. The draft is never sent.
- **Writing the CRM or any system of record** — CRM changes are *proposed* only; any "CRM updated,"
  "record updated," "written to the system of record," "posted to the account" language is rejected.
- **Trading / staging** — any order, trade list, or execution language ("order placed," "rebalance
  executed," "funds transferred"). Trading is `portfolio-rebalancing-assistant` (R4, approval-gated).
- **Suitability / Reg BI determination** — any statement that a recommendation is "suitable,"
  "approved," or a "best-interest determination made." Recommendations route to
  `suitability-reg-bi-reviewer` plus a human supervisor.
- **Guarantees / performance promises** — "guaranteed return," "risk-free," "will outperform,"
  "no downside."
- **Fabrication** — inventing discussion points, action items, disclosures, or citations the sources
  do not support; completing an action item that lacks an owner or due date by guessing.
- **Advice beyond documented inputs** — personalized investment/tax/legal advice.

## Draft states (this skill may set only these)

`draft-ready` (all 7 sections present, cited, complete; disclosures cover every flagged
recommendation; approvals `pending`) | `needs-data` (missing/uncited material input, incomplete
action item, or missing required disclosure). It may **not** set `approved`, `suitable`, `final`,
`sent`, `delivered`, or `written`. `draft_status` is always `draft`, `delivery_status` always
`not-delivered`, and `crm_write_status` always `not-written`.

## Required output screens (`scripts/validate_output.py`)

- All 7 required template sections present and titled (template fidelity).
- Every material section carries a citation (no unsupported assertions).
- Every recommendation flagged `requires_disclosure` is covered by a disclosure; every recommendation
  flagged `requires_suitability_review` records a route to `suitability-reg-bi-reviewer`.
- Every action item carries an owner, a due date, and a citation.
- Approval block present with Advisor and Supervisory Principal each `pending`.
- `draft_status == "draft"`, `delivery_status == "not-delivered"`, `crm_write_status == "not-written"`.
- No prohibited language (execution-as-done, sent/delivered-as-done, CRM-write-as-done,
  guarantee/performance, suitability/advice-as-done) — see [domain-rules.md](domain-rules.md).
- Standing note present.

## Segregation of duties

Drafting (this skill) is distinct from suitability review, supervisory approval, sending the
communication, writing the CRM, scheduling, and trading. The same person/skill must not both draft
the follow-up and approve its suitability, send it, or execute the resulting trades. Downstream
skills and human roles hold those entitlements.

## Data classification, privacy, records

- **Highly Confidential — customer NPI/PII.** Mask client/account identifiers to what the draft
  requires; keep NPI out of identifiers and logs.
- Retain the draft, source map, gaps list, and template/disclosures versions per firm
  books-and-records (SEC/FINRA recordkeeping, including communications-with-the-public retention).
  Log author identity on every read and draft generation.
- Escalate senior-investor or diminished-capacity concerns to `senior-investor-protection-screener`
  rather than resolving them here.
