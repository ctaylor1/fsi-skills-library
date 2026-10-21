#!/usr/bin/env python3
"""Run nonempty positive/negative eval inventories from isolated package copies."""
import argparse, json, os, shlex, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run():
    doc=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text())
    rows=[r for r in doc['capabilities'] if r['support_status']!='planned']+doc['retained_legacy']+doc['shared_owners']
    results=[]; errors=[]
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
    env['PYTHONDONTWRITEBYTECODE']='1'
    with tempfile.TemporaryDirectory(prefix='ir-phase1-portable-') as tmp:
        for row in rows:
            path=Path(tmp)/row['name']; shutil.copytree(ROOT/row['path'],path,ignore=shutil.ignore_patterns('__pycache__','.DS_Store','*.pyc'))
            spec=json.loads((path/'evals/evals.json').read_text())
            checks=[c for c in spec.get('evals',[]) if c.get('command') and 'expect_exit' in c]
            if not checks or not any(c['expect_exit'] for c in checks):errors.append(row['name']+': missing executable checks');continue
            for c in checks:
                command=shlex.split(c['command'])
                if not command or command[0] not in {'python','python3'}:
                    raise ValueError('portable command must use a direct Python entrypoint: '+row['name'])
                command[0]=sys.executable
                proc=subprocess.run(command,cwd=path,capture_output=True,text=True,env=env,timeout=60)
                output=proc.stdout+proc.stderr
                ok=proc.returncode==c['expect_exit'] and all(x in output for x in c.get('expect_contains',[]))
                # A traceback/missing dependency is never acceptable negative evidence.
                ok=ok and not any(s in output for s in ('Traceback (most recent call last)','ModuleNotFoundError','No such file or directory'))
                results.append({'skill':row['name'],'check':c['id'],'expected_exit':c['expect_exit'],'exit':proc.returncode,'passed':ok})
                if not ok:errors.append(row['name']+'/'+c['id']+': '+output[:1800])
    return {'schema_version':'ir-portable-evidence/1.0','python':sys.version,'interpreter':sys.executable,'packages':len(rows),'checks':len(results),'passed':sum(r['passed'] for r in results),'results':results,'errors':errors,'professional_acceptance':'not-established'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path);args=p.parse_args()
    report=run()
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
    raise SystemExit(bool(report['errors']))
