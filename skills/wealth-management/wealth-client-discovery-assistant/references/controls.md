# Discovery controls

R3; draft-only; mandatory human review. Fixed flags: `human_review_required: true`,
`action_taken: false`, `delivery_status: not-delivered`.

Permitted outputs are `review-ready` intake evidence or `needs-data` gap reports. Neither means
identity verified, account approved, advice suitable, or client authority confirmed. Never make
KYC/AML/sanctions decisions, recommendations, legal/tax determinations, or CRM/account writes.

- Do not create missing values, source IDs, timestamps, members, ownership, or goals.
- Preserve client-reported versus documented status and all unresolved findings.
- Validate supplied identity references; do not merge households or substitute members.
- Input hashes/artifact IDs identify evidence versions; they are not approval credentials.
- Minimize and mask identifiers; restrict the retained input snapshot to approved recipients.
- Do not publish, send, file, or persist in an external system from this skill.

Production gates remain open: approved intake/source policies, real read-only integration tests,
privacy/retention configuration, domain/compliance SME review, and independent real-model tests
of extraction, routing, source support, and adversarial inputs. Local fixture tests do not close them.
