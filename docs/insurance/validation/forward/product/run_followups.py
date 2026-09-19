from pathlib import Path
import json,subprocess,sys
ROOT=Path('/tmp/insurance-product-forward-20260918');PYTHON='/tmp/fsi-p0-venv/bin/python'
variants=[]
q=json.loads((ROOT/'cases/02-mixed-currency-quotes/input.json').read_text())
for row in q['quotes']:
 row['currency']='USD';row['coverages'][0]['limit']=None
variants.append(('05-unavailable-quote-limits','premium-quote-comparator',q,'Compare annual property quotes A USD 1,000 and B USD 900 with identical USD 1,000 deductibles. Both quote extracts omit the building limit; their actual limits are unknown. Same source date and term. Show what is comparable and what remains missing.','Both missing limits are represented by null; all currencies are USD.'))
r=json.loads((ROOT/'cases/04-ceded-illustration/input.json').read_text())
r['layer']['layer_premium']=0
r['clauses'][2]['text']='One reinstatement restores erosion pro rata as to amount at 100 percent of the zero layer premium, with no time adjustment. The specified layer premium is USD 0.'
variants.append(('06-zero-premium-reinstatement','reinsurance-treaty-interpreter',r,'Illustrate the same eligible USD 12m loss in a USD 10m excess USD 5m layer, USD 20m aggregate, one reinstatement restoring erosion pro rata as to amount. The supplied contract expressly sets the base layer premium to USD 0; reinstatement premium is 100% pro rata by amount with no time adjustment. Explain restoration separately from the premium charge.','Only the expressly supplied base premium and matching synthetic wording change from case04. Zero is permitted by the native nonnegative-premium validator.'))
p=json.loads((ROOT/'cases/01-paid-reserving/input.json').read_text())
p['large_loss_threshold']=100
variants.append(('07-no-large-loss-schedule','reserving-analysis-assistant',p,'Develop this aggregate paid triangle and assess whether losses of USD 100,000 or more distort it. The unit is USD thousands and the large-loss threshold is 100. Only aggregate triangle values are supplied; no claim-level large-loss schedule or count is available.','No large_losses field is supplied; it is unavailable, not an explicitly complete empty schedule.'))
for name,pkg,doc,request,adapt in variants:
 d=ROOT/'cases'/name;d.mkdir(exist_ok=True)
 (d/'input.json').write_text(json.dumps(doc,indent=2)+'\n');(d/'raw-request.md').write_text(request+'\n');(d/'input-adaptation.md').write_text(adapt+'\n')
 logs=[]
 for stage,script,inp in [('input-validation','validate_input.py','input.json'),('calculation','calculate_or_transform.py','input.json')]:
  args=[PYTHON,str(ROOT/pkg/'scripts'/script),str(d/inp)];res=subprocess.run(args,capture_output=True,text=True)
  (d/(stage+'.stdout.txt')).write_text(res.stdout);(d/(stage+'.stderr.txt')).write_text(res.stderr)
  logs.append({'stage':stage,'command':args,'exit_code':res.returncode})
  if stage=='calculation' and res.returncode==0:
   out=json.JSONDecoder().raw_decode(res.stdout)[0];(d/'native-output.json').write_text(json.dumps(out,indent=2)+'\n')
 if pkg=='reinsurance-treaty-interpreter':
  out['narrative']='Illustrative arithmetic under the supplied reviewed assumptions: ceded amount USD 7,000,000 and remaining aggregate USD 13,000,000. The native result reports reinstated amount USD 0 and reinstatement premium USD 0. The contract supplies one reinstatement despite the zero premium; the zero restoration is a calculation defect, so this native result is not accepted for professional use.'
  for c in out['clauses']: c['plain_summary']='The supplied wording states: '+c['source_text']
  sys.path.insert(0,str(ROOT/pkg/'scripts'));from insurance_contract import build_artifact;sys.path.pop(0)
  a=out['artifact'];out['artifact']=build_artifact(doc,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
 else:
  out['narrative']='Evaluation-only native output. The limitations and disposition are documented in findings.md; no unsupported comparative or large-loss conclusion is adopted.'
  sys.path.insert(0,str(ROOT/pkg/'scripts'));from insurance_contract import build_artifact;sys.path.pop(0)
  a=out['artifact'];out['artifact']=build_artifact(doc,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
 (d/'final-output.json').write_text(json.dumps(out,indent=2)+'\n')
 args=[PYTHON,str(ROOT/pkg/'scripts/validate_output.py'),str(d/'final-output.json')];res=subprocess.run(args,capture_output=True,text=True)
 (d/'final-output-validation.stdout.txt').write_text(res.stdout);(d/'final-output-validation.stderr.txt').write_text(res.stderr);logs.append({'stage':'final-output-validation','command':args,'exit_code':res.returncode})
 (d/'run-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if name.startswith('05'): result={k:out[k] for k in ['cost_comparison_status','lowest_annualized_total_cost_quote_id','cost_spread','comparability_flags']}
 elif name.startswith('06'): result=out['recovery_illustration']['occurrences'][0]
 else: result={'large_loss':out['segments'][0]['large_loss'],'artifact_completeness':out['artifact']['completeness']}
 print(name,json.dumps(result),res.stdout)
