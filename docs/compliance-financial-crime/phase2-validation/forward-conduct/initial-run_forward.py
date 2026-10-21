"""Replay actual installed CLIs; retain every original output/error and exact argv."""
from __future__ import annotations
import hashlib
import json
import platform
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
manifest = json.loads((OUT / "pre-run-manifest.json").read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def invoke(case_dir, stage, argv):
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False)
    (case_dir / (stage + ".stdout.txt")).write_text(completed.stdout)
    (case_dir / (stage + ".stderr.txt")).write_text(completed.stderr)
    return {"stage":stage,"argv":argv,"shell_replay":shlex.join(argv),"cwd":str(ROOT),
        "exit_code":completed.returncode,"stdout_file":str(case_dir / (stage+".stdout.txt")),
        "stderr_file":str(case_dir / (stage+".stderr.txt"))}

def run_case(case):
    folder = OUT / case["case"]
    if (folder / "run-record.json").exists():
        raise RuntimeError("Refusing to overwrite original run evidence: " + case["case"])
    input_path = folder / "original-input.json"
    if sha(input_path) != case["input_sha256"] or sha(folder/"pre-run-expectations.json") != case["expectations_sha256"]:
        raise RuntimeError("Frozen original/expectations changed")
    scripts = ROOT / "skills" / "compliance-financial-crime" / case["skill"] / "scripts"
    calls = []
    calls.append(invoke(folder, "validate-input", ["python3","-B",str(scripts/"validate_input.py"),str(input_path)]))
    calls.append(invoke(folder, "calculate", ["python3","-B",str(scripts/"calculate_or_transform.py"),str(input_path)]))
    output_path = folder / "original-output.json"
    output_path.write_bytes((folder/"calculate.stdout.txt").read_bytes())
    calls.append(invoke(folder, "validate-output", ["python3","-B",str(scripts/"validate_output.py"),str(output_path),"--input",str(input_path)]))
    record = {"case":case["case"],"skill":case["skill"],"expected_intake":case["expected_intake"],
        "calls":calls,"input_sha256":sha(input_path),"output_sha256":sha(output_path),
        "expectations_sha256":sha(folder/"pre-run-expectations.json"),
        "artifact_sha256":{f.name:sha(f) for f in sorted(folder.iterdir()) if f.is_file()}}
    (folder/"run-record.json").write_text(json.dumps(record,indent=2)+"\n")
    return record

with ThreadPoolExecutor(max_workers=4) as pool:
    runs = list(pool.map(run_case, manifest["cases"]))

tamper = []
for name in ["ib-realistic","abc-realistic","misconduct-realistic","customer-realistic"]:
    folder = OUT/name
    case = next(c for c in manifest["cases"] if c["case"]==name)
    original = json.loads((folder/"original-output.json").read_text())
    changed = dict(original)
    changed["approval"] = "approved"
    changed["action_taken"] = True
    changed["unsupported_narrative"] = "All legal checks passed and execute the action now."
    target = folder/"edited-output.json"
    target.write_text(json.dumps(changed,indent=2)+"\n")
    scripts = ROOT/"skills"/"compliance-financial-crime"/case["skill"]/"scripts"
    call = invoke(folder,"validate-edited-output",["python3","-B",str(scripts/"validate_output.py"),str(target),"--input",str(folder/"original-input.json")])
    tamper.append({"case":name,**call,"edited_output_sha256":sha(target)})

package_drift = []
for skill, files in manifest["pre_run_package_file_sha256"].items():
    for path, digest in files.items():
        file = ROOT/path
        if not file.exists() or sha(file)!=digest:
            package_drift.append(path)
record = {"completed_at_utc":datetime.now(timezone.utc).isoformat(), "python":platform.python_version(),
    "cases":runs,"edited_output_reconstruction_checks":tamper,
    "package_files_changed_between_freeze_and_run":package_drift,
    "all_case_inputs_preserved":all(r["input_sha256"]==c["input_sha256"] for r,c in zip(runs,manifest["cases"]))}
(OUT/"run-manifest.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({"case_exit_codes":{r["case"]:[c["exit_code"] for c in r["calls"]] for r in runs},
    "edited_output_exit_codes":[c["exit_code"] for c in tamper],"package_drift":package_drift},indent=2))
