#!/usr/bin/env python3
"""Execute affected packages' declared checks from isolated temporary installations."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def check_package(relative):
    source=ROOT/relative
    results=[]
    with tempfile.TemporaryDirectory(prefix='fsi-investment-portable-') as directory:
        package=Path(directory)/source.name
        shutil.copytree(source,package,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        spec=json.loads((package/'evals/evals.json').read_text())
        env=dict(os.environ);env.pop('PYTHONPATH',None);env['PYTHONDONTWRITEBYTECODE']='1'
        for case in spec['evals']:
            if not case.get('command') or 'expect_exit' not in case:continue
            try:
                run=subprocess.run(case['command'],shell=True,cwd=package,env=env,
                                   capture_output=True,text=True,timeout=60)
                output=run.stdout+run.stderr
                passed=run.returncode==case['expect_exit'] and all(s in output for s in case.get('expect_contains',[]))
                result={'id':case['id'],'passed':passed,'exit':run.returncode,'expected_exit':case['expect_exit']}
                if not passed:result['output']=output[-6000:]
            except subprocess.TimeoutExpired:
                result={'id':case['id'],'passed':False,'error':'isolated command timeout'}
            results.append(result)
    return {'package':relative,'checks':results,'passed':bool(results) and all(r['passed'] for r in results)}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    moves=json.loads((ROOT/'catalog/asset-management-migrations.json').read_text())['migrations']
    phase2=json.loads((ROOT/'catalog/asset-management-phase2-capabilities.json').read_text())
    phase3=json.loads((ROOT/'catalog/asset-management-phase3-capabilities.json').read_text())
    phase4=json.loads((ROOT/'catalog/asset-management-phase4-capabilities.json').read_text())
    packages=sorted({r['new_path'] for r in moves}|{row['path'] for row in phase2['new_packages'].values()}|{row['path'] for row in phase3['new_packages'].values()}|{row['path'] for row in phase4['new_packages'].values()}|{'skills/asset-management/asset-management-router'})
    with ThreadPoolExecutor(max_workers=4) as executor:results=list(executor.map(check_package,packages))
    report={'scope':'Isolated offline package commands; not professional/source/deployment acceptance',
            'packages':len(results),'checks':sum(len(r['checks']) for r in results),
            'passed':all(r['passed'] for r in results),'results':results}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    for r in results:
        if not r['passed']:print(json.dumps(r,indent=2))
    print(f"Portable investment packages: {report['packages']} packages, {report['checks']} checks, "+('PASS' if report['passed'] else 'FAIL'))
    return int(not report['passed'])

if __name__=='__main__':raise SystemExit(main())
