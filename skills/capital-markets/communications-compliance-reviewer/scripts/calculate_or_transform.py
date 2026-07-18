#!/usr/bin/env python3
"""Deterministic communications-compliance rule engine for communications-compliance-reviewer.

Reads one communication record (see validate_input.py), classifies it under the
communications rulebook, runs the configured content / disclosure / supervision / retention /
escalation checks, attaches cited evidence to every finding, and maps the fired findings to a
recommended review disposition band.

IMPORTANT: this produces *findings, cited evidence, and a recommended disposition for a
registered principal to adjudicate* only. It never approves a communication, clears it for
use, files it, or closes a review. The disposition mapping is deterministic and documented in
references/domain-rules.md. Rule citations are orientation labels; the firm's Written
Supervisory Procedures (WSPs) and current rule text govern.

Usage:
  python calculate_or_transform.py communication.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Advisory compliance review only; not a supervisory approval, regulated "
              "determination, or filing. A registered principal must independently review and "
              "adjudicate this communication before any use, distribution, regulatory filing, "
              "or review closure.")

# ---- rule library (config-overridable via doc['config']) --------------------------------
PROHIBITED_PATTERNS = [
    (r"guarantee[ds]?\b", "guarantee of performance or return"),
    (r"guaranteed\s+\d+(\.\d+)?\s*%", "guaranteed specific return"),
    (r"risk[- ]free", "'risk-free' claim"),
    (r"\bno risk\b", "'no risk' claim"),
    (r"riskless", "'riskless' claim"),
    (r"can(?:'|no|not| ?)t lose", "'cannot lose money' claim"),
    (r"\bpromise[ds]?\b", "promissory statement"),
    (r"assured\s+returns?", "assured-return claim"),
]
PREDICTION_PATTERNS = [
    (r"we\s+predict\b", "prediction of future performance"),
    (r"will\s+(double|triple|grow|increase|rise|outperform|beat)", "prediction of future performance"),
    (r"projected?\s+(returns?|growth|gains?|performance)", "projection of performance"),
]
MNPI_PATTERNS = [
    (r"material non-?public", "possible material non-public information"),
    (r"\bmnpi\b", "possible material non-public information"),
    (r"inside information", "possible inside information reference"),
    (r"not yet public", "reference to not-yet-public information"),
    (r"before the (public )?announcement", "pre-announcement information reference"),
]
ABUSE_PATTERNS = [
    (r"pump", "possible market-manipulation reference"),
    (r"manipulat", "possible market-manipulation reference"),
    (r"front[- ]run", "possible front-running reference"),
    (r"spoof", "possible spoofing reference"),
    (r"wash trade", "possible wash-trade reference"),
]
COMPLAINT_PATTERNS = [
    (r"\bcomplaint\b", "possible customer complaint"),
    (r"unauthorized trade", "alleged unauthorized activity"),
    (r"misrepresent", "allegation of misrepresentation"),
    (r"\bsue\b|lawsuit|attorney general", "threatened legal / regulatory action"),
]
BENEFIT_TERMS = ["return", "returns", "profit", "profits", "gain", "gains", "grow", "growth",
                 "outperform", "fortune", "fortunes", "wealth", "upside", "high yield"]
PERFORMANCE_TERMS = ["return", "returns", "performance", "yield", "%", "gain", "gains",
                     "made fortunes", "track record"]
TESTIMONIAL_TERMS = ["testimonial", "clients say", "client says", "past clients", "made fortunes",
                     "my advisor made", "review from a client"]

SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


def _cfg(doc: dict) -> dict:
    cfg = {"retail_threshold": 25}
    cfg.update(doc.get("config") or {})
    return cfg


def _cite(doc: dict) -> str:
    return f"comm:{doc.get('source_ref', '?')}@{doc.get('as_of', '?')}"


def _scan(body_low: str, patterns) -> list[tuple[str, str]]:
    """Return (matched_text, label) for each pattern that hits."""
    out = []
    for pat, label in patterns:
        m = re.search(pat, body_low)
        if m:
            out.append((m.group(0), label))
    return out


def classify(doc: dict, cfg: dict) -> str:
    aud = str(doc.get("audience"))
    if aud == "internal":
        return "internal"
    if aud == "institutional":
        return "institutional communication"
    # retail
    rc = doc.get("recipient_count")
    try:
        rc = int(rc)
    except (TypeError, ValueError):
        rc = None
    if rc is not None and rc <= cfg["retail_threshold"]:
        return "correspondence"
    return "retail communication"  # conservative default when count is missing/large


def compute(doc: dict) -> dict:
    cfg = _cfg(doc)
    body = str(doc.get("body") or "")
    low = body.lower()
    cls = classify(doc, cfg)
    present = {str(x).lower() for x in (doc.get("disclosures_present") or [])}
    cite = _cite(doc)
    findings: list[dict] = []
    escalation_routes: list[dict] = []

    is_public = cls in ("retail communication", "correspondence", "institutional communication")
    is_retail = cls in ("retail communication", "correspondence")

    def add(ftype, rule, severity, reason, evidence, remediation):
        findings.append({"finding_type": ftype, "rule": rule, "severity": severity,
                         "reason": reason, "evidence": evidence, "remediation": remediation})

    # 1. prohibited / promissory claims (all public comms; still relevant internally for MNPI only)
    if is_public:
        hits = _scan(low, PROHIBITED_PATTERNS)
        if hits:
            add("prohibited_claim", "FINRA Rule 2210(d)(1)", "high",
                "communication contains prohibited promissory, guarantee, or 'no-risk' language",
                [{"quote": q, "issue": lbl, "location": "body", "citation": cite} for q, lbl in hits],
                "Remove or substantiate; guarantees, 'risk-free', and 'cannot-lose' claims are prohibited.")

        # 2. predictions / projections of performance
        phits = _scan(low, PREDICTION_PATTERNS)
        if phits:
            add("performance_prediction", "FINRA Rule 2210(d)(1)(F)", "high",
                "communication predicts or projects future investment performance",
                [{"quote": q, "issue": lbl, "location": "body", "citation": cite} for q, lbl in phits],
                "Remove predictions/projections of performance or limit to permitted projection use with basis and disclosures.")

        # 3. fair & balanced (benefits without a risk disclosure)
        benefit_hits = [t for t in BENEFIT_TERMS if t in low]
        if benefit_hits and "risk_disclosure" not in present:
            add("fair_and_balanced", "FINRA Rule 2210(d)(1)(A)", "medium",
                "benefits/returns are described without a corresponding risk disclosure (one-sided)",
                [{"quote": ", ".join(sorted(set(benefit_hits))), "issue": "no risk_disclosure tag present",
                  "location": "body", "citation": cite}],
                "Add balanced discussion of material risks and a risk disclosure.")

    # 4. required disclosures (retail communications and correspondence)
    if is_retail:
        missing = []
        if "firm_name" not in present:
            missing.append({"quote": "firm/member name disclosure", "issue": "member identity not disclosed",
                            "location": "disclosures", "citation": cite})
        perf_mentioned = any(t in low for t in PERFORMANCE_TERMS)
        if perf_mentioned and "past_performance" not in present:
            missing.append({"quote": "past-performance disclaimer", "issue": "performance discussed without disclaimer",
                            "location": "disclosures", "citation": cite})
        if str(doc.get("channel")) in ("website", "social_media") and "brokercheck" not in present:
            missing.append({"quote": "BrokerCheck reference", "issue": "retail website/social without BrokerCheck reference",
                            "location": "disclosures", "citation": cite})
        testimonial = bool(doc.get("contains_testimonial")) or any(t in low for t in TESTIMONIAL_TERMS)
        if testimonial and "testimonial_disclosure" not in present:
            missing.append({"quote": "testimonial disclosures", "issue": "testimonial without required disclosures",
                            "location": "body", "citation": cite})
        if missing:
            add("missing_required_disclosure", "FINRA Rule 2210(d)", "medium",
                "one or more required disclosures for this communication class are absent",
                missing,
                "Add each missing required disclosure before the communication is used.")

    # 5. supervision
    sup = doc.get("supervision") if isinstance(doc.get("supervision"), dict) else {}
    if cls == "retail communication":
        if not sup.get("principal_pre_approved"):
            add("supervision_gap", "FINRA Rule 2210(b)(1) / Rule 3110", "high",
                "retail communication has no registered-principal pre-approval before first use",
                [{"quote": "principal_pre_approved=" + str(sup.get("principal_pre_approved")),
                  "issue": "no principal pre-approval on record", "location": "supervision", "citation": cite}],
                "Obtain registered-principal (e.g., Series 24/26) pre-approval before first use.")
    else:
        if not sup.get("reviewed") and not sup.get("principal_pre_approved"):
            add("supervision_gap", "FINRA Rule 3110(b)", "medium",
                f"{cls} has no supervisory review on record",
                [{"quote": "reviewed=" + str(sup.get("reviewed")),
                  "issue": "no supervisory review on record", "location": "supervision", "citation": cite}],
                "Evidence supervisory review per the firm's WSPs.")

    # 6. retention / recordkeeping
    ret = doc.get("retention") if isinstance(doc.get("retention"), dict) else {}
    if ret.get("channel_approved") is False:
        add("off_channel", "SEC Rule 17a-4 / FINRA Rule 4511", "high",
            "business communication sent on an unapproved (off-channel) medium not captured for retention",
            [{"quote": "channel=" + str(doc.get("channel")) + "; channel_approved=false",
              "issue": "off-channel business communication", "location": "retention", "citation": cite}],
            "Move to an approved, captured channel; ensure the record is retained in an approved archive.")
    elif not ret.get("archived"):
        add("retention_gap", "SEC Rule 17a-4 / FINRA Rule 4511", "medium",
            "communication is not recorded as archived in an approved retention system",
            [{"quote": "archived=" + str(ret.get("archived")),
              "issue": "not archived", "location": "retention", "citation": cite}],
            "Confirm the communication is captured and retained in the approved archive.")

    # 7. escalation (all communications, incl. internal)
    esc_ev = []
    for q, lbl in _scan(low, MNPI_PATTERNS) + _scan(low, ABUSE_PATTERNS):
        esc_ev.append({"quote": q, "issue": lbl, "location": "body", "citation": cite})
    if esc_ev:
        add("escalation_needed", "FINRA Rule 3110 supervision / market-conduct", "high",
            "communication contains language that may indicate MNPI misuse or market abuse",
            esc_ev,
            "Do not adjudicate here; route to electronic-communications surveillance.")
        escalation_routes.append({"reason": "possible MNPI / market abuse",
                                   "route_to": "surveillance-alert-triager",
                                   "then": "market-surveillance-alert-investigator"})
    comp_ev = [{"quote": q, "issue": lbl, "location": "body", "citation": cite}
               for q, lbl in _scan(low, COMPLAINT_PATTERNS)]
    if comp_ev:
        add("escalation_needed", "FINRA Rule 4513 / Rule 4530 (complaints)", "high",
            "communication appears to contain or reference a customer complaint",
            comp_ev,
            "Do not adjudicate here; route to complaint handling.")
        escalation_routes.append({"reason": "possible customer complaint",
                                   "route_to": "complaint-resolution-assistant"})

    # ---- deterministic disposition mapping (see references/domain-rules.md) ---------------
    sevs = {f["severity"] for f in findings}
    if "high" in sevs:
        disposition = "Escalate"
    elif "medium" in sevs:
        disposition = "Remediate"
    elif "low" in sevs:
        disposition = "Advisory"
    else:
        disposition = "No-exceptions"

    remediation_prompts = []
    if findings:
        seen = set()
        for f in findings:
            if f["remediation"] not in seen:
                seen.add(f["remediation"])
                remediation_prompts.append(f["remediation"])

    fired = sorted({f["finding_type"] for f in findings})
    return {
        "review_id": f"ccr-{doc['comm_id']}-{doc['as_of']}-0001",
        "comm_id": doc["comm_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "classification": cls,
        "findings": findings,
        "fired_finding_types": fired,
        "recommended_disposition": disposition,
        "escalation_routes": escalation_routes,
        "remediation_prompts": remediation_prompts,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "communication_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
