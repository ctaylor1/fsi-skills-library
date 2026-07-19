#!/usr/bin/env python3
"""Deterministic payment-fraud case builder for payment-fraud-case-investigator.

For each fraud alert/case it: resolves the parties, scores fraud risk from documented,
explainable signals across the six evidence categories (device, identity, behavior,
transaction, beneficiary, network), builds a time-ordered chronology, assembles a fully
cited evidence bundle, and emits a durable case_id plus a disposition **recommendation**.

Hard boundaries baked in (mirrored by validate_output.py):
  - It NEVER closes a case, makes a fraud determination, blocks an account, or files a SAR.
  - Every disposition is a RECOMMENDATION for a human adjudicator (recommend-* / route /
    needs-evidence); no decision, closure, or filing state can be produced.
  - A sanctions/adverse-media proximity flag routes to a sanctions specialist; an APP/BEC
    social-engineering flag routes to a BEC specialist (this skill does not adjudicate those).
  - Evidence completeness gates any "recommend-legitimate": a case is never cleared by
    guessing over missing evidence — it becomes needs-evidence instead.

Usage: python calculate_or_transform.py cases.json | --selftest
Prints the case-investigation JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# ---- Documented, explainable signal weights (a versioned contract, not judgment) --------
DEFAULT_WEIGHTS = {
    "device": {"new_device": 2, "device_id_changed": 1, "ip_geo_mismatch": 2, "emulator_flag": 3},
    "identity": {"credential_reset_recent": 3, "contact_change_recent": 2, "kyc_unverified": 2},
    "behavior": {"velocity_spike": 2, "off_pattern_amount": 2, "unusual_hour": 1},
    "transaction": {"high_risk_mcc": 2, "cross_border": 1, "structuring_pattern": 3},
    "beneficiary": {"new_beneficiary": 1, "mule_watchlist_hit": 4, "beneficiary_new_30d": 2},
    "network": {"shared_device_ring": 3},
}
DEFAULT_CFG = {
    "weights": DEFAULT_WEIGHTS,
    "sanctions_flag": 4,
    "linked_case_each": 2, "linked_case_cap": 4,
    "prior_case_each": 1, "prior_case_cap": 3,
    "high_min": 8, "low_max": 3,
}
# Categories that must be present and non-empty before a case may be recommended legitimate.
REQUIRED_EVIDENCE = ("device", "identity", "behavior", "transaction", "beneficiary")
ALLOWED_DISPOSITIONS = {
    "recommend-fraud", "recommend-legitimate", "recommend-elevated-monitoring",
    "needs-evidence", "route-specialist",
}
STANDING_NOTE = (
    "Investigation evidence and a disposition recommendation only; no case has been closed, "
    "no fraud determination has been made, and no filing has been performed. Human "
    "adjudication is required before any block, closure, filing, or customer commitment."
)


def _mask(value) -> str:
    s = str(value or "")
    if s.startswith("****"):
        return s
    return ("****" + s[-4:]) if len(s) > 4 else "****"


def _band(score: int, cfg: dict) -> str:
    if score >= cfg["high_min"]:
        return "High"
    if score <= cfg["low_max"]:
        return "Low"
    return "Elevated"


def _complete(evidence: dict) -> tuple[bool, list[str]]:
    missing = [c for c in REQUIRED_EVIDENCE if not (evidence.get(c) or {})]
    return (not missing), missing


def _score(case: dict, cfg: dict) -> tuple[int, list[str]]:
    """Sum documented signal weights. Returns (score, human-readable reasons)."""
    score, reasons = 0, []
    evidence = case.get("evidence") or {}
    weights = cfg["weights"]
    for cat in ("device", "identity", "behavior", "transaction", "beneficiary", "network"):
        signals = evidence.get(cat) or {}
        for sig, pts in weights.get(cat, {}).items():
            if signals.get(sig):
                score += pts
                reasons.append(f"{cat}.{sig} +{pts}")
    flags = case.get("flags") or {}
    if flags.get("sanctions_adverse_media"):
        score += cfg["sanctions_flag"]
        reasons.append(f"sanctions/adverse-media +{cfg['sanctions_flag']}")
    linked = case.get("linked_fraud_case_ids") or []
    if linked:
        pts = min(len(linked) * cfg["linked_case_each"], cfg["linked_case_cap"])
        score += pts
        reasons.append(f"linked fraud cases ({len(linked)}) +{pts}")
    prior = int(case.get("prior_fraud_cases_180d") or 0)
    if prior:
        pts = min(prior * cfg["prior_case_each"], cfg["prior_case_cap"])
        score += pts
        reasons.append(f"prior fraud cases ({prior}) +{pts}")
    return score, reasons


def _cite(case: dict, key: str) -> str:
    return (case.get("source_refs") or {}).get(key) or (case.get("source_refs") or {}).get("case") or "unknown"


def _chronology(case: dict) -> list[dict]:
    events = []
    if case.get("opened_at"):
        events.append({"ts": case["opened_at"], "type": "case_opened",
                       "detail": f"Fraud alert opened on channel {case.get('channel','?')}",
                       "citation": _cite(case, "case")})
    for t in case.get("transactions") or []:
        events.append({
            "ts": t.get("ts"), "type": "transaction",
            "detail": f"{t.get('direction','?')} {t.get('amount')} {case.get('currency','')} "
                      f"txn={t.get('txn_id')} benef={_mask(t.get('beneficiary_ref'))}".strip(),
            "citation": t.get("source_ref") or _cite(case, "transaction"),
        })
    for ev in case.get("timeline_events") or []:
        events.append({"ts": ev.get("ts"), "type": ev.get("type", "event"),
                       "detail": ev.get("detail", ""),
                       "citation": ev.get("source_ref") or _cite(case, "case")})
    return sorted(events, key=lambda e: (e.get("ts") or ""))


def _evidence_items(case: dict, cfg: dict) -> list[dict]:
    items, evidence, weights = [], case.get("evidence") or {}, cfg["weights"]
    for cat in ("device", "identity", "behavior", "transaction", "beneficiary", "network"):
        signals = evidence.get(cat) or {}
        for sig in weights.get(cat, {}):
            if signals.get(sig):
                items.append({"category": cat, "signal": sig, "value": True,
                              "citation": _cite(case, cat)})
    return items


def _parties(case: dict) -> list[dict]:
    parties = [{"role": "customer", "ref": _mask(case.get("customer_id")),
                "citation": _cite(case, "identity")}]
    benef = case.get("primary_beneficiary_ref")
    if benef:
        parties.append({"role": "beneficiary", "ref": _mask(benef),
                        "citation": _cite(case, "beneficiary")})
    return parties


def _network_links(case: dict) -> list[dict]:
    return [{"linked_case_id": cid, "citation": _cite(case, "network")}
            for cid in (case.get("linked_fraud_case_ids") or [])]


def _disposition(case: dict, score: int, band: str, complete: bool):
    """Deterministic mapping to a RECOMMENDATION. Never a decision/closure/filing."""
    flags = case.get("flags") or {}
    if flags.get("sanctions_adverse_media"):
        return "route-specialist", "sanctions-match-adjudicator", (
            "Sanctions/adverse-media proximity present; route to the sanctions specialist for "
            "match adjudication. This skill does not adjudicate sanctions matches.")
    if flags.get("app_scam_reported") or flags.get("bec_indicator"):
        return "route-specialist", "phishing-and-bec-investigator", (
            "Authorized-push-payment / business-email-compromise indicators present; route to "
            "the BEC specialist for social-engineering investigation.")
    if not complete and band != "High":
        return "needs-evidence", None, (
            "Required evidence is incomplete and signals are not decisive; gather the missing "
            "evidence before any recommendation. The case is not resolved by guessing.")
    if band == "High":
        return "recommend-fraud", None, (
            "Evidence is consistent with a fraud pattern; recommend a fraud adjudicator review "
            "and action this case. No determination, block, or filing is made here.")
    if band == "Low":
        return "recommend-legitimate", None, (
            "Evidence is complete and signals are low; recommend releasing the hold pending "
            "human review. This is a recommendation, not a clearance.")
    return "recommend-elevated-monitoring", None, (
        "Mixed signals below the fraud threshold; recommend elevated monitoring and human "
        "review rather than a fraud recommendation or release.")


def investigate_case(case: dict, cfg: dict) -> dict:
    case_id = f"PFC-{case.get('alert_id')}"
    score, reasons = _score(case, cfg)
    band = _band(score, cfg)
    complete, missing = _complete(case.get("evidence") or {})
    disp, route, rationale = _disposition(case, score, band, complete)

    evidence_items = _evidence_items(case, cfg)
    chronology = _chronology(case)
    parties = _parties(case)
    network_links = _network_links(case)
    citations = sorted({i["citation"] for i in evidence_items}
                       | {e["citation"] for e in chronology}
                       | {p["citation"] for p in parties}
                       | {n["citation"] for n in network_links}
                       | {_cite(case, "case")})

    bundle = {
        "case_id": case_id,
        "customer_id_masked": _mask(case.get("customer_id")),
        "account_ref": case.get("account_ref"),
        "channel": case.get("channel"),
        "amount": case.get("amount"),
        "currency": case.get("currency"),
        "chronology": chronology,
        "parties": parties,
        "evidence_items": evidence_items,
        "network_links": network_links,
        "risk_score": score,
        "risk_band": band,
        "score_reasons": reasons,
        "evidence_complete": complete,
        "missing_evidence": missing,
        "recommended_disposition": disp,
        "recommendation_rationale": rationale,
        "citations": citations,
    }
    rec = {
        "alert_id": case.get("alert_id"),
        "case_id": case_id,
        "risk_score": score,
        "risk_band": band,
        "disposition": disp,
        "recommendation_rationale": rationale,
        "evidence_bundle": bundle,
        "needs": [f"evidence category: {m}" for m in missing] if disp == "needs-evidence" else [],
    }
    if route:
        rec["route_specialist"] = route
    return rec


def investigate(doc: dict) -> dict:
    cfg = {**DEFAULT_CFG, **{k: v for k, v in (doc.get("scoring_config") or {}).items()}}
    cfg["weights"] = {**DEFAULT_WEIGHTS, **((doc.get("scoring_config") or {}).get("weights") or {})}
    records = [investigate_case(c, cfg) for c in doc.get("cases", [])]
    summary = {"total": len(records)}
    for d in sorted(ALLOWED_DISPOSITIONS):
        summary[d] = sum(1 for r in records if r["disposition"] == d)
    return {
        "config_version": doc.get("config_version"),
        "rules_version": doc.get("rules_version"),
        "cases": records,
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "cases_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(investigate(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
