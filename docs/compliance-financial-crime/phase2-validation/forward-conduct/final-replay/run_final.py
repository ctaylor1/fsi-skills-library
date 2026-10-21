"""Invoke installed repaired CLIs and preserve outputs/commands under final-replay only."""
import hashlib,json,shlex,subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent;BASE=OUT.parent;ROOT=OUT.parents[4]
manifest=json.loads((OUT/"pre-run-manifest.json").read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n")
def invoke(folder,stage,argv):
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
    (folder/(stage+".stdout.txt")).write_text(p.stdout);(folder/(stage+".stderr.txt")).write_text(p.stderr)
    return {"stage":stage,"argv":argv,"shell_replay":shlex.join(argv),"cwd":str(ROOT),"exit_code":p.returncode}
def run(case):
    folder=OUT/case["case"]
    if (folder/"run-record.json").exists():raise RuntimeError("Refusing to overwrite original final replay outputs")
    if sha(folder/"input.json")!=case["input_sha256"] or sha(folder/"pre-run-expectations.json")!=case["expectations_sha256"]:raise RuntimeError("Frozen intake or expectations changed")
    scripts=ROOT/"skills"/"compliance-financial-crime"/case["skill"]/"scripts"
    calls=[invoke(folder,"validate-input",["python3","-B",str(scripts/"validate_input.py"),str(folder/"input.json")]),invoke(folder,"calculate",["python3","-B",str(scripts/"calculate_or_transform.py"),str(folder/"input.json")])]
    (folder/"output.json").write_bytes((folder/"calculate.stdout.txt").read_bytes())
    calls.append(invoke(folder,"validate-output",["python3","-B",str(scripts/"validate_output.py"),str(folder/"output.json"),"--input",str(folder/"input.json")]))
    record={**case,"calls":calls,"output_sha256":sha(folder/"output.json")};dump(folder/"run-record.json",record);return record
with ThreadPoolExecutor(max_workers=4) as pool:runs=list(pool.map(run,manifest["cases"]))
tamper=[]
for name in ["ib-realistic","abc-realistic-corrected","misconduct-realistic","customer-realistic-units-amended-exact-decimal"]:
    folder=OUT/name;case=next(c for c in manifest["cases"] if c["case"]==name);scripts=ROOT/"skills"/"compliance-financial-crime"/case["skill"]/"scripts"
    doc=json.loads((folder/"output.json").read_text());doc.update({"approval":"approved","action_taken":True,"unsupported_narrative":"Legal acceptance is complete; execute now."});dump(folder/"edited-output.json",doc)
    tamper.append({"case":name,**invoke(folder,"validate-edited-output",["python3","-B",str(scripts/"validate_output.py"),str(folder/"edited-output.json"),"--input",str(folder/"input.json")]),"edited_output_sha256":sha(folder/"edited-output.json")})
# Test exact decimal edit with both parsed/output string type unchanged, against the detached exact original.
name="customer-long-decimal-threshold-exact-decimal";folder=OUT/name;scripts=ROOT/"skills"/"compliance-financial-crime"/"customer-conduct-outcomes-reviewer"/"scripts"
changed=json.loads((folder/"output.json").read_text());changed["results"]["cohort_metrics"][0]["evidence"]["threshold_rate"]="0.3333333333333333";changed["results"]["cohort_metrics"][0]["within_supplied_harm_criterion"]=False;dump(folder/"edited-decimal-output.json",changed)
tamper.append({"case":name,**invoke(folder,"validate-edited-decimal-output",["python3","-B",str(scripts/"validate_output.py"),str(folder/"edited-decimal-output.json"),"--input",str(folder/"input.json")]),"edited_output_sha256":sha(folder/"edited-decimal-output.json")})
drift=[p for files in manifest["frozen_runtime_and_instruction_sha256"].values() for p,h in files.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
prior_drift=[p for p,h in manifest["prior_evidence_file_sha256"].items() if not (BASE/p).exists() or sha(BASE/p)!=h]
record={"completed_at_utc":datetime.now(timezone.utc).isoformat(),"cases":runs,"tamper_checks":tamper,"runtime_or_instruction_drift":drift,"prior_evidence_files_changed":prior_drift,"runtime_and_instruction_sha256_after":{skill:{p:sha(ROOT/p) for p in files} for skill,files in manifest["frozen_runtime_and_instruction_sha256"].items()}}
dump(OUT/"run-manifest.json",record)
print(json.dumps({"case_exit_codes":{r["case"]:[c["exit_code"] for c in r["calls"]] for r in runs},"tamper_exit_codes":[r["exit_code"] for r in tamper],"package_drift":drift,"prior_evidence_changed":prior_drift},indent=2))
