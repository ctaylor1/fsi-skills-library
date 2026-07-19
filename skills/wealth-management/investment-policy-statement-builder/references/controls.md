# Controls — investment-policy-statement-builder

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft artifact for human adjudication, never an action.
- **Human approval:** `required` — for the recommendation itself (advisor), the suitability/Reg BI
  and supervision sign-off (compliance/supervisor), and client acceptance (signature). This skill
  records those approvals as `pending`; it does not grant, simulate, or bypass them.

## Prohibited (fail closed)

- **Suitability / Reg BI determination** or any statement that an allocation is "suitable,"
  "approved," or a "best-interest determination made."
- **Trading / staging** — any order, trade list, or execution language.
- **Delivery / filing / finalization / signature** — "sent," "submitted," "filed," "delivered,"
  "final and binding," "signed and executed."
- **Guarantees / performance promises** — "guaranteed return," "risk-free," "will outperform."
- **Fabrication** — inventing objectives, tax positions, allocations, or citations the sources do
  not support; re-weighting an inconsistent allocation to "make it sum."
- **Advice beyond documented inputs** — personalized investment/tax/legal advice.

## Draft states (this skill may set only these)

`draft-ready` (all required sections present, cited, consistent; approvals `pending`) |
`needs-data` (missing/uncited material input). It may **not** set `approved`, `suitable`, `final`,
`delivered`, `filed`, `signed`, or `executed`. `draft_status` is always `draft` and
`delivery_status` is always `not-delivered`.

## Required output screens (`scripts/validate_output.py`)

- All 13 required template sections present (template fidelity).
- Every allocation line and material figure carries a citation (no unsupported assertions).
- Allocation targets sum to 100% (± 0.1) and each target sits within its min/max band.
- Overall risk tolerance equals the most conservative of ability/willingness/capacity.
- Approval block present with advisor, compliance, and client each `pending`.
- `draft_status == "draft"` and `delivery_status == "not-delivered"`.
- No prohibited language (approval-as-done, trade/execution, filing/delivery/finalization,
  guarantee/performance) — see [domain-rules.md](domain-rules.md).
- Standing note present.

## Segregation of duties

Drafting (this skill) is distinct from suitability review, supervisory approval, trading, and client
delivery. The same person/skill must not both draft the IPS and approve its suitability or execute
the resulting trades. Downstream skills and human roles hold those entitlements.

## Data classification, privacy, records

- **Highly Confidential — customer NPI/PII.** Mask client/account identifiers to what the draft
  requires; keep NPI out of identifiers and logs.
- Retain the draft, source map, gaps list, and template/tax-assumption versions per firm
  books-and-records (SEC/FINRA recordkeeping). Log author identity on every read and draft
  generation. Escalate senior-investor or diminished-capacity concerns to
  `senior-investor-protection-screener` rather than resolving them here.
