# Adjacent-Skill Handoffs — policy-wording-comparator

This skill produces a cited **wording-comparison pack** (`comparison_id`) and stops. It does not
decide coverage or compliance, approve/file/bind a form, or close a review.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `policy-document-explainer` | The user actually wants a plain-language explanation of one policy, not a form-vs-form diff | form + section refs |
| `coverage-gap-analyzer` | The question is whether the wording covers a stated need/exposure (adequacy), not what changed between forms | needs + policy terms |
| `policy-renewal-reviewer` | The comparison is expiring-vs-proposed renewal terms for a customer explanation | expiring + proposed terms |
| `reinsurance-treaty-interpreter` | The wording is a reinsurance treaty (attachment, reinstatements, recoverability) | treaty clauses |
| `premium-quote-comparator` | The comparison is about premium/price across quotes, not wording | quotes |

## Upstream (may request a comparison pack)

`underwriting-workbench-assistant`, `submission-intake-triager`, and `policy-renewal-reviewer` may
request a wording comparison when a manuscript endorsement or a new edition appears in casework. A
scheduled monitor is **not** used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Human / licensed handoffs (not catalog skills)

The following are **not** other skills — they are actions reserved for people and authorized systems,
and this skill only prepares evidence and questions for them:

- **Product counsel / compliance** adjudicate materiality, coverage intent, and regulatory
  implications, and decide whether the subject form is acceptable.
- **Regulatory affairs / the filing system** decide whether and how to file a form with a state or
  regulator; this skill never files, approves, or clears a form for filing.
- **Underwriting authority** decides whether to use a manuscript wording on a risk; this skill never
  binds or authorizes coverage.

## Duplicate-execution prevention

- This skill computes and evidences **wording findings only**; it must not reach a coverage/compliance
  disposition, approve/file/bind, or close the review — those belong to the human reviewer and the
  authorized systems above.
- Downstream skills reuse the `comparison_id` evidence rather than re-diffing the forms.
