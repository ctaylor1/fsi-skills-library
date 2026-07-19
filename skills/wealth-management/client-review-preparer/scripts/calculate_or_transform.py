#!/usr/bin/env python3
"""Deterministic client-review-pack assembler for client-review-preparer.

For each client review: confirm required inputs are present, confirm the entity is resolved,
confirm every holding/performance/total references a known account, check that every content
item cites a source in the review's inventory, screen source freshness (with a tighter
threshold for holdings/performance), tie out holdings to reported account values and account
values to the household total, confirm the required disclosures for the review type are
present, flag overdue open actions, surface life events, drift, senior-investor, and
recommendation-contemplated indicators as ROUTING flags (never adjudicated here), and -- only
when all invariants hold -- assemble a draft review pack with a citations index and a recorded
approvals block from an approved template.

It NEVER makes or communicates an investment recommendation, suitability decision, trade,
closure, or filing; never writes any system of record; never sends, submits, or delivers the
pack; gives no investment, legal, or tax advice; and states nothing a cited source does not
support. When a required input is missing, the entity is unresolved, an account reference is
unknown, content cites an unknown source, a cited critical source is stale (and unacknowledged),
holdings do not tie out, or a required disclosure is missing, the review is flagged (not
packaged) with the reason.

Usage: python calculate_or_transform.py reviews.json | --selftest
Prints the review-pack assembly JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Client-review preparation draft for internal advisor use only; this skill does not make "
    "or communicate any investment recommendation, suitability decision, trade, closure, or "
    "filing, does not send, submit, or deliver the pack, and does not write any CRM or system "
    "of record; it gives no investment, legal, or tax advice; every item must be verified "
    "against its cited source and adjudicated by a licensed human before use."
)
DEFAULT_FRESHNESS_DAYS = 30
DEFAULT_CRITICAL_FRESHNESS_DAYS = 7
# Content whose sources must be fresh under the tighter "critical" threshold.
CRITICAL_CONTENT = {"holdings", "performance"}
# Required disclosures per review type (versioned config; deployment overrides via
# doc["disclosure_config"]). Reg BI / Form CRS orientation; the firm's config is authoritative.
DEFAULT_DISCLOSURE_CONFIG = {
    "annual": ["FORM-CRS", "REG-BI-DISCLOSURE", "FEE-SCHEDULE", "PERFORMANCE-DISCLOSURE"],
    "semiannual": ["FEE-SCHEDULE", "PERFORMANCE-DISCLOSURE"],
    "ad-hoc": ["PERFORMANCE-DISCLOSURE"],
}
# (list_key, label, text_field)
CONTENT_SPEC = [
    ("holdings", "holding", "security"),
    ("performance", "performance row", "period"),
    ("goals", "goal", "goal"),
    ("plan_items", "plan item", "item"),
    ("prior_notes", "prior note", "note"),
    ("service_history", "service case", "case_ref"),
    ("life_events", "life event", "event"),
    ("open_actions", "open action", "action"),
    ("discussion_questions", "discussion question", "question"),
    ("disclosures", "disclosure", "disclosure_id"),
]
APPROVALS_REQUIRED = [
    "Advisor review and sign-off",
    "Supervisory / principal review before the pack is used in a client meeting",
    "Suitability / Reg BI review (required if any recommendation is contemplated) — routed to suitability-reg-bi-reviewer",
]


def _as_of(doc) -> date:
    return date.fromisoformat(str(doc.get("as_of_date")))


def _cite(s) -> str:
    return f"{s.get('system','?')}:{s.get('ref','?')}@{s.get('date','?')}"


def _age_days(s, as_of):
    d = s.get("date")
    try:
        return (as_of - date.fromisoformat(str(d))).days
    except Exception:
        return None


def _content_items(r):
    """Yield (list_key, label, text, source_id) for every content item."""
    for list_key, label, text_field in CONTENT_SPEC:
        for item in r.get(list_key) or []:
            yield list_key, label, item.get(text_field), item.get("source_id")


def _round2(x):
    return round(float(x or 0), 2)


def _portfolio_summary(r, sources):
    """Per-account holdings tie-out + household roll-up. Returns (summary, breaks)."""
    breaks = []
    holdings_by_acct = {}
    for h in r.get("holdings") or []:
        holdings_by_acct.setdefault(h.get("account_id"), []).append(h)

    acct_lines = []
    total_reported = 0.0
    for a in r.get("accounts") or []:
        aid = a.get("account_id")
        reported = _round2(a.get("reported_value"))
        total_reported += reported
        hs = holdings_by_acct.get(aid, [])
        holdings_value = _round2(sum(_round2(h.get("market_value")) for h in hs))
        tie_ok = holdings_value == reported
        if not tie_ok:
            breaks.append(f"account {aid}: holdings {holdings_value} != reported {reported}")
        sid = a.get("source_id")
        acct_lines.append({
            "account_id": aid,
            "type": a.get("type"),
            "registration": a.get("registration"),
            "reported_value": reported,
            "holdings_value": holdings_value,
            "tie_out_ok": tie_ok,
            "citation": _cite(sources[sid]) if sid in sources else None,
            "holdings": [{"security": h.get("security"), "asset_class": h.get("asset_class"),
                          "market_value": _round2(h.get("market_value")),
                          "citation": _cite(sources[h.get("source_id")]) if h.get("source_id") in sources else None}
                         for h in hs],
        })
    total_reported = _round2(total_reported)
    household_reported = r.get("household_reported_value")
    household_ok = True
    if household_reported is not None and _round2(household_reported) != total_reported:
        household_ok = False
        breaks.append(f"household total {_round2(household_reported)} != sum of accounts {total_reported}")
    summary = {
        "total_value": total_reported,
        "household_reported_value": _round2(household_reported) if household_reported is not None else None,
        "tie_out_ok": not breaks,
        "household_rollup_ok": household_ok,
        "accounts": acct_lines,
    }
    return summary, breaks


def prep_review(r, doc, as_of, freshness, critical_freshness, disclosure_config):
    rec = {"client_id": r.get("client_id"), "household_name": r.get("household_name"),
           "review_type": r.get("review_type")}

    # 1. needs-data: required inputs present (do not guess a relationship)
    needs = []
    if not r.get("household_name"):
        needs.append("household_name")
    if not r.get("advisor"):
        needs.append("advisor")
    if not (r.get("accounts") or []):
        needs.append("accounts")
    if not (r.get("goals") or []):
        needs.append("goals")
    if needs:
        rec.update(status="needs-data", packageable=False, needs=needs, citations=[])
        return rec

    sources = {s.get("source_id"): s for s in r.get("sources") or []}
    account_ids = {a.get("account_id") for a in r.get("accounts") or []}

    # 2. unresolved-entity (never guess who the client is)
    if not r.get("entity_resolved"):
        rec.update(status="unresolved-entity", packageable=False,
                   reason="entity not resolved; a human confirms the household identity")
        return rec

    # 3. account-identity: every holding/performance/account references a known account
    identity_gaps = []
    for a in r.get("accounts") or []:
        if not a.get("type") or not a.get("registration"):
            identity_gaps.append(f"account {a.get('account_id')} missing type/registration")
    for k, h in enumerate(r.get("holdings") or []):
        if h.get("account_id") not in account_ids:
            identity_gaps.append(f"holding[{k}] references unknown account {h.get('account_id')!r}")
    for k, p in enumerate(r.get("performance") or []):
        scope = p.get("scope")
        if scope != "household" and scope not in account_ids:
            identity_gaps.append(f"performance[{k}] references unknown account {scope!r}")
    if identity_gaps:
        rec.update(status="account-identity-gap", packageable=False, identity_gaps=identity_gaps)
        return rec

    # 4. content-to-source integrity
    unsupported = []
    for _lk, label, text, sid in _content_items(r):
        if sid not in sources:
            unsupported.append({"type": label, "text": text, "source_id": sid})
    for k, a in enumerate(r.get("accounts") or []):
        if a.get("source_id") not in sources:
            unsupported.append({"type": "account", "text": a.get("account_id"), "source_id": a.get("source_id")})
    if unsupported:
        rec.update(status="unsupported-content", packageable=False, unsupported=unsupported)
        return rec

    # 5. freshness of cited sources (tighter threshold for holdings/performance)
    critical_ids, general_ids = set(), set()
    for list_key, _label, _text, sid in _content_items(r):
        if sid not in sources:
            continue
        (critical_ids if list_key in CRITICAL_CONTENT else general_ids).add(sid)
    for a in r.get("accounts") or []:
        sid = a.get("source_id")
        if sid in sources:
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
    if stale_unack:
        rec.update(status="stale-source", packageable=False, stale_unacknowledged=stale_unack)
        return rec

    # 6. holdings/performance tie-out
    summary, breaks = _portfolio_summary(r, sources)
    if breaks:
        rec.update(status="tieout-break", packageable=False, tie_out_breaks=breaks,
                   portfolio_summary=summary)
        return rec

    # 7. disclosure coverage
    required_disc = list(disclosure_config.get(r.get("review_type"), []))
    present_disc = [d.get("disclosure_id") for d in r.get("disclosures") or []]
    missing_disc = [d for d in required_disc if d not in present_disc]
    if missing_disc:
        rec.update(status="disclosure-gap", packageable=False,
                   disclosure_check={"required": required_disc, "present": present_disc, "missing": missing_disc})
        return rec

    # ---- packageable: assemble the review pack -------------------------------------------
    cited_ids = critical_ids | general_ids
    citations = sorted({_cite(sources[sid]) for sid in cited_ids})
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

    open_actions = [{"action": a.get("action"), "owner": a.get("owner"),
                     "due_date": a.get("due_date"), "status": a.get("status"),
                     "overdue": _overdue(a), "citation": _c(a)}
                    for a in r.get("open_actions") or []]
    life_events = [{"event": e.get("event"), "date": e.get("date"), "citation": _c(e)}
                   for e in r.get("life_events") or []]

    flags = r.get("flags") or {}
    # Surfaced routing (recommendations for a human; never an action or decision taken here).
    routing = []
    if flags.get("recommendation_contemplated"):
        routing.append({"reason": "a product or allocation change is contemplated for this meeting",
                        "route": "suitability-reg-bi-reviewer before any recommendation is made; advisor + supervisory approval"})
    if flags.get("drift_flag"):
        routing.append({"reason": "allocation drift indicated (surfaced, not adjudicated)",
                        "route": "portfolio-rebalancing-assistant — any trade requires advisor and client authorization"})
    if flags.get("senior_investor"):
        routing.append({"reason": "senior-investor / potential-vulnerability indicator present",
                        "route": "senior-investor-protection-screener for trained human review"})
    if life_events:
        routing.append({"reason": "life event(s) surfaced that may change goals or plan assumptions",
                        "route": "financial-goal-progress-analyzer to re-check goal progress"})

    disclosures = [{"disclosure_id": d.get("disclosure_id"), "citation": _c(d)}
                   for d in r.get("disclosures") or []]
    discussion_agenda = [{"question": q.get("question"), "citation": _c(q)}
                         for q in r.get("discussion_questions") or []]

    rec.update(status="draft-review", packageable=True)
    rec["review_pack"] = {
        "client_id": r.get("client_id"),
        "household_name": r.get("household_name"),
        "advisor": r.get("advisor"),
        "review_type": r.get("review_type"),
        "as_of_date": as_of.isoformat(),
        "accounts": [{"account_id": a["account_id"], "type": a["type"], "registration": a["registration"]}
                     for a in r.get("accounts") or []],
        "portfolio_summary": summary,
        "performance": [{"scope": p.get("scope"), "period": p.get("period"),
                         "return_pct": p.get("return_pct"), "benchmark_pct": p.get("benchmark_pct"),
                         "citation": _c(p)} for p in r.get("performance") or []],
        "goals": [{"goal": g.get("goal"), "target": g.get("target"),
                   "target_date": g.get("target_date"), "citation": _c(g)}
                  for g in r.get("goals") or []],
        "plan_items": [{"item": p.get("item"), "status": p.get("status"), "citation": _c(p)}
                       for p in r.get("plan_items") or []],
        "prior_notes": [{"note": n.get("note"), "date": n.get("date"), "citation": _c(n)}
                        for n in r.get("prior_notes") or []],
        "service_history": [{"case_ref": s.get("case_ref"), "summary": s.get("summary"),
                             "status": s.get("status"), "citation": _c(s)}
                            for s in r.get("service_history") or []],
        "life_events": life_events,
        "open_actions": open_actions,
        "discussion_agenda": discussion_agenda,
        "disclosures": disclosures,
        "disclosure_check": {"required": required_disc, "present": present_disc, "missing": missing_disc},
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
    disclosure_config = {**DEFAULT_DISCLOSURE_CONFIG, **(doc.get("disclosure_config") or {})}
    reviews = [prep_review(r, doc, as_of, freshness, critical_freshness, disclosure_config)
               for r in doc["reviews"]]

    def _count(s):
        return sum(1 for b in reviews if b.get("status") == s)

    summary = {
        "total": len(reviews),
        "draft_review": _count("draft-review"),
        "needs_data": _count("needs-data"),
        "unresolved_entity": _count("unresolved-entity"),
        "account_identity_gap": _count("account-identity-gap"),
        "unsupported_content": _count("unsupported-content"),
        "stale_source": _count("stale-source"),
        "tieout_break": _count("tieout-break"),
        "disclosure_gap": _count("disclosure-gap"),
    }
    return {"config_version": doc.get("config_version"), "as_of_date": as_of.isoformat(),
            "freshness_days": freshness, "critical_freshness_days": critical_freshness,
            "reviews": reviews, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reviews_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
