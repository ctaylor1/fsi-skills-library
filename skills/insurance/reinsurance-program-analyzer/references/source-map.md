# Sources and native schema

Public anchors reviewed 2026-09-18:

- [NAIC reinsurance overview](https://content.naic.org/insurance-topics/reinsurance): Reinsurance contract and risk-transfer context; exact obligations derive from each agreement.

Source hierarchy: operative supplied contract/application and endorsements; current carrier/jurisdiction procedure reviewed by an accountable specialist; dated system extracts; public context above. Record source_ref, version, date and exact document/section anchors; a content hash is not authentication. Do not invent a production connector.

## Common input

Top-level case_id, as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of?}], explicit unresolved_issues [], optional upstream_artifacts [], and data. The common profile fields are profile_id,version,source_refs[],effective_from,effective_to,jurisdictions[],lines_of_business[]; native profiles also carry source_ref for their main clause anchor. Null means unknown; explicit zero means a supplied zero. All money uses stated currency units and finite decimal values. No FX conversion occurs.

## Native data

`data.program_terms`: common profile fields. `data.programs`: [{program_id,currency,loss_basis:ground_up_occurrence_loss,period_start,period_end,fixed_premium,scenario_additional_premiums:{scenario_id:amount},layers:[{layer_id,type:quota_share|occurrence_xol,inuring_basis:remaining_loss,attachment,limit,share,aggregate_limit,prior_erosion,source_ref}],source_ref}]. `data.scenarios`: [{scenario_id,currency,loss_basis,period_start,period_end,events:[{event_id,event_date,gross_loss,eligible_layer_ids:[],source_ref}],source_ref}]. Monetary values are decimal amounts in stated currency, not thousands/millions. An explicit zero-loss event represents a no-loss scenario.

All source_ref values must resolve to top-level sources. Supply evidence-backed values rather than output-ready assertions. Every ledger/evidence record retains its native identity and source. Source snapshots dated after as_of stay partial. The packaged input fixture is synthetic and is a runnable contract example, not an approved procedure or rate/rule table.
