"""Freeze final intakes separately, retaining original expectations and exact lexical lineage."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent;BASE=OUT.parent;PREVIOUS=BASE/"replay";ROOT=OUT.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
records=json.loads((PREVIOUS/"run-manifest.json").read_text())["cases"]+[json.loads((PREVIOUS/"customer-long-decimal-threshold"/"run-record.json").read_text())]
cases=[]
for r in records:
    name=r["case"];folder=OUT/name;folder.mkdir(exist_ok=False)
    source=PREVIOUS/name
    for filename in ["input.json","raw-facts.json"]:(folder/filename).write_bytes((source/filename).read_bytes())
    # Preserve the exact prior before-run expectation bytes; revised contract checks are a separate artifact.
    (folder/"prior-pre-run-expectations.json").write_bytes((source/"pre-run-expectations.json").read_bytes())
    if (BASE/name/"pre-run-expectations.json").exists():(folder/"initial-pre-run-expectations.json").write_bytes((BASE/name/"pre-run-expectations.json").read_bytes())
    customer=r["skill"]=="customer-conduct-outcomes-reviewer"
    rejected=r.get("expected_intake")=="reject"
    expectations={"case":name,"kind":"unchanged-prior-intake","prior_expectations_retained_unchanged":True,"expected_intake":"reject" if rejected else "accept","expected_contract_behavior":
        "Invalid harms > observed rejected; no native result." if rejected else
        "Fractional numeric JSON thresholds remain precision-incomplete; comparison unknown. Unsupported/missing units also withhold dependent rates. Preserve prior positive comparison expectations as incomplete intake; do not credit as positive exact-threshold acceptance." if customer else
        "Retain previously supported domain findings, repaired authority gaps, scope/evidence/dates and professional boundaries."}
    dump(folder/"pre-run-expectations.json",expectations)
    cases.append({"case":name,"skill":r["skill"],"kind":"unchanged-prior-intake","expected_intake":expectations["expected_intake"],"input_sha256":sha(folder/"input.json"),"prior_input_sha256":sha(source/"input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json"),"prior_expectations_sha256":sha(folder/"prior-pre-run-expectations.json")})

for source_name in ["customer-realistic-units-amended","customer-unit-mismatch-units-amended","customer-unknown-zero-units-amended","customer-exact-threshold-pilot","customer-long-decimal-threshold"]:
    name=source_name+"-exact-decimal";folder=OUT/name;folder.mkdir(exist_ok=False)
    source=PREVIOUS/source_name;text=(source/"input.json").read_text();doc=json.loads(text);lexical=json.loads(text,parse_float=str,parse_int=str)
    doc["request_id"]=name;doc["object_id"]="SYNTHETIC-"+name;doc["workflow"]["context"]["object_id"]=doc["object_id"]
    supplement={"source_ref":"SYN-EXACT-DECIMAL-SUPPLEMENT","version":"synthetic-exact-lexeme-declaration-v1","received_at":"2026-10-03","publication_date":"2026-10-03","classification":doc["workflow"]["classification"],"permitted_audiences":[doc["workflow"]["audience"]],"facts":[]}
    amendments=[]
    for row,lexrow in zip(doc["data"]["cohorts"],lexical["data"]["cohorts"]):
        value=lexrow["threshold_rate"]["value"]
        assert isinstance(value,str)
        old_fact_ids=row["threshold_rate"]["fact_ids"]
        original_facts=[f for s in lexical["sources"] for f in s["facts"] if f["fact_id"] in old_fact_ids]
        assert original_facts and all(f["value"]==value for f in original_facts)
        fact_id=name+":"+row["cohort_id"]+".threshold_rate.exact-decimal"
        fact={"fact_id":fact_id,"value":value,"excerpt":"New synthetic supplied exact-decimal declaration preserves raw JSON numeric lexeme "+value+" from "+source_name+" threshold and matching source fact, without rounding or changing the criterion. Source truth remains unverified."}
        supplement["facts"].append(fact)
        row["threshold_rate"]={"value":value,"source_refs":[supplement["source_ref"]],"fact_ids":[fact_id]}
        amendments.append({"cohort_id":row["cohort_id"],"raw_numeric_json_lexeme":value,"prior_source_fact_ids":old_fact_ids,"new_string_value":value,"new_fact_id":fact_id})
    doc["sources"].append(supplement);doc["workflow"]["sources"].append({"source_ref":supplement["source_ref"],"version":supplement["version"]})
    dump(folder/"input.json",doc);dump(folder/"raw-facts.json",{"unchanged_prior_raw_facts_file":str(source/"raw-facts.json"),"prior_raw_facts_sha256":sha(source/"raw-facts.json"),"exact_threshold_lexeme_supplement":amendments})
    dump(folder/"amendment.json",{"original_case":source_name,"original_input_sha256":sha(source/"input.json"),"new_case":name,"changes":["New request/object ID","Threshold claims now use exact decimal strings from the raw prior JSON lexemes; a separate newly supplied synthetic supplement maps matching string source values. Existing numeric source facts remain untouched in the registry.","No count, unit, barrier, period, population, rate or threshold magnitude changed."],"threshold_lineage":amendments,"source_assurance":"supplied-unverified"})
    if source_name=="customer-long-decimal-threshold":expected="All units unique-customers, 1/3 is BELOW exact string 0.33333333333333333334; comparison true. No precision shortening or acceptance based only on displayed rate."
    elif source_name=="customer-exact-threshold-pilot":expected="All units unique-customers, 1/3 is ABOVE exact string 0.3333333333333333; comparison false despite identical displayed rate."
    elif source_name=="customer-realistic-units-amended":expected="ALL 3%/80% coverage and vulnerable 15%/50%; both above exact string 0.02 criterion. Known zero harm positive denominator yields comparison true; zero denominator remains unknown; missing group and barriers retained."
    elif source_name=="customer-unit-mismatch-units-amended":expected="Explicit event/customer grain remains unsupported; exact threshold string does not rescue harm, coverage or criterion comparisons."
    else:expected="Unknown denominator and zero population remain withheld; known zero harm/positive denominator produces observed zero and true exact string comparison while vulnerability remains unknown."
    dump(folder/"pre-run-expectations.json",{"case":name,"kind":"separate-exact-decimal-amendment","frozen_before_cli_run":True,"expected_intake":"accept","expected_supported_findings":[expected],"new_synthetic_source_truth":"unverified","unknowns":"No whole-population outcome, causal harm, legal applicability, professional acceptance or operational action established."})
    cases.append({"case":name,"skill":"customer-conduct-outcomes-reviewer","kind":"separate-exact-decimal-amendment","expected_intake":"accept","input_sha256":sha(folder/"input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json")})

def new_customer(name,row_values,expectation,expected_intake="accept"):
    folder=OUT/name;folder.mkdir(exist_ok=False)
    doc=json.loads((OUT/"customer-exact-threshold-pilot-exact-decimal"/"input.json").read_text())
    doc["request_id"]=name;doc["object_id"]="SYNTHETIC-"+name;doc["workflow"]["context"]["object_id"]=doc["object_id"]
    source={"source_ref":"SYN-FINAL-BOUNDARY-FACTS","version":"synthetic-boundary-v1","received_at":"2026-10-03","publication_date":"2026-10-03","classification":doc["workflow"]["classification"],"permitted_audiences":[doc["workflow"]["audience"]],"facts":[]}
    def claim(label,value):
        fact={"fact_id":name+":"+label,"value":value,"excerpt":"Independent supplied synthetic boundary fact "+label+"="+json.dumps(value)};source["facts"].append(fact)
        return {"value":value,"source_refs":[source["source_ref"]],"fact_ids":[fact["fact_id"]]}
    review={k:v["value"] for k,v in doc["data"]["review"].items()};review["expected_cohorts"]=[r["cohort_id"] for r in row_values]
    rows=[]
    for vals in row_values:
        label=vals["cohort_id"];data={"population":10,"observed":10,"harms":1,"vulnerable":False,"value_barriers":[],"support_barriers":[],"threshold_rate":"0.02"};data.update({k:v for k,v in vals.items() if k!="cohort_id"});rows.append({"cohort_id":label,**{k:claim(label+"."+k,v) for k,v in data.items()}})
    doc["data"]={"review":{k:claim("review."+k,v) for k,v in review.items()},"cohorts":rows};doc["sources"]=[source];doc["workflow"]["sources"]=[{"source_ref":source["source_ref"],"version":source["version"]}]
    dump(folder/"input.json",doc);dump(folder/"raw-facts.json",source["facts"]);dump(folder/"pre-run-expectations.json",{"case":name,"kind":"independent-boundary-challenge","frozen_before_cli_run":True,"expected_intake":expected_intake,"expected_supported_findings":[expectation],"professional_boundary":"Internal supplied-unverified draft; no population acceptance or action."})
    cases.append({"case":name,"skill":"customer-conduct-outcomes-reviewer","kind":"independent-boundary-challenge","expected_intake":expected_intake,"input_sha256":sha(folder/"input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json")})

new_customer("customer-integer-zero-one",[{"cohort_id":"ZERO-ZERO","harms":0,"threshold_rate":0},{"cohort_id":"POSITIVE-ZERO","threshold_rate":0},{"cohort_id":"ALL-HARM-ONE","harms":10,"threshold_rate":1},{"cohort_id":"FLOAT-ONE","threshold_rate":1.0}],"Integer zero: zero harm true and positive harm false. Integer one: all harmed ratio 1 true. Floating numeric 1.0 remains precision-incomplete with comparison unknown.")
new_customer("customer-max-decimal-string",[{"cohort_id":"MAX-STRING","population":3,"observed":3,"harms":1,"threshold_rate":"0."+"3"*254}],"256-character plain decimal string accepted exactly; finite repeating-3 decimal is below 1/3, so criterion false.")
for suffix,value,expectation in [("exponent","3.3e-1","Exponent string unsupported; intake and calculator reject."),("over-one","1.00000000000000000001","Exact string above 1 rejected without float rounding into range."),("overlength","0."+"3"*255,"257-character exact string rejected by the documented 256-character limit.")]:new_customer("customer-invalid-string-"+suffix,[{"cohort_id":"INVALID","threshold_rate":value}],expectation,"reject")

# Freeze runtime and relevant instruction docs; pending generated package manifests are excluded.
runtime=["domain.py","foundation_contract.py","native_integrity.py","calculate_or_transform.py","validate_input.py","validate_output.py"]
hashes={}
for skill in sorted({c["skill"] for c in cases}):
    package=ROOT/"skills"/"compliance-financial-crime"/skill
    paths=[package/"SKILL.md"]+[package/"scripts"/f for f in runtime]+[p for p in package.joinpath("references").glob("*.md")]+[package/"assets"/"output-template.md"]
    hashes[skill]={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths) if p.is_file()}
    for filename in runtime:
        target=OUT/"method-snapshot"/skill/filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((package/"scripts"/filename).read_bytes())
prior={str(p.relative_to(BASE)):sha(p) for p in BASE.rglob("*") if p.is_file() and OUT not in p.parents}
dump(OUT/"pre-run-manifest.json",{"prepared_at_utc":datetime.now(timezone.utc).isoformat(),"cases":cases,"frozen_runtime_and_instruction_sha256":hashes,"excluded_from_package_hash_freeze":"Generated package manifests awaiting root sync; evaluations/golden fixtures are not replay inputs.","prior_evidence_file_sha256":prior,"prior_check_states":{"initial":{"total":94,"passed":91,"failed":3},"first_replay":{"total":140,"passed":139,"failed":1}},"representation_amendment_policy":"Explicit new string source facts preserve raw prior numeric lexemes, including the long 0.33333333333333333334 literal. No prior threshold/units/facts/expectations overwritten or defaulted."})
print(json.dumps({"cases_frozen":len(cases),"unchanged_prior":18,"exact_string_amendments":5,"independent_boundary_intakes":5,"expected_valid":sum(c["expected_intake"]=="accept" for c in cases),"expected_rejected":sum(c["expected_intake"]=="reject" for c in cases)},indent=2))
