# Domain Rules — financial-document-version-comparator

Deterministic structural diff of two document versions. It locates changes; it never judges
significance.

## Inputs
Each version: `doc_id`, `version`, `sections[]` with `id`, `heading`, `text`, and optional
`values` (named data fields). The two versions must share the same `doc_id`.

## Change taxonomy
| Change type | Fires when | Location/evidence |
| ----------- | ---------- | ----------------- |
| `section_added` | A section `id` in version B is absent from A | section id + heading (B) |
| `section_removed` | A section `id` in A is absent from B | section id + heading (A) |
| `text_changed` | Same `id`, normalized `text` differs | section id + before/after excerpt |
| `value_changed` | Same `id`, a `values[field]` differs | section id + field + before → after |

**Text normalization** (before comparison): collapse whitespace, strip, case-fold. Whitespace/
case-only differences are NOT reported; a substantive wording change always is.

## Disposition mapping (review-only)
- `clean` — no changes.
- `changes-for-review` — ≥1 change. A location summary for a human reviewer, **not** a
  materiality/significance/approval judgment.

## Hard boundaries (fail closed)
- Never assess materiality, legal significance, or disclosure sufficiency; never approve/edit/
  publish a version.
- Refuse to compare different `doc_id`s. If section `id`s are absent, flag the mapping ambiguity
  rather than inventing correspondences.
