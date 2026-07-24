# Domain Rules — nav-preparation-tie-out

Deterministic NAV-component tie-out: how the fund book of record is matched to each
independent verifier source, how disagreements are classified into a fixed **break
taxonomy**, how the result **ties out**, and how resolutions are **proposed** (never
executed). Tolerances, materiality, the date cutoff, and the component→verifier mapping are
configuration (versioned, owned by Asset Management investment & product), not hard-coded
judgments.

## Components and pairing (deterministic)

Seven NAV components are reconciled, each against a configured verifier source:

| Component | Book of record | Verifier (default) | Unit |
| --------- | -------------- | ------------------ | ---- |
| `position` | ABOR | custodian | quantity |
| `price` | ABOR | approved pricing source | price |
| `cash` | ABOR | custodian | amount (per currency) |
| `accrual` | ABOR | administrator | amount |
| `income` | ABOR | administrator | amount |
| `expense` | ABOR | administrator | amount |
| `shares` | ABOR | administrator / transfer agent | shares |

Within a component, records are grouped by `key`; book and verifier rows on the same key are
sorted by `(as_of, line_id)` and paired positionally. For each pair (`delta = book − verifier`,
rounded to the component's precision):

- `abs(delta) <= tolerance(component)` **and** as-of dates within `date_tolerance_days`
  → **matched** (no break);
- `abs(delta) > tolerance(component)` → the component's **value break**
  (`quantity_break`, `price_break`, `cash_break`, `accrual_break`, `income_break`,
  `expense_break`, or `shares_break`), `impact = delta`;
- amounts agree but as-of dates differ beyond `date_tolerance_days` → **timing_difference**
  (documented reconciling item, `impact = 0`, no resolution).

Leftover rows on a key with no counterpart are **missing_record** (present in book, absent at
verifier → `impact = +book`; present at verifier, absent in book → `impact = −verifier`).

## Break taxonomy

| Break type | Fires when | `impact` (signed) | Proposed resolution |
| ---------- | ---------- | ----------------- | ------------------- |
| `quantity_break` | Position quantity: book vs custodian beyond tolerance | book − custodian | Investigate; propose adjustment for review (never posted) |
| `price_break` | Price: book vs approved pricing source beyond tolerance | book − pricing | **Route to `valuation-exception-packet`** — never choose a price |
| `cash_break` | Cash: book vs custodian beyond tolerance | book − custodian | Investigate; propose adjustment for review |
| `accrual_break` | Accrual: book vs administrator beyond tolerance | book − administrator | Investigate; propose adjustment for review |
| `income_break` | Income: book vs administrator beyond tolerance | book − administrator | Investigate; propose adjustment for review |
| `expense_break` | Expense: book vs administrator beyond tolerance | book − administrator | Investigate; propose adjustment for review |
| `shares_break` | Shares outstanding: book vs administrator/TA beyond tolerance | book − administrator | Investigate; propose adjustment for review |
| `missing_record` | Component on one source with no counterpart on the other | ±that side's value | Investigate the one-sided record; propose adjustment for review |
| `timing_difference` | Matched value, as-of/settlement dates differ beyond cutoff | 0 (nets next cycle) | **None** — documented reconciling item |

Each break carries a `material` flag (`abs(impact) >= materiality(component)`; timing items are
never material). `price_break` items **must** route to `valuation-exception-packet`.

## Tie-out invariants (enforced by `scripts/validate_output.py`)

Control totals are computed for the additive components grouped by currency
(`cash`, `accrual`, `income`, `expense`, `shares`). `position` and `price` are line-level only
(quantities and prices do not sum meaningfully across instruments).

1. For each `(component, currency)` control total: `difference == book_total − verifier_total`
   **and** `difference == breaks_impact_sum` (the group's breaks fully explain the difference);
   `ties_out == true`.
2. `validate_output` independently **recomputes** each `breaks_impact_sum` from the break list
   and confirms it equals the stated value — a dropped or added break fails closed.
3. Overall `residual == sum(difference − breaks_impact_sum) == 0`.
4. `out_of_tolerance_count == captured_break_count == count(non-timing breaks)`.

## Idempotency & lineage

`input_fingerprint` = SHA-256 of the normalized inputs + config. `tie_out_id` =
`npt-{fund}-{share_class|NA}-{as_of}-{fingerprint[:8]}`. It has **no timestamp or random
component**, so identical inputs reproduce an identical tie-out. Every break traces to its
book/verifier source rows via `lineage` citations.

## Hard boundaries (fail closed)

- **Never strike NAV.** The skill produces a tie-out/break packet; it does not compute,
  strike, finalize, or certify a NAV per share. No `nav_per_share` / `struck_nav` field is ever
  emitted.
- **Never choose a price.** Price disagreements are evidenced and **routed to
  `valuation-exception-packet`**; the skill does not select, override, or fair-value a price.
- **Never post an accounting entry.** Resolutions are `status: "PROPOSED"` with
  `chooses_value`, `strikes_nav`, and `posts_entry` all false. Posting is a separate,
  authorized human/system action.
- **Do not decide which source is right.** A break is a disagreement to evidence and route,
  not adjudicate.
- **Do not net or suppress breaks** to force a tie. If a control total does not tie, surface
  the residual rather than fabricating a plug.
- **Tolerances, materiality, and the component→verifier map come from the versioned config**,
  never tuned per tie-out to make a break disappear.
- **Timing differences are documented, not repaired** — they clear as the lagging source
  settles.
