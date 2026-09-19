# Sources and native schema

Public anchors reviewed 2026-09-18:

- [NAIC accelerated underwriting](https://content.naic.org/insurance-topics/accelerated-underwriting): Medical evidence, external-data limitations and underwriting governance context; not a carrier-specific decision rule.

Source hierarchy: operative supplied contract/application and endorsements; current carrier/jurisdiction procedure reviewed by an accountable specialist; dated system extracts; public context above. Record source_ref, version, date and exact document/section anchors; a content hash is not authentication. Do not invent a production connector.

## Common input

Top-level case_id, as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of?}], explicit unresolved_issues [], optional upstream_artifacts [], and data. The common profile fields are profile_id,version,source_refs[],effective_from,effective_to,jurisdictions[],lines_of_business[]; native profiles also carry source_ref for their main clause anchor. Null means unknown; explicit zero means a supplied zero. All money uses stated currency units and finite decimal values. No FX conversion occurs.

## Native data

`data.application`: application_id, applicant_id, currency, purpose, coverage_amount, existing_coverage, annual_income, source_ref. `data.criteria`: common profile fields, source_ref, requirements [{requirement_id,kind:medical|financial,document_type,max_age_days}], financial_multiple_limit. `data.evidence`: [{evidence_id,application_id,applicant_id,document_type,as_of,status:received|pending|conflicting,source_ref}]. `data.disclosures`: [{topic,application_value,evidence_value,evidence_id,source_ref}]. Explicit null financial values remain unknown. The fixture gives a complete runnable schema.

All source_ref values must resolve to top-level sources. Supply evidence-backed values rather than output-ready assertions. Every ledger/evidence record retains its native identity and source. Source snapshots dated after as_of stay partial. The packaged input fixture is synthetic and is a runnable contract example, not an approved procedure or rate/rule table.
