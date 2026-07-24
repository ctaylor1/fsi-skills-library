# Controls — research-publication-preparation-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any publication, distribution, publication approval, or
  rating/target determination.

## Prohibited (fail closed)
- No **publishing or distributing** the note.
- No **publication approval** or **clearance**.
- No **setting/determining/changing** the rating or target price.
- No **clearing a restricted ticker**; no assuming a missing disclosure is present.

## Required output screen (`scripts/validate_output.py`)
- Every gap and flag carries a citation.
- No publish/approval/rating language (regex: we publish/publish the note/note is approved/cleared
  for publication/we rate it/the rating is set/approved for distribution/distribute the note).
- Suggested disposition is review-only (`ready-for-compliance-review` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The preparer is not the supervisory analyst or compliance; the packet supports, never replaces,
the review-and-publish process. Research independence and MNPI barriers apply.

## Data classification, privacy, records
- **Highly Confidential (MNPI / client-confidential).** Enforce information barriers.
- Retain packet + citations + config versions; log read + external-delivery approval.

## Reproducibility
`prep_id` binds output to the exact note draft and config versions.
