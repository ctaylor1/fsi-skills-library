"""Compare original CLI evidence with independently frozen practitioner expectations."""
from __future__ import annotations
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent
manifest = json.loads((OUT/"run-manifest.json").read_text())
checks=[]
def check(case, identifier, passed, expected, actual):
    checks.append({"case":case,"check_id":identifier,"passed":bool(passed),"expected":expected,"actual":actual})
def output(case): return json.loads((OUT/case/"original-output.json").read_text())
def rows(case,key,id_key): return {r[id_key]:r for r in output(case)["results"][key]}
def count_claims(value):
    if isinstance(value,dict):
        if set(value)=={"value","source_refs","fact_ids"}: return 1
        return sum(count_claims(v) for v in value.values())
    if isinstance(value,list): return sum(count_claims(v) for v in value)
    return 0

for run in manifest["cases"]:
    case=run["case"]
    codes=[c["exit_code"] for c in run["calls"]]
    if case.startswith("abc-") and not case.endswith("-corrected"):
        check(case,"harness_enum_error_retained",codes[:2]==[1,1],"Initial descriptive benefit_type is rejected; this is a harness error, not package defect.",codes)
        continue
    if run["expected_intake"]=="reject":
        check(case,"invalid_count_intake_stops",codes[:2]==[1,1] and (OUT/case/"original-output.json").stat().st_size==0,"Reject harms > observed; emit no native output",codes)
        continue
    check(case,"actual_cli_validation",codes==[0,0,0],"Installed input CLI, calculator and detached output CLI all exit 0",codes)
    if codes[1]: continue
    doc=output(case)
    original=json.loads((OUT/case/"original-input.json").read_text())
    retained={k:doc[k] for k in ["request_id","object_id","object_type","as_of","knowledge_cutoff","classification","audience","role"]}
    expected={k:original[k] if k in original else original["workflow"][k] for k in retained}
    check(case,"scope_date_audience_retained",retained==expected and doc["context"]==original["workflow"]["context"],expected,retained)
    check(case,"all_claim_locators_retained",len(doc["claim_bindings"])==count_claims(original["data"]),count_claims(original["data"]),len(doc["claim_bindings"]))
    boundary={k:doc[k] for k in ["source_assurance","human_review_required","draft","action_taken","approval","execution"]}
    boundary_expected={"source_assurance":"supplied-unverified","human_review_required":True,"draft":True,"action_taken":False,"approval":"not_requested","execution":"not_performed"}
    check(case,"professional_boundary",boundary==boundary_expected,boundary_expected,boundary)
    check(case,"inherited_issue_retained",all(i in doc["unresolved_issues"] for i in original["workflow"]["unresolved_issues"]),original["workflow"]["unresolved_issues"],doc["unresolved_issues"])

r=rows("ib-realistic","request_reviews","request_id")
check("ib-realistic","ib_valid",r["WALL-VALID"]["scope_consistent_with_supplied_authority"] is True,"Exact planned actor/information/purpose/period scope consistent",r["WALL-VALID"])
reasons=r["ACCESS-MISMATCH"]["reasons"]
check("ib-realistic","ib_mismatches",len(reasons)==5 and all(any(word in reason for reason in reasons) for word in ["actor","purpose","information set","dates","need-to-know"]),"All five known mismatches explicit",reasons)
check("ib-realistic","ib_list",r["LIST-REMOVAL"]["scope_consistent_with_supplied_authority"] is False and any("operation" in reason for reason in r["LIST-REMOVAL"]["reasons"]),"List change outside access/wall-cross authority",r["LIST-REMOVAL"])
check("ib-realistic","ib_unknown",r["CLASS-UNKNOWN"]["scope_consistent_with_supplied_authority"] is None and r["CLASS-UNKNOWN"]["scope"]["classification"] is None,"Classification unknown and overall comparison withheld",r["CLASS-UNKNOWN"])
r=rows("ib-partial-known-mismatch","request_reviews","request_id")["PARTIAL-ACTOR"]
check("ib-partial-known-mismatch","ib_partial_actor",any("actor" in reason for reason in r["reasons"]),"Known EMP-999 versus EMP-102 actor mismatch retained even while classification unknown",r)
r=rows("ib-access-with-list-proposal","request_reviews","request_id")["ACCESS-AND-REMOVE"]
check("ib-access-with-list-proposal","ib_embedded_list",any("list" in reason.lower() for reason in r["reasons"]),"Separate list-change authority issue for access-only mandate",r)

r=rows("abc-realistic-corrected","engagement_reviews","engagement_id")
high=r["HIGH-SUCCESS-FEE"]
check("abc-realistic-corrected","abc_high",high["amount_to_benchmark_ratio"]=="2.500000000000" and high["within_supplied_criterion"] is False and len(high["review_reasons"])==4 and len(high["counterevidence"])==2,"Ratio 2.5; four review triggers and both counterexplanations retained",high)
matched=r["MATCHED-SERVICES"]
check("abc-realistic-corrected","abc_matched",matched["amount_to_benchmark_ratio"]=="1.000000000000" and matched["within_supplied_criterion"] is True and matched["review_state"]=="evidence-reconciled-draft" and matched["payment_approved"] is False,"Matched evidence draft, ratio 1, no payment approval",matched)
for label,identifier in [("MIXED-CURRENCY","abc_currency"),("MISSING-BENCHMARK","abc_benchmark")]:
    row=r[label]
    check("abc-realistic-corrected",identifier,row["amount_to_benchmark_ratio"] is None and row["within_supplied_criterion"] is None and row["review_state"]=="needs-ABC-review","Ratio/criterion withheld; review required",row)
r=rows("abc-exact-boundary-corrected","engagement_reviews","engagement_id")
check("abc-exact-boundary-corrected","abc_precision",r["ROUNDING-EDGE"]["amount_to_benchmark_ratio"]=="1.000000000000" and r["ROUNDING-EDGE"]["within_supplied_criterion"] is False,"Display rounded to 12 places, decision uses exact raw 1.0000000000005 > 1",r["ROUNDING-EDGE"])
check("abc-exact-boundary-corrected","abc_zero",r["ZERO-BENCHMARK"]["amount_to_benchmark_ratio"] is None and r["ZERO-BENCHMARK"]["within_supplied_criterion"] is None,"Zero benchmark prevents division",r["ZERO-BENCHMARK"])
doc=output("abc-conflict-recipient-corrected"); r=doc["results"]["engagement_reviews"][0]
check("abc-conflict-recipient-corrected","abc_conflict",r["evidence"]["recipient"] is None and r["evidence"]["government_link"] is None and r["review_state"]=="needs-ABC-review" and any("conflicts" in i for i in doc["unresolved_issues"]),"Recipient unknown and conflicting official link withheld; independent ratio does not create favorable review",r)

doc=output("misconduct-realistic"); r=doc["results"]
check("misconduct-realistic","mi_timeline",[e["event_id"] for e in r["timeline"]]==["SUPERVISOR-APPROVAL","AUTOMATED-CORRECTION","CREDIT-NOTE","OVERRIDE"] and all(e["eligible_for_timeline"] for e in r["timeline"]),"Chronological, all within supplied mandate/date/evidence scope",r["timeline"])
h=r["hypotheses"]
check("misconduct-realistic","mi_hypotheses",len(h)==2 and h[0]["supports"]==["OVERRIDE"] and h[0]["contradicts"]==["SUPERVISOR-APPROVAL"] and h[0]["neutral"]==["CREDIT-NOTE"] and h[0]["contradiction_unresolved"] is True and all(x["conclusion"]=="not-adjudicated" for x in h),"Supporting, contrary, neutral evidence and competing hypothesis retained without adjudication",h)
check("misconduct-realistic","mi_plans",[p["within_supplied_mandate"] for p in r["evidence_interview_plan"]]==[True,False] and all(p["execution"]=="not-performed" for p in r["evidence_interview_plan"]),"Neutral interview within scope; device proposal outside; no execution",r["evidence_interview_plan"])
r=output("misconduct-unknown-polarity")["results"]
check("misconduct-unknown-polarity","mi_unknown_polarity",r["timeline"][0]["evidence"]["polarity"] is None and r["timeline"][0]["eligible_for_timeline"] is False and r["hypotheses"]==[],"Accepted unknown polarity withheld without crash or assignment",r)
r=output("misconduct-event-receipt-date")["results"]
check("misconduct-event-receipt-date","mi_receipt",r["timeline"][0]["eligible_for_timeline"] is False and r["hypotheses"]==[] and any("receipt date" in i for i in r["timeline"][0]["issues"]),"Event after source receipt excluded from timeline support",r)

r=rows("customer-realistic","cohort_metrics","cohort_id")
check("customer-realistic","cc_rates",r["ALL"]["observed_harm_rate"]==.03 and r["ALL"]["observation_coverage"]==.8 and r["VULNERABLE"]["observed_harm_rate"]==.15 and r["VULNERABLE"]["observation_coverage"]==.5 and r["ALL"]["within_supplied_harm_criterion"] is False and r["VULNERABLE"]["within_supplied_harm_criterion"] is False,"ALL 3%/80% coverage; VULNERABLE 15%/50%; both exceed 2%",r)
doc=output("customer-realistic")
check("customer-realistic","cc_missing",doc["results"]["missing_expected_cohorts"]==["SWITCHERS"] and "not summed" in doc["results"]["aggregation"],"Missing switchers retained; overlapping cohorts not aggregated",doc["results"]["missing_expected_cohorts"])
check("customer-realistic","cc_zero",r["ASSISTED-DIGITAL"]["observed_harm_rate"] is None and r["ASSISTED-DIGITAL"]["observation_coverage"]==0 and r["MOBILE-ONLY"]["observed_harm_rate"]==0 and r["MOBILE-ONLY"]["observation_coverage"]==1,"Zero denominator is null rate; known zero numerator is zero rate",[r["ASSISTED-DIGITAL"],r["MOBILE-ONLY"]])
check("customer-realistic","cc_population_boundary",all(x["population_good_outcomes_conclusion"]=="not-established" for x in r.values()) and doc["results"]["individual_complaint_resolution"]=="not-performed","No whole-population favorable inference or individual remedy",doc["results"])
r=output("customer-unit-mismatch")["results"]
check("customer-unit-mismatch","cc_unit_mismatch",r["cohort_metrics"][0]["observed_harm_rate"] is None and r["cohort_metrics"][0]["within_supplied_harm_criterion"] is None,"Explicit events/customer grain mismatch should withhold unique-customer harm proportion",r)
r=rows("customer-unknown-zero","cohort_metrics","cohort_id")
check("customer-unknown-zero","cc_unknown_zero",all(r[k]["observed_harm_rate"] is None and r[k]["within_supplied_harm_criterion"] is None for k in ["UNKNOWN-DENOM","ZERO-POP"]) and r["MISSING-FLAG"]["vulnerable_customer_segment"] is None and r["MISSING-FLAG"]["observed_harm_rate"]==0,"Unknown denominator/empty population withheld, missing vulnerability remains unknown, observed zero preserved",r)

for edited in manifest["edited_output_reconstruction_checks"]:
    check(edited["case"],"edited_output_rejected",edited["exit_code"]==1,"Added approval/action/narrative rejected against detached original",edited["exit_code"])
check("all","package_snapshot_unchanged",manifest["package_files_changed_between_freeze_and_run"]==[],"No package files changed during validation",manifest["package_files_changed_between_freeze_and_run"])
check("all","all_original_inputs_unchanged",manifest["all_case_inputs_preserved"],"All original input bytes preserve pre-run SHA256",manifest["all_case_inputs_preserved"])
assessment={"status":"PARTIAL - native checks pass but three practitioner expectations fail",
    "scope":"Four assigned conduct packages; actual installed CLIs and independently constructed supplied synthetic cases only.",
    "checks":checks,"counts":{"total":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)},
    "failures":[c for c in checks if not c["passed"]],
    "harness_limitations":["Three initial ABC requests rejected because evaluator used a descriptive benefit_type rather than native enum. Originals preserved, corrected cases separately frozen and run.","Initial run_forward.py executed all original CLI stages but aborted at edited-output JSON loading of the rejected ABC output. Initial runner source preserved; resume loaded existing records without overwriting originals.","No end-to-end real-model narrative evaluation, source authentication, legal acceptance, institutional authority, receiver handoff or operational readiness established.","Package instructions explicitly assign semantic units and substantive review to the human draft; the customer unit mismatch is a demonstrated native limitation against the practitioner expectation, not a claim that source mappings establish unit equivalence."]}
(OUT/"assessment.json").write_text(json.dumps(assessment,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"status":assessment["status"],"counts":assessment["counts"],"failed_check_ids":[c["check_id"] for c in assessment["failures"]]},indent=2))
