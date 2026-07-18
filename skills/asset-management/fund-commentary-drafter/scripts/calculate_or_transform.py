#!/usr/bin/env python3
"""Deterministic fund-commentary draft assembler for fund-commentary-drafter.

Takes a reconciled commentary-inputs file and assembles a STRUCTURED DRAFT: it tie-outs
performance (excess == fund - benchmark) and attribution (effects sum == total excess ==
performance excess), builds a claim ledger where every narrative claim is bound to a source
citation or an APPROVED messaging id, and flags any proposed claim it cannot substantiate.

It never approves, sends, files, or publishes. Approvals are left `pending` for the product
and compliance reviewers. A claim that cannot be tied to a source is flagged `unsupported`
and excluded from the release-ready ledger — it is never silently asserted.

Usage: python calculate_or_transform.py commentary_inputs.json | --selftest
Prints the commentary-draft JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

PERF_TOL = 0.011      # excess vs (fund - benchmark), in percentage points
ATTRIB_TOL = 0.10     # attribution effects sum vs total excess (allows interaction/residual)
REQUIRED_SECTIONS = [
    "performance_summary", "attribution", "positioning", "flows",
    "market_context", "outlook", "disclosures",
]
STANDING_NOTE = ("Draft only - not for distribution until product and compliance approvals "
                 "are recorded; this skill does not send, file, or publish.")


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _perf_tieout(rp):
    fund, bench, excess = _f(rp.get("fund_return_pct")), _f(rp.get("benchmark_return_pct")), _f(rp.get("excess_return_pct"))
    computed = round(fund - bench, 4)
    ok = rp.get("reconciled") is True and abs(computed - excess) <= PERF_TOL
    detail = f"excess {excess:.2f}% == fund {fund:.2f}% - benchmark {bench:.2f}% ({computed:.2f}%)"
    return ok, detail, excess


def _attrib_tieout(att, perf_excess):
    effects = att.get("effects") or []
    s = round(sum(_f(e.get("contribution_pct")) for e in effects), 4)
    total = _f(att.get("total_excess_pct"))
    ok = (att.get("reconciled") is True
          and abs(s - total) <= ATTRIB_TOL
          and abs(total - perf_excess) <= PERF_TOL)
    detail = (f"effects sum {s:.2f}% == total_excess {total:.2f}% (tol {ATTRIB_TOL}); "
              f"total == performance excess {perf_excess:.2f}%")
    return ok, detail, s


def _known_source_ids(doc):
    ids = set()
    rp = doc.get("reconciled_performance") or {}
    if rp.get("source_ref"):
        ids.add(rp["source_ref"])
    att = doc.get("attribution") or {}
    if att.get("source_ref"):
        ids.add(att["source_ref"])
    for e in att.get("effects") or []:
        if e.get("source_ref"):
            ids.add(e["source_ref"])
    for grp in ("positioning", "market_context"):
        for item in doc.get(grp) or []:
            if item.get("source_ref"):
                ids.add(item["source_ref"])
    fl = doc.get("flows") or {}
    if fl.get("source_ref"):
        ids.add(fl["source_ref"])
    for m in doc.get("approved_messaging") or []:
        if m.get("status") == "approved" and m.get("id"):
            ids.add(m["id"])
    return ids


def build_draft(doc: dict) -> dict:
    fund = doc.get("fund") or {}
    period = doc.get("period") or {}
    plabel = period.get("label", "")
    rp = doc.get("reconciled_performance") or {}
    att = doc.get("attribution") or {}

    perf_ok, perf_detail, perf_excess = _perf_tieout(rp)
    attrib_ok, attrib_detail, _ = _attrib_tieout(att, perf_excess)
    known = _known_source_ids(doc)

    ledger, unsupported = [], []

    def add(cid, section, text, source_refs, category):
        refs = [r for r in source_refs if r]
        supported = bool(refs)
        rec = {"id": cid, "section": section, "text": text, "source_refs": refs,
               "supported": supported, "category": category, "period_label": plabel}
        if supported:
            ledger.append(rec)
        else:
            rec["reason"] = "no source citation"
            unsupported.append(rec)
        return rec

    # 1. Performance summary
    add("C-PERF", "performance_summary",
        f"For {plabel}, the {fund.get('fund_name','fund')} ({fund.get('share_class','')}) returned "
        f"{_f(rp.get('fund_return_pct')):.2f}% versus {_f(rp.get('benchmark_return_pct')):.2f}% for the "
        f"{fund.get('benchmark','benchmark')}, an excess return of {_f(rp.get('excess_return_pct')):.2f}%.",
        [rp.get("source_ref")], "performance")

    # 2. Attribution (lead claim + one per effect)
    effects = att.get("effects") or []
    lead = max(effects, key=lambda e: _f(e.get("contribution_pct")), default=None)
    if lead:
        add("C-ATTR-LEAD", "attribution",
            f"The largest positive contributor to relative return was {lead.get('name','')} "
            f"({_f(lead.get('contribution_pct')):+.2f}%).",
            [att.get("source_ref"), lead.get("source_ref")], "attribution")
    for i, e in enumerate(effects):
        add(f"C-ATTR-{i}", "attribution",
            f"{str(e.get('name','')).capitalize()} contributed {_f(e.get('contribution_pct')):+.2f}% "
            f"to relative return.",
            [e.get("source_ref"), att.get("source_ref")], "attribution")

    # 3. Positioning
    for i, p in enumerate(doc.get("positioning") or []):
        add(f"C-POS-{i}", "positioning", p.get("statement", ""), [p.get("source_ref")], "positioning")

    # 4. Flows
    fl = doc.get("flows") or {}
    if fl:
        add("C-FLOW", "flows",
            f"Net flows for the period were {_f(fl.get('net_flows_musd')):+.1f}m {fund.get('currency','')}.",
            [fl.get("source_ref")], "flows")

    # 5. Market context
    for i, m in enumerate(doc.get("market_context") or []):
        add(f"C-MKT-{i}", "market_context", m.get("statement", ""), [m.get("source_ref")], "market_context")

    # 6. Approved messaging -> outlook / assigned section (only status == approved)
    unapproved_messaging = []
    for m in doc.get("approved_messaging") or []:
        if m.get("status") == "approved":
            add(f"C-MSG-{m.get('id','?')}", m.get("section", "outlook"), m.get("text", ""),
                [m.get("id")], "messaging")
        else:
            unapproved_messaging.append(m.get("id"))

    # 7. Proposed free-text draft claims: substantiate against known sources / approved messaging
    for d in doc.get("draft_claims") or []:
        refs = [r for r in (d.get("source_refs") or []) if r]
        resolved = [r for r in refs if r in known]
        if refs and len(resolved) == len(refs):
            add(d.get("id", "C-DRAFT"), d.get("section", "outlook"), d.get("text", ""),
                resolved, "drafted")
        else:
            unresolved = [r for r in refs if r not in known] or ["<none>"]
            unsupported.append({"id": d.get("id", "C-DRAFT"), "section": d.get("section", "outlook"),
                                "text": d.get("text", ""), "source_refs": refs, "supported": False,
                                "category": "drafted",
                                "reason": f"unresolved/absent source(s): {unresolved}"})

    # Sections view
    sections = {}
    for key in REQUIRED_SECTIONS:
        if key == "disclosures":
            sections[key] = {"heading": "Important information",
                             "disclosures": list(doc.get("disclosures") or [])}
        else:
            claim_ids = [c["id"] for c in ledger if c["section"] == key]
            sections[key] = {"heading": key.replace("_", " ").title(), "claim_ids": claim_ids}

    disclosures_present = list(doc.get("disclosures") or [])
    required_disclosures = list(doc.get("required_disclosures") or [])

    return {
        "template_version": doc.get("template_version"),
        "fund": fund,
        "period": period,
        "sections": sections,
        "claim_ledger": ledger,
        "unsupported_claims": unsupported,
        "tie_outs": {
            "performance": {"ok": perf_ok, "detail": perf_detail},
            "attribution": {"ok": attrib_ok, "detail": attrib_detail},
        },
        "period_fidelity": {"ok": bool(plabel), "period_label": plabel},
        "disclosures_present": disclosures_present,
        "required_disclosures": required_disclosures,
        "unapproved_messaging": [x for x in unapproved_messaging if x],
        "approvals": {"product": {"status": "pending"}, "compliance": {"status": "pending"}},
        "delivery_status": "draft",
        "action_mode": "draft-only",
        "standing_note": STANDING_NOTE,
        "summary": {
            "claims_total": len(ledger) + len(unsupported),
            "claims_supported": len(ledger),
            "claims_unsupported": len(unsupported),
            "performance_tie_out": perf_ok,
            "attribution_tie_out": attrib_ok,
        },
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "commentary_inputs.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_draft(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
