from pathlib import Path
import json
from copy import deepcopy
D=Path(__file__).resolve().parent
# Reuse only this evaluator's locally authored runner, never package internals.
exec((D/'exercise.py').read_text().split('# Independently authored economic dossier:')[0])
seeds=json.loads((D/'seed-requests.json').read_text()); outputs={}
def probe(label,kind,mutate):
 r=deepcopy(seeds[kind]);mutate(r['data']);
 args={'wallet':('wallet-and-mobile-money-program-designer','validate_input.py','calculate_or_transform.py'),'platform':('platform-payment-flow-designer','validate_advanced_platform_input.py','review_advanced_platform.py'),'card':('commercial-payment-workflow-designer','validate_commercial_card_input.py','review_commercial_card.py')}[kind]
 outputs[label]=run(label,*args,r)
 return outputs[label]
probe('wallet-unknown-redemption','wallet',lambda d:d['events'][1].update(state='unknown'))
probe('wallet-settled-unfunded-issuance','wallet',lambda d:d['events'][0].update(funding_state='pending'))
probe('wallet-missing-agent-evidence','wallet',lambda d:d['program_pack'].pop('agent_liquidity_ref'))
probe('wallet-duplicate-redemption','wallet',lambda d:d['events'].append(deepcopy(d['events'][1])))
probe('wallet-wrong-backing-beneficiary','wallet',lambda d:d['backing'][0].update(beneficiary_issuer_entity_id='agent-co'))
probe('wallet-shared-backing-account','wallet',lambda d:d['backing'].append({**deepcopy(d['backing'][0]),'backing_id':'second-description-same-money'}))
probe('wallet-unknown-backing','wallet',lambda d:d['backing'][0].update(amount=None))
pass_wallet=deepcopy(seeds['wallet']);pass_wallet['jurisdiction']='US';pass_wallet['data'].update(model='credential-pass-through',positions=[],events=[],backing=[]);pass_wallet['data']['program_pack'].update(jurisdiction='US',country='US');pass_wallet['data']['channels']=[row(channel_id='app-channel',type='app',participant_access_ref='provider-app-access',fraud_support_ref='provider-app-fraud')]
outputs['wallet-pass-through']=run('wallet-pass-through','wallet-and-mobile-money-program-designer','validate_input.py','calculate_or_transform.py',pass_wallet)
probe('platform-duplicate-batch-member','platform',lambda d:d['batches'][0]['payout_ids'].append('pending-a'))
probe('platform-cross-entity-batch','platform',lambda d:d['batches'][0].update(owner_entity_id='seller-b'))
probe('platform-wrong-owner-account','platform',lambda d:d['accounts'][2].update(owner_entity_id='platform'))
probe('platform-unconserved-subtree','platform',lambda d:d['allocations'][2].update(amount='1401'))
probe('platform-internal-payout','platform',lambda d:d['payouts'][0].update(allocation_id='group-a'))
probe('platform-duplicate-economic-segment','platform',lambda d:d['payouts'][0].update(economic_id='econ-refund-a'))
probe('platform-pending-collection','platform',lambda d:d['charges'][0].update(state='pending'))
probe('commercial-unknown-outcome','card',lambda d:d['attempts'][1].update(state='unknown'))
probe('commercial-unconfirmed-settlement','card',lambda d:d['attempts'][0].pop('settlement_ref'))
probe('commercial-supplier-mismatch','card',lambda d:d['attempts'][2].update(supplier_ref='substituted-supplier'))
probe('commercial-expired-credential','card',lambda d:d['credentials'][0].update(valid_until='2026-09-18T15:00:00Z'))
probe('commercial-one-time-reuse','card',lambda d:d['credentials'][0].update(usage_mode='one-time',max_uses=1))
probe('commercial-duplicate-economic-id','card',lambda d:d['attempts'][2].update(economic_id='economic-held'))
probe('commercial-history-future','card',lambda d:d['attempts'][0].update(occurred_at='2026-09-19T10:00:00Z'))
probe('commercial-limit-excess','card',lambda d:d['credentials'][0].update(total_limit='900'))
probe('commercial-unknown-limit','card',lambda d:d['credentials'][0].update(total_limit=None))
fleet=deepcopy(seeds['card']);fleet['data']['program_type']='fleet';fleet['data']['credentials'][0]['allowed_mccs']=['5541']
for a in fleet['data']['attempts']:a.update(mcc='5541',vehicle_ref='fleet-vehicle-17',driver_or_fleet_policy_ref='reviewed-driver-fleet-policy')
outputs['commercial-fleet-normal']=run('commercial-fleet-normal','commercial-payment-workflow-designer','validate_commercial_card_input.py','review_commercial_card.py',fleet)
fleet['data']['attempts'][2].pop('driver_or_fleet_policy_ref')
outputs['commercial-fleet-driver-missing']=run('commercial-fleet-driver-missing','commercial-payment-workflow-designer','validate_commercial_card_input.py','review_commercial_card.py',fleet)
(D/'commands-boundaries.json').write_text(json.dumps(commands,indent=2)+'\n')
(D/'boundary-observations.json').write_text(json.dumps({k:{'status':v.get('status'),'errors':v.get('errors'),'findings':[f['code'] for f in v.get('findings',[])],'result':v.get('result')} for k,v in outputs.items()},indent=2)+'\n')
print(json.dumps({k:{'status':v.get('status'),'errors':v.get('errors'),'findings':[f['code'] for f in v.get('findings',[])]} for k,v in outputs.items()},indent=2))
