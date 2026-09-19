import hashlib,json,os,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path("/Users/taylor/DevRepo/Skills/fsi-skills-library")
OUT=Path("/tmp/payments-phase2-routing-forward")
PROMPT=Path("/Users/taylor/.codex/attachments/1010ab0a-480a-43a9-a569-652ade106553/pasted-text.txt")
choices=json.loads((OUT/"choices.json").read_text())
section=PROMPT.read_text().split("### 8. Evaluate routing and composability",1)[1].split("### 9.",1)[0]
requests=[line[2:].strip() for line in section.splitlines() if line.startswith("- ")]
assert len(requests)==len(choices)==18
inventory=sorted({p.parent.name for p in (ROOT/"skills").glob("*/*/SKILL.md")})
(OUT/"installed-inventory.json").write_text(json.dumps(inventory,indent=2)+"\n")
source_files=[PROMPT,ROOT/"skills/payments/payments-router/references/routes.json",
              ROOT/"skills/payments/payments-router/scripts/route.py",
              ROOT/"skills/payments/payments-router/scripts/payment_contract.py",
              ROOT/"skills/payments/bank-payment-workflow-designer/references/rail-profiles.json"]
source_files+=sorted((ROOT/"skills/payments").glob("*/SKILL.md"))
def hashes():
 return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
before=hashes()
(OUT/"source-hashes-before.json").write_text(json.dumps(before,indent=2)+"\n")
env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}
results=[]
for i,(request,decision) in enumerate(zip(requests,choices),1):
 case=OUT/f"case-{i:02d}";case.mkdir(exist_ok=True)
 (case/"request.txt").write_text(request+"\n")
 (case/"decision.json").write_text(json.dumps(decision,indent=2)+"\n")
 inp={"intent":decision["intent"],"requested_action":decision["action"],"available_skills":inventory}
 for key in ("participant","rail"):
  if decision.get(key):inp[key]=decision[key]
 (case/"input.json").write_text(json.dumps(inp,indent=2)+"\n")
 commands=[]
 cmd=["python3","-B",str(ROOT/"skills/payments/payments-router/scripts/route.py"),str(case/"input.json")]
 proc=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True)
 (case/"native-output.json").write_text(proc.stdout)
 (case/"route.stderr.txt").write_text(proc.stderr)
 commands.append({"argv":cmd,"shell":shlex.join(cmd),"cwd":str(ROOT),"environment_overrides":{"PYTHONDONTWRITEBYTECODE":"1"},"exit_code":proc.returncode})
 native=json.loads(proc.stdout) if proc.returncode==0 else None
 vcmd=["python3","-B",str(ROOT/"skills/payments/payments-router/scripts/route.py"),"--validate",str(case/"native-output.json")]
 vproc=subprocess.run(vcmd,cwd=ROOT,env=env,text=True,capture_output=True)
 (case/"validate.stdout.txt").write_text(vproc.stdout)
 (case/"validate.stderr.txt").write_text(vproc.stderr)
 commands.append({"argv":vcmd,"shell":shlex.join(vcmd),"cwd":str(ROOT),"environment_overrides":{"PYTHONDONTWRITEBYTECODE":"1"},"exit_code":vproc.returncode})
 record={"case_id":f"case-{i:02d}","request":request,"intent_selection":decision,"input":inp,
         "commands":commands,"native_output":native,"route_exit":proc.returncode,"validation_exit":vproc.returncode}
 (case/"record.json").write_text(json.dumps(record,indent=2)+"\n")
 results.append(record)
 print(json.dumps({"case":i,"intent":decision["intent"],"exit":proc.returncode,"validation_exit":vproc.returncode,"native":native},ensure_ascii=False))
after=hashes()
(OUT/"source-hashes-after.json").write_text(json.dumps(after,indent=2)+"\n")
(OUT/"results.json").write_text(json.dumps({"run_at":datetime.now(timezone.utc).isoformat(),"scope":"Independent agent intent selection and structured routing only; not target task quality or professional acceptance.","excluded_materials":["evals/evals.json","test_routing.py","prior evaluation artifacts"],"source_hashes_unchanged":before==after,"cases":results},indent=2)+"\n")
