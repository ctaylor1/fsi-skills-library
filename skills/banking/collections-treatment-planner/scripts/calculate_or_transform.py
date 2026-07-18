#!/usr/bin/env python3
"""Deterministic collections treatment-option engine for collections-treatment-planner.

Reads a de-identified collections case file (see validate_input.py), derives the
delinquency band, runs the contact-suppression and contact-frequency screens, flags
enhanced-care handling for vulnerability, and maps the case to the set of *eligible*
treatment options with policy citations and eligibility evidence. It emits a machine
-readable core the SKILL wraps in a plain-language recommendation pack.

IMPORTANT (R3 decision-support): this produces treatment *recommendations and evidence*
only. Every option and every outreach action requires human adjudication and authorization.
The engine NEVER approves a treatment, sets up an arrangement, closes a case, files, reports
to a bureau, or writes any system of record. Eligibility rules are configuration (versioned,
owned by collections policy), documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py case.json | --selftest
Prints the treatment-plan JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CONFIG = {
    "call_cap_window_days": 7,   # Reg F 7-in-7 call-frequency presumption window
    "call_cap": 7,               # presumed max phone attempts per debt within the window
    "band_early_max": 29,        # 1..29 DPD -> Early
    "band_mid_max": 59,          # 30..59 DPD -> Mid
    "band_late_max": 89,         # 60..89 DPD -> Late ; 90+ -> Severe
    "reminder_max_dpd": 89,
    "due_date_change_max_dpd": 29,
    "arrangement_min_dpd": 30,
    "settlement_min_dpd": 90,
    "re_age_min_dpd": 60,
}

DISCLAIMER = (
    "Recommendations and evidence only; every treatment option and outreach action requires "
    "human adjudication and authorization. No collections decision has been made, no case has "
    "been closed, and no system of record has been updated."
)


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _band(dpd: int, cfg: dict) -> str:
    if dpd <= 0:
        return "Current"
    if dpd <= cfg["band_early_max"]:
        return "Early"
    if dpd <= cfg["band_mid_max"]:
        return "Mid"
    if dpd <= cfg["band_late_max"]:
        return "Late"
    return "Severe"


def _pol(rule_id: str, cfg_version) -> str:
    return f"policy:{rule_id}@{cfg_version}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    cfg_ver = doc.get("config_version")
    dpd = int(doc["days_past_due"])
    band = _band(dpd, cfg)
    as_of = _parse_dt(doc["as_of"])
    src = f"case:acct={doc['account_id']};as_of={doc['as_of']}"

    # --- suppression screen (hard boundary: honor legal/consent suppressions) ---
    sup = doc.get("suppression") or {}
    sup_reasons = []
    if sup.get("cease_communication"):
        sup_reasons.append("cease-communication request on file (FDCPA 1692c(c)) — halt outreach except permitted notices")
    if sup.get("attorney_represented"):
        sup_reasons.append("consumer is attorney-represented — route contact through counsel, not the consumer")
    if sup.get("dispute_pending"):
        sup_reasons.append("debt/validation dispute pending — pause collection outreach until resolved")
    if sup.get("do_not_contact_window_active"):
        sup_reasons.append("do-not-contact window active — no outreach during the restricted window")
    if sup.get("bankruptcy_flag"):
        sup_reasons.append("bankruptcy flag — automatic-stay handling; route to specialized workflow")
    outreach_suppressed = bool(sup_reasons)

    # --- contact-frequency screen (Reg F 7-in-7 call presumption) ---
    window_start = as_of - timedelta(days=cfg["call_cap_window_days"])
    calls = [c for c in (doc.get("contact_history") or [])
             if str(c.get("channel")) == "phone" and window_start <= _parse_dt(c["date"]) <= as_of]
    calls_last = len(calls)
    calls_remaining = max(0, cfg["call_cap"] - calls_last)
    phone_eligible = (calls_remaining > 0) and not outreach_suppressed

    # --- enhanced-care (vulnerability) screen ---
    vind = list(doc.get("vulnerability_indicators") or [])
    enhanced_care = bool(vind)

    # --- affordability (indicative only; never a credit/affordability decision) ---
    aff = doc.get("affordability") or {}
    inc = aff.get("disclosed_income_monthly")
    exp = aff.get("disclosed_expenses_monthly")
    surplus = None
    if isinstance(inc, (int, float)) and isinstance(exp, (int, float)):
        surplus = round(float(inc) - float(exp), 2)

    # --- treatment eligibility (config-driven; see references/domain-rules.md) ---
    treatments = []

    def add(name, eligible, rationale, rule_id, extra_ev=None):
        ev = [{"basis": f"days_past_due={dpd} ({band})", "citation": src}]
        if extra_ev:
            ev.append(extra_ev)
        # eligible options carry a policy citation; ineligible options record the rule missed
        ev.append({"basis": f"eligibility rule {rule_id}", "citation": _pol(rule_id, cfg_ver)})
        treatments.append({
            "treatment": name, "eligible": bool(eligible), "rationale": rationale,
            "evidence": ev, "requires_human_review": True,
        })

    add("payment_reminder", 1 <= dpd <= cfg["reminder_max_dpd"],
        "standard reminder outreach is in range for this delinquency band" if 1 <= dpd <= cfg["reminder_max_dpd"]
        else "outside the reminder DPD range", "TRT-REM-01")

    add("promise_to_pay", dpd >= 1,
        "consumer may be offered the option to schedule a promise-to-pay date" if dpd >= 1
        else "account not past due", "TRT-PTP-02")

    arr_ok = dpd >= cfg["arrangement_min_dpd"] and (surplus is not None and surplus > 0)
    add("payment_arrangement", arr_ok,
        (f"DPD >= {cfg['arrangement_min_dpd']} and disclosed monthly surplus {surplus} > 0 supports an indicative short-term plan"
         if arr_ok else
         (f"disclosed surplus not positive or unknown (surplus={surplus})" if dpd >= cfg["arrangement_min_dpd"]
          else f"DPD below arrangement floor {cfg['arrangement_min_dpd']}")),
        "TRT-ARR-03",
        {"basis": f"disclosed_surplus_monthly={surplus}", "citation": src} if surplus is not None else None)

    hard_ok = enhanced_care
    add("hardship_forbearance", hard_ok,
        "vulnerability/hardship context present — hardship treatment eligible for specialist consideration" if hard_ok
        else "no hardship or vulnerability indicator on file", "TRT-HRD-04",
        {"basis": f"vulnerability_indicators={vind}", "citation": src} if vind else None)

    add("due_date_change", dpd <= cfg["due_date_change_max_dpd"],
        f"due-date change is appropriate only at DPD <= {cfg['due_date_change_max_dpd']}"
        if dpd <= cfg["due_date_change_max_dpd"] else
        f"DPD {dpd} exceeds due-date-change ceiling {cfg['due_date_change_max_dpd']}", "TRT-DDC-05")

    add("re_age_review", dpd >= cfg["re_age_min_dpd"],
        f"account may be reviewed for re-age eligibility at DPD >= {cfg['re_age_min_dpd']} (human eligibility check required)"
        if dpd >= cfg["re_age_min_dpd"] else f"DPD below re-age review floor {cfg['re_age_min_dpd']}", "TRT-RAG-06")

    add("settlement_referral", dpd >= cfg["settlement_min_dpd"],
        f"late-stage account (DPD >= {cfg['settlement_min_dpd']}) may be referred to a specialist to consider settlement"
        if dpd >= cfg["settlement_min_dpd"] else f"DPD below settlement referral floor {cfg['settlement_min_dpd']}",
        "TRT-STL-07")

    add("external_credit_counseling_referral", enhanced_care,
        "offer a referral to a non-profit credit-counseling agency given hardship/vulnerability context" if enhanced_care
        else "no hardship/vulnerability context indicating a counseling referral", "TRT-CCR-08",
        {"basis": f"vulnerability_indicators={vind}", "citation": src} if vind else None)

    add("specialist_referral", enhanced_care,
        "route to a hardship/vulnerable-customer specialist for enhanced-care handling" if enhanced_care
        else "no vulnerability indicator requiring specialist routing", "TRT-SPC-09",
        {"basis": f"vulnerability_indicators={vind}", "citation": src} if vind else None)

    eligible_names = [t["treatment"] for t in treatments if t["eligible"]]

    # --- recommended outreach plan (channels honor suppression + call caps) ---
    preferred = (doc.get("preferences") or {}).get("preferred_channel")
    if outreach_suppressed:
        eligible_channels, suppressed_channels = [], ["phone", "email", "letter", "secure_message"]
        cadence = "outreach suppressed — do not initiate outbound contact; handle only permitted notices per the suppression reason(s)"
        tone = "n/a (suppressed)"
    else:
        eligible_channels = ["secure_message", "email", "letter"]
        if phone_eligible:
            eligible_channels.append("phone")
        suppressed_channels = [] if phone_eligible else ["phone"]
        if preferred and preferred in eligible_channels:
            eligible_channels = [preferred] + [c for c in eligible_channels if c != preferred]
        cadence = (f"phone attempts remaining under the {cfg['call_cap']}-in-{cfg['call_cap_window_days']}d "
                   f"presumption: {calls_remaining}; observe quiet-hours (local 8:00-21:00) before any call")
        tone = ("supportive, non-pressuring, hardship-aware; lead with available options and specialist support"
                if enhanced_care else "informational and respectful; present options, avoid pressure")

    # deterministic next-review suggestion (triage only, not a decision)
    next_review = {"Current": 30, "Early": 14, "Mid": 10, "Late": 7, "Severe": 5}[band]

    care_prompts = []
    if enhanced_care:
        care_prompts = [
            "Confirm and record the vulnerability/hardship context with consent before acting.",
            "Prefer forbearance/affordability-based options over escalation.",
            "Offer specialist support and, where useful, a non-profit credit-counseling referral.",
            "Do not treat disclosed hardship as an adverse decision input; avoid stigmatizing language.",
        ]

    return {
        "plan_id": f"ctp-{str(doc['account_id']).replace('*','')}-{doc['as_of']}-0001",
        "account_id": doc["account_id"],
        "as_of": doc["as_of"],
        "config_version": cfg_ver,
        "product_type": doc.get("product_type"),
        "delinquency": {"days_past_due": dpd, "band": band},
        "suppression": {"outreach_suppressed": outreach_suppressed, "reasons": sup_reasons},
        "contact_caps": {
            "window_days": cfg["call_cap_window_days"], "call_cap": cfg["call_cap"],
            "calls_last_window": calls_last, "calls_remaining": calls_remaining,
            "phone_outreach_eligible": phone_eligible,
        },
        "enhanced_care": {"required": enhanced_care, "indicators": vind},
        "affordability": {"disclosed_surplus_monthly": surplus, "indicative_only": True},
        "eligible_treatments": treatments,
        "recommended_treatments": eligible_names,
        "outreach_plan": {
            "eligible_channels": eligible_channels, "suppressed_channels": suppressed_channels,
            "cadence_note": cadence, "tone": tone,
        },
        "next_review_days": next_review,
        "requires_human_adjudication": True,
        "care_prompts": care_prompts,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "collections_case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
