"""Hand-constructed expected calculations and source/authority boundaries."""
import copy,json
from pathlib import Path
from calculate_or_transform import compute,validate as validate_input
from validate_output import validate
P=Path(__file__).resolve().parents[1]/'evals/files'
d=json.loads((P/'input.json').read_text());expected=json.loads((P/'independent-expectations.json').read_text())
r=compute(d)
for path,value in expected.items():
    actual=r['results']
    for part in path.split('.'):actual=actual[int(part)] if isinstance(actual,list) else actual[part]
    assert actual==value,(path,actual,value)
assert validate(r,d)==[]
assert r['action_taken'] is False and r['human_review_required'] is True
for mutate in ['output','input','embedded']:
    bad=copy.deepcopy(r);original=copy.deepcopy(d)
    if mutate=='output':bad['fabricated_conclusion']='approved'
    elif mutate=='input':original['unknown_material_input']='different'
    else:bad['source_input']=original
    assert validate(bad,original),mutate
assert validate(r)
for mutate in ['future','unregistered','action','nonfinite','audience']:
    bad=copy.deepcopy(d)
    if mutate=='future':bad['sources'][0]['known_at']='2026-09-22'
    elif mutate=='unregistered':bad['sources'][0]['source_ref']='MISSING'
    elif mutate=='action':bad['requested_action']='execute'
    elif mutate=='nonfinite':bad['unused']=float('nan')
    else:bad['audience']='public'
    assert validate_input(bad),mutate
print('independent calculation and boundary checks passed')
