from pathlib import Path
import json,hashlib,datetime,subprocess,shlex
R=Path('/tmp/insurance-p3-forward-analytics');repo=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');py='/tmp/fsi-p0-venv/bin/python';records=[]
for name in ['insurance-premium-audit-reviewer','insurance-producer-compensation-reconciler']:
 p=R/name;d=json.loads((p/'native-input.json').read_text())
 if name=='insurance-premium-audit-reviewer':
  for row in d['data']['exposures']:row['basis_record_id']=row['exposure_id']
  changes={'data.exposures[0].basis_record_id':'PAY-W','data.exposures[1].basis_record_id':'PAY-O'};evidence='raw/payroll.md §1 already identifies warehouse record PAY-W and office record PAY-O as separate non-overlapping source records.'
 else:
  d['data']['events'][-1]['chargeback_basis']='Agreement AG7 clause7: specified premium-refund trigger evidenced2026-09-04 authorizes25% reversal of E1.'
  changes={'data.events[2].chargeback_basis':d['data']['events'][-1]['chargeback_basis']};evidence='raw/agreement.md §2 and raw/events.md §2 already provide clause7, trigger, E1 linkage, date and fraction.'
 inp=p/'native-input-mapping-supplement.json';inp.write_text(json.dumps(d,indent=2)+'\n');note={'reason':'Concurrent schema/interface change observed after docs-first case freeze: original docs as read lacked explicit field names; original runs safely withheld totals. Original raw facts, requests and expected arithmetic unchanged. No original evidence or input overwritten.','evidence':evidence,'only_added_fields':changes,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_sha256':hashlib.sha256(inp.read_bytes()).hexdigest()};(p/'mapping-supplement.json').write_text(json.dumps(note,indent=2)+'\n')
 rd=p/'mapping-replay';rd.mkdir(exist_ok=True);hashes={}
 for f in (repo/'skills/insurance'/name/'scripts').glob('*.py'):
  if not f.name.startswith('test_'):hashes[str(f.relative_to(repo))]=hashlib.sha256(f.read_bytes()).hexdigest()
 (rd/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
 for phase,script,ip in [('input','validate_input.py',inp),('calculate','calculate_or_transform.py',inp),('output','validate_output.py',rd/'result.json')]:
  argv=[py,str(repo/'skills/insurance'/name/'scripts'/script),str(ip)];run=subprocess.run(argv,cwd=repo,capture_output=True,text=True)
  (rd/f'{phase}.stdout').write_text(run.stdout);(rd/f'{phase}.stderr').write_text(run.stderr)
  records.append({'skill':name,'phase':phase,'argv':argv,'command':shlex.join(argv),'exit':run.returncode,'stdout':str(rd/f'{phase}.stdout'),'stderr':str(rd/f'{phase}.stderr')})
  if phase=='calculate' and not run.returncode:(rd/'result.json').write_text(run.stdout)
  print(name,phase,run.returncode)
  if run.returncode:print(run.stdout,run.stderr);break
(R/'mapping-replay-executions.json').write_text(json.dumps(records,indent=2)+'\n')
