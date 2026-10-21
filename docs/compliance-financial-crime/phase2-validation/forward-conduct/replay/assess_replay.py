"""Independent expectations for the frozen repaired-method replay and amended intakes."""
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;BASE=OUT.parent
manifest=json.loads((OUT/"run-manifest.json").read_text())
supplement=json.loads((OUT/"customer-long-decimal-threshold"/"run-record.json").read_text())
checks=[]
def check(case,identifier,passed,expected,actual): checks.append({"case":case,"check_id":identifier,"passed":bool(passed),"expected":expected,"actual":actual})
def doc(case):return json.loads((OUT/case/"output.json").read_text())
def rows(case,key,idkey):return {r[idkey]:r for r in doc(case)["results"][key]}
def claims(v):
    if isinstance(v,dict):return 1 if set(v)=={"value","source_refs","fact_ids"} else sum(claims(i) for i in v.values())
    return sum(claims(i) for i in v) if isinstance(v,list) else 0
for record in manifest["cases"]+[supplement]:
    name=record["case"]; codes=[c["exit_code"] for c in record["calls"]]
    if record.get("expected_intake")=="reject":
        check(name,"malformed_count_stops",codes[:2]==[1,1] and (OUT/name/"output.json").stat().st_size==0,"Invalid harms > observed rejected; no output",codes);continue
    check(name,"installed_cli_triplet",codes==[0,0,0],"All installed input/calculation/detached-output CLI calls pass",codes)
    if codes[1]:continue
    output=doc(name); original=json.loads((OUT/name/"input.json").read_text())
    check(name,"scope_time_audience_retained",all(output[k]==original[k] for k in ["request_id","object_id","object_type","as_of","knowledge_cutoff"]) and all(output[k]==original["workflow"][k] for k in ["role","classification","audience"]) and output["context"]==original["workflow"]["context"],"Exact supplied context/date/audience/role retained",{k:output[k] for k in ["request_id","as_of","knowledge_cutoff","audience"]})
    check(name,"claim_locators_retained",len(output["claim_bindings"])==claims(original["data"]),claims(original["data"]),len(output["claim_bindings"]))
    expected={"source_assurance":"supplied-unverified","human_review_required":True,"draft":True,"action_taken":False,"approval":"not_requested","execution":"not_performed"};actual={k:output[k] for k in expected}
    check(name,"professional_boundary",expected==actual,expected,actual)
    check(name,"inherited_issues_retained",all(i in output["unresolved_issues"] for i in original["workflow"]["unresolved_issues"]),original["workflow"]["unresolved_issues"],output["unresolved_issues"])
    if record.get("kind")=="unchanged-initial-intake":check(name,"original_input_bytes_unchanged",record["input_sha256"]==record["initial_input_sha256"],record["initial_input_sha256"],record["input_sha256"])

r=rows("ib-realistic","request_reviews","request_id")
check("ib-realistic","exact_scope_positive",r["WALL-VALID"]["scope_consistent_with_supplied_authority"] is True,"Exact actor/info/purpose/planned-period match",r["WALL-VALID"])
check("ib-realistic","all_five_mismatches",len(r["ACCESS-MISMATCH"]["reasons"])==5,"Actor, purpose, information, dates, need-to-know mismatches retained",r["ACCESS-MISMATCH"]["reasons"])
check("ib-realistic","standalone_list_gap",r["LIST-REMOVAL"]["scope_consistent_with_supplied_authority"] is False and any("list-change authority" in i for i in r["LIST-REMOVAL"]["reasons"]),"Standalone list proposal receives separate authority gap",r["LIST-REMOVAL"])
check("ib-realistic","classification_unknown",r["CLASS-UNKNOWN"]["scope"]["classification"] is None and r["CLASS-UNKNOWN"]["scope_consistent_with_supplied_authority"] is None,"Classification/overall comparison unknown when no known mismatch",r["CLASS-UNKNOWN"])
r=rows("ib-partial-known-mismatch","request_reviews","request_id")["PARTIAL-ACTOR"]
check("ib-partial-known-mismatch","known_actor_repair",r["scope_consistent_with_supplied_authority"] is False and any("actor" in i for i in r["reasons"]) and any("classification" in i for i in r["reasons"]),"Known actor mismatch and classification uncertainty both explicit; overall comparison false",r)
r=rows("ib-access-with-list-proposal","request_reviews","request_id")["ACCESS-AND-REMOVE"]
check("ib-access-with-list-proposal","embedded_list_repair",r["scope_consistent_with_supplied_authority"] is False and any("list-change authority" in i for i in r["reasons"]),"Access-only mandate does not cover embedded list proposal",r)

r=rows("abc-realistic-corrected","engagement_reviews","engagement_id")
check("abc-realistic-corrected","high_fee_and_counterevidence",r["HIGH-SUCCESS-FEE"]["amount_to_benchmark_ratio"]=="2.500000000000" and r["HIGH-SUCCESS-FEE"]["within_supplied_criterion"] is False and len(r["HIGH-SUCCESS-FEE"]["review_reasons"])==4 and len(r["HIGH-SUCCESS-FEE"]["counterevidence"])==2,"Ratio 2.5, four issues and both counterexplanations retained",r["HIGH-SUCCESS-FEE"])
check("abc-realistic-corrected","matched_services_draft",r["MATCHED-SERVICES"]["amount_to_benchmark_ratio"]=="1.000000000000" and r["MATCHED-SERVICES"]["within_supplied_criterion"] is True and r["MATCHED-SERVICES"]["payment_approved"] is False,"Matched ratio 1 is draft and never payment approval",r["MATCHED-SERVICES"])
for name in ["MIXED-CURRENCY","MISSING-BENCHMARK"]:check("abc-realistic-corrected",name.lower()+"_withheld",r[name]["amount_to_benchmark_ratio"] is None and r[name]["within_supplied_criterion"] is None,"Ratio/criterion withheld",r[name])
r=rows("abc-exact-boundary-corrected","engagement_reviews","engagement_id")
check("abc-exact-boundary-corrected","raw_ratio_edge",r["ROUNDING-EDGE"]["amount_to_benchmark_ratio"]=="1.000000000000" and r["ROUNDING-EDGE"]["within_supplied_criterion"] is False,"Exact 1.0000000000005 exceeds 1 despite rounded display",r["ROUNDING-EDGE"])
check("abc-exact-boundary-corrected","zero_benchmark",r["ZERO-BENCHMARK"]["amount_to_benchmark_ratio"] is None,"No divide by zero",r["ZERO-BENCHMARK"])
r=doc("abc-conflict-recipient-corrected")["results"]["engagement_reviews"][0]
check("abc-conflict-recipient-corrected","conflict_no_favorable_review",r["evidence"]["recipient"] is None and r["evidence"]["government_link"] is None and r["review_state"]=="needs-ABC-review","Unknown recipient/conflict withheld, no favorable review",r)

r=doc("misconduct-realistic")["results"]
check("misconduct-realistic","ordered_timeline",[e["event_id"] for e in r["timeline"]]==["SUPERVISOR-APPROVAL","AUTOMATED-CORRECTION","CREDIT-NOTE","OVERRIDE"] and all(e["eligible_for_timeline"] for e in r["timeline"]),"Same correct source-bound chronology",r["timeline"])
check("misconduct-realistic","hypothesis_matrix",len(r["hypotheses"])==2 and r["hypotheses"][0]["supports"]==["OVERRIDE"] and r["hypotheses"][0]["contradicts"]==["SUPERVISOR-APPROVAL"] and r["hypotheses"][0]["neutral"]==["CREDIT-NOTE"] and r["hypotheses"][0]["contradiction_unresolved"] is True,"Support/counterevidence/alternative retained, no adjudication",r["hypotheses"])
check("misconduct-realistic","collection_scope",[p["within_supplied_mandate"] for p in r["evidence_interview_plan"]]==[True,False] and all(p["execution"]=="not-performed" for p in r["evidence_interview_plan"]),"Interview within scope; phone forensic outside; no execution",r["evidence_interview_plan"])
for case,reason in [("misconduct-unknown-polarity","unknown"),("misconduct-event-receipt-date","receipt date")]:
    r=doc(case)["results"];check(case,"event_withheld",r["timeline"][0]["eligible_for_timeline"] is False and r["hypotheses"]==[] and any(reason in i for i in doc(case)["unresolved_issues"]),"Ambiguity/impossible receipt chronology withheld",r)

for case in ["customer-realistic","customer-unit-mismatch","customer-unknown-zero"]:
    d=doc(case);r=d["results"]
    check(case,"missing_typed_units_partial",r["metric_definition_evidence_consistent"] is False and all(row[k] is None for row in r["cohort_metrics"] for k in ["observed_harm_rate","observation_coverage","within_supplied_harm_criterion"]) and all(r["review_scope"][k] is None for k in ["population_unit","numerator_unit","denominator_unit"]),"Unchanged intake accepted, all missing-unit metrics withheld with no default",r)

r=rows("customer-realistic-units-amended","cohort_metrics","cohort_id")
check("customer-realistic-units-amended","positive_customer_rates",r["ALL"]["observed_harm_rate"]==.03 and r["ALL"]["observation_coverage"]==.8 and r["VULNERABLE"]["observed_harm_rate"]==.15 and r["VULNERABLE"]["observation_coverage"]==.5 and r["ALL"]["within_supplied_harm_criterion"] is False and r["VULNERABLE"]["within_supplied_harm_criterion"] is False,"Explicit unique-customer units restore ALL 3%/80% and vulnerable 15%/50%, both above 2%",r)
check("customer-realistic-units-amended","zero_and_missing",r["MOBILE-ONLY"]["observed_harm_rate"]==0 and r["ASSISTED-DIGITAL"]["observed_harm_rate"] is None and doc("customer-realistic-units-amended")["results"]["missing_expected_cohorts"]==["SWITCHERS"],"Observed zero differs from zero denominator; missing switchers retained",r)
r=doc("customer-unit-mismatch-units-amended")["results"]
check("customer-unit-mismatch-units-amended","mixed_units_repair",r["review_scope"]["numerator_unit"]=="events" and r["metric_definition_evidence_consistent"] is False and all(r["cohort_metrics"][0][k] is None for k in ["observed_harm_rate","observation_coverage","within_supplied_harm_criterion"]),"Explicit event/customer units withheld under unique-customer-only method",r)
r=rows("customer-unknown-zero-units-amended","cohort_metrics","cohort_id")
check("customer-unknown-zero-units-amended","unknown_zero_distinction",all(r[k]["observed_harm_rate"] is None and r[k]["within_supplied_harm_criterion"] is None for k in ["UNKNOWN-DENOM","ZERO-POP"]) and r["MISSING-FLAG"]["observed_harm_rate"]==0 and r["MISSING-FLAG"]["vulnerable_customer_segment"] is None,"Typed units do not fill missing counts or vulnerability; valid known zero remains zero",r)
for case in ["customer-realistic-units-amended","customer-unit-mismatch-units-amended","customer-unknown-zero-units-amended"]:
    r=doc(case); bindings=[b for b in r["claim_bindings"] if b["native_input_pointer"].endswith(("population_unit","numerator_unit","denominator_unit"))]
    check(case,"new_unit_source_locators",len(bindings)==3 and all(b["consistency"]=="exact-supplied-fact" and b["source_refs"]==["SYN-TYPED-UNIT-SUPPLEMENT"] for b in bindings),"Three explicit newly supplied synthetic unit facts mapped, not defaulted",bindings)
r=doc("customer-exact-threshold-pilot")["results"]["cohort_metrics"][0]
check("customer-exact-threshold-pilot","fraction_above_short_decimal",r["observed_harm_rate"]==.3333333333333333 and r["within_supplied_harm_criterion"] is False,"Exact 1/3 exceeds the supplied 16-digit decimal threshold despite same displayed rate",r)
check("customer-long-decimal-threshold","long_decimal_lexeme_preserved",supplement["independent_expectation_passed"],"Exact 1/3 is within numeric JSON decimal 0.33333333333333333334; preserve precise threshold or explicitly reject/withhold unsupported precision",supplement["actual_row"])
for record in manifest["edited_output_checks"]:check(record["case"],"tamper_rejected",record["exit_code"]==1,"Edited approval/action/narrative rejected against current original",record["exit_code"])
for record in manifest["historical_snapshot_reconstruction"]:
    check(record["case"],"historical_source_hashes",record["source_snapshot_matches_initial_hashes"],"Historical scripts match initial recorded hashes",record["source_snapshot_matches_initial_hashes"])
    check(record["case"],"historical_byte_reconstruction",record["original_output_bytes_reconstructed"] and all(c["exit_code"]==0 for c in record["calls"]),"All historical CLI calls pass and reconstruct initial output bytes exactly",record["reconstructed_output_sha256"])
check("all","initial_evidence_unchanged",manifest["initial_evidence_files_changed"]==[],"Initial 91/94 artifact state preserved",manifest["initial_evidence_files_changed"])
check("all","frozen_method_drift_absent",manifest["current_package_drift_during_replay"]==[],"Current package hashes stable during main replay",manifest["current_package_drift_during_replay"])
assessment={"status":"PARTIAL - original three conduct gaps addressed in bounded replay; one new decimal lexical-precision expectation fails","initial_assessment_unchanged":{"total":94,"passed":91,"failed":3},"checks":checks,"counts":{"total":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)},"failures":[c for c in checks if not c["passed"]],"case_counts":{"unchanged_original_valid":12,"unchanged_original_malformed":1,"explicit_unit_amendments":3,"new_precision_challenges":2,"total_current_method_cases":18},"limitations":["Replay expectations for original no-unit customer intakes differ explicitly from the initial rate expectations; those originals remain partial rather than retroactively treated as successful positive rate cases.","New unit evidence is synthetic supplied-unverified; no professional/authority/source acceptance established.","Long-decimal numeric JSON precision is not preserved by float parsing even though the count-ratio comparator uses exact Fraction arithmetic.","Four tamper checks and historical reconstruction are bounded software evidence, not source truth or institutional action authority."]}
(OUT/"assessment.json").write_text(json.dumps(assessment,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"status":assessment["status"],"counts":assessment["counts"],"failed_ids":[c["check_id"] for c in assessment["failures"]]},indent=2))
