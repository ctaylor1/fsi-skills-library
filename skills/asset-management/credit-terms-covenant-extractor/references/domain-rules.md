# Domain Rules — credit-terms-covenant-extractor

How raw credit-document candidates are **normalized** into canonical fields with citations.
Every rule is deterministic and versioned in the controlled content library; the scripts
apply them without interpreting a term's legal effect. Orientation references: the governing
document's own defined terms take precedence, then the firm's credit-research data standard.
Nothing here computes a covenant test or determines compliance.

## Canonical fields

| Field | Canonical shape | Normalization rule |
| ----- | --------------- | ------------------ |
| `maturity` | `{maturity_date: ISO-8601}` | Parse `Month DD, YYYY` / `DD Month YYYY` / `YYYY-MM-DD` / `MM/DD/YYYY` to ISO. Unparseable → `needs_review`. |
| `coupon` | `{type, frequency, rate_pct}` or `{type: floating, index, spread_bps}` | Fixed if a `%` rate and no index; floating if `SOFR/LIBOR/EURIBOR/prime/base rate` or `+ N bps`. Frequency from semi-annual/quarterly/annual/monthly. |
| `seniority` | `{seniority, rank}` | Map to ranked ladder: senior_secured (1), senior_unsecured (2), senior_subordinated (3), subordinated (4), junior_subordinated (5). Off-ladder → `needs_review`. |
| `collateral` | `{secured, lien_priority, description}` | `secured` if lien/secured/collateral/pledge/charge; `lien_priority` first/second when stated. |
| `call_provision` | `{make_whole, non_call_until, callable, raw}` | Capture booleans and the first stated non-call date factually. No make-whole valuation, no yield/price math. |
| `covenant` | `{covenant_type, threshold_value, threshold_unit, raw}` | Classify incurrence vs maintenance by structural keywords; capture a stated `Nx` threshold **descriptively**. Never evaluate the test. |
| `basket` | `{basket_type, cap_floor_usd, raw}` | Classify general_debt/builder/restricted_payments/other; capture a stated dollar cap. Grower/ratio/defined-term baskets → `needs_review`. |

Fields are **independent**; each is reported with its own status, value, and citation. There
is no composite score and no derived judgment about the credit.

## Statuses

| Status | Meaning |
| ------ | ------- |
| `extracted` | Normalized deterministically from unambiguous source text, with a page-level citation. |
| `needs_review` | Ambiguous, off-ladder, unparseable, or conflicting — surfaced for human reading, **no** definitive value emitted. |
| `not_found` | An expected field had no candidate in the document. |

## Ambiguity markers (route to `needs_review`, never resolve)

`subject to`, `as defined`, `to be determined`, `TBD`, `to be agreed`, `[•]`/`[●]`,
`intentionally omitted`, `unless otherwise`, `as the context requires`, `at the issuer's
discretion`. Any candidate whose source text contains a marker is `needs_review`. Two
conflicting candidates for a single-value field (`maturity`, `coupon`, `seniority`,
`collateral`) are both flagged `needs_review` — the extractor never picks a winner.

## Hard boundaries (fail closed)

- Never determine, state, or imply **covenant compliance**, a **test result**, **headroom**,
  or an **event of default** — capture the mechanic and threshold as raw text and route the
  test to `covenant-compliance-monitor`.
- Never **interpret ambiguous language** or resolve a defined-term cross-reference — flag
  `needs_review`.
- Never give an **investment view** (buy/sell/hold, over/underweight, rating).
- Never **monitor** an issuer over time — route to `credit-surveillance-packet`.
- Never emit a term **without a page-level citation**.

## Versioning & durable IDs

- `doc_version` (draft/execution/filed) and `effective_date` are recorded; drafts flag all
  fields `needs_review` (terms not fixed). Amendments supersede base terms — extract fresh.
- The normalization rule set is versioned; `extraction_id = ctce-{doc_id}-{effective_date}
  -NNNN` binds the output to the exact document and rules for reproducibility.
