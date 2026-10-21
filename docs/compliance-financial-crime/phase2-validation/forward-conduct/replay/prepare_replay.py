"""Freeze separate repaired-method intakes, explicit amendments and expectations."""
from __future__ import annotations
import copy, hashlib, json, platform
from datetime import datetime, timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
BASE=OUT.parent
ROOT=OUT.parents[4]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
initial=json.loads((BASE/"run-manifest.json").read_text())
initial_hashes=json.loads((BASE/"artifact-hashes.json").read_text())
cases=[]
for record in initial["cases"]:
    name=record["case"]
    if name.startswith("abc-") and not name.endswith("-corrected"): continue
    folder=OUT/name
    folder.mkdir(exist_ok=False)
    (folder/"input.json").write_bytes((BASE/name/"original-input.json").read_bytes())
    (folder/"raw-facts.json").write_bytes((BASE/name/"raw-facts.json").read_bytes())
    original_exp=json.loads((BASE/name/"pre-run-expectations.json").read_text())
    changes=[]
    expectations=copy.deepcopy(original_exp)
    if name.startswith("customer-") and record["expected_intake"]=="accept":
        changes=["Original has no typed count-unit claims. Current method must accept a partial intake but withhold every rate, coverage and criterion; missing units are not defaulted from prose."]
        expectations["expected_supported_findings"]=["Original population/observed/harm counts, barriers, vulnerability, expected/missing cohorts, context and provenance remain supplied facts."]
        expectations["expected_unknown_or_withheld_findings"]=["All harm rates, coverage ratios and threshold comparisons withheld because typed units are absent.","No units inferred or defaulted from the original prose."]
    if name=="ib-partial-known-mismatch": changes=["Overall comparison is now false because the established actor mismatch remains explicit, despite unknown classification. Initial output used null and omitted this mismatch."]
    if name=="ib-access-with-list-proposal": changes=["Overall comparison is now false and separate list-change authority mismatch is explicit. Initial output used true with no reasons."]
    expectations["replay_expectation_changes"]=changes
    expectations["initial_input_unchanged"]=True
    dump(folder/"pre-run-expectations.json",expectations)
    cases.append({"case":name,"skill":record["skill"],"expected_intake":record["expected_intake"],"kind":"unchanged-initial-intake","input_sha256":sha(folder/"input.json"),"initial_input_sha256":record["input_sha256"],"expectations_sha256":sha(folder/"pre-run-expectations.json")})

for name in ["customer-realistic","customer-unit-mismatch","customer-unknown-zero"]:
    new=name+"-units-amended"
    folder=OUT/new; folder.mkdir(exist_ok=False)
    doc=json.loads((BASE/name/"original-input.json").read_text())
    doc["request_id"]=new; doc["object_id"]="SYNTHETIC-"+new; doc["workflow"]["context"]["object_id"]=doc["object_id"]
    numerator="events" if name=="customer-unit-mismatch" else "unique-customers"
    source={"source_ref":"SYN-TYPED-UNIT-SUPPLEMENT","version":"synthetic-unit-declaration-v1","received_at":"2026-10-03","publication_date":"2026-10-03","classification":doc["workflow"]["classification"],"permitted_audiences":[doc["workflow"]["audience"]],"facts":[]}
    units={"population_unit":"unique-customers","numerator_unit":numerator,"denominator_unit":"unique-customers"}
    additions=[]
    raw=json.loads((BASE/name/"raw-facts.json").read_text())
    basis=[f for f in raw if f["locator"] in {"review.numerator_definition","review.denominator_definition"} or f["locator"].endswith((".population",".observed",".harms"))]
    for field,value in units.items():
        fact_id=new+":"+field
        fact={"fact_id":fact_id,"value":value,"excerpt":"Explicit supplemental synthetic reviewer declaration: "+field+"="+value+" for "+name+". Grounded in separately retained original numerator/denominator definitions and count records; source truth is unverified. This is newly supplied unit evidence, not a default inferred by the method."}
        source["facts"].append(fact)
        doc["data"]["review"][field]={"value":value,"source_refs":[source["source_ref"]],"fact_ids":[fact_id]}
        additions.append({"native_pointer":"/data/review/"+field,"value":value,"source_ref":source["source_ref"],"fact_id":fact_id,"excerpt":fact["excerpt"]})
    doc["sources"].append(source); doc["workflow"]["sources"].append({"source_ref":source["source_ref"],"version":source["version"]})
    dump(folder/"input.json",doc)
    dump(folder/"raw-facts.json",{"original_case":name,"original_raw_facts_sha256":sha(BASE/name/"raw-facts.json"),"original_grounding_facts":basis,"new_explicit_unit_assertions":additions})
    amendment={"original_case":name,"original_input_sha256":sha(BASE/name/"original-input.json"),"new_case":new,"changes":["New request/object identifier; detached original and initial outcome remain untouched.","Three new exact source-bound typed unit claims and one synthetic unverified supplemental source record; existing substantive count/definition/threshold/barrier claims retained without changes."],"units":units,"grounding":basis,"not_established":["No institutional source authentication, legal applicability, professional acceptance or truth of the supplemental unit assertion is established."]}
    dump(folder/"amendment.json",amendment)
    exp=json.loads((BASE/name/"pre-run-expectations.json").read_text()); exp["case"]=new; exp["initial_input_unchanged"]=False
    exp["explicit_unit_amendment"]=units
    if numerator=="events":
        exp["expected_supported_findings"]=["Events/customer units are now explicitly source-bound and incompatible with the current unique-customer-only proportion method."]
        exp["expected_unknown_or_withheld_findings"]=["Harm rate, coverage and criterion comparison withheld; metric definition evidence consistent is false. Counts and barriers retained without customer-harm extrapolation."]
    dump(folder/"pre-run-expectations.json",exp)
    cases.append({"case":new,"skill":"customer-conduct-outcomes-reviewer","expected_intake":"accept","kind":"explicit-unit-amendment","input_sha256":sha(folder/"input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json")})

# A small pilot gives a realistic independent exact-ratio challenge: 1/3 is just above the supplied decimal criterion.
name="customer-exact-threshold-pilot"; folder=OUT/name; folder.mkdir(exist_ok=False)
doc=json.loads((OUT/"customer-realistic-units-amended"/"input.json").read_text())
doc["request_id"]=name; doc["object_id"]="SYNTHETIC-"+name; doc["workflow"]["context"]["object_id"]=doc["object_id"]
source={"source_ref":"SYN-PILOT-UNIT-COUNTS","version":"synthetic-pilot-v1","received_at":"2026-10-03","publication_date":"2026-10-03","classification":doc["workflow"]["classification"],"permitted_audiences":[doc["workflow"]["audience"]],"facts":[]}
facts=[]
def claim(label,value):
    fact={"fact_id":name+":"+label,"value":value,"excerpt":"Independent synthetic pilot fact "+label+"="+json.dumps(value,ensure_ascii=False)}
    source["facts"].append(fact); facts.append(fact)
    return {"value":value,"source_refs":[source["source_ref"]],"fact_ids":[fact["fact_id"]]}
review={k:v["value"] for k,v in doc["data"]["review"].items()}; review["product"]="Synthetic three-customer assisted-support pilot"; review["expected_cohorts"]=["PILOT"]
doc["data"]={"review":{k:claim("review."+k,v) for k,v in review.items()},"cohorts":[{"cohort_id":"PILOT",**{k:claim("PILOT."+k,v) for k,v in {"population":3,"observed":3,"harms":1,"vulnerable":True,"value_barriers":[],"support_barriers":["One observed harmful callback failure"],"threshold_rate":0.3333333333333333}.items()}}]}
doc["sources"]=[source]; doc["workflow"]["sources"]=[{"source_ref":source["source_ref"],"version":source["version"]}]
dump(folder/"input.json",doc); dump(folder/"raw-facts.json",facts)
dump(folder/"pre-run-expectations.json",{"case":name,"skill":"customer-conduct-outcomes-reviewer","frozen_before_run":True,"expected_intake":"accept","expected_supported_findings":["One harmed unique customer of three observed; all typed units explicitly unique-customers.","Displayed rate is 0.3333333333333333, but exact 1/3 exceeds decimal threshold 0.3333333333333333, so within criterion false.","Coverage is 1; no population acceptance or causal inference."],"expected_unknown_or_withheld_findings":["Source truth, threshold legitimacy and professional acceptance remain unverified."],"independently_chosen_challenge":"Tiny observed pilot exact fraction versus finite decimal threshold; do not compare only the displayed binary-float result."})
cases.append({"case":name,"skill":"customer-conduct-outcomes-reviewer","expected_intake":"accept","kind":"new-independent-challenge","input_sha256":sha(folder/"input.json"),"expectations_sha256":sha(folder/"pre-run-expectations.json")})

package_hashes={}
for skill in sorted({c["skill"] for c in cases}):
    package=ROOT/"skills"/"compliance-financial-crime"/skill
    package_hashes[skill]={str(p.relative_to(ROOT)):sha(p) for p in sorted(package.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
dump(OUT/"pre-run-manifest.json",{"prepared_at_utc":datetime.now(timezone.utc).isoformat(),"python":platform.python_version(),"cases":cases,"current_package_sha256":package_hashes,"initial_artifact_sha256":initial_hashes,"initial_assessment":{"total":94,"passed":91,"failed":3},"expectation_basis":"Repaired information-barrier methods plus explicit optional typed-unit customer contract; original no-unit intakes must remain partial, no original facts silently amended."})
print(json.dumps({"replay_cases_frozen":len(cases),"unchanged_original_cases":sum(c["kind"]=="unchanged-initial-intake" for c in cases),"separate_unit_amendments":3,"new_exact_threshold_challenges":1},indent=2))
