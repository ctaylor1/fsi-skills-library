# Collection design: request-for-payment and pay-by-bank

Use the common Phase 2 envelope (schema_version, request_id, as_of, jurisdiction,
participant, registered sources, upstream_issues, data). Native data.requests is a
list of unique request and immutable message identities. Each row has request_id,
message_id, requester_ref, payer_ref, beneficiary_ref, amount (nonnegative decimal),
currency, rail_profile_id, channel=request-for-payment|pay-by-bank,
state=open|cancelled|expired|unknown, issued_on/expires_on ISO dates and source_ids.

Optional access_review needs participant_reach_ref, scheme_profile_ref and
requester_legitimacy_ref for an evidence-complete draft. Optional payer_response
has response_id, decision=accept|reject|unknown, consent_ref, review_ref and exact
binding {request_id,payer_ref,beneficiary_ref,amount,currency}. Empty/absent evidence
stays a gap. Amount zero is a probe, never a payment proposal. Binding comparison
is exact, including amount representation; canonicalize source formatting explicitly.
Each supplied response_id must be a nonempty string unique across this request
set. Reusing one immutable response identity for different requests is rejected;
this normalized schema does not represent a batch response with multiple bindings.

This helper implements normalized RFP review for US-FEDNOW and US-RTP only; no
pain.013 XML parser or SEPA/UK request-to-pay adapter is supplied. Pay-by-bank covers
credit-push collection design on a matching, currently reviewed rail profile; it
never converts a request into direct-debit authority. Dates are day-grain review
context, not an expiry/cutoff clock calculator. Institution timezone, effective time,
reachability and current scheme rules must be reviewed before any action.

Run `python scripts/validate_collection_input.py INPUT.json`,
`python scripts/review_collection.py INPUT.json`, then
`python scripts/validate_collection_output.py OUTPUT.json --input INPUT.json`.
The result retains exact request/response binding and gap list. Even a complete
response only prompts assembly of a separate native initiation-control request.
A cancellation of the collection request never rolls back an existing payment.

Source orientation reviewed 2026-09-18:
[FedNow Operating Procedures April 2026 v3.6](https://www.frbservices.org/binaries/content/assets/crsocms/resources/rules-regulations/042826-fednow-service-operating-procedures.pdf),
sections16/16.1: nonvalue request, acceptance and separate credit transfer; zero-value
probe. [RTP current rule library](https://www.theclearinghouse.org/payment-systems/rtp/document-library)
requires participant/version-specific source packs. Public orientation is not a
complete or licensed operating-rule implementation. Other collection designs retain
unsupported-profile gaps; no response or permission is inferred from a rail label.
