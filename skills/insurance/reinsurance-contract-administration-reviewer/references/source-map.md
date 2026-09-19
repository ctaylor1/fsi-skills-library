# Sources and native schema

Public anchors reviewed 2026-09-18:

- [NAIC reinsurance overview](https://content.naic.org/insurance-topics/reinsurance): Contract-specific obligations and differing reinsurance regulatory status.
- [NAIC covered agreements overview](https://content.naic.org/insurance-topics/covered-agreement): Collateral treatment varies by status, jurisdiction and applicable provisions; not a universal percentage.

Source hierarchy: operative supplied contract/application and endorsements; current carrier/jurisdiction procedure reviewed by an accountable specialist; dated system extracts; public context above. Record source_ref, version, date and exact document/section anchors; a content hash is not authentication. Do not invent a production connector.

## Common input

Top-level case_id, as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of?}], explicit unresolved_issues [], optional upstream_artifacts [], and data. The common profile fields are profile_id,version,source_refs[],effective_from,effective_to,jurisdictions[],lines_of_business[]; native profiles also carry source_ref for their main clause anchor. Null means unknown; explicit zero means a supplied zero. All money uses stated currency units and finite decimal values. No FX conversion occurs.

## Native data

`data.scope`: treaty_id,counterparty_id,period_start,period_end,currency,basis:ceded_paid_recoverable. `data.administration_terms`: common profile fields plus notice_inventory_complete:true only after reviewing all applicable obligations. `data.opening_recoverable` and `closing_recoverable`: exact scope + amount,source_ref. `data.statements`, `bordereaux`, `cash`, `adjustments`: arrays of exact scope + record_id,claim_id,amount,source_ref. Charges and receipts are positive; adjustments signed. `data.collateral`: exact scope + required_amount,held_eligible_amount,source_ref. `data.notices`: [{notice_id,treaty_id,counterparty_id,due_date,sent_date:null|date,evidence_source_ref:null|source,source_ref}].

All source_ref values must resolve to top-level sources. Supply evidence-backed values rather than output-ready assertions. Every ledger/evidence record retains its native identity and source. Source snapshots dated after as_of stay partial. The packaged input fixture is synthetic and is a runnable contract example, not an approved procedure or rate/rule table.
