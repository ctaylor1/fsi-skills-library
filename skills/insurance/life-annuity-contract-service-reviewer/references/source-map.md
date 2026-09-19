# Sources and native schema

Public anchors reviewed 2026-09-18:

- [FINRA annuities overview](https://www.finra.org/investors/investing/investment-products/annuities): Product distinctions and contract risks.
- [FINRA indexed annuity considerations](https://www.finra.org/investors/insights/complicated-risks-and-rewards-indexed-annuities): Withdrawals can incur charges and alter benefits; exact terms come from the contract.
- [NAIC life buyer guide](https://content.naic.org/sites/default/files/publication-lig-lp-consumer-life.pdf): Owner and beneficiary concepts; does not resolve assignments or disputed authority.

Source hierarchy: operative supplied contract/application and endorsements; current carrier/jurisdiction procedure reviewed by an accountable specialist; dated system extracts; public context above. Record source_ref, version, date and exact document/section anchors; a content hash is not authentication. Do not invent a production connector.

## Common input

Top-level case_id, as_of (YYYY-MM-DD), context {capacity,represented_party,object_id,jurisdiction,line_of_business}, sources [{source_ref,version,as_of?}], explicit unresolved_issues [], optional upstream_artifacts [], and data. The common profile fields are profile_id,version,source_refs[],effective_from,effective_to,jurisdictions[],lines_of_business[]; native profiles also carry source_ref for their main clause anchor. Null means unknown; explicit zero means a supplied zero. All money uses stated currency units and finite decimal values. No FX conversion occurs.

## Native data

`data.contract`: contract_id, owner_id, beneficiary_ids[], assignee_ids[], product_type, currency, account_value, value_date, source_ref. `data.request`: request_id,contract_id,requester_id,action:withdrawal|surrender|beneficiary_change,requested_amount or proposed_beneficiary_id,source_ref. `data.service_terms`: common profile fields,source_ref,authorized_actor_ids[],consents_required[],formula:supplied_deduction_bridge,surrender_charge,market_value_adjustment_signed,loan_offset,withholding,benefit_before,benefit_after. `data.consents`: [{actor_id,contract_id,request_id,status:received,as_of,source_ref}].

`data.contract.value_date` is the original valuation snapshot date in YYYY-MM-DD form. For withdrawal/surrender arithmetic, it must equal top-level `as_of` exactly. Missing/null dates and valid prior or future dates remain in retained evidence, emit `valuation_date_missing`, `valuation_date_stale` or `valuation_date_future`, and leave `results.value_scenario` null. An invalid calendar date fails structural input validation. A prior-day closing snapshot is not accepted as same-day evidence. Obtain a source-backed valuation for the review date; do not change the supplied raw date to make the scenario run. This package has no configurable stale-value tolerance.

All source_ref values must resolve to top-level sources. Supply evidence-backed values rather than output-ready assertions. Every ledger/evidence record retains its native identity and source. Source snapshots dated after as_of stay partial. The packaged input fixture is synthetic and is a runnable contract example, not an approved procedure or rate/rule table.
