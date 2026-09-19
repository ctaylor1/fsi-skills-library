from pathlib import Path
import json, subprocess, shlex, hashlib, datetime
from decimal import Decimal, localcontext

ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT=Path('/tmp/insurance-p2-forward-claims')
PYTHON='/tmp/fsi-p0-venv/bin/python'
skills=json.loads((OUT/'design-lock.json').read_text())['skills']
summary=[]
for skill in skills:
    case=OUT/skill
    commands=[]
    for script,input_name,output_name in [('validate_input.py','input.json','validate_input.json'),('calculate_or_transform.py','input.json','output.json'),('validate_output.py','output.json','validate_output.json')]:
        command=[PYTHON,str(ROOT/'skills/insurance'/skill/'scripts'/script),str(case/input_name)]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        (case/output_name).write_text(result.stdout)
        commands.append({'command':shlex.join(command),'cwd':str(ROOT),'exit_code':result.returncode,'stdout_file':str(case/output_name),'stdout':result.stdout if script!='calculate_or_transform.py' else '(Full unmodified stdout in output.json)','stderr':result.stderr})
    (case/'execution-log.json').write_text(json.dumps(commands,indent=2)+'\n')
    before=json.loads((case/'implementation-source-hashes.json').read_text())
    changed=[p for p,v in before.items() if hashlib.sha256((ROOT/'skills/insurance'/skill/p).read_bytes()).hexdigest()!=v]
    output=json.loads((case/'output.json').read_text())
    summary.append({'skill':skill,'exit_codes':[c['exit_code'] for c in commands],'source_changes_during_execution':changed,'status':output.get('status'),'completeness':output.get('completeness'),'evaluability':output.get('evaluability'),'findings':output.get('findings'),'results':output.get('results')})
(OUT/'run-summary.json').write_text(json.dumps(summary,indent=2)+'\n')

# Arithmetic independently rederived from the raw source numbers, not imported
# from native inputs or skill implementations. Rounded only for comparison.
D=Decimal
with localcontext() as context:
    context.prec=38
    adjusted=(D('4875000')*D('1.075')*D('1.025'))/D('3900')
    prospective=(D('2940000')*D('1.09'))/D('3900')
    blended=(D('0.65')*prospective)+(D('0.35')*D('875'))
    indicated=(blended+D('128')+D('62')+D('41'))/D('0.720')
    change=indicated/adjusted-D('1')
    rate={'current_adjusted_premium_per_exposure':adjusted,'experience_loss_lae_per_exposure':prospective,'credibility_blended_loss_lae_per_exposure':blended,'indicated_premium_per_exposure':indicated,'indicated_change':change}
    native=json.loads((OUT/'pc-rate-adequacy-analyzer/output.json').read_text())['results']
    rate_check={k:{'independent_exact_decimal':str(v),'six_place_expected':str(v.quantize(D('.000001'))),'native':native[k],'matches':v.quantize(D('.000001'))==D(native[k])} for k,v in rate.items()}
    positions={'reported_incurred_indemnity':D('18450.75')+D('41800'),'reported_incurred_expense':D('2175.25')+D('6400')}
    repair={'projected_gross_total_indemnity':D('18450.75')+D('36920.50'),'projected_gross_total_expense':D('2175.25')+D('5150'),'proposed_change_in_case_indemnity':D('36920.50')-D('41800'),'proposed_change_in_case_expense':D('5150')-D('6400'),'net_scenario_total':D('18450.75')+D('36920.50')+D('2175.25')+D('5150')-D('4500')}
    contested={'projected_gross_total_indemnity':str(D('18450.75')+D('52600')),'projected_gross_total_expense':str(D('2175.25')+D('11200')),'proposed_change_in_case_indemnity':str(D('52600')-D('41800')),'proposed_change_in_case_expense':str(D('11200')-D('6400')),'net_scenario_total':None,'note':'Known gross/case values can be independently computed, but helper suppresses this whole scenario because recovery is unknown. No zero recovery is assumed.'}
    native_fin=json.loads((OUT/'claim-financial-evaluation-assistant/output.json').read_text())['results']
    fin_check={'position':{k:{'expected':str(v),'native':native_fin['current_position'][k],'matches':D(native_fin['current_position'][k])==v} for k,v in positions.items()},'repair':{k:{'expected':str(v),'native':native_fin['scenarios'][0][k],'matches':D(native_fin['scenarios'][0][k])==v} for k,v in repair.items()},'contested_independent_known_amounts':contested}
    result={'method':'Independent Decimal arithmetic sourced from frozen raw source statements; no native imports; explicit expected values only after scenario design locked.','rate':rate_check,'financial':fin_check,'payment_independent':{'final':'28460.25','initial':'18450.75','total_settled':str(D('28460.25')+D('18450.75')),'remaining_authority_for_final':str(D('35000')-D('28460.25')),'repeat_payment_expected':'blocked','closure_expected':'blocked until reopening owner/routing is supplied'}}
    (OUT/'independent-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['skill','exit_codes','source_changes_during_execution','status','completeness','evaluability']} for r in summary],indent=2))
print('Independent arithmetic matches:',all(x['matches'] for x in rate_check.values()),all(x['matches'] for x in fin_check['repair'].values()))
