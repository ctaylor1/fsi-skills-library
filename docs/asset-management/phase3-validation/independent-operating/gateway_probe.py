"""Independent synthetic gateway protocol probes; no network or real credentials."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs,urlsplit
ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('review_gateway',ROOT/'shared/asset-management/licensed_data_connector.py')
gateway=importlib.util.module_from_spec(spec);spec.loader.exec_module(gateway)
NOW=datetime(2026,10,4,14,tzinfo=timezone.utc)
REQUEST=dict(request_id='FWD-GATEWAY-7',dataset='review-feed',object_id='FUND-C',as_of='2026-10-03',knowledge_cutoff='2026-10-04',purpose='research',audience='internal-review')
POLICY=dict(schema_version=gateway.VERSION,policy_id='synthetic-policy',version='v1',approval_reference='synthetic-review-only',principal='fixture-principal',base_url='https://gateway.invalid',approved_origins=['https://gateway.invalid'],token_env='SYNTHETIC_GATEWAY_TOKEN',datasets={'review-feed':dict(purposes=['research'],audiences=['internal-review'])},timeout_seconds=1,max_attempts=2,max_bytes=10000,receipt_max_age_seconds=60)
TOKEN='synthetic-not-a-real-secret'
class Transport:
 def __init__(self,change=None,transient=False):self.calls=[];self.change=change;self.transient=transient
 def __call__(self,url,token,timeout,max_bytes):
  self.calls.append(urlsplit(url).path)
  assert token==TOKEN
  if self.transient:raise gateway.TransientError()
  q={k:v[0] for k,v in parse_qs(urlsplit(url).query).items()}
  value=dict(q,principal=POLICY['principal'],schema_version=gateway.VERSION)
  if self.calls[-1]=='/v1/permissions':value.update(operation='read',allowed=True,license_version='fixture-license-v2',checked_at=NOW.isoformat(),expires_at=(NOW+timedelta(seconds=30)).isoformat())
  else:value.update(snapshot_id='point-in-time-fixture',records=[dict(record_id='r7',value='17.25')],records_sha256=gateway.digest([dict(record_id='r7',value='17.25')]))
  if self.change:self.change(value,self.calls[-1])
  return value

def perform(policy=None,transport=None,clock=None):
 return gateway.read_snapshot(REQUEST,policy or POLICY,environment={'SYNTHETIC_GATEWAY_TOKEN':TOKEN},transport=transport or Transport(),clock=clock or (lambda:NOW),nonce_factory=lambda:'fresh-fixture-nonce')
results=[]
def rejected(name,transport,expected_calls=1,policy=None,clock=None):
 try:perform(policy,transport,clock)
 except (ValueError,TypeError) as exc:
  assert len(transport.calls)==expected_calls,(name,transport.calls)
  results.append(dict(case=name,expected='reject',observed='reject',calls=transport.calls,error=str(exc),passed=True))
 else:raise AssertionError(name+' was accepted')

t=Transport();out=perform(transport=t)
assert t.calls==['/v1/permissions','/v1/snapshots']
assert out['permission_verified_at_gateway'] is False and out['read_performed'] is False and out['access_observation']=='synthetic-transport'
assert out['records']==[dict(record_id='r7',value='17.25')]
results.append(dict(case='fresh-point-in-time-synthetic-read',expected='synthetic-only',observed=out['access_observation'],calls=t.calls,passed=True))
rejected('permission-denial',Transport(lambda v,p:v.update(allowed=False) if p.endswith('permissions') else None))
rejected('wrong-principal',Transport(lambda v,p:v.update(principal='different')))
rejected('wrong-nonce',Transport(lambda v,p:v.update(nonce='old')))
rejected('expired-permission',Transport(lambda v,p:v.update(expires_at=NOW.isoformat()) if p.endswith('permissions') else None))
rejected('snapshot-hash-corruption',Transport(lambda v,p:v.update(records_sha256='0'*64) if p.endswith('snapshots') else None),2)
rejected('snapshot-context-corruption',Transport(lambda v,p:v.update(object_id='FUND-D') if p.endswith('snapshots') else None),2)
t=Transport();rejected('permission-expires-during-read',t,2,clock=lambda: NOW+timedelta(seconds=31 if len(t.calls)>1 else 0))
rejected('bounded-retry-exhaustion',Transport(transient=True),2)
for key,badvalue in [('max_attempts',True),('max_attempts',4),('max_bytes',2000001)]:
 p=copy.deepcopy(POLICY);p[key]=badvalue;rejected('invalid-'+key+'-'+str(badvalue),Transport(),0,policy=p)
for list_field,malformed in [('purposes','licensed-research-only'),('audiences','external-internal-review-legacy')]:
 p=copy.deepcopy(POLICY);p['datasets']['review-feed'][list_field]=malformed;t=Transport()
 try:perform(p,t)
 except (ValueError,TypeError):results.append(dict(case='string-'+list_field,expected='reject-malformed-policy',observed='reject',passed=True))
 else:results.append(dict(case='string-'+list_field,expected='reject-malformed-policy',observed='accepted-substring-policy',calls=t.calls,passed=False,policy_field=malformed))
t=Transport(lambda v,p:v.update(debug_authorization='Bearer '+TOKEN) if p.endswith('permissions') else None)
try:
 out=perform(transport=t);leaked=TOKEN in json.dumps(out);observed='credential-present-in-output' if leaked else 'not-present'
except (ValueError,TypeError):
 leaked=False;observed='read-withheld'
results.append(dict(case='permission-debug-credential-reflection',expected='do-not-serialize-bearer-credential',observed=observed,passed=not leaked,field='permission_receipt.debug_authorization'))
try:gateway.NoRedirect().redirect_request(None,None,None,None,None,None)
except ValueError:results.append(dict(case='redirect-handler',expected='reject',observed='reject',passed=True))
else:raise AssertionError('redirect accepted')
output=dict(no_live_network=True,no_real_credentials=True,results=results,passed=sum(r['passed'] for r in results),failed=sum(not r['passed'] for r in results))
Path(__file__).with_name('gateway-probe-results.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
