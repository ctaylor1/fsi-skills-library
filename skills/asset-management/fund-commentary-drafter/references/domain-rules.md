# Domain Rules — fund-commentary-drafter

Orientation references: fund marketing-communication standards (past-performance,
fair/balanced presentation, prohibited/guarantee language), the firm's disclosure set, and
the approved messaging library. The firm's marketing-review policy and its approved
messaging/disclosure content are **versioned contracts** and take precedence.

## Tie-out rules (deterministic)

Numbers are reproduced only when they reconcile. Tolerances are configuration, not judgment.

| Tie-out | Rule | Default tolerance |
| ------- | ---- | ----------------- |
| Performance excess | `excess_return == fund_return − benchmark_return` and `reconciled == true` | 0.011 pp |
| Attribution sum | `sum(effect contributions) == total_excess` and `reconciled == true` | 0.10 pp (allows interaction/residual) |
| Cross-check | `attribution total_excess == performance excess` | 0.011 pp |

If any tie-out fails, the figure is **not** drafted — the input is returned for
reconciliation (see `validate_input.py` warnings and `validate_output.py` errors).

## Claim substantiation (the core control)

Every factual or performance statement is a **claim** with ≥1 source citation:

- **Data claims** (performance, attribution, positioning, flows, market context) cite the
  reconciled data source for the exact period.
- **Forward/thematic claims** (outlook) cite an **approved** messaging id
  (`status == "approved"`). Non-approved messaging is not a valid basis.
- A proposed free-text `draft_claim` is accepted only if **all** its `source_refs` resolve to
  a known data source or an approved messaging id; otherwise it is flagged **unsupported** and
  excluded — never asserted.
- Each claim carries the commentary `period_label`; a mismatched period is a fidelity error.

## Prohibited / misleading language (fail closed)

Screened against the claim narrative (not the approved disclosure boilerplate):

- Return **guarantees** ("guaranteed", "assured returns", "promise").
- **"risk-free"**, "cannot lose", "no risk of loss", "safe investment".
- Performance **promises** ("will outperform").

Standard disclosures (e.g. "past performance is not a guarantee of future results") live in
the disclosures block and are excluded from this screen.

## Required disclosures

`required_disclosures ⊆ disclosures_present`. The default set includes past-performance,
benchmark definition, and marketing-communication status; configure per fund/jurisdiction.

## Hard boundaries (fail closed)

- **No unsupported claim** is ever asserted.
- **No prohibited/misleading** marketing language.
- **No un-reconciled numbers** are drafted.
- **No forward/thematic text** outside the approved messaging library.
- **No sending, filing, publishing, or distributing** — draft-only; product **and**
  compliance sign-off are required before a human delivers.

## Draft package — required contents

Header (fund, share class, benchmark, currency, period, template/prior-commentary versions);
the seven required sections; the claim ledger with citations and period labels; the
performance and attribution tie-out block; the disclosures set; the product and compliance
sign-off block; the draft-only standing note.
