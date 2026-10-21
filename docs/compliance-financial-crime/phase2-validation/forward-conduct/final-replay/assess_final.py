"""Assess preserved final outputs separately from initial/first-replay failed expectations."""
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;BASE=OUT.parent
manifest=json.loads((OUT/"run-manifest.json").read_text());pre=json.loads((OUT/"pre-run-manifest.json").read_text())
checks=[];legacy=[]
def check(case,identifier,passed,expected,actual):checks.append({"case":case,"check_id":identifier,"passed":bool(passed),"expected":expected,"actual":actual})
def doc(case):return json.loads((OUT/case/"output.json").read_text())
def rows(case,key,idkey):return {r[idkey]:r for r in doc(case)["results"][key]}
def claim_count(v):
    if isinstance(v,dict):return 1 if set(v)=={"value","source_refs","fact_ids"} else sum(claim_count(x) for x in v.values())
    return sum(claim_count(x) for x in v) if isinstance(v,list) else 0
for record in manifest["cases"]:
    name=record["case"];codes=[c["exit_code"] for c in record["calls"]];folder=OUT/name
    if record["kind"]=="unchanged-prior-intake":
        check(name,"unchanged_prior_input_bytes",record["input_sha256"]==record["prior_input_sha256"],record["prior_input_sha256"],record["input_sha256"])
        preserved=hashlib.sha256((folder/"prior-pre-run-expectations.json").read_bytes()).hexdigest()
        check(name,"prior_expectations_preserved",preserved==record["prior_expectations_sha256"],record["prior_expectations_sha256"],preserved)
    if record["expected_intake"]=="reject":
        check(name,"intake_stops_invalid_case",codes[:2]==[1,1] and (folder/"output.json").stat().st_size==0,"Reject invalid counts/plain decimal string, emit no native output",codes);continue
    check(name,"installed_cli_triplet",codes==[0,0,0],"Input validator/calculator/detached output validator all exit 0",codes)
    if codes[1]:continue
    output=doc(name);original=json.loads((folder/"input.json").read_text())
    check(name,"scope_time_audience",all(output[k]==original[k] for k in ["request_id","object_id","object_type","as_of","knowledge_cutoff"]) and all(output[k]==original["workflow"][k] for k in ["role","classification","audience"]) and output["context"]==original["workflow"]["context"],"Scope/time/audience/classification/role retained",{k:output[k] for k in ["request_id","as_of","audience"]})
    check(name,"all_claim_bindings",len(output["claim_bindings"])==claim_count(original["data"]),claim_count(original["data"]),len(output["claim_bindings"]))
    expected={"source_assurance":"supplied-unverified","human_review_required":True,"draft":True,"action_taken":False,"approval":"not_requested","execution":"not_performed"};actual={k:output[k] for k in expected}
    check(name,"professional_boundary",expected==actual,expected,actual)
    check(name,"inherited_issues",all(i in output["unresolved_issues"] for i in original["workflow"]["unresolved_issues"]),original["workflow"]["unresolved_issues"],output["unresolved_issues"])

r=rows("ib-realistic","request_reviews","request_id")
check("ib-realistic","positive_exact_actor_scope",r["WALL-VALID"]["scope_consistent_with_supplied_authority"] is True,"Exact named authority scope draft only",r["WALL-VALID"])
check("ib-realistic","all_known_access_mismatches",len(r["ACCESS-MISMATCH"]["reasons"])==5,"Actor/purpose/information/date/need-to-know mismatches remain",r["ACCESS-MISMATCH"])
check("ib-realistic","list_authority_and_unknown_classification",r["LIST-REMOVAL"]["scope_consistent_with_supplied_authority"] is False and r["CLASS-UNKNOWN"]["scope_consistent_with_supplied_authority"] is None,"Standalone list change mismatched; classification unknown withheld",[r["LIST-REMOVAL"],r["CLASS-UNKNOWN"]])
for name,word in [("ib-partial-known-mismatch","actor"),("ib-access-with-list-proposal","list-change authority")]:
    r=doc(name)["results"]["request_reviews"][0];check(name,"original_authority_gap_resolved",r["scope_consistent_with_supplied_authority"] is False and any(word in i for i in r["reasons"]),"Known authority problem explicit despite unrelated unknowns/mixed proposal",r)
r=rows("abc-realistic-corrected","engagement_reviews","engagement_id")
check("abc-realistic-corrected","high_fee_counterevidence",r["HIGH-SUCCESS-FEE"]["amount_to_benchmark_ratio"]=="2.500000000000" and r["HIGH-SUCCESS-FEE"]["within_supplied_criterion"] is False and len(r["HIGH-SUCCESS-FEE"]["review_reasons"])==4 and len(r["HIGH-SUCCESS-FEE"]["counterevidence"])==2,"High fee, services/diligence/link concerns and counterevidence retained",r["HIGH-SUCCESS-FEE"])
check("abc-realistic-corrected","matched_evidence_no_approval",r["MATCHED-SERVICES"]["within_supplied_criterion"] is True and r["MATCHED-SERVICES"]["payment_approved"] is False,"Matched evidence draft never approves payment",r["MATCHED-SERVICES"])
check("abc-realistic-corrected","noncomparable_ratios_withheld",all(r[k]["amount_to_benchmark_ratio"] is None and r[k]["within_supplied_criterion"] is None for k in ["MIXED-CURRENCY","MISSING-BENCHMARK"]),"Mixed currency/missing benchmark withhold",[r["MIXED-CURRENCY"],r["MISSING-BENCHMARK"]])
r=rows("abc-exact-boundary-corrected","engagement_reviews","engagement_id")
check("abc-exact-boundary-corrected","raw_ratio_and_zero",r["ROUNDING-EDGE"]["amount_to_benchmark_ratio"]=="1.000000000000" and r["ROUNDING-EDGE"]["within_supplied_criterion"] is False and r["ZERO-BENCHMARK"]["amount_to_benchmark_ratio"] is None,"Unrounded 1.0000000000005 above 1; zero benchmark withheld",r)
r=doc("abc-conflict-recipient-corrected")["results"]["engagement_reviews"][0]
check("abc-conflict-recipient-corrected","unknown_and_conflict",r["evidence"]["recipient"] is None and r["evidence"]["government_link"] is None and r["review_state"]=="needs-ABC-review","Unknown recipient/conflict do not become favorable",r)
r=doc("misconduct-realistic")["results"]
check("misconduct-realistic","chronology_hypotheses",[e["event_id"] for e in r["timeline"]]==["SUPERVISOR-APPROVAL","AUTOMATED-CORRECTION","CREDIT-NOTE","OVERRIDE"] and len(r["hypotheses"])==2 and r["hypotheses"][0]["contradiction_unresolved"] is True,"Correct chronology, counterevidence and alternative hypothesis",r)
check("misconduct-realistic","mandated_plans",[p["within_supplied_mandate"] for p in r["evidence_interview_plan"]]==[True,False] and all(p["execution"]=="not-performed" for p in r["evidence_interview_plan"]),"Interview permitted; device proposal outside; no contact/collection",r["evidence_interview_plan"])
for case in ["misconduct-unknown-polarity","misconduct-event-receipt-date"]:
    r=doc(case)["results"];check(case,"timeline_withheld",r["timeline"][0]["eligible_for_timeline"] is False and r["hypotheses"]==[],"Ambiguity/impossible receipt chronology remain excluded",r)

unchanged_customers=[r["case"] for r in manifest["cases"] if r["kind"]=="unchanged-prior-intake" and r["skill"]=="customer-conduct-outcomes-reviewer" and r["expected_intake"]=="accept"]
for name in unchanged_customers:
    r=doc(name)["results"]
    check(name,"legacy_numeric_comparison_unknown",all(x["within_supplied_harm_criterion"] is None for x in r["cohort_metrics"]),"Numeric floating threshold comparisons unknown; positive comparison not credited",r["cohort_metrics"])
    eligible=[x for x in r["cohort_metrics"] if x["observed_harm_rate"] is not None]
    if eligible:check(name,"specific_precision_issue",all(any("precision unestablished" in issue for issue in x["review_issues"]) for x in eligible),"Every otherwise eligible fractional numeric threshold requests exact decimal evidence",eligible)
    legacy.append({"case":name,"comparison_status":"INCOMPLETE-PRECISION-INTAKE; no exact-threshold positive/negative acceptance credited","rate_scope_status":"metrics-withheld-missing-or-mixed-units" if not r["metric_definition_evidence_consistent"] else "counts/units support observed rates; threshold comparison withheld","prior_expectations_file":str(OUT/name/"prior-pre-run-expectations.json"),"actual_comparison":[x["within_supplied_harm_criterion"] for x in r["cohort_metrics"]]})

for name in ["customer-realistic","customer-unit-mismatch","customer-unknown-zero","customer-unit-mismatch-units-amended"]:
    r=doc(name)["results"];check(name,"missing_or_mixed_units_no_default",r["metric_definition_evidence_consistent"] is False and all(x[k] is None for x in r["cohort_metrics"] for k in ["observed_harm_rate","observation_coverage"]),"Missing/mixed units cannot be inferred/defaulted or rescued by numbers",r)

name="customer-realistic-units-amended-exact-decimal";r=rows(name,"cohort_metrics","cohort_id")
check(name,"restored_exact_comparisons",r["ALL"]["observed_harm_rate"]==.03 and r["ALL"]["observation_coverage"]==.8 and r["VULNERABLE"]["observed_harm_rate"]==.15 and r["VULNERABLE"]["observation_coverage"]==.5 and r["ALL"]["within_supplied_harm_criterion"] is False and r["VULNERABLE"]["within_supplied_harm_criterion"] is False,"ALL 3%/80%, vulnerable 15%/50%; exact string 0.02 exceeded",r)
check(name,"zero_and_missing_groups",r["MOBILE-ONLY"]["observed_harm_rate"]==0 and r["MOBILE-ONLY"]["within_supplied_harm_criterion"] is True and r["ASSISTED-DIGITAL"]["observed_harm_rate"] is None and r["ASSISTED-DIGITAL"]["within_supplied_harm_criterion"] is None and doc(name)["results"]["missing_expected_cohorts"]==["SWITCHERS"],"Known zero accepts exact criterion; zero denominator/missing switchers unresolved",r)
name="customer-unit-mismatch-units-amended-exact-decimal";r=doc(name)["results"]
check(name,"exact_string_does_not_rescue_units",r["metric_definition_evidence_consistent"] is False and r["review_scope"]["numerator_unit"]=="events" and all(x[k] is None for x in r["cohort_metrics"] for k in ["observed_harm_rate","observation_coverage","within_supplied_harm_criterion"]),"Events/customer unsupported despite exact threshold",r)
name="customer-unknown-zero-units-amended-exact-decimal";r=rows(name,"cohort_metrics","cohort_id")
check(name,"unknown_zero_vulnerability",all(r[k]["observed_harm_rate"] is None and r[k]["within_supplied_harm_criterion"] is None for k in ["UNKNOWN-DENOM","ZERO-POP"]) and r["MISSING-FLAG"]["vulnerable_customer_segment"] is None and r["MISSING-FLAG"]["observed_harm_rate"]==0 and r["MISSING-FLAG"]["within_supplied_harm_criterion"] is True,"Zero/null counts distinct; missing vulnerability remains; observed zero exact criterion true",r)
for name,value,expected in [("customer-exact-threshold-pilot-exact-decimal","0.3333333333333333",False),("customer-long-decimal-threshold-exact-decimal","0.33333333333333333334",True)]:
    r=doc(name)["results"]["cohort_metrics"][0];check(name,"exact_decimal_string_lexeme",r["evidence"]["threshold_rate"]==value and r["within_supplied_harm_criterion"] is expected and r["observed_harm_rate"]==.3333333333333333,"Preserve source string "+value+"; exact count-ratio criterion="+str(expected),r)
for record in manifest["cases"]:
    if record["kind"]!="separate-exact-decimal-amendment":continue
    name=record["case"];r=doc(name);bindings=[b for b in r["claim_bindings"] if b["native_input_pointer"].endswith("/threshold_rate")]
    check(name,"explicit_exact_source_mapping",len(bindings)==len(r["results"]["cohort_metrics"]) and all(b["source_refs"]==["SYN-EXACT-DECIMAL-SUPPLEMENT"] and b["consistency"]=="exact-supplied-fact" for b in bindings),"New strings explicitly source-mapped, not silently supplied as defaults",bindings)
r=rows("customer-integer-zero-one","cohort_metrics","cohort_id")
check("customer-integer-zero-one","integer_exact_boundaries",[r[k]["within_supplied_harm_criterion"] for k in ["ZERO-ZERO","POSITIVE-ZERO","ALL-HARM-ONE"]]==[True,False,True],"Integer 0: 0 harms true, positive harms false; integer 1: ratio1 true",r)
check("customer-integer-zero-one","floating_boundary_stays_partial",r["FLOAT-ONE"]["within_supplied_harm_criterion"] is None and any("precision" in i for i in r["FLOAT-ONE"]["review_issues"]),"Numeric float 1.0 remains precision-incomplete under exact contract",r["FLOAT-ONE"])
r=doc("customer-max-decimal-string")["results"]["cohort_metrics"][0]
check("customer-max-decimal-string","max_supported_precision",len(r["evidence"]["threshold_rate"])==256 and r["within_supplied_harm_criterion"] is False,"256-character finite decimal below 1/3 accepted exactly; criterion false",r)
for record in manifest["tamper_checks"]:check(record["case"],record["stage"]+"_rejects",record["exit_code"]==1,"Edited output rejected against immutable detached input",record["exit_code"])
check("all","frozen_runtime_docs_equal",manifest["runtime_or_instruction_drift"]==[] and manifest["runtime_and_instruction_sha256_after"]==pre["frozen_runtime_and_instruction_sha256"],"Frozen runtime/instruction SHA256 before and after equal; pending manifests excluded",manifest["runtime_or_instruction_drift"])
check("all","earlier_artifacts_unchanged",manifest["prior_evidence_files_changed"]==[],"Initial 91/94 and first replay139/140 artifacts/snapshots unchanged",manifest["prior_evidence_files_changed"])
counts={"total":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)}
assessment={"status":"PASS - bounded final contract replay; legacy intakes remain partial, professional acceptance unestablished","counts":counts,"checks":checks,"failures":[c for c in checks if not c["passed"]],"prior_check_states_unchanged":pre["prior_check_states"],"measured_execution":{"cases":28,"valid_cases":24,"rejected_cases":4,"primary_cli_invocations":84,"tampered_output_validator_invocations":5,"total_installed_cli_invocations":89},"legacy_incomplete_precision_intakes":legacy,"remaining_limits":["No source authentication, legal/institutional/professional acceptance or operational execution established.","Legacy floats cannot establish original decimal precision. Their partial-intake checks are not counted as successful prior positive threshold comparisons.","Exact threshold supplements are new synthetic supplied-unverified representations grounded in retained raw prior JSON lexemes. Current output active exact strings preserve the source value. Unused old numeric registry values in new serialized amended JSON may display ordinary float rounding; originals and lexical lineage remain separately immutable.","Typed units are explicit supplied assertions; current method supports unique-customer binary proportions only, not arbitrary events/customer rates."]}
(OUT/"assessment.json").write_text(json.dumps(assessment,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"status":assessment["status"],"counts":counts,"execution":assessment["measured_execution"],"failed_ids":[c["check_id"] for c in assessment["failures"]]},indent=2))
