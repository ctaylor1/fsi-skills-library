"""Run current installed CLIs without changing any initial evidence."""
from __future__ import annotations
import hashlib,json,shlex,subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent; BASE=OUT.parent; ROOT=OUT.parents[4]
manifest=json.loads((OUT/"pre-run-manifest.json").read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n")
def invoke(folder,stage,argv):
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,check=False)
    (folder/(stage+".stdout.txt")).write_text(p.stdout); (folder/(stage+".stderr.txt")).write_text(p.stderr)
    return {"stage":stage,"argv":argv,"shell_replay":shlex.join(argv),"cwd":str(ROOT),"exit_code":p.returncode,"stdout_file":str(folder/(stage+".stdout.txt")),"stderr_file":str(folder/(stage+".stderr.txt"))}
def run_case(case):
    folder=OUT/case["case"]
    if (folder/"run-record.json").exists(): raise RuntimeError("Refusing to overwrite replay originals")
    if sha(folder/"input.json")!=case["input_sha256"] or sha(folder/"pre-run-expectations.json")!=case["expectations_sha256"]: raise RuntimeError("Frozen replay intake/expectations changed")
    scripts=ROOT/"skills"/"compliance-financial-crime"/case["skill"]/"scripts"
    calls=[invoke(folder,"validate-input",["python3","-B",str(scripts/"validate_input.py"),str(folder/"input.json")]),invoke(folder,"calculate",["python3","-B",str(scripts/"calculate_or_transform.py"),str(folder/"input.json")])]
    (folder/"output.json").write_bytes((folder/"calculate.stdout.txt").read_bytes())
    calls.append(invoke(folder,"validate-output",["python3","-B",str(scripts/"validate_output.py"),str(folder/"output.json"),"--input",str(folder/"input.json")]))
    r={**case,"calls":calls,"output_sha256":sha(folder/"output.json")}
    dump(folder/"run-record.json",r); return r
with ThreadPoolExecutor(max_workers=4) as pool: runs=list(pool.map(run_case,manifest["cases"]))
edited=[]
for name in ["ib-realistic","abc-realistic-corrected","misconduct-realistic","customer-realistic-units-amended"]:
    folder=OUT/name; case=next(c for c in manifest["cases"] if c["case"]==name)
    doc=json.loads((folder/"output.json").read_text()); doc.update({"approval":"approved","action_taken":True,"unsupported_narrative":"All legal checks passed; execute now."})
    target=folder/"edited-output.json"; dump(target,doc)
    scripts=ROOT/"skills"/"compliance-financial-crime"/case["skill"]/"scripts"
    edited.append({"case":name,**invoke(folder,"validate-edited-output",["python3","-B",str(scripts/"validate_output.py"),str(target),"--input",str(folder/"input.json")]),"edited_sha256":sha(target)})
historical=[]
oldmanifest=json.loads((BASE/"pre-run-manifest.json").read_text())
for name,skill in [("ib-partial-known-mismatch","information-barrier-reviewer"),("ib-access-with-list-proposal","information-barrier-reviewer"),("customer-unit-mismatch","customer-conduct-outcomes-reviewer")]:
    folder=OUT/"historical-snapshot-reconstruction"/name; folder.mkdir(parents=True,exist_ok=False)
    scripts=ROOT/"docs"/"compliance-financial-crime"/"phase2-validation"/"initial-implementation"/skill
    source_hash_match=all(sha(scripts/filename)==oldmanifest["pre_run_package_file_sha256"][skill]["skills/compliance-financial-crime/"+skill+"/scripts/"+filename] for filename in ["domain.py","foundation_contract.py","native_integrity.py","calculate_or_transform.py","validate_input.py","validate_output.py"])
    inp=BASE/name/"original-input.json"
    calls=[invoke(folder,"validate-input",["python3","-B",str(scripts/"validate_input.py"),str(inp)]),invoke(folder,"calculate",["python3","-B",str(scripts/"calculate_or_transform.py"),str(inp)])]
    (folder/"output.json").write_bytes((folder/"calculate.stdout.txt").read_bytes())
    calls.append(invoke(folder,"validate-output",["python3","-B",str(scripts/"validate_output.py"),str(folder/"output.json"),"--input",str(inp)]))
    historical.append({"case":name,"source_snapshot_matches_initial_hashes":source_hash_match,"calls":calls,"reconstructed_output_sha256":sha(folder/"output.json"),"original_output_sha256":sha(BASE/name/"original-output.json"),"original_output_bytes_reconstructed":(folder/"output.json").read_bytes()==(BASE/name/"original-output.json").read_bytes()})
drift=[path for files in manifest["current_package_sha256"].values() for path,digest in files.items() if not (ROOT/path).exists() or sha(ROOT/path)!=digest]
initial_drift=[path for path,digest in manifest["initial_artifact_sha256"].items() if not (BASE/path).exists() or sha(BASE/path)!=digest]
record={"completed_at_utc":datetime.now(timezone.utc).isoformat(),"cases":runs,"edited_output_checks":edited,"historical_snapshot_reconstruction":historical,"current_package_drift_during_replay":drift,"initial_evidence_files_changed":initial_drift}
dump(OUT/"run-manifest.json",record)
print(json.dumps({"case_exit_codes":{r["case"]:[c["exit_code"] for c in r["calls"]] for r in runs},"tamper_exit_codes":[c["exit_code"] for c in edited],"historical_reconstructed":[c["original_output_bytes_reconstructed"] for c in historical],"initial_evidence_changed":initial_drift,"package_drift":drift},indent=2))
