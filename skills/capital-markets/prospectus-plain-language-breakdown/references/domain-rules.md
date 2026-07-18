# Domain Rules — prospectus-plain-language-breakdown

These are the rules the breakdown applies. They are **coverage and faithfulness** rules, not
advice rules — none of them produce an opinion, a recommendation, or a suitability judgment.
The deterministic screen in `scripts/validate_output.py` enforces the machine-checkable
parts (required-topic coverage, citation coverage, no-advice, disclaimer).

## Required disclosure topics (must be covered or flagged as a gap)

Every breakdown must address each topic below. If the document does not disclose a topic, the
breakdown records it in `data_gaps` — it is never invented.

| Topic key | Plain-language question it answers | Typical prospectus location |
| --------- | ---------------------------------- | --------------------------- |
| `fees` | What does it cost to buy, hold, and sell? | Fee table / "Fees and Expenses" |
| `strategy` | How does it invest, and in what? | "Principal Investment Strategies" |
| `liquidity` | How and when can I get my money out? | Redemption / "Buying and Selling Shares" |
| `conflicts` | Who benefits, and how might their interests differ from mine? | "Conflicts of Interest", adviser/affiliate disclosures |
| `risks` | What can go wrong; can I lose money? | "Principal Risks" |
| `obligations` | What am I agreeing to or required to do? | Investor eligibility, minimums, holding conditions, tax elections |

## Recommended (optional) topics — cover when the document discloses them

`tax`, `distributions`, `performance`, `management` (adviser/sub-adviser), `governance`.
These enrich the breakdown but are not required for completeness.

## Fee taxonomy (report each line as the document states it)

Report fees as **distinct lines** with page cites; do not collapse them into one number
unless the document itself states a total (e.g., "Total Annual Fund Operating Expenses").

| Fee line | What it is |
| -------- | ---------- |
| Sales load (front-end / back-end / CDSC) | Charge to buy or sell shares |
| Management / advisory fee | Paid to the adviser for managing assets |
| 12b-1 / distribution & service fee | Ongoing distribution/marketing charge |
| Other expenses | Administrative, custody, transfer-agent, etc. |
| Total annual operating expenses (expense ratio) | The document's stated total, if given |
| Fee waivers / expense reimbursements | Temporary reductions, with expiry, if disclosed |
| Redemption / exchange / account fees | Charges tied to specific transactions |

**Share classes differ.** Fees, loads, and 12b-1 charges vary by class; never blend classes
or carry one class's figure to another. Cite the class alongside the page.

## Liquidity / redemption terms to state exactly

Redemption frequency, notice period, lock-up period, gates or redemption limits, settlement
timing, and any suspension conditions — stated exactly as the document frames them, with the
page cite. Do not characterize liquidity as "good" or "limited"; state the mechanics.

## Faithfulness rules

- **Do not soften risk.** Translate principal risks without downgrading severity (e.g., keep
  "you may lose your entire investment").
- **Do not editorialize.** No "expensive", "cheap", "attractive", "low-risk", "worth it".
- **Statutory controls.** On a summary-vs-statutory conflict, cite both; the statutory
  document is controlling.
- **Past/forward statements** are reported as the document frames them, never restated as
  your own expectation or projection.

## Jurisdiction note

Default jurisdiction is **US** (SEC-registered offerings: statutory prospectus, summary
prospectus, SAI). Configure additional jurisdiction packs (e.g., EU PRIIPs KID / UCITS KIID)
per deployment; the required-topic set and fee taxonomy are mapped to the local document in
the jurisdiction pack.
