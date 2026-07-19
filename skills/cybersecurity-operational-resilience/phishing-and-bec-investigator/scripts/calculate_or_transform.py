#!/usr/bin/env python3
"""Deterministic phishing/BEC investigation engine for phishing-and-bec-investigator.

For each reported message it extracts indicators (authentication failures, lookalike/
impersonated sender, reply-to mismatch, malicious links, suspicious attachments, BEC
payment requests, behavioral pressure), scores risk from explainable inputs, builds a
durable case with an evidence bundle (chronology + parties + amounts + citations), and
emits a disposition RECOMMENDATION plus recommended containment / fraud-coordination steps.

It NEVER closes a case, reaches a final determination, blocks/quarantines a message, resets
a credential, files, or recalls a payment. Duplicates of an open case are linked, not
re-investigated. Missing header/authentication evidence yields `needs-data`, never a guess.

Usage: python calculate_or_transform.py reports.json | --selftest
Prints the investigation JSON to stdout. `--selftest` also runs an invariant self-check and
prints a line ending in "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_SCORING = {
    "spf": {"fail": 2, "softfail": 1, "none": 1},
    "dkim": {"fail": 2, "none": 1},
    "dmarc": {"fail": 3},
    "lookalike_domain": 4,
    "reply_to_mismatch": 2,
    "display_impersonation": 2,
    "malicious_link": 3, "malicious_link_cap": 6,
    "suspicious_attachment": 3,
    "payment_request": 3, "vendor_bank_change": 4,
    "urgency": 1, "secrecy": 1, "first_contact": 1,
    "critical_min": 12, "high_min": 8, "medium_min": 4,
}
SUSPICIOUS_ATTACH_EXT = (".html", ".htm", ".hta", ".js", ".vbs", ".exe", ".scr", ".iso", ".lnk")
CASE_PREFIX = "PHBEC-"
STANDING_NOTE = ("Investigative recommendation only; no case has been closed, no "
                 "determination is final, no message has been blocked or quarantined, no "
                 "credential has been reset, and no payment has been recalled - every "
                 "containment and fraud-coordination step requires human authorization.")

# ---- helpers ---------------------------------------------------------------

_HOMOGLYPH = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "$": "s"})


def _deconfuse(s: str) -> str:
    return (s or "").lower().translate(_HOMOGLYPH)


def _lev(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _domain(email_or_url: str) -> str:
    s = (email_or_url or "").strip().lower()
    if "@" in s:
        return s.split("@", 1)[1]
    s = s.split("://", 1)[-1]
    return s.split("/", 1)[0].split(":", 1)[0]


def _lookalike(domain: str, known: list) -> str | None:
    """Return the known domain this one mimics (homoglyph or near-edit), else None."""
    d = (domain or "").lower()
    if not d or d in {k.lower() for k in known}:
        return None
    for k in known:
        kl = k.lower()
        if _deconfuse(d) == _deconfuse(kl) and d != kl:
            return k
    for k in known:
        kl = k.lower()
        if d != kl and _lev(d, kl) <= 2:
            return k
    return None


def _mask_email(e: str) -> str:
    if not e or "@" not in e:
        return e or "?"
    local, dom = e.split("@", 1)
    return (local[0] + "***") + "@" + dom


def _mask_acct(a: str) -> str:
    a = str(a or "")
    return ("****" + a[-3:]) if len(a) > 3 else "****"


def _raw_ip(host: str) -> bool:
    parts = host.split(".")
    return len(parts) == 4 and all(p.isdigit() for p in parts)


# ---- indicator extraction --------------------------------------------------

def _indicators(r: dict, doc: dict, cfg: dict):
    msg = r.get("message") or {}
    src = r.get("source_ref", "?")
    known = doc.get("known_domains") or []
    watch = [w.lower() for w in (doc.get("impersonation_watchlist") or [])]
    inds, score, why = [], 0, []

    from_addr = msg.get("from_addr") or ""
    from_dom = _domain(from_addr)

    # authentication
    auth = msg.get("auth_results") or {}
    for proto in ("spf", "dkim", "dmarc"):
        val = str(auth.get(proto, "")).lower()
        pts = cfg.get(proto, {}).get(val)
        if pts:
            score += pts
            why.append(f"{proto.upper()} {val} +{pts}")
            inds.append({"type": f"auth-{proto}-{val}",
                         "detail": f"{proto.upper()} result = {val}",
                         "citation": f"{src};headers.authentication-results"})

    # lookalike sender domain
    mimic = _lookalike(from_dom, known)
    if mimic:
        score += cfg["lookalike_domain"]
        why.append(f"lookalike sender domain +{cfg['lookalike_domain']}")
        inds.append({"type": "lookalike-domain",
                     "detail": f"{from_dom} mimics {mimic}",
                     "citation": f"{src};headers.from"})

    # reply-to mismatch
    reply_to = msg.get("reply_to")
    if reply_to and _domain(reply_to) != from_dom:
        score += cfg["reply_to_mismatch"]
        why.append(f"reply-to mismatch +{cfg['reply_to_mismatch']}")
        inds.append({"type": "reply-to-mismatch",
                     "detail": f"reply-to {_domain(reply_to)} != from {from_dom}",
                     "citation": f"{src};headers.reply-to"})

    # display-name impersonation of a watchlisted party from a non-corporate domain
    disp = (msg.get("from_display") or "").lower()
    from_known = from_dom in {k.lower() for k in known}
    hit = next((w for w in watch if w in disp), None)
    if hit and not from_known:
        score += cfg["display_impersonation"]
        why.append(f"display-name impersonation +{cfg['display_impersonation']}")
        inds.append({"type": "display-impersonation",
                     "detail": f"display name invokes '{hit}' from external domain {from_dom}",
                     "citation": f"{src};headers.from-display"})

    # malicious links
    link_pts = 0
    for u in (msg.get("urls") or []):
        href_dom = _domain(u.get("href", ""))
        disp_dom = _domain(u.get("display", ""))
        reason = None
        if href_dom and disp_dom and href_dom != disp_dom:
            reason = f"link text shows {disp_dom} but points to {href_dom}"
        elif _lookalike(href_dom, known):
            reason = f"link host {href_dom} mimics {_lookalike(href_dom, known)}"
        elif _raw_ip(href_dom):
            reason = f"link points to raw IP {href_dom}"
        if reason and link_pts < cfg["malicious_link_cap"]:
            add = min(cfg["malicious_link"], cfg["malicious_link_cap"] - link_pts)
            link_pts += add
            inds.append({"type": "malicious-link", "detail": reason,
                         "citation": f"{src};body.url"})
    if link_pts:
        score += link_pts
        why.append(f"malicious link(s) +{link_pts}")

    # suspicious attachments
    for att in (msg.get("attachments") or []):
        name = str(att.get("name", "")).lower()
        if name.endswith(SUSPICIOUS_ATTACH_EXT):
            score += cfg["suspicious_attachment"]
            why.append(f"suspicious attachment +{cfg['suspicious_attachment']}")
            inds.append({"type": "suspicious-attachment",
                         "detail": f"attachment {att.get('name')} ({att.get('type','?')})",
                         "citation": f"{src};body.attachment"})

    # BEC payment request
    pay = r.get("payment_request") or {}
    bec_bank_change = False
    if pay.get("requested"):
        score += cfg["payment_request"]
        why.append(f"payment request +{cfg['payment_request']}")
        registry = {v.get("account_ref") for v in (doc.get("vendor_bank_registry") or [])}
        bene = pay.get("beneficiary_account")
        bec_bank_change = bool(pay.get("vendor_bank_change")) or (bene is not None and bene not in registry)
        detail = (f"{pay.get('type','payment')} request {pay.get('amount')} "
                  f"{pay.get('currency','')} to {_mask_acct(pay.get('beneficiary_account'))}")
        inds.append({"type": "payment-request", "detail": detail.strip(),
                     "citation": f"{src};body.payment-request"})
        if bec_bank_change:
            score += cfg["vendor_bank_change"]
            why.append(f"beneficiary/vendor bank change +{cfg['vendor_bank_change']}")
            inds.append({"type": "vendor-bank-change",
                         "detail": f"beneficiary {_mask_acct(pay.get('beneficiary_account'))} "
                                   f"not in approved vendor bank registry",
                         "citation": f"{src};body.payment-request"})

    # behavioral pressure
    beh = r.get("behavior") or {}
    if beh.get("urgency"):
        score += cfg["urgency"]; why.append(f"urgency +{cfg['urgency']}")
    if beh.get("requests_secrecy"):
        score += cfg["secrecy"]; why.append(f"secrecy +{cfg['secrecy']}")
    if beh.get("first_contact_external"):
        score += cfg["first_contact"]; why.append(f"first external contact +{cfg['first_contact']}")

    return inds, score, why, {"malicious_link": link_pts > 0, "bec_bank_change": bec_bank_change,
                              "attachment": any(i["type"] == "suspicious-attachment" for i in inds),
                              "impersonation": bool(mimic) or (hit and not from_known),
                              "auth_fail": any(i["type"].startswith("auth-") for i in inds)}


def _band(score: int, cfg: dict) -> str:
    if score >= cfg["critical_min"]:
        return "Critical"
    if score >= cfg["high_min"]:
        return "High"
    if score >= cfg["medium_min"]:
        return "Medium"
    return "Low"


def _chronology(r: dict, inds: list):
    msg = r.get("message") or {}
    src = r.get("source_ref", "?")
    ev = []
    if msg.get("received_at"):
        ev.append({"ts": msg["received_at"],
                   "event": f"Message received by {len(msg.get('recipients') or []) or 1} recipient(s)",
                   "citation": f"{src};headers.date"})
    pay = r.get("payment_request") or {}
    if pay.get("requested") and msg.get("received_at"):
        ev.append({"ts": msg["received_at"],
                   "event": f"{pay.get('type','payment')} request for {pay.get('amount')} "
                            f"{pay.get('currency','')} to {_mask_acct(pay.get('beneficiary_account'))}".strip(),
                   "citation": f"{src};body.payment-request"})
    if r.get("reported_at"):
        ev.append({"ts": r["reported_at"],
                   "event": f"Reported to SOC by {_mask_email(r.get('reported_by'))}",
                   "citation": f"{src};report"})
    for rid in (r.get("related_report_ids") or []):
        ev.append({"ts": msg.get("received_at") or r.get("reported_at") or "",
                   "event": f"Linked related report {rid}",
                   "citation": f"{src};related"})
    return sorted(ev, key=lambda e: e["ts"])


def _dup_parent(r: dict, open_cases: list):
    msg = r.get("message") or {}
    subj = (msg.get("subject") or "").strip().lower()
    fa = (msg.get("from_addr") or "").strip().lower()
    for c in open_cases:
        if (c.get("from_addr", "").lower() == fa
                and (c.get("subject", "").strip().lower() == subj)):
            return c
    return None


def investigate_report(r: dict, doc: dict, cfg: dict) -> dict:
    case_id = CASE_PREFIX + str(r.get("report_id"))
    src = r.get("source_ref", "?")
    msg = r.get("message") or {}
    top_citation = f"{src};report"

    rec = {"report_id": r.get("report_id"), "case_id": case_id,
           "risk_score": 0, "risk_band": "Low", "risk_reason": "",
           "indicators": [], "recommended_disposition": None, "disposition_reason": "",
           "evidence_bundle": None, "recommended_containment": [],
           "recommended_fraud_coordination": [], "route_specialist": None, "needs": []}

    # needs-data: cannot analyze without authentication evidence or a sender
    auth = msg.get("auth_results")
    if not msg.get("from_addr") or not isinstance(auth, dict) or not all(
            auth.get(k) for k in ("spf", "dkim", "dmarc")):
        if not msg.get("from_addr"):
            rec["needs"].append("sender address (message.from_addr)")
        else:
            rec["needs"].append("email authentication results (SPF/DKIM/DMARC)")
        rec["recommended_disposition"] = "needs-data"
        rec["disposition_reason"] = "insufficient header/authentication evidence to investigate"
        rec["indicators"] = [{"type": "needs-data", "detail": "; ".join(rec["needs"]),
                              "citation": top_citation}]
        return rec

    inds, score, why, sig = _indicators(r, doc, cfg)
    band = _band(score, cfg)
    rec.update({"risk_score": score, "risk_band": band,
                "risk_reason": "; ".join(why) or "no adverse indicators",
                "indicators": inds})

    # possible-duplicate of an open case -> link, do not re-investigate
    parent = _dup_parent(r, doc.get("open_cases") or [])
    if parent:
        rec["recommended_disposition"] = "possible-duplicate"
        rec["disposition_reason"] = f"same sender+subject as open case {parent.get('case_id')}"
        rec["linked_case_id"] = parent.get("case_id")
        rec["evidence_bundle"] = _bundle(r, case_id, inds, [top_citation])
        return rec

    # substantive recommendation (recommendation only)
    if sig["bec_bank_change"] and (sig["auth_fail"] or sig["impersonation"]):
        rec["recommended_disposition"] = "recommend-bec-fraud"
        rec["disposition_reason"] = "fraudulent payment request with beneficiary/vendor bank change and sender anomalies"
        rec["route_specialist"] = "payment-fraud-case-investigator"
        rec["recommended_fraud_coordination"] = [
            "Recommend the payments team assess a beneficiary-bank recall/hold (requires approval)",
            "Recommend out-of-band verification with the named vendor via a known-good contact (requires approval)"]
        rec["recommended_containment"] = [
            "Recommend quarantine of matching messages across mailboxes (requires approval)",
            "Recommend sender/domain block-list addition (requires approval)"]
    elif sig["malicious_link"] and (sig["auth_fail"] or sig["impersonation"]):
        rec["recommended_disposition"] = "recommend-credential-phishing"
        rec["disposition_reason"] = "credential-harvesting link with sender authentication anomalies"
        rec["route_specialist"] = "identity-access-reviewer"
        rec["recommended_containment"] = [
            "Recommend quarantine of matching messages across mailboxes (requires approval)",
            "Recommend forced credential reset for exposed recipients (requires approval)",
            "Recommend URL/domain block at the secure web gateway (requires approval)"]
    elif sig["attachment"] and (sig["auth_fail"] or sig["impersonation"]):
        rec["recommended_disposition"] = "recommend-malware-phishing"
        rec["disposition_reason"] = "suspicious attachment with sender authentication anomalies"
        rec["route_specialist"] = "cyber-incident-response-coordinator"
        rec["recommended_containment"] = [
            "Recommend quarantine of matching messages across mailboxes (requires approval)",
            "Recommend endpoint sweep for the attachment hash (requires approval)"]
    elif score >= cfg["medium_min"]:
        rec["recommended_disposition"] = "recommend-suspicious"
        rec["disposition_reason"] = "sender/behavioral anomalies without a confirmed payload; analyst review"
        rec["route_specialist"] = "cyber-incident-response-coordinator" if band in ("High", "Critical") else None
    else:
        rec["recommended_disposition"] = "recommend-benign"
        rec["disposition_reason"] = "authentication passes, known sender domain, no payload or payment request"

    rec["evidence_bundle"] = _bundle(r, case_id, inds, [top_citation])
    return rec


def _bundle(r: dict, case_id: str, inds: list, base_citations: list) -> dict:
    msg = r.get("message") or {}
    pay = r.get("payment_request") or {}
    src = r.get("source_ref", "?")
    amounts = None
    if pay.get("requested"):
        amounts = {"amount": pay.get("amount"), "currency": pay.get("currency"),
                   "beneficiary_account": _mask_acct(pay.get("beneficiary_account")),
                   "vendor": pay.get("vendor"),
                   "citation": f"{src};body.payment-request"}
    citations = list(base_citations) + [i["citation"] for i in inds]
    return {
        "case_id": case_id,
        "chronology": _chronology(r, inds),
        "parties": {
            "sender": _mask_email(msg.get("from_addr")),
            "sender_display": msg.get("from_display"),
            "reply_to": _mask_email(msg.get("reply_to")) if msg.get("reply_to") else None,
            "recipient_count": len(msg.get("recipients") or []),
            "reported_by": _mask_email(r.get("reported_by")),
        },
        "indicators": inds,
        "amounts": amounts,
        "citations": sorted(set(citations)),
    }


def investigate(doc: dict) -> dict:
    cfg = {**DEFAULT_SCORING, **(doc.get("scoring_config") or {})}
    records = [investigate_report(r, doc, cfg) for r in doc["reports"]]
    dispo = {}
    for r in records:
        dispo[r["recommended_disposition"]] = dispo.get(r["recommended_disposition"], 0) + 1
    return {"config_version": doc.get("config_version"), "investigations": records,
            "summary": {"total": len(records), "by_disposition": dispo},
            "standing_note": STANDING_NOTE}


# ---- self-check ------------------------------------------------------------

ALLOWED = {"recommend-bec-fraud", "recommend-credential-phishing", "recommend-malware-phishing",
           "recommend-suspicious", "recommend-benign", "needs-data", "possible-duplicate"}


def _selfcheck(out: dict) -> list:
    errs = []
    for r in out.get("investigations", []):
        cid = r.get("case_id", "?")
        if not str(r.get("case_id", "")).startswith(CASE_PREFIX):
            errs.append(f"{cid}: non-durable case_id")
        if r.get("recommended_disposition") not in ALLOWED:
            errs.append(f"{cid}: disposition not in allowed recommendation set")
        b = r.get("evidence_bundle")
        if r.get("recommended_disposition") not in ("needs-data",):
            if not b or not b.get("citations"):
                errs.append(f"{cid}: evidence bundle missing citations")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reports_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    out = investigate(doc)
    print(json.dumps(out, indent=2))
    if selftest:
        errs = _selfcheck(out)
        for e in errs:
            print("ERROR", e)
        print(f"calculate self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
