# Adjacent-Skill Handoffs — premium-quote-comparator

This skill produces a normalized **quote comparison** (`comparison_id`) and stops. It does
not advise, select coverage, assess whether coverage fits the customer's exposures, explain
a single policy in depth, or evaluate policy wording against a standard.

## Downstream (route the human/user to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `coverage-gap-analyzer` | The user asks whether a quote's coverage is adequate for their needs/exposures (not just quote-vs-quote) | `comparison_id` + stated needs |
| `policy-wording-comparator` | The user needs clause/endorsement wording compared against approved forms/standard | quote/form references |
| `policy-document-explainer` | The user wants one policy or quote document explained in plain language | the specific document |
| `policy-renewal-reviewer` | The comparison is expiring-vs-proposed renewal terms for an in-force policy | expiring + proposed terms |
| `submission-intake-triager` | Raw broker emails/ACORD/PDFs must first be ingested and structured before comparison | source documents |

## Upstream (may call this skill)

`submission-intake-triager` or a producer workbench may hand structured quotes to this skill
for a normalized side-by-side. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **normalizes and compares** quotes and surfaces differences; it must not advise,
  select, rank-as-advice, or judge coverage adequacy — those belong to `coverage-gap-analyzer`
  and a licensed producer.
- Downstream skills reuse the `comparison_id` and its citations rather than re-normalizing the
  same quotes.
