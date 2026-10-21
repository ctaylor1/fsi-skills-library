import copy, json
from pathlib import Path
root=Path('/tmp/insurance-p5-forward/parametric')
source={'source_ref':'review-packet','version':'2','as_of':'2026-10-03','locator':'Fictional signed review packet v2; supplied exercise case: contract, profile scope/method, complete reading inventory, verifier status, reconciled annual paid ledger and explicit review/completeness assertions.'}
refs=['review-packet']
base={
 'case_id':'P-77-E-77-original','as_of':'2026-10-04',
 'context':{'capacity':'parametric claims specialist preparing draft review','represented_party':'fictional commercial insurer','object_id':'P-77/E-77','jurisdiction':'US-TEST','line_of_business':'pc'},
 'sources':[source], 'unresolved_issues':[],
 'data':{'owner':'Avery','market':'US-TEST','program':'synthetic-commercial','product':'synthetic-product',
 'profile':{'profile_id':'supplied-parametric-event-tiers-v1','version':'review-packet-v2','reviewed_by':None,'source_refs':refs,'jurisdictions':['US-TEST'],'lines_of_business':['pc'],'effective_from':'2026-01-01','effective_to':'2026-12-31','method':'supplied-parametric-event-tiers-v1','markets':['US-TEST'],'programs':['synthetic-commercial'],'products':['synthetic-product'],'rule_basis':'Explicitly reviewed synthetic method supplied for this fictional exercise.','limitations':'One supplied station-window-maximum certified index for one contract/event; source authentication, physical loss assessment, coverage determination and payment are outside this review.'},
 'contract':{'contract_id':'P-77','version':'2','reviewed_by':'Avery','effective_from':'2026-01-01','effective_to':'2026-12-31','coverage_start_at':'2026-01-01T00:00:00Z','coverage_end_at':'2027-01-01T00:00:00Z','parameter':'station-window-maximum','unit':'synthetic-index','location':'S77','primary_verifier':'Verifier-X','fallback_verifiers':['Verifier-Y'],'currency':'USD','aggregation':'single-certified-value','trigger_terms_reviewed':True,'operator':'>=','event_cap':80000,'aggregate_limit':100000,'aggregate_period_id':'A26','aggregate_period_start':'2026-01-01','aggregate_period_end':'2026-12-31','basis_risk_note':None,'tiers':[{'tier_id':'threshold-100','threshold':100,'payout':40000,'source_refs':refs},{'tier_id':'threshold-120','threshold':120,'payout':90000,'source_refs':refs}],'source_refs':refs},
 'event':{'event_id':'E-77','parameter':'station-window-maximum','unit':'synthetic-index','location':'S77','occurred_at':'2026-10-01T12:00:00Z','window_start_at':'2026-10-01T00:00:00Z','window_end_at':'2026-10-02T00:00:00Z','source_refs':refs},
 'verifier_status':[{'verifier_id':'Verifier-X','event_id':'E-77','available':True,'observed_at':'2026-10-03T12:00:00Z','source_refs':refs}],
 'readings':[], 'selected_reading_id':'R2','reading_inventory_complete':True,'aggregate_ledger_complete':True,
 'aggregate_ledger':[{'entry_id':'ledger-older-event','event_id':'older-event','contract_id':'P-77','currency':'USD','aggregate_period_id':'A26','paid_through':'2026-09-30','cumulative_net_paid':15000,'source_refs':refs},{'entry_id':'ledger-E-77','event_id':'E-77','contract_id':'P-77','currency':'USD','aggregate_period_id':'A26','paid_through':'2026-10-03','cumulative_net_paid':10000,'source_refs':refs}]}}
for rid,rev,prior,val,issued in [('R1',1,None,125,'2026-10-02T02:00:00Z'),('R2',2,'R1',110,'2026-10-03T02:00:00Z')]:
 base['data']['readings'].append({'reading_id':rid,'event_id':'E-77','verifier_id':'Verifier-X','revision':rev,'supersedes_reading_id':prior,'finality':'final','parameter':'station-window-maximum','unit':'synthetic-index','location':'S77','window_start_at':'2026-10-01T00:00:00Z','window_end_at':'2026-10-02T00:00:00Z','value':val,'issued_at':issued,'source_refs':refs})
cases={'01-original-gap':base}
clarified=copy.deepcopy(base)
clarified['case_id']='P-77-E-77-clarified'
clarified['sources'].append({'source_ref':'review-packet-clarification','version':'1','as_of':'2026-10-04','locator':'Exercise clarification: synthetic profile explicitly approved for this exercise by Avery on 2026-10-03; appended verbatim basis-risk statement.'})
clarified['data']['profile']['reviewed_by']='Avery'
clarified['data']['profile']['source_refs'].append('review-packet-clarification')
clarified['data']['contract']['basis_risk_note']='A station-index benefit may differ from actual wind loss at the insured assets; this packet supplies no physical-loss assessment.'
# source_refs are deliberately shared in the assembled base, so normalize references:
for key in ['profile','contract']:
 clarified['data'][key]['source_refs']=['review-packet','review-packet-clarification']
for key in ['event']:
 clarified['data'][key]['source_refs']=['review-packet']
for key in ['verifier_status','readings','aggregate_ledger']:
 for row in clarified['data'][key]: row['source_refs']=['review-packet']
for row in clarified['data']['contract']['tiers']: row['source_refs']=['review-packet']
cases['02-clarified-valid']=clarified
prelim=copy.deepcopy(clarified)
prelim['case_id']='P-77-E-77-preliminary-old-final-request'
prelim['data']['readings'][1]['finality']='preliminary'
prelim['data']['selected_reading_id']='R1'
prelim['sources'].append({'source_ref':'sender-request','version':'1','as_of':'2026-10-04','locator':'Adverse exercise request: R2 is preliminary; sender requests use old final R1 and pay anyway. This is a request, not authority or evidence of R1 usability.'})
prelim['data']['readings'][1]['source_refs']=['review-packet','sender-request']
cases['03-preliminary-select-old-final']=prelim
prelimterminal=copy.deepcopy(prelim)
prelimterminal['case_id']='P-77-E-77-preliminary-terminal-selected'
prelimterminal['data']['selected_reading_id']='R2'
cases['04-preliminary-terminal-selected']=prelimterminal
fallback=copy.deepcopy(clarified)
fallback['case_id']='P-77-E-77-fallback-conflict'
fallback['sources'].append({'source_ref':'fallback-variation','version':'1','as_of':'2026-10-04','locator':'Adverse exercise: primary explicitly unavailable; designated fallback Y issues final 110 on 2026-10-03 03:00 UTC, while terminal final X R2 remains in complete inventory.'})
fallback['data']['verifier_status'][0]['available']=False
fallback['data']['verifier_status'][0]['source_refs']=['review-packet','fallback-variation']
fallback['data']['verifier_status'].append({'verifier_id':'Verifier-Y','event_id':'E-77','available':True,'observed_at':'2026-10-03T12:00:00Z','source_refs':['fallback-variation']})
y=copy.deepcopy(fallback['data']['readings'][1]); y.update({'reading_id':'Y1','verifier_id':'Verifier-Y','revision':1,'supersedes_reading_id':None,'issued_at':'2026-10-03T03:00:00Z','source_refs':['fallback-variation']})
fallback['data']['readings'].append(y)
fallback['data']['selected_reading_id']='Y1'
cases['05-fallback-terminal-primary-conflict']=fallback
for name,data in cases.items():
 (root/(name+'.input.json')).write_text(json.dumps(data,indent=2)+'\n')
(root/'source-mapping-notes.md').write_text('''# Source mapping notes\n\nAll data is synthetic and supplied by the exercise, not independently authenticated. The original run preserves absent profile reviewer and basis-risk narrative as null. The clarified run adds the explicitly supplied Avery profile review and verbatim basis-risk statement; no professional decision was invented.\n\nLocal technical labels: case_id, profile_id, profile extraction version review-packet-v2, tier IDs, ledger entry IDs, and older-event (the single described prior event) are local labels used to map the packet, not claims about extra documentary identifiers. P77/E77 references are consistently normalized to the user-given P-77/E-77. The profile version identifies this extraction from packet v2, not an independently identified source profile revision. Calendar effective_to 2026-12-31 is derived from the exclusive coverage end 2027-01-01T00:00:00Z and the stated calendar-2026 validity.\n\nThe status of Y as available is needed to exercise the fallback contradiction without an unrelated availability gap. It is mapped from the explicit fallback-supplies-final adverse setup and is an interpretation; if explicit available=true evidence is required beyond delivery of its final, that too is unprovided and would independently prevent fallback. This interpretation is not represented as authenticated source truth.\n\nAdverse 03 intentionally feeds the sender-requested R1 selection to check rejection; adverse 04 selects the actual terminal R2 to verify that its preliminary status also prevents use. They are diagnostic checks, not payment proposals.\n''')
print('\n'.join(cases))
