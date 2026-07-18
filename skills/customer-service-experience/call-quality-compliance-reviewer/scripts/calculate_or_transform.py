#!/usr/bin/env python3
"""Deterministic, explainable quality/compliance review for call-quality-compliance-reviewer.

Reads an interaction file (see validate_input.py), runs the configured rubric checks over
the turns, attaches evidence + citations to each fired finding, and maps the fired set to a
suggested QA disposition band. Emits a machine-readable core the SKILL wraps in a
plain-language review.

IMPORTANT: This produces explainable *findings and a triage suggestion* only. It never
produces a determination of agent misconduct, a regulatory-breach finding, a pass/fail
score that drives discipline, or any action. The disposition mapping is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py interaction.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Quality-review evidence only; not a determination of misconduct, a "
              "regulatory breach, or a disciplinary decision. No action has been taken.")

# Severity of each rubric check. "critical" = compliance-critical (routes to human
# compliance review); "coaching" = quality/soft (routes to coaching). Severity drives the
# deterministic disposition band; it is NOT a determination.
CRITICAL = {"recording_consent_disclosure", "identity_authentication",
            "required_disclosures", "prohibited_language", "fair_treatment_vulnerability"}
COACHING = {"complaint_acknowledgement", "commitment_capture", "empathy_courtesy"}

# Default rubric markers/lexicon (overridden by doc['rubric']; versioned in deployment).
DEFAULT_RUBRIC = {
    "recording_notice_markers": [
        "this call is being recorded", "call may be recorded", "recorded for quality",
        "monitored or recorded", "recorded and monitored"],
    "auth_completed_markers": [
        "identity verified", "you are verified", "you're verified", "thanks for verifying",
        "verification complete", "successfully verified", "passed verification"],
    "account_specific_markers": [
        "your balance", "account balance", "available balance", "your account number",
        "recent transactions", "your payment is due", "outstanding balance",
        "your card ending"],
    "required_disclosures": [
        {"id": "mini_miranda", "products": ["collections"],
         "markers": ["attempt to collect a debt", "information obtained will be used"]},
        {"id": "apr_disclosure", "products": ["lending"],
         "markers": ["annual percentage rate", "apr of", "the apr"]},
        {"id": "investment_risk_disclosure", "products": ["investment"],
         "markers": ["past performance", "may lose value", "involves risk", "not guaranteed"]},
    ],
    "prohibited_lexicon": [
        {"id": "guaranteed_return", "phrases": [
            "guaranteed return", "guaranteed profit", "risk-free", "cannot lose",
            "can't lose", "no risk at all"]},
        {"id": "absolute_promise", "phrases": [
            "you will definitely", "i promise you will", "100% approved", "guaranteed approval"]},
        {"id": "improper_threat", "phrases": [
            "have you arrested", "send someone to your house", "garnish your wages today"]},
    ],
    "vulnerability_markers": [
        "passed away", "bereavement", "lost my job", "disability", "can't afford",
        "cannot afford", "struggling to pay", "mental health", "financial hardship",
        "recently widowed"],
    "accommodation_markers": [
        "take your time", "i can note that", "specialist team", "hardship program",
        "support options", "refer you to", "extra support", "breathing space"],
    "complaint_markers": [
        "want to complain", "make a complaint", "not happy", "unacceptable",
        "speak to a manager", "terrible service", "this is a complaint"],
    "complaint_ack_markers": [
        "i'm sorry", "i am sorry", "apologize", "apologise", "raise a complaint",
        "log this", "escalate this", "complaint reference"],
    "commitment_markers": [
        "i'll call you back", "i will call you back", "we'll refund", "we will refund",
        "i'll send", "we will process", "follow up with you", "get back to you",
        "i'll arrange"],
    "distress_markers": [
        "i'm really worried", "i am worried", "this is stressful", "i'm scared",
        "i'm panicking", "desperate", "at my wits"],
    "empathy_markers": [
        "i understand", "i can imagine", "that sounds", "i'm here to help",
        "i hear you", "let me help", "i'm sorry to hear"],
    "disclosure_deadline_turns": 4,
}


def _low(s) -> str:
    return str(s or "").lower()


def _cite(interaction_id: str, turn: dict) -> str:
    ref = f"transcript:int={interaction_id};turn={turn.get('turn_id', '?')}"
    return ref + (f"@{turn['ts']}" if turn.get("ts") else "")


def _scope_cite(interaction_id: str, scan: str, n: int) -> str:
    return f"transcript:int={interaction_id};scan={scan};agent_turns={n}"


def _has_marker(text: str, markers: list) -> bool:
    t = _low(text)
    return any(m in t for m in markers)


def compute(doc: dict) -> dict:
    rb = {**DEFAULT_RUBRIC, **(doc.get("rubric") or {})}
    interaction_id = doc["interaction_id"]
    channel = doc["channel"]
    ctx = doc.get("context") or {}
    requires_auth = bool(ctx.get("requires_authentication"))
    product = _low(ctx.get("product_context")) or "general"
    stated_vuln = bool(ctx.get("customer_stated_vulnerability"))

    turns = list(doc["turns"])  # preserve given order (ts is best-effort)
    agent_turns = [t for t in turns if t.get("speaker") == "agent"]
    customer_turns = [t for t in turns if t.get("speaker") == "customer"]
    n_agent = len(agent_turns)

    findings, not_evaluable = [], []

    def add(check, fired, reason, evidence, rubric_ref):
        findings.append({
            "check": check, "severity": "critical" if check in CRITICAL else "coaching",
            "fired": fired, "reason": reason, "evidence": evidence, "rubric_ref": rubric_ref})

    # ---- recording_consent_disclosure (voice only) ----
    if channel == "voice":
        deadline = rb["disclosure_deadline_turns"]
        early = agent_turns[:deadline] + [t for t in turns if t.get("speaker") == "ivr"][:deadline]
        hit = next((t for t in early if _has_marker(t.get("text"), rb["recording_notice_markers"])), None)
        fired = hit is None
        ev = ([{"turn_id": hit["turn_id"], "quote": "recording notice present",
                "citation": _cite(interaction_id, hit)}] if hit
              else [{"scope": "early_agent_or_ivr_turns", "turns_scanned": len(early),
                     "citation": _scope_cite(interaction_id, "recording_notice", n_agent)}])
        add("recording_consent_disclosure", fired,
            f"no call recording/monitoring notice in the first {deadline} agent/IVR turns"
            if fired else "recording/monitoring notice present",
            ev, "rubric.recording_notice_markers")
    else:
        not_evaluable.append({"check": "recording_consent_disclosure", "why": f"channel={channel}"})

    # ---- identity_authentication (when required) ----
    if requires_auth:
        # index of first account-specific disclosure vs first auth-complete marker
        first_auth = next((i for i, t in enumerate(turns)
                           if t.get("speaker") == "agent" and _has_marker(t.get("text"), rb["auth_completed_markers"])), None)
        first_acct = next((i for i, t in enumerate(turns)
                           if t.get("speaker") == "agent" and _has_marker(t.get("text"), rb["account_specific_markers"])), None)
        if first_auth is None:
            fired, reason = True, "authentication was required but no verification-complete marker was found"
            ev = [{"scope": "agent_turns", "turns_scanned": n_agent,
                   "citation": _scope_cite(interaction_id, "auth_completed", n_agent)}]
        elif first_acct is not None and first_acct < first_auth:
            fired = True
            leak = turns[first_acct]
            reason = "account-specific information was disclosed before authentication completed"
            ev = [{"turn_id": leak["turn_id"], "quote": "account-specific disclosure before auth",
                   "citation": _cite(interaction_id, leak)}]
        else:
            fired, reason = False, "authentication completed before account-specific disclosure"
            ev = [{"turn_id": turns[first_auth]["turn_id"], "quote": "verification complete",
                   "citation": _cite(interaction_id, turns[first_auth])}]
        add("identity_authentication", fired, reason, ev, "rubric.auth_completed_markers")
    else:
        not_evaluable.append({"check": "identity_authentication", "why": "requires_authentication is false"})

    # ---- required_disclosures (product-specific; one finding per applicable item) ----
    applicable = [d for d in rb["required_disclosures"] if product in [_low(p) for p in d.get("products", [])]]
    if applicable:
        agent_text = " ".join(_low(t.get("text")) for t in agent_turns)
        for d in applicable:
            present = any(m in agent_text for m in d["markers"])
            ev = ([{"scope": "agent_turns", "turns_scanned": n_agent,
                    "citation": _scope_cite(interaction_id, f"disclosure_{d['id']}", n_agent)}])
            add("required_disclosures", not present,
                f"required disclosure '{d['id']}' for product '{product}' not detected"
                if not present else f"required disclosure '{d['id']}' present",
                ev, f"rubric.required_disclosures[{d['id']}]")
    else:
        not_evaluable.append({"check": "required_disclosures", "why": f"no required disclosure configured for product '{product}'"})

    # ---- prohibited_language ----
    hits = []
    for t in agent_turns:
        tl = _low(t.get("text"))
        for item in rb["prohibited_lexicon"]:
            for phrase in item["phrases"]:
                if phrase in tl:
                    hits.append({"turn_id": t["turn_id"], "category": item["id"],
                                 "phrase": phrase, "citation": _cite(interaction_id, t)})
    add("prohibited_language", bool(hits),
        f"{len(hits)} prohibited-language match(es) in agent turns" if hits else "no prohibited language detected",
        hits, "rubric.prohibited_lexicon")

    # ---- fair_treatment_vulnerability ----
    vuln_turns = [t for t in customer_turns if _has_marker(t.get("text"), rb["vulnerability_markers"])]
    if stated_vuln or vuln_turns:
        acknowledged = any(_has_marker(t.get("text"), rb["accommodation_markers"]) for t in agent_turns)
        ev = [{"turn_id": t["turn_id"], "quote": "customer vulnerability cue",
               "citation": _cite(interaction_id, t)} for t in vuln_turns] or \
             [{"scope": "context.customer_stated_vulnerability", "turns_scanned": n_agent,
               "citation": _scope_cite(interaction_id, "vulnerability_context", n_agent)}]
        add("fair_treatment_vulnerability", not acknowledged,
            "customer vulnerability cue present but no accommodation/referral offered by agent"
            if not acknowledged else "vulnerability acknowledged with accommodation/referral",
            ev, "rubric.accommodation_markers")
    else:
        not_evaluable.append({"check": "fair_treatment_vulnerability", "why": "no vulnerability cue in context or customer turns"})

    # ---- complaint_acknowledgement (coaching) ----
    comp_turns = [t for t in customer_turns if _has_marker(t.get("text"), rb["complaint_markers"])]
    if comp_turns:
        ack = any(_has_marker(t.get("text"), rb["complaint_ack_markers"]) for t in agent_turns)
        add("complaint_acknowledgement", not ack,
            "customer expressed a complaint but the agent did not acknowledge/log/route it"
            if not ack else "complaint acknowledged",
            [{"turn_id": t["turn_id"], "quote": "complaint cue", "citation": _cite(interaction_id, t)} for t in comp_turns],
            "rubric.complaint_markers")
    else:
        not_evaluable.append({"check": "complaint_acknowledgement", "why": "no complaint cue in customer turns"})

    # ---- commitment_capture (coaching) ----
    commit_turns = [t for t in agent_turns if _has_marker(t.get("text"), rb["commitment_markers"])]
    add("commitment_capture", bool(commit_turns),
        f"{len(commit_turns)} agent commitment(s) to capture as follow-up" if commit_turns else "no explicit agent commitments detected",
        [{"turn_id": t["turn_id"], "quote": "agent commitment", "citation": _cite(interaction_id, t)} for t in commit_turns],
        "rubric.commitment_markers")

    # ---- empathy_courtesy (coaching) ----
    distress_turns = [t for t in customer_turns if _has_marker(t.get("text"), rb["distress_markers"])]
    if distress_turns:
        empathy = any(_has_marker(t.get("text"), rb["empathy_markers"]) for t in agent_turns)
        add("empathy_courtesy", not empathy,
            "customer distress cue present but no empathy acknowledgement by agent"
            if not empathy else "empathy acknowledgement present",
            [{"turn_id": t["turn_id"], "quote": "customer distress cue", "citation": _cite(interaction_id, t)} for t in distress_turns],
            "rubric.empathy_markers")
    else:
        not_evaluable.append({"check": "empathy_courtesy", "why": "no distress cue in customer turns"})

    fired = [f for f in findings if f["fired"]]
    fired_critical = [f["check"] for f in fired if f["severity"] == "critical"]
    fired_coaching = [f["check"] for f in fired if f["severity"] == "coaching"]

    # deterministic disposition mapping (see references/domain-rules.md)
    if fired_critical:
        disposition = "Compliance review required"
    elif fired_coaching:
        disposition = "Coaching recommended"
    else:
        disposition = "Meets expectations"

    considerations = []
    if fired:
        considerations = [
            "recording/authentication may have occurred in an IVR segment or prior transfer not in this transcript",
            "a required disclosure may have been delivered in writing (email/SMS) outside the audio",
            "ASR/transcription errors can hide a spoken marker — spot-check the audio before dispositioning",
            "partial or redacted transcript can suppress a marker that was actually present",
            "product_context may be mislabeled, changing which disclosures are required",
        ]

    return {
        "review_id": f"cqc-{interaction_id}-{doc['as_of']}-0001",
        "interaction_id": interaction_id,
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "channel": channel,
        "product_context": product,
        "findings": findings,
        "fired_findings": [f["check"] for f in fired],
        "fired_critical": fired_critical,
        "fired_coaching": fired_coaching,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "considerations": considerations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "interaction_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
