from pathlib import Path
import json
root=Path('/tmp/cfc-phase3-forward-detection');original=json.loads((root/'before-run-expectations.json').read_text());cases=[]
for case in original['cases']:
 if not case['id'].startswith('m1-'):continue
 doc=json.loads((root/case['input']).read_text());doc['object_id']='RAPID-OUTFLOW-81'
 if case['id']!='m1-native-context-mismatch':doc['workflow']['context']['object_id']='RAPID-OUTFLOW-81'
 new={**case,'id':case['id']+'-scope-adapted','input':case['id']+'-scope-adapted.json','scope_adapter':'Change only native object/context ID to the actual scenario_id; source-bound scenario, evidence and independent expectation otherwise preserved. Intentional native-context mismatch remains mismatched.'}
 (root/new['input']).write_text(json.dumps(doc,indent=2)+'\n');cases.append(new)
(root/'before-corrected-run-expectations.json').write_text(json.dumps({'created_before_native_runs':True,'original_intakes_and_initial_logs_preserved':True,'reason':'Initial forward raw packets represented a review ID, but native M1 requires object_id=scenario_id. Corrected identity adapter retains all raw evidence and substantive expectation.','cases':cases},indent=2)+'\n')
# Reuse evaluator mechanics with a distinct declared input and output evidence file.
s=(root/'run_forward.py').read_text().replace("before-run-expectations.json","before-corrected-run-expectations.json").replace("packages-before-hashes.json","packages-corrected-before-hashes.json").replace("ROOT/'result.json'","ROOT/'corrected-result.json'")
(root/'run_corrected_forward.py').write_text(s)
print(len(cases),'scope-corrected intakes preserved before native run')
