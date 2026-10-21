"""Preserve rejected initial originals; correct only synthetic input enum in new cases."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
OUT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((OUT/"pre-run-manifest.json").read_text())
cases=[]
for old in ["abc-realistic","abc-exact-boundary","abc-conflict-recipient"]:
    new=old+"-corrected"
    folder=OUT/new
    folder.mkdir(exist_ok=False)
    doc=json.loads((OUT/old/"original-input.json").read_text())
    # Change identifiers and all fact IDs consistently; retain the substantive evidence.
    text=json.dumps(doc).replace(old+":",new+":")
    doc=json.loads(text)
    doc["request_id"]=new
    doc["object_id"]="SYNTHETIC-"+new
    doc["workflow"]["context"]["object_id"]=doc["object_id"]
    for row in doc["data"]["engagements"]:
        row["benefit_type"]["value"]="intermediary"
    for source in doc["sources"]:
        for fact in source["facts"]:
            if fact["fact_id"].endswith(".benefit_type"):
                fact["value"]="intermediary"
                fact["excerpt"]=fact["excerpt"].replace("intermediary service fee","intermediary")
    facts=json.loads((OUT/old/"raw-facts.json").read_text().replace(old+":",new+":"))
    for fact in facts:
        if fact["fact_id"].endswith(".benefit_type"):
            fact["raw_value"]="intermediary"
            fact["excerpt"]=fact["excerpt"].replace("intermediary service fee","intermediary")
    exp=json.loads((OUT/old/"pre-run-expectations.json").read_text())
    exp["case"]=new
    exp["harness_correction"]="Initial request used descriptive benefit_type 'intermediary service fee'; authoritative enum is 'intermediary'. Initial rejection is retained as harness error, not package defect. No substantive expected findings changed."
    for filename,value in [("original-input.json",doc),("raw-facts.json",facts),("pre-run-expectations.json",exp)]:
        (folder/filename).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
    cases.append({"case":new,"skill":"anti-bribery-corruption-reviewer","input":str(folder/"original-input.json"),"input_sha256":sha(folder/"original-input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json"),"raw_facts_sha256":sha(folder/"raw-facts.json"),"expected_intake":"accept"})
record={"prepared_at_utc":datetime.now(timezone.utc).isoformat(),"cases":cases,"correction_scope":"Synthetic harness enum only. Original rejected evidence preserved. Expectations frozen before corrected CLI execution.","package_file_sha256":manifest["pre_run_package_file_sha256"]}
(OUT/"pre-run-corrections.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({"corrected_cases_frozen":len(cases)}))
