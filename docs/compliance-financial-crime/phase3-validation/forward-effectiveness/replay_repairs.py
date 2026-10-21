from pathlib import Path
import subprocess,json,hashlib
from decimal import Decimal
import sys
base=Path('/tmp/cfc-phase3-forward-effectiveness');repo=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime')
rows=[]
for name,package in [('M2-original','transaction-monitoring-effectiveness-reviewer'),('M2-cost-supported-time-unknown','transaction-monitoring-effectiveness-reviewer'),('T2-scoped-exhibit-missing','financial-crime-case-quality-reviewer')]:
 raw=base/(name+'.json');previous=base/(name+'-result.json');before=hashlib.sha256(raw.read_bytes()).hexdigest()
 command=[sys.executable,'-B',str(repo/package/'scripts/calculate_or_transform.py'),str(raw)]
 proc=subprocess.run(command,capture_output=True,text=True,cwd=base)
 outpath=base/(name+'-after-repair-result.json');outpath.write_text(proc.stdout)
 (base/(name+'-after-repair.stderr')).write_text(proc.stderr)
 out=json.loads(proc.stdout);r=out['results']
 if name=='M2-original':
  metrics=r['operational_unit_measures'];matched=Decimal(metrics['minutes_per_completed_review']['decimal'])==Decimal(60) and metrics['cost_per_completed_review'] is None
  expected='known time60 retained while cost unknown; selected sample precision/recall1/2 retained'
  matched=matched and r['sample_precision']['numerator']==1 and r['sample_precision']['denominator']==2 and r['sample_recall']['numerator']==1 and r['sample_recall']['denominator']==2
 elif name.startswith('M2-cost'):
  metrics=r['operational_unit_measures'];matched=metrics['minutes_per_completed_review'] is None and Decimal(metrics['cost_per_completed_review']['decimal'])==Decimal('30.125')
  expected='USD gross cost30.125 retained while time unknown'
 else:
  metrics={'counts':r['observed_criterion_counts'],'criterion':r['case_criterion_checks'][0]['eligible_observed_result'],'threshold':r['within_supplied_exception_threshold']}
  matched=r['observed_criterion_counts']=={'pass':5,'fail':1,'unknown':4} and r['case_criterion_checks'][0]['eligible_observed_result']=='fail' and r['within_supplied_exception_threshold'] is None
  expected='known unavailable required exhibit causes evidence-completeness fail; dependent checks unknown; threshold withheld'
 vcmd=[sys.executable,'-B',str(repo/package/'scripts/validate_output.py'),str(outpath),'--input',str(raw)]
 validated=subprocess.run(vcmd,capture_output=True,text=True,cwd=base)
 (base/(name+'-after-repair-validation.json')).write_text(validated.stdout)
 entry={'input':raw.name,'input_sha256':before,'input_unchanged':before==hashlib.sha256(raw.read_bytes()).hexdigest(),'initial_output_preserved':previous.exists(),'command':command,'actual_exit':proc.returncode,'detached_validation_command':vcmd,'detached_validation_exit':validated.returncode,'independent_prior_expectation':expected,'actual':metrics,'matched_prior_expectation':bool(matched),'boundary_preserved':out['action_taken'] is False and out['source_truth']=='unverified' and out['human_review_required'] is True}
 rows.append(entry)
 assert matched and validated.returncode==0 and entry['input_unchanged'] and entry['boundary_preserved'],entry
summary={'status':'Independent prior findings repaired on unchanged raw evidence','replays':rows,'scope':'Native deterministic behavior only; prior raw/expectations/results preserved, no source authentication or professional acceptance established'}
(base/'after-repair-replay-findings.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'matched_prior_expectations':len(rows),'rows':[{k:v for k,v in row.items() if k in ['input','actual','matched_prior_expectation','detached_validation_exit']} for row in rows]},indent=2))
