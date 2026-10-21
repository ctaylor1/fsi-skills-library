#!/usr/bin/env python3
"""This is first-line triage of supplied extracts. The legacy `approved-suppressed` value is a proposed state only (`proposed_only=true`); no alert or case is actually suppressed. Priority weights are illustrative and uncalibrated. Currency support is USD; convert and evidence other currencies upstream.

Offline Phase 1 calculation; see references/domain-rules.md.
"""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path
from native_integrity import attach_source

DEFAULT_PRIORITY = {
    "risk": {"High": 3, "Medium": 1, "Low": 0},
    "amount": [(100000, 3), (25000, 2), (10000, 1)],
    "sanctions_flag": 4, "typology_hint": 2, "high_risk_geo": 2,
    "velocity_per_prior": 1, "velocity_cap": 3,
    "p1_min": 7, "p2_min": 3,
}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-WL-INTERNAL", "SUP-SEASONAL-01"}
STANDING_NOTE = ("First-line triage only; no case has been closed, no customer exonerated, "
                 "and no SAR filed.")


def _cite(a):
    return f"casemgmt:{a.get('source_ref','?')}"


def _priority(a, cfg):
    score, why = 0, []
    cust = a.get("customer") or {}
    r = cfg["risk"].get(cust.get("risk_rating"), 0)
    if r:
        score += r; why.append(f"risk {cust.get('risk_rating')} +{r}")
    raw_amount = a.get("amount_total")
    amt = raw_amount if isinstance(raw_amount, (int, float)) and not isinstance(raw_amount, bool) and math.isfinite(raw_amount) and raw_amount >= 0 else 0
    for thr, pts in cfg["amount"]:
        if amt >= thr:
            score += pts; why.append(f"amount>={thr} +{pts}"); break
    if (a.get("flags") or {}).get("sanctions_adverse_media"):
        score += cfg["sanctions_flag"]; why.append(f"sanctions/adverse-media +{cfg['sanctions_flag']}")
    if a.get("typology_hint"):
        score += cfg["typology_hint"]; why.append(f"typology hint +{cfg['typology_hint']}")
    if cust.get("high_risk_geo"):
        score += cfg["high_risk_geo"]; why.append(f"high-risk geo +{cfg['high_risk_geo']}")
    prior = a.get("prior_alerts_90d")
    vel = min(prior * cfg["velocity_per_prior"], cfg["velocity_cap"]) if isinstance(prior, int) and not isinstance(prior, bool) and prior >= 0 else 0
    if vel:
        score += vel; why.append(f"velocity +{vel}")
    band = "P1 (Elevated)" if (score >= cfg["p1_min"] or (a.get("flags") or {}).get("sanctions_adverse_media")) \
        else "P2 (Standard)" if score >= cfg["p2_min"] else "P3 (Low)"
    return score, band, why


def _dup_parent(a, open_cases):
    for c in open_cases:
        if (c.get("entity_id") == a.get("entity_id") and c.get("rule_id") == a.get("rule_id")
                and c.get("period") == a.get("period")):
            shared = set(c.get("txn_ids") or []) & set(a.get("txn_ids") or [])
            if shared and set(a.get("txn_ids") or []) == set(c.get("txn_ids") or []):
                return c, "exact"
            if shared:
                return c, "partial"    # overlap -> possible duplicate (linked, not suppressed)
    return None, None


def _period_issues(period, as_of, label="alert period"):
    """Chronology must be real, ordered and historical as of this assessment."""
    try:
        assessed = date.fromisoformat(as_of)
        start = date.fromisoformat(period["from"])
        end = date.fromisoformat(period["to"])
        if any(not isinstance(value, str) or parsed.isoformat() != value for value, parsed in ((as_of, assessed), (period["from"], start), (period["to"], end))):
            raise ValueError("noncanonical date")
    except (ValueError, TypeError, KeyError):
        return [f"{label}: real YYYY-MM-DD period and as_of dates required"]
    issues = []
    if start > end: issues.append(f"{label}: start is after end")
    if start > assessed or end > assessed: issues.append(f"{label}: activity is after assessment as_of")
    return issues


def _authorization(doc, alert, rule_id):
    """Check the scope of supplied approval evidence; does not authenticate its issuer."""
    if _period_issues(alert.get("period"), doc.get("as_of")):
        return None
    for auth in doc.get("suppression_authorizations") or []:
        try:
            active = date.fromisoformat(auth["effective_from"]) <= date.fromisoformat(doc["as_of"]) <= date.fromisoformat(auth["effective_to"])
        except (KeyError, TypeError, ValueError):
            continue
        if (active and auth.get("status") == "approved" and auth.get("approved_by")
                and auth.get("approval_ref") and auth.get("source_ref")
                and auth.get("rule_id") == rule_id
                and auth.get("config_version") == doc.get("config_version")
                and auth.get("alert_id") == alert.get("alert_id")
                and auth.get("entity_id") == alert.get("entity_id")
                and auth.get("period") == alert.get("period")
                and set(auth.get("txn_ids") or []) == set(alert.get("txn_ids") or [])
                and (rule_id != "SUP-SEASONAL-01" or auth.get("pattern_id") == alert.get("seasonal_pattern_id"))):
            return auth
    return None


def triage_alert(a, doc, cfg):
    case_id = f"AML-{a.get('alert_id')}"
    citations = [_cite(a)]
    cust = a.get("customer") or {}
    sanctioned = bool((a.get("flags") or {}).get("sanctions_adverse_media"))
    score, band, why = _priority(a, cfg)

    rec = {"alert_id": a.get("alert_id"), "case_id": case_id, "priority_score": score,
           "priority_band": band, "priority_reason": "; ".join(why), "citations": citations,
           "suppression": None, "escalation_bundle": None, "needs": []}

    rec["proposed_only"] = True
    rec["needs"].extend(_period_issues(a.get("period"), doc.get("as_of")))
    flags = a.get("flags") or {}
    if not isinstance(flags.get("sanctions_adverse_media"), bool):
        rec["needs"].append("screening flag status")
    amount = a.get("amount_total")
    if a.get("currency") != "USD" or isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
        rec["needs"].append("USD amount with currency (FX conversion is not implemented)")
    if not isinstance(cust.get("high_risk_geo"), bool):
        rec["needs"].append("customer geography-risk status")
    if not isinstance(a.get("prior_alerts_90d"), int) or isinstance(a.get("prior_alerts_90d"), bool) or a["prior_alerts_90d"] < 0:
        rec["needs"].append("prior alert count")

    # needs-data (do not clear an alert by guessing)
    if cust.get("risk_rating") not in cfg["risk"] or not a.get("txn_ids"):
        if cust.get("risk_rating") not in cfg["risk"]:
            rec["needs"].append("customer risk rating")
        if not a.get("txn_ids"):
            rec["needs"].append("triggering transaction ids")
    rec["priority_complete"] = not rec["needs"]
    if rec["needs"] and not sanctioned:
        rec["priority_band"] = "Unrated"
        rec["disposition"] = "needs-data"
        return rec

    parent, kind = _dup_parent(a, doc.get("open_cases") or [])

    # sanctions/adverse-media overrides suppression -> escalate
    if sanctioned:
        rec["disposition"] = "escalate-to-investigation"
        rec["route_specialist"] = "sanctions-match-investigator"
    elif kind == "exact" and _authorization(doc, a, "SUP-DUP-01"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-DUP-01",
                              "evidence": {"parent_case_id": parent.get("case_id"),
                                           "matched_txns": sorted(set(a["txn_ids"]) & set(parent.get("txn_ids", [])))},
                              "rule_set_version": doc.get("config_version"),
                              "authorization": _authorization(doc, a, "SUP-DUP-01")}
        return rec
    elif a.get("legs_internal") and set(a.get("leg_accounts") or []) <= set(doc.get("approved_whitelist") or []) and a.get("leg_accounts") and _authorization(doc, a, "SUP-WL-INTERNAL"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-WL-INTERNAL",
                              "evidence": {"whitelisted_accounts": a["leg_accounts"]},
                              "rule_set_version": doc.get("config_version"),
                              "authorization": _authorization(doc, a, "SUP-WL-INTERNAL")}
        return rec
    elif a.get("seasonal_pattern_id") and _authorization(doc, a, "SUP-SEASONAL-01"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-SEASONAL-01",
                              "evidence": {"pattern_id": a["seasonal_pattern_id"], "qualifying_txns": a["txn_ids"]},
                              "rule_set_version": doc.get("config_version"),
                              "authorization": _authorization(doc, a, "SUP-SEASONAL-01")}
        return rec
    elif kind in ("partial", "exact"):
        rec["disposition"] = "possible-duplicate"
        rec["linked_case_id"] = parent.get("case_id")
        return rec
    else:
        rec["disposition"] = "escalate-to-investigation"

    # escalation bundle for escalated alerts
    rec["escalation_bundle"] = {
        "case_id": case_id,
        "entity": a.get("entity_id"),
        "account_ref": a.get("account_ref"),
        "rule_id": a.get("rule_id"),
        "period": a.get("period"),
        "amount_total": a.get("amount_total"),
        "txn_ids": a.get("txn_ids"),
        "kyc": {"risk_rating": cust.get("risk_rating"), "high_risk_geo": cust.get("high_risk_geo")},
        "flags": a.get("flags") or {},
        "typology_hint": a.get("typology_hint"),
        "linked_cases": [parent.get("case_id")] if parent else [],
        "recommended_priority": band,
        "citations": citations,
    }
    return rec


def _compute_unbound(doc: dict) -> dict:
    cfg = {**DEFAULT_PRIORITY, **(doc.get("priority_config") or {})}
    records = [triage_alert(a, doc, cfg) for a in doc["alerts"]]
    summary = {
        "total": len(records),
        "escalated": sum(1 for r in records if r["disposition"] == "escalate-to-investigation"),
        "approved_suppressed": sum(1 for r in records if r["disposition"] == "approved-suppressed"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "possible_duplicate": sum(1 for r in records if r["disposition"] == "possible-duplicate"),
    }
    return {"config_version": doc.get("config_version"), "as_of": doc.get("as_of"), "triage": records,
            "summary": summary, "priority_thresholds": {"p1_min": cfg["p1_min"], "p2_min": cfg["p2_min"]},
            "standing_note": STANDING_NOTE}


def triage(doc):
    """Reject invalid intake before producing a native result; warnings remain partial."""
    from validate_input import validate as validate_input
    errors, _warnings = validate_input(doc)
    if errors:
        raise ValueError("invalid aml-alert-triager input: " + "; ".join(errors))
    try:
        return attach_source(_compute_unbound(doc), doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        raise ValueError("invalid aml-alert-triager input: " + str(exc)) from exc


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "alerts_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = triage(doc)
    except ValueError as exc:
        print("ERROR " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
