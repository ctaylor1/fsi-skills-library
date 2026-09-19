# Sources and native schema

Public anchors reviewed 2026-09-18:

- [NAIC life buyer guide](https://content.naic.org/sites/default/files/publication-lig-lp-consumer-life.pdf): Life policy and beneficiary concepts; operative contract and jurisdiction determine claim requirements.

Source hierarchy: operative supplied contract/application and endorsements; current carrier/jurisdiction procedure reviewed by an accountable specialist; dated system extracts; public context above. Record source_ref, version, date and exact document/section anchors; a content hash is not authentication. Do not invent a production connector.

## Common input

Top-level case_id, as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of?}], explicit unresolved_issues [], optional upstream_artifacts [], and data. The common profile fields are profile_id,version,source_refs[],effective_from,effective_to,jurisdictions[],lines_of_business[]; native profiles also carry source_ref for their main clause anchor. Null means unknown; explicit zero means a supplied zero. All money uses stated currency units and finite decimal values. No FX conversion occurs.

## Native data

`data.policy`: policy_id,insured_id,issue_date,effective_date,currency,source_ref. `data.death`: insured_id,date,source_ref. `data.claim_terms`: common profile fields,source_ref,contestability_end,requirements[{requirement_id,document_type,max_age_days?}]. `data.evidence`: [{evidence_id,policy_id,insured_id,document_type,as_of,status,source_ref}]. `data.beneficiary_records`: [{record_id,policy_id,version,effective_date,designation_status:active|superseded|disputed,beneficiaries:[{beneficiary_id,share}],source_ref}]. `data.amount_bridge`: policy_id,currency,base_benefit,additional_benefits,loan_balance,loan_interest,prior_payments,interest_credit,source_ref.

All source_ref values must resolve to top-level sources. Supply evidence-backed values rather than output-ready assertions. Every ledger/evidence record retains its native identity and source. Source snapshots dated after as_of stay partial. The packaged input fixture is synthetic and is a runnable contract example, not an approved procedure or rate/rule table.
