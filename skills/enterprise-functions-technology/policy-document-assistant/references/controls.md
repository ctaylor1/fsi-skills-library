# Controls — policy-document-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The skill assembles a controlled policy/procedure **draft** and
  stages nothing for execution.
- **Human approval:** `external-delivery` — owner, legal, and compliance approval is required
  before the draft is delivered externally or activated. Internal analytical iteration may be
  reviewer-sampled. Approval is **recorded**, not performed, by this skill.

## Prohibited (fail closed)

- **Publishing, activating, filing, or making a policy effective**, or writing it into the
  policy/content system of record. This skill is draft-only.
- **Unsupported assertions:** any normative "shall/must" statement not mapped to an
  `approved` requirement with an authoritative source. No requirement, no clause.
- **Inventing or paraphrasing a requirement** to justify a clause, or citing a superseded,
  draft, or non-approved requirement.
- **Personalized legal advice** or a binding regulatory interpretation — the skill assembles
  approved requirements; it does not opine on what the law requires beyond them.
- **Backdating or self-recording approvals** — approval slots are filled by the human
  approvers, not by the skill.

## Draft states (this skill may set only these)

`draft` → `ready-for-review` (all sections assembled, all normative clauses sourced) →
`approvals-recorded` (human approvers signed). It may **not** set `published`, `effective`,
`active`, or `filed`.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present: `document-control`, `purpose`, `scope`,
  `policy-statements`, `roles-responsibilities`, `related-documents`,
  `review-version-history`, `approvals`.
- Every normative clause maps to ≥1 `approved` source; `unsupported_clauses` is empty; no
  unsupported-claim language ("industry best practice", "studies show", etc.).
- Each required approval role is recorded `approved` with an approver and date.
- `new_version` ties out to the version-bump rule; `next_review_date` ties out to the tier
  review cadence.
- No publication / activation / filing language anywhere (draft-only screen).
- Standing note present.

## Segregation of duties

Drafting is separate from **approving** and from **publishing/activating**. The author of a
draft must not also be the sole approver, and neither drafting nor approval activates the
policy — activation into the system of record is a distinct, human, controlled action.

## Data classification, privacy, records

- **Confidential.** Policies may reference control environments, thresholds, and named owner
  roles; treat drafts as internal and share only with the review chain.
- Retain each draft with its requirements-register version, policy-standard config version,
  source mapping, change summary, and recorded approvals so the deliverable is reproducible
  and auditable. Log author identity and every approval.
