#!/usr/bin/env python3
"""Deterministic RM client-brief assembler for relationship-manager-client-briefer.

For each client: confirm required inputs are present, confirm the entity is resolved, check
that every content item cites a source in the client's inventory, screen source freshness
(with a tighter threshold for exposures/covenants/profitability), tie out committed and
outstanding exposure, flag overdue open actions, surface covenant breaches and adverse news
as ROUTING flags (never adjudicated here), and -- only when all invariants hold -- assemble a
draft brief with a citations index from an approved template.

It NEVER sends/submits/distributes/files the brief, never writes CRM or any system of record,
never makes or communicates a credit / covenant / pricing / risk-rating decision, gives no
investment, legal, or tax advice, and states nothing a cited source does not support. When a
required input is missing, the entity is unresolved, content cites an unknown source, or a
cited critical source is stale (and unacknowledged), the client is flagged (not packaged)
with the reason.

Usage: python calculate_or_transform.py clients.json | --selftest
Prints the brief-assembly JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Relationship-manager client brief for internal preparation only; this skill does not "
    "send, submit, distribute, or file the brief and does not write any CRM or system of "
    "record, does not make or communicate any credit, covenant, pricing, or risk-rating "
    "decision, gives no investment, legal, or tax advice, and every item must be verified "
    "against its cited source before use."
)
DEFAULT_FRESHNESS_DAYS = 30
DEFAULT_CRITICAL_FRESHNESS_DAYS = 10
# Content whose sources must be fresh under the tighter "critical" threshold.
CRITICAL_CONTENT = {"exposures", "covenants", "profitability"}
# (list_key, label, text_field)
CONTENT_SPEC = [
    ("exposures", "exposure", "facility"),
    ("covenants", "covenant", "name"),
    ("profitability", "profitability metric", "metric"),
    ("products", "product", "product"),
    ("service_cases", "service case", "case_ref"),
    ("news", "news item", "headline"),
    ("pipeline", "pipeline opportunity", "opportunity"),
    ("contacts", "contact", "name"),
    ("cross_sell", "cross-sell idea", "idea"),
    ("open_actions", "open action", "action"),
]
APPROVALS_REQUIRED = [
    "Relationship manager review and sign-off",
    "Credit/risk review (required if the brief informs a credit action, renewal, or covenant matter)",
]


def _as_of(doc) -> date:
    return date.fromisoformat(str(doc.get("as_of_date")))


def _cite(s) -> str:
    return f"{s.get('system','?')}:{s.get('ref','?')}@{s.get('date','?')}"


def _age_days(s, as_of) -> "int | None":
    d = s.get("date")
    try:
        return (as_of - date.fromisoformat(str(d))).days
    except Exception:
        return None


def _content_items(c):
    """Yield (list_key, label, text, source_id) for every content item."""
    for list_key, label, text_field in CONTENT_SPEC:
        for item in c.get(list_key) or []:
            yield list_key, label, item.get(text_field), item.get("source_id")


def _round2(x):
    return round(float(x or 0), 2)


def _exposure_summary(c, sources):
    lines = []
    total_committed = 0.0
    total_outstanding = 0.0
    for e in c.get("exposures") or []:
        committed = _round2(e.get("committed"))
        outstanding = _round2(e.get("outstanding"))
        total_committed += committed
        total_outstanding += outstanding
        sid = e.get("source_id")
        lines.append({
            "facility": e.get("facility"),
            "committed": committed,
            "outstanding": outstanding,
            "citation": _cite(sources[sid]) if sid in sources else None,
        })
    total_committed = _round2(total_committed)
    total_outstanding = _round2(total_outstanding)
    util = _round2(100.0 * total_outstanding / total_committed) if total_committed else 0.0
    return {
        "total_committed": total_committed,
        "total_outstanding": total_outstanding,
        "utilization_pct": util,
        "lines": lines,
    }


def brief_client(c, doc, as_of, freshness, critical_freshness):
    rec = {"client_id": c.get("client_id"), "legal_name": c.get("legal_name")}

    # 1. needs-data: required inputs present (do not guess a relationship)
    needs = []
    if not c.get("legal_name"):
        needs.append("legal_name")
    if not c.get("relationship_manager"):
        needs.append("relationship_manager")
    if not c.get("exposures"):
        needs.append("exposures")
    if needs:
        rec.update(status="needs-data", packageable=False, needs=needs, citations=[])
        return rec

    sources = {s.get("source_id"): s for s in c.get("sources") or []}

    # 2. unresolved-entity (never guess who the client is)
    entity_resolved = bool(c.get("entity_resolved"))
    rec["entity_resolved"] = entity_resolved

    # 3. content-to-source integrity
    unsupported = []
    for _lk, label, text, sid in _content_items(c):
        if sid not in sources:
            unsupported.append({"type": label, "text": text, "source_id": sid})
    rec["content_integrity"] = {"all_sourced": not unsupported, "unsupported": unsupported}

    # 4. freshness of cited sources (tighter threshold for exposures/covenants/profitability)
    critical_ids, general_ids = set(), set()
    for list_key, _label, _text, sid in _content_items(c):
        if sid not in sources:
            continue
        if list_key in CRITICAL_CONTENT:
            critical_ids.add(sid)
        else:
            general_ids.add(sid)
    general_ids -= critical_ids  # critical threshold wins if a source is cited both ways
    stale_unack = []
    for sid, threshold, kind in (
        [(s, critical_freshness, "critical") for s in sorted(critical_ids)]
        + [(s, freshness, "general") for s in sorted(general_ids)]
    ):
        s = sources[sid]
        age = _age_days(s, as_of)
        if age is not None and age > threshold and not s.get("stale_ack"):
            stale_unack.append({"source_id": sid, "age_days": age, "threshold": threshold,
                                "kind": kind, "citation": _cite(s)})
    rec["stale_check"] = {"freshness_days": freshness,
                          "critical_freshness_days": critical_freshness,
                          "stale_unacknowledged": stale_unack}

    # status precedence
    if not entity_resolved:
        rec.update(status="unresolved-entity", packageable=False)
        return rec
    if unsupported:
        rec.update(status="unsupported-content", packageable=False)
        return rec
    if stale_unack:
        rec.update(status="stale-source", packageable=False)
        return rec

    # ---- packageable: assemble the brief -------------------------------------------------
    cited_ids = critical_ids | general_ids
    citations = [_cite(sources[sid]) for sid in sorted(cited_ids)]
    rec["citations"] = citations

    def _c(item):
        sid = item.get("source_id")
        return _cite(sources[sid]) if sid in sources else None

    def _overdue(a):
        if a.get("status") == "open" and a.get("due_date"):
            try:
                return date.fromisoformat(str(a["due_date"])) < as_of
            except Exception:
                return False
        return False

    covenants = [{"name": cv.get("name"), "status": cv.get("status"),
                  "test_date": cv.get("test_date"), "citation": _c(cv)}
                 for cv in c.get("covenants") or []]
    news = [{"headline": n.get("headline"), "date": n.get("date"),
             "adverse": bool(n.get("adverse")), "citation": _c(n)}
            for n in c.get("news") or []]

    covenant_flags = {"breached": [cv["name"] for cv in covenants if cv["status"] == "breached"],
                      "at_risk": [cv["name"] for cv in covenants if cv["status"] == "at-risk"]}
    news_flags = {"adverse": [n["headline"] for n in news if n["adverse"]]}
    rec["covenant_flags"] = covenant_flags
    rec["news_flags"] = news_flags

    # Surfaced routing (recommendations for a human; never an action or decision taken here)
    routing = []
    if covenant_flags["breached"]:
        routing.append({"reason": "covenant breach surfaced (not adjudicated)",
                        "route": "covenant-compliance-monitor; credit/risk review before any waiver or credit action"})
    if news_flags["adverse"]:
        routing.append({"reason": "adverse news/media surfaced (not adjudicated)",
                        "route": "adverse-media-investigator"})
    rec["routing"] = routing

    rec.update(status="draft-brief", packageable=True)
    rec["brief"] = {
        "client_id": c.get("client_id"),
        "legal_name": c.get("legal_name"),
        "relationship_manager": c.get("relationship_manager"),
        "as_of_date": as_of.isoformat(),
        "exposure_summary": _exposure_summary(c, sources),
        "covenants": covenants,
        "profitability": [{"metric": p.get("metric"), "value": p.get("value"),
                           "period": p.get("period"), "citation": _c(p)}
                          for p in c.get("profitability") or []],
        "products": [{"product": p.get("product"), "status": p.get("status"), "citation": _c(p)}
                     for p in c.get("products") or []],
        "service_cases": [{"case_ref": s.get("case_ref"), "summary": s.get("summary"),
                           "status": s.get("status"), "severity": s.get("severity"),
                           "citation": _c(s)} for s in c.get("service_cases") or []],
        "news": news,
        "pipeline": [{"opportunity": o.get("opportunity"), "stage": o.get("stage"),
                      "amount": o.get("amount"), "citation": _c(o)}
                     for o in c.get("pipeline") or []],
        "contacts": [{"name": ct.get("name"), "role": ct.get("role"), "citation": _c(ct)}
                     for ct in c.get("contacts") or []],
        "cross_sell": [{"idea": x.get("idea"), "rationale": x.get("rationale"), "citation": _c(x)}
                       for x in c.get("cross_sell") or []],
        "open_actions": [{"action": a.get("action"), "owner": a.get("owner"),
                          "due_date": a.get("due_date"), "status": a.get("status"),
                          "overdue": _overdue(a), "citation": _c(a)}
                         for a in c.get("open_actions") or []],
        "routing": routing,
        "citations": citations,
        "reviewer_signoff_required": True,
        "approvals": {"required": list(APPROVALS_REQUIRED), "recorded": False},
    }
    return rec


def build(doc: dict) -> dict:
    as_of = _as_of(doc)
    freshness = int(doc.get("freshness_days") or DEFAULT_FRESHNESS_DAYS)
    critical_freshness = int(doc.get("critical_freshness_days") or DEFAULT_CRITICAL_FRESHNESS_DAYS)
    briefs = [brief_client(c, doc, as_of, freshness, critical_freshness) for c in doc["clients"]]

    def _count(s):
        return sum(1 for b in briefs if b.get("status") == s)

    summary = {
        "total": len(briefs),
        "draft_brief": _count("draft-brief"),
        "needs_data": _count("needs-data"),
        "unresolved_entity": _count("unresolved-entity"),
        "unsupported_content": _count("unsupported-content"),
        "stale_source": _count("stale-source"),
    }
    return {"as_of_date": as_of.isoformat(), "freshness_days": freshness,
            "critical_freshness_days": critical_freshness,
            "briefs": briefs, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "clients_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
