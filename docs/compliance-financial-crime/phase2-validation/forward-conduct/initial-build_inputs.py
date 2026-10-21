"""Independent synthetic conduct requests. Build and freeze expectations before any CLI run."""
from __future__ import annotations
import copy
import hashlib
import json
import platform
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SKILLS = ["information-barrier-reviewer", "anti-bribery-corruption-reviewer", "misconduct-investigation-assistant", "customer-conduct-outcomes-reviewer"]

def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Packet:
    def __init__(self, case, skill, object_type, audience, classification="compliance_confidential"):
        self.case, self.skill = case, skill
        self.facts = []
        self.doc = {"request_id": case, "object_id": "SYNTHETIC-" + case, "object_type": object_type,
            "as_of": "2026-10-03", "knowledge_cutoff": "2026-10-03", "workflow": {
                "context": {"institution_id": "SYNTHETIC-HARBOR-FINANCIAL", "legal_entity_id": "SYNTHETIC-HF-01",
                    "capacity": "mandated internal decision support", "represented_party": "synthetic institution",
                    "object_id": "SYNTHETIC-" + case, "object_type": object_type, "jurisdiction": "supplied UK/US business perimeter; legal applicability unassessed",
                    "line_of_business": "synthetic conduct compliance", "purpose": "independent offline conduct review"},
                "as_of": "2026-10-03", "role": "decision_support", "classification": classification,
                "audience": audience, "allowed_audiences": [audience], "sources": [],
                "unresolved_issues": ["Synthetic supplied evidence; source authenticity and institutional authority unverified."]},
            "sources": [], "data": {}}
        self.source("SYN-RECORDS", audience, classification)
        self.source("SYN-MANDATE-POLICY", audience, classification)

    def source(self, ref, audience=None, classification=None, received="2026-10-03", published="2026-10-02"):
        audience = audience or self.doc["workflow"]["audience"]
        classification = classification or self.doc["workflow"]["classification"]
        s = {"source_ref": ref, "version": "synthetic-v1", "received_at": received, "publication_date": published,
            "classification": classification, "permitted_audiences": [audience], "facts": []}
        self.doc["sources"].append(s)
        self.doc["workflow"]["sources"].append({"source_ref": ref, "version": "synthetic-v1"})
        return s

    def claim(self, locator, value, ref="SYN-RECORDS", excerpt=None):
        fact = {"fact_id": self.case + ":" + locator, "value": value,
            "excerpt": excerpt or "Synthetic raw record " + locator + ": " + json.dumps(value, ensure_ascii=False)}
        next(s for s in self.doc["sources"] if s["source_ref"] == ref)["facts"].append(fact)
        self.facts.append({"locator": locator, "raw_value": value, "source_ref": ref, "fact_id": fact["fact_id"], "excerpt": fact["excerpt"]})
        return {"value": value, "source_refs": [ref], "fact_ids": [fact["fact_id"]]}

    def row(self, label_key, label, values, policy_fields=()):
        return {label_key: label, **{k: self.claim(label + "." + k, v, "SYN-MANDATE-POLICY" if k in policy_fields else "SYN-RECORDS") for k, v in values.items()}}

    def save(self, request, supported, unknown, challenges, expected_intake="accept", check_ids=()):
        folder = OUT / self.case
        folder.mkdir(parents=True, exist_ok=False)
        dump(folder / "original-input.json", self.doc)
        dump(folder / "raw-facts.json", self.facts)
        exp = {"case": self.case, "skill": self.skill, "synthetic_request": request,
            "expected_intake": expected_intake, "expected_supported_findings": supported,
            "expected_unknown_or_withheld_findings": unknown, "independently_chosen_challenges": challenges,
            "check_ids": list(check_ids), "professional_boundary": "Internal draft only; no access/list change, payment approval, witness contact, device search, guilt/HR adjudication, complaint resolution, legal acceptance or live execution.",
            "frozen_before_cli_run": True}
        dump(folder / "pre-run-expectations.json", exp)
        return {"case": self.case, "skill": self.skill, "input": str(folder / "original-input.json"),
            "input_sha256": sha(folder / "original-input.json"), "expectations_sha256": sha(folder / "pre-run-expectations.json"),
            "raw_facts_sha256": sha(folder / "raw-facts.json"), "expected_intake": expected_intake}

cases = []
IB_FIELDS = ("authority_person_id", "authority_information_ids", "authority_purpose", "authority_starts_on", "authority_ends_on", "authority_scope")

def ib_values(**overrides):
    v = {"operation": "wall-crossing", "person_id": "EMP-102", "information_ids": ["ORION-FORECAST-Q4"],
        "classification": "MNPI", "purpose": "ORION financing diligence", "need_to_know": True,
        "starts_on": "2026-10-05", "ends_on": "2026-10-06", "authority_person_id": "EMP-102",
        "authority_information_ids": ["ORION-FORECAST-Q4"], "authority_purpose": "ORION financing diligence",
        "authority_starts_on": "2026-10-04", "authority_ends_on": "2026-10-10", "authority_scope": ["wall-crossing", "access"],
        "restrictions": ["Named control-room recipients only", "No onward distribution; restricted-list controls retained"], "list_changes": []}
    v.update(overrides)
    return v

p = Packet("ib-realistic", SKILLS[0], "information_barrier_review", "synthetic_control_room", "mnpi")
p.doc["data"] = {"requests": [
    p.row("request_id", "WALL-VALID", ib_values(), IB_FIELDS),
    p.row("request_id", "ACCESS-MISMATCH", ib_values(operation="access", person_id="EMP-103", information_ids=["ORION-FORECAST-Q4", "ORION-CUSTOMER-LIST"], purpose="Sales prospecting", ends_on="2026-10-12", need_to_know=False), IB_FIELDS),
    p.row("request_id", "LIST-REMOVAL", ib_values(operation="list-change", list_changes=["Remove ORION common equity from restricted list"]), IB_FIELDS),
    p.row("request_id", "CLASS-UNKNOWN", ib_values(classification=None), IB_FIELDS)]}
cases.append(p.save("Review a proposed financing wall crossing, a broader access request and a restricted-list removal without granting access. Materiality of one information set has not been determined.",
    ["WALL-VALID exact supplied actor/information/purpose/operation/period comparison is consistent; future requested access dates are planned, not future observed evidence.", "ACCESS-MISMATCH identifies wrong actor, information set, purpose, period and false need-to-know.", "LIST-REMOVAL is outside supplied operation authority; access permission is not list-removal permission."],
    ["CLASS-UNKNOWN needs specialist classification review; no public classification inferred.", "All source truth/authority and legal materiality remain unverified."], ["Multiple mismatches", "Planned versus actual dates", "Unknown materiality"], check_ids=["ib_valid", "ib_mismatches", "ib_list", "ib_unknown"]))

p = Packet("ib-partial-known-mismatch", SKILLS[0], "information_barrier_review", "synthetic_control_room", "mnpi")
p.doc["data"] = {"requests": [p.row("request_id", "PARTIAL-ACTOR", ib_values(person_id="EMP-999", classification=None), IB_FIELDS)]}
cases.append(p.save("Review EMP-999 access when the mandate names EMP-102 and information classification is still pending.",
    ["The known actor mismatch should remain an explicit review finding despite unknown classification."],
    ["Overall consistency and classification are withheld."], ["One missing fact must not erase a separately established mismatch"], check_ids=["ib_partial_actor"]))

p = Packet("ib-access-with-list-proposal", SKILLS[0], "information_barrier_review", "synthetic_control_room", "mnpi")
p.doc["data"] = {"requests": [p.row("request_id", "ACCESS-AND-REMOVE", ib_values(operation="access", authority_scope=["access"], list_changes=["Remove ORION common equity from restricted list after granting access"]), IB_FIELDS)]}
cases.append(p.save("Assess named access and the separate proposal to remove the issuer from the restricted list; the supplied mandate grants only access.",
    ["Named access may be scope-consistent, but the list-removal proposal requires an explicit separate authority gap/decision point."],
    ["List change permission and release condition remain unestablished."], ["Mixed operation embedded in list_changes field"], check_ids=["ib_embedded_list"]))

ABC_FIELDS = ("benchmark_amount", "benchmark_currency", "proportionality_limit", "policy_applies")
def abc_values(**overrides):
    v = {"benefit_type": "intermediary service fee", "recipient": "SYNTHETIC-RIVER-ADVISORY", "services": "Three documented market-access workshops", "delivered_services": "Three documented market-access workshops",
        "amount": 10000, "benchmark_amount": 10000, "currency": "USD", "benchmark_currency": "USD", "proportionality_limit": 1.2,
        "government_link": False, "due_diligence_complete": True, "policy_applies": True,
        "counterevidence": ["Completion log supplied; no government connection identified by the synthetic diligence record"]}
    v.update(overrides)
    return v

p = Packet("abc-realistic", SKILLS[1], "abc_engagement_review", "synthetic_abc_legal")
p.doc["data"] = {"engagements": [
    p.row("engagement_id", "HIGH-SUCCESS-FEE", abc_values(amount=62500, benchmark_amount=25000, proportionality_limit=1.5, government_link=True, due_diligence_complete=False, delivered_services="One workshop evidenced; two unverified", counterevidence=["Contract contains staged milestones; timing difference may explain missing completion evidence", "Government-linked shareholder is reported to be a passive investor"]), ABC_FIELDS),
    p.row("engagement_id", "MATCHED-SERVICES", abc_values(), ABC_FIELDS),
    p.row("engagement_id", "MIXED-CURRENCY", abc_values(amount=12000, currency="EUR"), ABC_FIELDS),
    p.row("engagement_id", "MISSING-BENCHMARK", abc_values(benchmark_amount=None), ABC_FIELDS)]}
cases.append(p.save("Review intermediary compensation, performed work, diligence and government connections, retaining plausible counterexplanations and withholding payment approval.",
    ["HIGH-SUCCESS-FEE ratio 2.500000000000 exceeds supplied 1.5; incomplete diligence, government-link review trigger and performed-service discrepancy retained.", "MATCHED-SERVICES ratio 1.000000000000 is within supplied 1.2 criterion; still only draft evidence reconciliation.", "Counterevidence remains visible and a government link is not guilt."],
    ["MIXED-CURRENCY ratio withheld without comparable currency basis.", "MISSING-BENCHMARK ratio/criterion withheld; no invented benchmark or payment approval."], ["Counterevidence", "Currency comparability", "Partial service delivery"], check_ids=["abc_high", "abc_matched", "abc_currency", "abc_benchmark"]))

p = Packet("abc-exact-boundary", SKILLS[1], "abc_engagement_review", "synthetic_abc_legal")
p.doc["data"] = {"engagements": [p.row("engagement_id", "ROUNDING-EDGE", abc_values(amount=2000000000001, benchmark_amount=2000000000000, proportionality_limit=1), ABC_FIELDS), p.row("engagement_id", "ZERO-BENCHMARK", abc_values(benchmark_amount=0), ABC_FIELDS)]}
cases.append(p.save("Check an exact compensation ratio just above a supplied limit and a non-comparable zero benchmark; do not round the criterion decision into a pass.",
    ["ROUNDING-EDGE exact ratio 1.0000000000005 is above 1; criterion false even though 12-place half-even display is 1.000000000000."],
    ["ZERO-BENCHMARK ratio/criterion withheld; zero is supplied evidence, not an unknown or invented denominator."], ["Unrounded criterion comparison", "Division by zero"], check_ids=["abc_precision", "abc_zero"]))

p = Packet("abc-conflict-recipient", SKILLS[1], "abc_engagement_review", "synthetic_abc_legal")
v = abc_values(recipient=None, government_link=True)
row = p.row("engagement_id", "UNKNOWN-RECIPIENT", v, ABC_FIELDS)
p.source("SYN-COUNTER-RECORD")
contrary = p.claim("UNKNOWN-RECIPIENT.government_link_contrary", False, "SYN-COUNTER-RECORD", "Synthetic updated diligence reports no government ownership; unresolved conflict with earlier declaration.")
row["government_link"]["source_refs"].extend(contrary["source_refs"])
row["government_link"]["fact_ids"].extend(contrary["fact_ids"])
p.doc["data"] = {"engagements": [row]}
cases.append(p.save("Review a service fee with unknown actual benefit recipient and conflicting government-link declarations.",
    ["Conflicting government link remains unresolved with both source locators retained; ratio alone can be calculated from independent comparable amounts."],
    ["Recipient and official-link conclusion withheld; favorable reconciliation and guilt conclusion prohibited."], ["Exact conflicting fact mappings", "Unknown recipient"], check_ids=["abc_conflict"]))

def misconduct_packet(case):
    p = Packet(case, SKILLS[2], "misconduct_investigation", "synthetic_investigations_legal_hr", "legal_restricted")
    m = {"authorized": True, "allegation_ids": ["AL-SVC"], "allowed_evidence_types": ["ledger_export", "email_export", "interview_notes"], "legal_owner": "SYNTHETIC-LEGAL-OWNER", "hr_owner": "SYNTHETIC-HR-OWNER"}
    p.doc["data"] = {"mandate": {k:p.claim("mandate." + k, v, "SYN-MANDATE-POLICY") for k,v in m.items()},
        "allegations": [p.row("allegation_id", "AL-SVC", {"description": "Allegation that EMP-44 deliberately overrode the intermediary invoice control to conceal an unsupported service fee."})], "events": [], "plans": []}
    return p

def event(p, label, date, proposition, evidence="ledger_export", hypothesis="EMP-44 intentionally bypassed invoice control", polarity="supports", allegation="AL-SVC", ref="SYN-RECORDS"):
    vals = {"allegation_id": allegation, "occurred_on": date, "proposition": proposition, "evidence_type": evidence, "hypothesis": hypothesis, "polarity": polarity}
    return {"event_id": label, **{k:p.claim(label + "." + k,v,ref) for k,v in vals.items()}}

p = misconduct_packet("misconduct-realistic")
p.doc["data"]["events"] = [
    event(p,"OVERRIDE","2026-10-01","Ledger export records EMP-44 override of invoice verification."),
    event(p,"SUPERVISOR-APPROVAL","2026-09-27","Email states supervisor permitted exception after review of staged milestones.","email_export",polarity="contradicts"),
    event(p,"AUTOMATED-CORRECTION","2026-09-28","Batch correction record reports mapping repair changed invoice flag.",hypothesis="Automated mapping correction explains apparent override"),
    event(p,"CREDIT-NOTE","2026-09-30","Credit note reverses duplicate invoice; intention is not stated.",polarity="neutral")]
p.doc["data"]["plans"] = [
    p.row("plan_id","NEUTRAL-INTERVIEW", {"allegation_id":"AL-SVC","evidence_type":"interview_notes","purpose":"Ask EMP-44 and supervisor separately: what instruction preceded the 2026-10-01 override, which milestones were verified, and could the 2026-09-28 mapping correction explain it?"}),
    p.row("plan_id","UNAUTHORIZED-PHONE", {"allegation_id":"AL-SVC","evidence_type":"personal_device_forensic","purpose":"Proposed personal-phone imaging to locate missing service correspondence; requires a new approved mandate and Legal/HR collection review."})]
cases.append(p.save("Support the authorized invoice-control investigation using dated records, competing explanations and a neutral interview plan; identify the out-of-scope personal-device proposal.",
    ["Timeline ordered 2026-09-27, 2026-09-28, 2026-09-30, 2026-10-01, independent of input order.", "First hypothesis has supports OVERRIDE, contradicts SUPERVISOR-APPROVAL and neutral CREDIT-NOTE; contradiction unresolved.", "Alternative automation hypothesis retained; neutral interview is within supplied evidence scope; phone forensic is outside."],
    ["Intent, guilt, independence, privilege and employment outcome remain unadjudicated; no contact or collection performed."], ["Contrary evidence", "Alternative hypothesis", "Mandate-limited collection"], check_ids=["mi_timeline", "mi_hypotheses", "mi_plans"]))

p = misconduct_packet("misconduct-unknown-polarity")
p.doc["data"]["events"] = [event(p,"AMBIGUOUS-RECORD","2026-09-30","Ledger annotation cannot yet be interpreted as support or counterevidence.",polarity="unknown")]
p.doc["data"]["plans"] = [p.row("plan_id","CLARIFY-ANNOTATION", {"allegation_id":"AL-SVC","evidence_type":"interview_notes","purpose":"Ask the ledger custodian to explain the annotation without assuming intent."})]
cases.append(p.save("Retain an ambiguous observed annotation whose polarity is unknown pending custodian explanation.",
    ["An accepted schema value should be processed without an unhandled error; ambiguity stays visible."],
    ["Unknown polarity should not be assigned to support/contradiction or guilt; hypothesis effect withheld."], ["Authoritative executable schema accepts unknown polarity"], check_ids=["mi_unknown_polarity"]))

p = misconduct_packet("misconduct-event-receipt-date")
p.source("SYN-EARLY-EXPORT", received="2026-09-30", published="2026-09-29")
p.doc["data"]["events"] = [event(p,"POST-RECEIPT-EVENT","2026-10-01","Export received on 2026-09-30 purports to observe a 2026-10-01 override.",ref="SYN-EARLY-EXPORT")]
p.doc["data"]["plans"] = [p.row("plan_id","REEXPORT", {"allegation_id":"AL-SVC","evidence_type":"ledger_export","purpose":"Request authorized custodian reconciliation of receipt and observed dates."})]
cases.append(p.save("Check a ledger record claiming an event after the source was received, while the event is before the review cutoff.",
    ["POST-RECEIPT-EVENT is excluded from eligible timeline/hypothesis support due to source receipt chronology."],
    ["No supported timeline evidence; actual event chronology remains unverified."], ["Event occurrence versus source receipt versus cutoff"], check_ids=["mi_receipt"]))

def customer_packet(case, **overrides):
    p = Packet(case, SKILLS[3], "customer_conduct_review", "synthetic_conduct_product")
    scope = {"product":"Synthetic retail overdraft", "distribution_role":"manufacturer and direct distributor", "window_from":"2026-07-01", "window_to":"2026-09-30", "metric":"support-friction customer harm rate",
        "numerator_definition":"Unique observed customers with at least one confirmed harmful support-friction outcome in the window",
        "denominator_definition":"Unique eligible customers whose support outcomes were observed in the window",
        "segmentation_basis":"All eligible customers plus overlapping vulnerability and channel segments; cohort counts must not be summed",
        "vulnerability_method":"Supplied customer-consented vulnerability flags at window start; missing flags remain unclassified",
        "expected_cohorts":["ALL", "VULNERABLE", "ASSISTED-DIGITAL", "MOBILE-ONLY", "SWITCHERS"]}
    scope.update(overrides)
    p.doc["data"] = {"review":{k:p.claim("review."+k,v,"SYN-MANDATE-POLICY") for k,v in scope.items()}, "cohorts":[]}
    return p

def cohort(p, label, population, observed, harms, vulnerable=False, value=(), support=(), threshold=0.02):
    return p.row("cohort_id", label, {"population":population,"observed":observed,"harms":harms,"vulnerable":vulnerable,"value_barriers":list(value),"support_barriers":list(support),"threshold_rate":threshold}, ("threshold_rate",))

p = customer_packet("customer-realistic")
p.doc["data"]["cohorts"] = [cohort(p,"ALL",1000,800,24,support=["Long call queues in observed branch-to-phone referrals"]),
    cohort(p,"VULNERABLE",120,60,9,True,value=["Repeat fees during support delays"],support=["Required callback could not use relay support"]),
    cohort(p,"ASSISTED-DIGITAL",75,0,0), cohort(p,"MOBILE-ONLY",150,150,0)]
cases.append(p.save("Assess quarterly overdraft support harm by overlapping cohort, retaining partial coverage, missing switchers and vulnerable customer barriers.",
    ["ALL harm rate 24/800=0.03 and coverage 800/1000=0.8; exceeds 0.02.", "VULNERABLE 9/60=0.15 and coverage 60/120=0.5; exceeds 0.02, retaining value/support barriers.", "MOBILE-ONLY valid zero harms produces observed 0 and coverage 1.", "ASSISTED-DIGITAL zero observed denominator yields null harm rate and coverage 0; SWITCHERS missing; overlapping cohorts not summed."],
    ["Whole-population good outcomes, selection bias and causal harm remain unestablished; individual complaints not resolved."], ["Zero numerator versus zero denominator", "Partial samples", "Missing expected group", "Vulnerable segment"], check_ids=["cc_rates", "cc_missing", "cc_zero"]))

p = customer_packet("customer-unit-mismatch", numerator_definition="Count of repeat support-friction EVENTS; one observed customer may contribute multiple harm events", expected_cohorts=["ALL"])
p.doc["data"]["cohorts"] = [cohort(p,"ALL",150,100,42)]
cases.append(p.save("Review 42 repeated harm events among 100 unique observed customers; do not present events/customer as a unique-customer harm proportion.",
    ["The supplied definitions explicitly declare incompatible event/customer grain and need metric reconstruction."],
    ["Unique-customer harm rate and criterion comparison withheld until the numerator is deduplicated to customers, or a correctly labeled events/customer metric is separately defined."], ["Numerator and denominator units differ despite numerically valid counts"], check_ids=["cc_unit_mismatch"]))

p = customer_packet("customer-unknown-zero", expected_cohorts=["UNKNOWN-DENOM", "ZERO-POP", "MISSING-FLAG"])
p.doc["data"]["cohorts"] = [cohort(p,"UNKNOWN-DENOM",200,None,0), cohort(p,"ZERO-POP",0,0,0), cohort(p,"MISSING-FLAG",50,50,0,vulnerable=None)]
cases.append(p.save("Preserve unknown observations, an empty eligible population, and unknown vulnerability flags without converting them to favorable outcomes.",
    ["MISSING-FLAG can report an observed zero harm rate with known counts while retaining unknown vulnerability segmentation."],
    ["UNKNOWN-DENOM and ZERO-POP harm rate/threshold withheld; missing denominator/zero population cannot establish good outcomes."], ["Unknown and zero remain distinct", "Missing vulnerability classification"], check_ids=["cc_unknown_zero"]))

p = customer_packet("customer-malformed-count", expected_cohorts=["ALL"])
p.doc["data"]["cohorts"] = [cohort(p,"ALL",150,100,101)]
cases.append(p.save("Request a rate from a numerator exceeding the observed denominator; route to intake correction.",
    ["Structural intake rejects harm numerator 101 > denominator 100; calculator must stop rather than emit a rate."], [], ["Count reconciliation"], expected_intake="reject", check_ids=["cc_bad_count"]))

package_hashes = {}
for skill in SKILLS:
    package = ROOT / "skills" / "compliance-financial-crime" / skill
    package_hashes[skill] = {str(f.relative_to(ROOT)):sha(f) for f in sorted(package.rglob("*")) if f.is_file() and "__pycache__" not in f.parts}
manifest = {"prepared_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
    "repo_root": str(ROOT), "method": "Fresh synthetic requests, original supplied facts and explicit expectations frozen before actual installed CLI execution. No implementation-agent notes or prior outputs consulted.",
    "cases": cases, "pre_run_package_file_sha256": package_hashes}
dump(OUT / "pre-run-manifest.json", manifest)
print(json.dumps({"cases_frozen":len(cases), "directory":str(OUT)},indent=2))
