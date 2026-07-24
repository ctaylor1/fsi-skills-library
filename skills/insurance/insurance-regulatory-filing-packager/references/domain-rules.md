# Domain Rules — insurance-regulatory-filing-packager

The approved filing checklist governs (versioned, per filing type and jurisdiction).
Orientation: complete filings, actuarial support for rate changes, required exhibits, and lawful
effective-date notice.

## Checks (deterministic)
| Check | Rule (default config) | Gap when |
| ----- | --------------------- | -------- |
| `component_completeness` | Every `required_component` for the filing type is present | A required component is absent or `present: false` |
| `exhibit_presence` | Every `required_exhibit` is present | A required exhibit is missing |
| `rate_support` | For rate filings, `proposed_rate_change_pct` ≤ indicated + `rate_tolerance_pct`, else a `rate_justification` component is present | Filed exceeds indicated beyond tolerance with no justification component |
| `effective_notice` | Days(`as_of` → `effective_date`) ≥ `min_notice_days` | Effective date is inside the required notice window |

Config (`required_components`, `required_exhibits`, `rate_tolerance_pct`, `min_notice_days`) is a
**versioned contract**; the output records the version. Thresholds are policy, never guessed.

## Disposition mapping (review-only)
- `ready-for-review` — no gaps fired (the analyst still reviews and submits).
- `gaps-for-review` — ≥1 gap. A triage suggestion for a human reviewer, **not** a submission or
  compliance determination.

## Hard boundaries (fail closed)
- Never submit/file; never approve or set a rate; never certify compliance; never fabricate a
  missing exhibit value.
- Rate adequacy itself is out of scope — route to `actuarial-model-run-assistant`.
