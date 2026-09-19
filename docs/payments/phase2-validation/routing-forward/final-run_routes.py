import hashlib,json,os,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path("/Users/taylor/DevRepo/Skills/fsi-skills-library")
OUT=Path("/tmp/payments-phase2-routing-forward")
original=json.loads((OUT/"results.json").read_text())
source_paths=list(json.loads((OUT/"source-hashes-before.json").read_text()))
source_paths+=list(json.loads((OUT/"additional-support-source-hashes.json").read_text()))
def hashes():
 return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(set(source_paths))}
before=hashes()
(OUT/"final-source-hashes-before.json").write_text(json.dumps(before,indent=2)+"\n")
for p in before:
 path=Path(p)
 relative=path.relative_to(ROOT) if path.is_relative_to(ROOT) else Path("original-request.txt")
 target=OUT/"final-source-snapshots"/relative
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(path.read_bytes())
cases=[{"case_id":"final-"+c["case_id"],"original_case":c["case_id"],"request":c["request"],
        "input":c["input"],"selection":c["intent_selection"],"variant":False} for c in original["cases"]]
for participant in ("merchant","bank","issuer"):
 original14=original["cases"][13]
 inp={**original14["input"],"participant":participant}
 cases.append({"case_id":"final-orchestration-"+participant,"original_case":"case-14","request":original14["request"],
               "clarification":"The participant is "+participant+".","input":inp,"variant":True,
               "expected_lead":"merchant-acceptance-strategy-designer" if participant=="merchant" else "payment-platform-architecture-reviewer"})
env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}
results=[]
for case in cases:
 folder=OUT/case["case_id"];folder.mkdir(exist_ok=True)
 (folder/"request.txt").write_text(case["request"]+"\n"+case.get("clarification","")+"\n")
 (folder/"input.json").write_text(json.dumps(case["input"],indent=2)+"\n")
 commands=[]
 for operation,args,stdout,stderr in (
  ("route",[str(folder/"input.json")],"native-output.json","route.stderr.txt"),
  ("validate",["--validate",str(folder/"native-output.json")],"validate.stdout.txt","validate.stderr.txt")):
  cmd=["python3","-B",str(ROOT/"skills/payments/payments-router/scripts/route.py")]+args
  proc=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True)
  (folder/stdout).write_text(proc.stdout);(folder/stderr).write_text(proc.stderr)
  commands.append({"operation":operation,"argv":cmd,"shell":shlex.join(cmd),"cwd":str(ROOT),
                   "environment_overrides":{"PYTHONDONTWRITEBYTECODE":"1"},"exit_code":proc.returncode})
 native=json.loads((folder/"native-output.json").read_text()) if commands[0]["exit_code"]==0 else None
 record={**case,"commands":commands,"native_output":native}
 (folder/"record.json").write_text(json.dumps(record,indent=2)+"\n")
 results.append(record)
 print(json.dumps({"case":case["case_id"],"status":native["status"],"lead":native["lead_skill"],
                   "support":native["supporting_skills"],"missing":native["missing_context"],
                   "route_exit":commands[0]["exit_code"],"validation_exit":commands[1]["exit_code"]}))
after=hashes()
(OUT/"final-source-hashes-after.json").write_text(json.dumps(after,indent=2)+"\n")
summary={"run_at":datetime.now(timezone.utc).isoformat(),"scope":"Unchanged 18 natural-language requests plus three explicit-role orchestration variants. Structured routing only; not target task or professional acceptance.",
         "source_hashes_unchanged":before==after,"original_inputs_unchanged":all(results[i]["input"]==original["cases"][i]["input"] for i in range(18)),"cases":results}
(OUT/"final-results.json").write_text(json.dumps(summary,indent=2)+"\n")
