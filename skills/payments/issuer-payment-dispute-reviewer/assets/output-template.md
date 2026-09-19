# Dispute Case Response — DRAFT (for human adjudication)

> Draft decision-support only. This skill does not decide any dispute, accept or deny a
> chargeback, issue provisional or final credit, assign liability, submit or file a response,
> or close a case; no cardholder or merchant account is debited or credited. A human
> adjudicator must review every recommendation and authorize any submission.

Fill every `{{placeholder}}` from validated sources. Do not add any assertion that is not
backed by a listed exhibit. Do not include full PAN — mask to last four.

## 1. Case identification

| Field | Value |
| ----- | ----- |
| Case reference | {{case_id}} |
| Role | {{role}} (issuer / acquirer) |
| Card network | {{network}} |
| Reason code | {{reason_code}} — {{reason_title}} |
| Disputed amount | {{dispute_amount}} {{currency}} |
| Transaction ID / Auth ID | {{txn_id}} / {{auth_id}} |
| Card (masked) | ****{{card_last4}} |
| Identity tie-out | {{identity_status}} |

## 2. Reason code & rule basis

| Field | Value |
| ----- | ----- |
| Reason code / category | {{reason_code}} / {{category}} |
| Current rule version | {{current_rule_version}} |
| Rule version current? | {{rule_current}} |

## 3. Deadline & timeline

| Field | Value |
| ----- | ----- |
| Dispute received | {{received_date}} |
| Response window | {{window_days}} days |
| Response deadline | {{response_deadline}} |
| Days remaining (as of {{processing_date}}) | {{days_remaining}} |
| Deadline status | {{deadline_status}} |

## 4. Evidence inventory

| Exhibit | Type | Source citation |
| ------- | ---- | --------------- |
| {{exhibit_ref}} | {{evidence_type}} | {{source_citation}} |

Required-evidence groups for {{reason_code}} satisfied: {{evidence_complete}}.

## 5. Draft response narrative

Concise, factual, reason-code-specific. Each statement cites an exhibit. No outcome
guarantees, no legal/financial advice, no "decided / submitted / filed / credited / closed"
language.

{{draft_response_narrative_with_exhibit_citations}}

## 6. Recommended disposition (decision-support only — not a decision)

- Recommended action: {{recommended_action}}
- Rationale: {{rationale}}
- Note: this is a recommendation for the adjudicator; the decision, any credit, and any
  submission are the human's.

## 7. Human review & authorization (required before any submission)

- [ ] Reason code and deadline verified against the current network rulebook.
- [ ] Evidence complete, correctly masked, and tied to the disputed transaction.
- [ ] Narrative contains no unsupported claim, outcome guarantee, or advice.
- [ ] Adjudication decision recorded by an authorized reviewer.
- [ ] Authorized to submit via the dispute case system.

Reviewer role: {{reviewer_role}}
Authorization status: {{authorization_status}}  (must remain `pending-human-authorization`
until a human authorizes)
Reviewer: ________________________  Date: ____________  Decision: represent / accept-liability
(review) / request-more-info / withdraw
