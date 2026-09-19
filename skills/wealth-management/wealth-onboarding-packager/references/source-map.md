# Input schema and source hierarchy

`wealth-p0-v1` envelope: request_id, de-identified household_id, ISO as_of, engagement capacity
(advisory/brokerage/private-bank/trust) and US jurisdiction, sources with source_id/reference/
owner/as_of/valid_until. Source dates must be internally valid and current at request as_of.
Every material domain record carries `source_ids[]`; these resolve to the dated registry.

| Record | Required content / meaning |
| --- | --- |
| relationship | relationship_id, service_scope, engagement_document_status received, source_ids |
| policy | version, owner, capacity, jurisdiction, account_requirements, consent_requirements, external_review_requirements, source_ids |
| accounts[] | unique account_id, registration, owner_ids, authorized_person_ids, authority_record_status received, source_ids |
| parties[] | unique party_id, role owner/authorized-person/beneficial-owner/trustee, identity_record_status received, source_ids |
| documents[] | unique document_id, account_id, kind matching policy, status received/missing/expired/conflict, valid_until date, source_ids |
| consents[] | unique consent_id, party_id, scope matching policy, status recorded/pending/declined, source_ids |
| external_reviews[] | unique review_id, kind kyc/sanctions/beneficial-ownership, account_id, covered party_ids, status completed-by-owner/pending/escalated, outcome no-unresolved-issues-recorded or outstanding outcome, owner_reference, source_ids |

Document valid_until is supplied expiry/review-through metadata; for non-expiring instruments,
the policy owner sets a review-through date. It is not an invented legal expiry date.
Identity and authority fields record possession of evidence, not a conclusion about validity.
External outcomes must be attributed to their authorized specialist owner. A completion label
is insufficient without account/party scope, owner reference and source coverage.

Hierarchy: engagement/custodian registration evidence; identity/authority/consent records;
specialist outcome records; owned firm checklist. Do not silently reconcile conflicts.
Source adapters and permission checks are not implemented. Supply only de-identified structured
statuses and document references, not raw passports, SSNs, account numbers or restricted SAR
narratives. Input snapshots retained for deterministic validation inherit original restrictions.
