"""Execute the standard package evaluation contract without shell interpolation."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
from domain import compute
ROOT=Path(__file__).resolve().parents[1]
fixtures=ROOT/'evals/files'
for suffix in ('golden','partial'):
    input_name='input_complete' if suffix=='golden' else 'input_partial'
    assert compute(json.loads((fixtures/(input_name+'.json')).read_text())) == json.loads((fixtures/('output_'+suffix+'.json')).read_text()), 'frozen native result differs: '+suffix
runs=[]
for evaluation in json.loads((ROOT/'evals/evals.json').read_text())['evals']:
    args=shlex.split(evaluation['command'])
    if args[0]=='python3': args[0]=sys.executable
    run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
    combined=run.stdout+run.stderr
    passed=run.returncode==evaluation['expect_exit'] and all(s in combined for s in evaluation['expect_contains'])
    runs.append({'id':evaluation['id'],'actual_exit':run.returncode,'passed':passed})
    if not passed:
        print(json.dumps(runs,indent=2))
        print(combined)
        raise SystemExit(1)
print(json.dumps({'passed':len(runs),'failed':0,'evaluations':runs},indent=2))
