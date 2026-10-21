"""Independently freeze a decimal-lexeme precision challenge before installed CLI calls."""
from __future__ import annotations
import hashlib,json,shlex,subprocess
from datetime import datetime,timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[4]
name="customer-long-decimal-threshold"; folder=OUT/name; folder.mkdir(exist_ok=False)
literal="0.33333333333333333334"
text=(OUT/"customer-exact-threshold-pilot"/"input.json").read_text().replace("customer-exact-threshold-pilot",name).replace("0.3333333333333333",literal)
(folder/"input.json").write_text(text)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n")
expected=Fraction(1,3)<=Fraction(Decimal(literal))
dump(folder/"raw-facts.json",{"counts":{"harms":1,"observed":3,"population":3},"source_bound_threshold_numeric_json_lexeme":literal,"typed_units":"unique-customers","threshold_lexeme_location":"/data/cohorts/0/threshold_rate/value and matching exact supplied source fact value","all_new_sources_remain_synthetic_unverified":True})
dump(folder/"pre-run-expectations.json",{"case":name,"frozen_at_utc":datetime.now(timezone.utc).isoformat(),"before_cli_run":True,"challenge":"Decimal JSON literal just above exact 1/3 must not collapse to the lower binary-float decimal and invert criterion.","expected_intake":"accept precise threshold or reject/withhold unsupported precision explicitly","expected_exact_ratio_within_supplied_decimal_criterion":expected,"expected_supported_findings":["Exact 1/3 is less than finite supplied decimal 0.33333333333333333334, so accepted decimal evidence requires within criterion true."],"expected_unknown_or_withheld_findings":["If numeric precision is unsupported, reject or withhold; do not report false from a changed threshold."],"professional_limits":"Synthetic numerical consistency only; no threshold legitimacy, source authentication, causal harm, professional acceptance or action established."})
scripts=ROOT/"skills"/"compliance-financial-crime"/"customer-conduct-outcomes-reviewer"/"scripts"
pre={"input_sha256":sha(folder/"input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json"),"script_sha256":{p.name:sha(p) for p in scripts.glob("*.py")}}
dump(folder/"pre-run-manifest.json",pre)
calls=[]
for stage,argv in [("validate-input",["python3","-B",str(scripts/"validate_input.py"),str(folder/"input.json")]),("calculate",["python3","-B",str(scripts/"calculate_or_transform.py"),str(folder/"input.json")])]:
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
    (folder/(stage+".stdout.txt")).write_text(p.stdout);(folder/(stage+".stderr.txt")).write_text(p.stderr)
    calls.append({"stage":stage,"argv":argv,"shell_replay":shlex.join(argv),"cwd":str(ROOT),"exit_code":p.returncode})
(folder/"output.json").write_bytes((folder/"calculate.stdout.txt").read_bytes())
argv=["python3","-B",str(scripts/"validate_output.py"),str(folder/"output.json"),"--input",str(folder/"input.json")]
p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);(folder/"validate-output.stdout.txt").write_text(p.stdout);(folder/"validate-output.stderr.txt").write_text(p.stderr)
calls.append({"stage":"validate-output","argv":argv,"shell_replay":shlex.join(argv),"cwd":str(ROOT),"exit_code":p.returncode})
doc=json.loads((folder/"output.json").read_text()) if calls[1]["exit_code"]==0 else None
row=doc["results"]["cohort_metrics"][0] if doc else None
passed=bool(calls[0]["exit_code"] or calls[1]["exit_code"] or (row and row["within_supplied_harm_criterion"] in [None,expected]))
record={"case":name,"skill":"customer-conduct-outcomes-reviewer","kind":"new-decimal-lexeme-precision-challenge","calls":calls,**pre,"output_sha256":sha(folder/"output.json"),"criterion_expected":expected,"actual_row":row,"independent_expectation_passed":passed}
dump(folder/"run-record.json",record)
print(json.dumps({"case":name,"codes":[c["exit_code"] for c in calls],"criterion_expected":expected,"criterion_actual":row["within_supplied_harm_criterion"] if row else None,"parsed_threshold":row["evidence"]["threshold_rate"] if row else None,"passed":passed},indent=2))
