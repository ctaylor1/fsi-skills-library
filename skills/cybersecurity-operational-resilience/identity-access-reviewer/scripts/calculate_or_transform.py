#!/usr/bin/env python3
"""Deterministic, explainable access-review findings for identity-access-reviewer.

Reads an access-review extract (see validate_input.py), computes the configured findings,
attaches evidence + citations to each fired finding, stages revocation *candidates* for
human approval, and maps the fired set to a review-priority band.

IMPORTANT: This produces explainable *findings, cited evidence, and staged recommendations*
only. It NEVER makes an access decision, revokes/disables/deprovisions access, completes a
certification, closes the review, or writes an IAM system of record. Every staged
revocation is a candidate marked "staged_for_approval"; a human control owner adjudicates.
The priority mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py review.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "inactivity_days": 90,
    "dormancy_days": 90,
    "certification_interval_days": 365,
    "max_entitlements": 15,
    "sod_rules": [],
}
DISCLAIMER = ("Access-review evidence and staged recommendations only; not an access "
              "decision. No entitlement has been revoked, disabled, or certified.")
# Findings that on their own justify elevating the review priority for a human.
ESCALATORS = {"sod_conflict", "dormant_privileged", "orphaned_account", "privileged_without_mfa"}
STAGED = "staged_for_approval"


def _parse_date(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(source_ref, date=None):
    return f"iam:{source_ref}" + (f"@{date}" if date else "")


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_date(doc["as_of"])
    accounts = {a["account_id"]: a for a in doc["accounts"]}
    grants = doc["entitlements"]
    idents = {i["user_id"]: i for i in (doc.get("identities") or [])}

    def gap_days(account):
        ll = account.get("last_login")
        if not ll:
            return None  # unknown -> treated as inactive/dormant conservatively
        return (as_of - _parse_date(ll)).days

    def inactive(account):
        g = gap_days(account)
        return (g is None) or (g >= cfg["inactivity_days"]), g

    def dormant(account):
        g = gap_days(account)
        return (g is None) or (g >= cfg["dormancy_days"]), g

    findings = []
    not_evaluable = []
    staged: dict[str, dict] = {}  # grant_id -> candidate (deduped)

    def add(name, fired, reason, evidence, criteria):
        findings.append({"finding": name, "fired": bool(fired), "reason": reason,
                         "evidence": evidence, "criteria": criteria,
                         "contribution": len(evidence) if fired else 0})

    def stage(grant, related_finding, reason):
        gid = grant["grant_id"]
        if gid not in staged:
            staged[gid] = {"grant_id": gid, "account_id": grant["account_id"],
                           "entitlement": grant["entitlement"], "related_finding": related_finding,
                           "reason": reason, "status": STAGED}

    # index grants per account / per user
    grants_by_acct: dict[str, list] = {}
    for g in grants:
        grants_by_acct.setdefault(g["account_id"], []).append(g)

    # ---- sod_conflict (per user, across their accounts) ----
    sod_rules = [tuple(sorted(pair)) for pair in cfg.get("sod_rules") or []]
    if sod_rules:
        # map user_id -> {entitlement: grant}
        user_ents: dict[str, dict] = {}
        for g in grants:
            acct = accounts.get(g["account_id"])
            uid = acct.get("user_id") if acct else None
            if uid is None:
                continue
            user_ents.setdefault(uid, {})[g["entitlement"]] = g
        sod_ev = []
        for uid, ents in user_ents.items():
            for a, b in sod_rules:
                if a in ents and b in ents:
                    ga, gb = ents[a], ents[b]
                    sod_ev.append({"user_id": uid, "entitlements": [a, b],
                                   "grant_ids": [ga["grant_id"], gb["grant_id"]],
                                   "citation": _cite(ga["source_ref"])})
                    # stage the more-privileged / second side for approval
                    target = gb if gb.get("privileged") and not ga.get("privileged") else ga
                    stage(target, "sod_conflict",
                          f"toxic-combination side of SoD pair ({a} + {b}) for {uid}")
        add("sod_conflict", bool(sod_ev),
            f"{len(sod_ev)} user(s) hold a toxic SoD entitlement pair" if sod_ev else "no SoD conflicts",
            sod_ev, {"sod_rules": [list(p) for p in sod_rules]})
    else:
        not_evaluable.append({"finding": "sod_conflict", "why": "no config.sod_rules"})

    # ---- dormant_privileged (privileged grant on a dormant account) ----
    dp_ev = []
    for g in grants:
        if not g.get("privileged"):
            continue
        acct = accounts.get(g["account_id"])
        if not acct:
            continue
        is_dormant, gd = dormant(acct)
        if is_dormant:
            dp_ev.append({"grant_id": g["grant_id"], "account_id": g["account_id"],
                          "entitlement": g["entitlement"], "gap_days": gd,
                          "citation": _cite(g["source_ref"], acct.get("last_login"))})
            stage(g, "dormant_privileged",
                  f"privileged entitlement on account inactive {gd if gd is not None else 'unknown'}d "
                  f"(>= {cfg['dormancy_days']})")
    add("dormant_privileged", bool(dp_ev),
        f"{len(dp_ev)} privileged grant(s) on dormant accounts" if dp_ev else "no dormant privileged access",
        dp_ev, {"dormancy_days": cfg["dormancy_days"]})

    # ---- inactive_account (any account inactive) ----
    ia_ev = []
    for aid, acct in accounts.items():
        is_inactive, gd = inactive(acct)
        if is_inactive:
            ia_ev.append({"account_id": aid, "user_id": acct.get("user_id"), "gap_days": gd,
                          "citation": _cite(acct["source_ref"], acct.get("last_login"))})
    add("inactive_account", bool(ia_ev),
        f"{len(ia_ev)} account(s) inactive >= {cfg['inactivity_days']}d" if ia_ev else "no inactive accounts",
        ia_ev, {"inactivity_days": cfg["inactivity_days"]})

    # ---- orphaned_account (owner terminated or not in identity roster) ----
    oa_ev = []
    for aid, acct in accounts.items():
        uid = acct.get("user_id")
        idn = idents.get(uid)
        reason = None
        if idn is None:
            reason = "owner not in identity roster"
        elif idn.get("hr_status") == "terminated":
            reason = "owner HR status terminated"
        if reason:
            oa_ev.append({"account_id": aid, "user_id": uid, "why": reason,
                          "citation": _cite(acct["source_ref"])})
            for g in grants_by_acct.get(aid, []):
                stage(g, "orphaned_account", f"grant on orphaned account ({reason})")
    add("orphaned_account", bool(oa_ev),
        f"{len(oa_ev)} orphaned account(s)" if oa_ev else "no orphaned accounts",
        oa_ev, {"checks": ["terminated owner", "owner missing from roster"]})

    # ---- unapproved_privileged (privileged grant with no approval_ref) ----
    up_ev = []
    for g in grants:
        if g.get("privileged") and not g.get("approval_ref"):
            acct = accounts.get(g["account_id"])
            up_ev.append({"grant_id": g["grant_id"], "account_id": g["account_id"],
                          "entitlement": g["entitlement"],
                          "citation": _cite(g["source_ref"])})
            stage(g, "unapproved_privileged", "privileged entitlement with no approval record")
    add("unapproved_privileged", bool(up_ev),
        f"{len(up_ev)} privileged grant(s) without an approval record" if up_ev else "all privileged grants approved",
        up_ev, {"requires": "approval_ref for privileged"})

    # ---- stale_certification (grant not certified within interval) ----
    sc_ev = []
    interval = cfg["certification_interval_days"]
    for g in grants:
        lc = g.get("last_certified")
        overdue = (not lc) or ((as_of - _parse_date(lc)).days > interval)
        if overdue:
            gd = None if not lc else (as_of - _parse_date(lc)).days
            sc_ev.append({"grant_id": g["grant_id"], "entitlement": g["entitlement"],
                          "last_certified": lc, "days_since": gd,
                          "citation": _cite(g["source_ref"], lc)})
    add("stale_certification", bool(sc_ev),
        f"{len(sc_ev)} grant(s) overdue for recertification (> {interval}d)" if sc_ev else "certifications current",
        sc_ev, {"certification_interval_days": interval})

    # ---- privileged_without_mfa ----
    pm_ev = []
    for g in grants:
        if not g.get("privileged"):
            continue
        acct = accounts.get(g["account_id"])
        if acct is not None and "mfa_enabled" in acct and acct.get("mfa_enabled") is False:
            pm_ev.append({"grant_id": g["grant_id"], "account_id": g["account_id"],
                          "entitlement": g["entitlement"],
                          "citation": _cite(g["source_ref"])})
    add("privileged_without_mfa", bool(pm_ev),
        f"{len(pm_ev)} privileged grant(s) on accounts without MFA" if pm_ev else "privileged access has MFA",
        pm_ev, {"requires": "mfa_enabled for privileged"})

    # ---- over_entitled (account holds too many entitlements) ----
    oe_ev = []
    for aid, gl in grants_by_acct.items():
        if len(gl) >= cfg["max_entitlements"]:
            acct = accounts.get(aid, {})
            oe_ev.append({"account_id": aid, "count": len(gl),
                          "citation": _cite(acct.get("source_ref", f"acct={aid}"))})
    add("over_entitled", bool(oe_ev),
        f"{len(oe_ev)} account(s) with >= {cfg['max_entitlements']} entitlements" if oe_ev else "no over-entitled accounts",
        oe_ev, {"max_entitlements": cfg["max_entitlements"]})

    fired = [f["finding"] for f in findings if f["fired"]]
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        priority = "Elevated"
    elif fired:
        priority = "Review"
    else:
        priority = "Informational"

    context_prompts = []
    if fired:
        context_prompts = [
            "approved standing exception or break-glass account on file",
            "recent role change / transfer still within grace period",
            "service or shared account operating by design (verify owner + rotation)",
            "planned leave of absence explaining inactivity",
            "certification in progress but not yet recorded",
        ]

    return {
        "review_id": f"iar-{doc.get('org_unit','org')}-{doc['as_of']}-0001",
        "org_unit": doc.get("org_unit"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "findings": findings,
        "fired_findings": fired,
        "not_evaluable": not_evaluable,
        "staged_revocations": list(staged.values()),
        "suggested_priority": priority,
        "context_prompts": context_prompts,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "access_review_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
