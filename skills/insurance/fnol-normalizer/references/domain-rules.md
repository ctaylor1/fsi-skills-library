# Domain Rules — fnol-normalizer

The controlled-vocabulary config governs (versioned). Orientation: a schema-conformant,
code-standardized intake record with data-quality exceptions surfaced for a human.

## Normalization (deterministic)
| Field | Rule |
| ----- | ---- |
| `loss_type` | Lowercase-trim `loss_type_raw`, look up in `loss_type_map`; unmapped → null + `unmapped_code` |
| `cause` | Lowercase-trim `cause_raw`, look up in `cause_map`; unmapped → null + `unmapped_code` |
| plain fields | `policy_number`, `loss_date`, `reported_date`, `claimant`, `loss_location` carried through |

## Checks (deterministic)
| Check | Rule | Exception when |
| ----- | ---- | -------------- |
| `missing_required` | Every `required_fields` entry has a non-empty raw/plain value | A required field is empty/absent |
| `unmapped_code` | Coded fields resolve in their vocabulary | Raw value present but not in the map |
| `date_order` | `loss_date` ≤ `reported_date` | Loss date is after the report date |

Config (`loss_type_map`, `cause_map`, `required_fields`) is a **versioned contract**; the output
records the version. Mappings are exact (post-normalization) lookups, never fuzzy guesses.

## Disposition mapping (review-only)
- `normalized` — no exceptions.
- `exceptions-for-review` — ≥1 exception. A triage suggestion for a human, **not** a claims
  decision.

## Hard boundaries (fail closed)
- Never determine coverage/liability/reserve; never open/route/adjudicate a claim; never guess a
  mapping or fabricate a required value; never infer a code from the narrative.
