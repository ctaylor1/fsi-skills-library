# Domain Rules — financial-statement-audit-assistant

Orientation references: risk-based financial-statement audit practice (planning, materiality,
sampling, misstatement accumulation and evaluation). The firm's audit methodology and its
**versioned planning parameters** take precedence and are the authoritative contract. This
skill mechanizes documented, explainable steps; it does **not** exercise auditor judgment or
reach conclusions.

## Tie-out / footing (deterministic)

For each financial-statement caption:

1. Sum the mapped trial-balance account balances (`tb_accounts`).
2. `difference = fs_amount − tb_sum`.
3. Status:
   - **tie** — `|difference| ≤ clearly_trivial_threshold`.
   - **difference** — `|difference| > clearly_trivial_threshold` (raise a finding + open item).
   - **unmapped** — a referenced trial-balance account is absent (needs-data; obtain mapping).

Every tie-out cites the FS source and each trial-balance account used.

## Monetary-unit sampling (deterministic, documented)

Inputs are configuration, not judgment: `tolerable_misstatement`, `reliability_factor`,
`sample_seed`.

| Step | Rule |
| ---- | ---- |
| Sampling interval | `round(tolerable_misstatement / reliability_factor)` |
| Key items | Any item with `amount ≥ interval` is examined **100%** (individually significant) |
| Residual selection | Systematic monetary-unit: `start = sample_seed mod interval`, then selection points at `start, start+interval, …`; an item is selected when a point falls in its cumulative monetary range |
| Coverage | `examined_value / population_total` where `examined_value = key items + selected items` |

The reliability factor and interval are recorded on the working paper so the selection is
reproducible. Sampling is **not performed** when there is no eligible population or the
parameters are invalid — the paper says so rather than inventing a sample.

## Misstatement accumulation (evaluation is the auditor's)

- Accumulate factual and projected misstatements **above** the clearly-trivial threshold.
- Report `aggregate_total` against `overall_materiality` with a status of
  `below-overall-materiality` or `at-or-above-overall-materiality`.
- This is a **presented comparison for auditor evaluation only** — never a conclusion that
  the statements are (or are not) fairly stated. The engagement team and partner evaluate.

## Hard boundaries (fail closed)

- **No audit opinion** — never state or imply an opinion, "presents fairly", "true and fair",
  "reasonable assurance", "free from material misstatement", or any qualified/unqualified/
  adverse/disclaimer conclusion.
- **No conclusion** on fair presentation, materiality sufficiency, or **going concern**.
- **No sign-off on behalf of a human**; approvals are recorded, not manufactured.
- **Draft-only** — never deliver, file, submit, or issue as final.
- **No unsupported assertions** — every tie-out, selection, and finding is cited.
- **No ICFR / SOX opinion** — control-design or operating-effectiveness conclusions are out
  of scope.

## Working-paper package — required contents

Engagement & scope; planning & materiality; source mapping & tie-outs (cited); sampling
approach & selections; testing results & exceptions (cited, each open for auditor
evaluation); misstatement summary (for auditor evaluation); open items & requests; recorded
approvals (preparer + reviewer, partner before delivery); the standing limitation note.
