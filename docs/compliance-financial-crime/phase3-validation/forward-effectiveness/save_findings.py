from pathlib import Path
import copy,json,subprocess,sys
base=Path('/tmp/cfc-phase3-forward-effectiveness');root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime')
verification=[]
for name,pkg in [('M2-original','transaction-monitoring-effectiveness-reviewer'),('T2-scoped-original','financial-crime-case-quality-reviewer')]:
 original=base/(name+'.json');output=base/(name+'-result.json');raw=json.loads(output.read_text())
 for mutation in ('action','narrative','result'):
  altered=copy.deepcopy(raw)
  if mutation=='action':altered['action_taken']=True
  elif mutation=='narrative':altered['approval_note']='Accepted and complete'
  else:altered['results']['source_faithfulness']='certified'
  path=base/(name+'-tamper-'+mutation+'.json');path.write_text(json.dumps(altered,indent=2)+'\n')
  command=[sys.executable,'-B',str(root/pkg/'scripts/validate_output.py'),str(path),'--input',str(original)]
  proc=subprocess.run(command,capture_output=True,text=True,cwd=base)
  (base/(name+'-tamper-'+mutation+'-validation.json')).write_text(proc.stdout)
  verification.append({'name':name,'mutation':mutation,'command':command,'actual_exit':proc.returncode,'rejected':proc.returncode==1})
 command=[sys.executable,'-B',str(root/pkg/'scripts/validate_output.py'),str(output)]
 proc=subprocess.run(command,capture_output=True,text=True,cwd=base)
 (base/(name+'-no-detached-original.stderr')).write_text(proc.stderr)
 verification.append({'name':name,'mutation':'missing-detached-original','command':command,'actual_exit':proc.returncode,'rejected':proc.returncode==2})
summary={'review_date':'2026-10-04','review_status':'Independent supplied-evidence forward review; actionable findings recorded, no reviewed package edits','inputs_and_expectations':'Independent raw synthetic intakes authored from SKILL/schema/domain docs. No unit tests, package expected outputs or golden fixtures were inspected. Before-run expectations preserved. Initial T2 exploratory intakes omitted counterevidence exhibit/link records; corrected unknown behavior was preserved and then complete raw intakes were frozen before replay.',
 'final_matrix':{'M2_scenarios':11,'T2_scenarios':11,'intake_rejections':4,'successful_detached_results':18,'tamper_rejections':6,'missing_detached_original_rejections':2},
 'findings':[
 {'id':'M2-optional-metric-dependency','severity':'P2','input':'M2-original.json','actual':'minutes_per_completed_review=null when analyst_minutes=240 and completed_reviews=4, because total_cost is unknown. Symmetric cost-only intake also yields null cost despite cost120.5 and reviews4.','expected':'Minutes60 survives unknown cost; USD gross cost30.125 survives unknown time. Unknowns withhold only dependent measures.','paired_input':'M2-cost-supported-time-unknown.json'},
 {'id':'T2-known-missing-exhibit-classification','severity':'P2-review-needed','input':'T2-scoped-exhibit-missing.json','actual':'Required exhibit availability is exact-source false. Evidence-completeness result is unknown; all5 case-A criteria unknown and fail count0, while mechanical exception is retained.','expected':'Known required-exhibit absence supports a known evidence-completeness failure; dependent chronology/reasoning may remain unknown. Preserve the known exception rather than classifying the absence itself as unknown.','limit':'Exception is visible in mechanical_exceptions and the favorable threshold is correctly withheld; classification of the known evidence-completeness failure is the concern.'}],
 'supported_observations':'M2 detection5 known /2detected, coverage5/6, eligible sample TP/FP/FN/TN1each and precision/recall1/2; unknown label/observation/leakage/independence block dependent sample measures; unknown material technology requirement blocks criterion but retains sample facts; exact threshold >0.5 fails. T2 complete intake10pass/2cases; chronology and counterevidence/tool mismatches become fail despite suppliedpass; partial cases excluded from denominator; unsupported professional mandate never issues assurance; context/access reject.',
 'verification':verification,'scope_limit':'Native deterministic behavior only. No real-model activation/routing, source authentication, actual human acceptance, engine/source truth, legal sufficiency, statistical population inference or independent assurance.'}
(base/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'final_scenarios':22,'detached_results':18,'tamper_and_missing_original_rejections':sum(v['rejected'] for v in verification),'findings':len(summary['findings'])}))
