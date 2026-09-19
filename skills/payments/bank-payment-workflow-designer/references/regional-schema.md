# Optional regional-design module — Phase 4

The existing core rail comparison and collection entrypoints keep their own US/EA/UK scope. Invoke review_regional.py explicitly for a domestic Pix/BRL, UPI/INR or Interac e-Transfer/CAD credit-push proposal; cross-border delivery needs a separate corridor design.

Use the foundation 1.0 envelope with jurisdiction BR/IN/CA. data.proposals is a list with unique proposal_id, profile_id (BR-PIX/IN-UPI/CA-INTERAC-ETRANSFER), use_case (domestic-consumer-credit/domestic-business-credit), payer_entity, payer_account_ref, payee_entity, payee_account_ref, amount positive decimal, currency, accountable_reviewer, intent_ref and nonempty registered source_ids.

`participant_review` contains access_ref, payer_reach_ref, payee_reach_ref, funding_arrangement_ref, limits_review_ref, fees_review_ref and operational_support_ref. They are actual-case evidence, not defaults. `rule_review` contains reviewer, reference, rule_version, activity_scope_ref, profile_id, jurisdiction, use_case, reviewed_on/review_due ISO dates. Dates and exact scope must match the proposal.

`beneficiary_review` has verification_ref, alias_resolution_ref, match_status matched/mismatch/unknown, reviewed_on/review_due dates and exact `binding` equal to payer_entity/payer_account_ref/payee_entity/payee_account_ref/amount/currency. Store opaque identifiers, no raw aliases or authentication secrets. For Interac, these additional fields are all inside beneficiary_review: delivery_mode autodeposit or security-question-review; autodeposit needs beneficiary_review.displayed_legal_name_review_ref; the other path needs beneficiary_review.secure-recipient-channel_review_ref. Never store the security answer.

Current rule and beneficiary review plus intent and access evidence can support assembling a separate local initiation review. They cannot establish payment authority or settlement. No native BR/IN/CA initiation adapter is added to the US/EA/UK core reviewer.

Read regional-profiles.json for sources, owner roles and distinctions. The profile review date is maintenance metadata; the named case reviewer and licensed participant source must still be verified. No automatic debit, UPI collect/mandate/international linkage or Interac international product is covered. Raw QR/network messages, aliases and actual financial-institution reach are not validated.

Commands: validate_regional_input.py request.json; review_regional.py request.json; validate_regional_output.py output.json --input request.json; test_regional.py. Empty/missing operating evidence is not silently filled. Source-bound recomputation detects artifact changes, not source falsity.
