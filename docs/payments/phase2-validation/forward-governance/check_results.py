import hashlib,json,pathlib
P=pathlib.Path('/tmp/payments-phase2-forward-governance');R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
def load(s):return json.loads((P/(s+'-output.json')).read_text())
checks=[]
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
 if not condition:raise AssertionError(name)
uk=load('1a-uk-emi');ea=load('1b-ea-no-national');unsupported=load('1c-unsupported')
check('UK no automatic deposit insurance/permission',uk['status']=='needs-evidence' and 'deposit-insured' in uk['result']['excluded_conclusions'] and uk['authority_granted'] is False)
check('UK safeguarding/permissions and customer claims preserved',{'uk-permissions','uk-safeguarding','uk-consumer'}.issubset({x['obligation_id'] for x in uk['result']['applicability_matrix']}) and uk['result']['funds_flow'][0]['customer_claim_against']=='SYNTH-UK-EMI under wallet terms')
check('EA national law gap explicit',ea['status']=='needs-evidence' and any(x['code']=='national-transposition-required' for x in ea['findings']))
check('Unsupported jurisdiction has no regional conclusion',unsupported['status']=='unsupported' and unsupported['result']=={} and unsupported['authority_granted'] is False)
good=load('2a-hub-design');bad=load('2b-hub-uncertain')
check('Complete hub retained four distinct authority models',good['status']=='draft' and len(good['result']['state_authority_map'])==4 and not good['findings'])
check('Hub draft never selects vendor or deploys',all(not x['selected'] for x in good['result']['decision_records']) and not good['result']['deployment_or_resilience_validated'] and all(not x['go_live_authorized'] for x in good['result']['migration_phases']) and not good['authority_granted'])
check('Unsafe retry and absent reconciliation stop complete flow review',bad['status']=='needs-evidence' and next(x for x in bad['result']['flow_assessments'] if x['flow_id']=='submit')['assessment']=='unresolved' and any('blind retry' in x['message'] for x in bad['findings']) and any('reconciliation' in x['message'] for x in bad['findings']))
p=load('3a-profile-prepare');stale=load('3b-profile-stale-review');first=load('3c-issuer-case001')['cases'][0];second=load('3d-issuer-profile-reuse')['cases'][0]
check('Profile preparation has no authority or calculated dates',p['status']=='supplied-profile-for-native-review' and not p['authority_granted'] and not p['deadlines_calculated'] and p['profile']['case_scope']['case_id']=='case001')
check('Changed scope cannot reuse specialist-review hash',stale['status']=='needs-review' and stale['profile']['status']=='draft')
check('Native case001 is only a review draft',first['disposition']=='draft-ready-for-review' and first['draft_response']['authorized_submission'] is False)
check('Native case002 rejects case001 profile',second['disposition']=='legal-profile-unresolved' and second['draft_response'] is None and any('different case scope' in x for x in second['needs']))
check('Future investigation-completion/error-determination dates not fabricated',{x['name'] for x in first['statutory_review']['clocks']}=={'error-notice','initial-investigation'})
for label in ['1a-uk-emi','1b-ea-no-national','1c-unsupported','2a-hub-design','2b-hub-uncertain']:
 d=load(label);inputdoc=json.loads((P/(label+'-input.json')).read_text());check(label+' retains original evidence and no actions',d['source_snapshot']==inputdoc and not d['action_taken'])
(P/'independent-assertions.json').write_text(json.dumps(checks,indent=2)+'\n')
before=json.loads((P/'source-sha256-before.json').read_text());after={k:hashlib.sha256((R/k).read_bytes()).hexdigest() for k in before}
(P/'source-sha256-after.json').write_text(json.dumps(after,indent=2)+'\n')
changed=[k for k in before if before[k]!=after[k]]
(P/'source-drift.json').write_text(json.dumps({'changed_since_initial_hash':changed},indent=2)+'\n')
print(json.dumps({'assertions_passed':len(checks),'source_files_hashed':len(before),'changed_since_initial_hash':changed},indent=2))
