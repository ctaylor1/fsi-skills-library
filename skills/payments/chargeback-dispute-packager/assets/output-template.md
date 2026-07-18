# Chargeback Representment Package — DRAFT (for human review)

> Draft representment package for human review only; this skill does not submit to any card
> network or acquirer, does not guarantee any dispute outcome, and every claim must be
> verified against current network rules before submission.

Fill every `{{placeholder}}` from validated sources. Do not add an assertion that is not
backed by a listed exhibit. Do not include full PAN — mask to last four.

## 1. Case identifiers

| Field | Value |
| ----- | ----- |
| Dispute / case reference | {{dispute_id}} |
| Card network | {{network}} |
| Reason code | {{reason_code}} — {{reason_title}} |
| Ruleset version | {{ruleset_version}} |
| Disputed amount | {{dispute_amount}} {{currency}} |

## 2. Transaction identity

| Field | Value |
| ----- | ----- |
| Transaction ID | {{txn_id}} |
| Acquirer reference number (ARN) | {{arn}} |
| Authorization code | {{auth_code}} |
| Transaction date | {{txn_date}} |
| Card (masked) | ****{{card_last4}} |

Identity tie-out: {{identity_status}} (currency and amount reconcile to the disputed
transaction; every exhibit references this transaction).

## 3. Deadline

| Field | Value |
| ----- | ----- |
| Chargeback date | {{chargeback_date}} |
| Representment window | {{window_days}} days |
| Representment due date | {{representment_due_date}} |
| Days remaining (as of {{as_of_date}}) | {{days_remaining}} |
| Deadline status | {{deadline_status}} |

## 4. Merchant rebuttal narrative

Concise, factual, and reason-code-specific. Each sentence cites an exhibit. No outcome
guarantees, no legal advice, no "we have submitted/filed" language.

{{rebuttal_narrative_with_exhibit_citations}}

## 5. Evidence index

| Exhibit | Type | Supports (narrative point) | Source citation |
| ------- | ---- | -------------------------- | --------------- |
| {{exhibit_id}} | {{evidence_type}} | {{supports_point}} | {{source_citation}} |

All required evidence groups for {{reason_code}} are satisfied: {{evidence_complete}}.

## 6. Compelling evidence (fraud reason codes only)

Eligibility flag: {{compelling_evidence_eligible}} — {{compelling_basis}}. Eligibility is for
the reviewer to weigh; it is not a prediction of the outcome.

## 7. Reviewer sign-off (required before submission)

- [ ] Reason code and deadline verified against the current network ruleset.
- [ ] Evidence complete, correctly masked, and tied to the disputed transaction.
- [ ] Narrative contains no unsupported claims, guarantees, or advice.
- [ ] Authorized to submit via the case portal / acquirer.

Reviewer: ________________________  Date: ____________  Decision: submit / revise / withdraw
