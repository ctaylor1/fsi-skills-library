"""Execute repository-format native CLI evaluations without a shell."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
base=Path(__file__).resolve().parents[1]
cases=json.loads((base/'evals/evals.json').read_text())['evals']
results=[]
for case in cases:
    command=shlex.split(case['command'])
    if command[0]=='python3': command[0]=sys.executable
    proc=subprocess.run(command,cwd=base,capture_output=True,text=True)
    combined=proc.stdout+proc.stderr
    passed=proc.returncode==case['expect_exit'] and all(text in combined for text in case['expect_contains'])
    results.append({'id':case['id'],'passed':passed,'actual_exit':proc.returncode,'expect_exit':case['expect_exit']})
    if not passed: print(combined,file=sys.stderr)
print(json.dumps({'skill':base.name,'evaluations':results,'passed':sum(r['passed'] for r in results),'total':len(results),'scope':'Native synthetic checks only'},indent=2))
raise SystemExit(any(not r['passed'] for r in results))
