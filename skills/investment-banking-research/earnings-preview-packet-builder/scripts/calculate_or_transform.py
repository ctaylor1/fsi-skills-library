#!/usr/bin/env python3
"""Deterministic earnings-preview packet assembly engine for earnings-preview-packet-builder.

Takes a preview build request (event calendar, consensus, prior guidance, historical KPIs,
controversies/debate points, sensitivities, open questions, a versioned packet template, and
recorded approvals) and assembles a DRAFT, source-backed pre-event preview packet:

  - orders items by the template's required sections and computes a per-item readiness
    status (`ready` / `needs-source` / `unsupported-claim` / `needs-approval`);
  - maps every data point to its cited, approved source;
  - performs DESCRIPTIVE arithmetic only: positions each metric's consensus value against
    the company's prior guidance range (below/within/above + gap to midpoint), and computes
    YoY/QoQ deltas over the reported historical KPI series;
  - rolls up the required supervisory-analyst, research-compliance, and legal approvals and
    sets a packet status.

HARD BOUNDARY: it NEVER originates a forecast, price target, rating, or trade view; every
forward-looking figure is carried with its third-party attribution (consensus/company
guidance) and a source_ref. The consensus-vs-guidance positioning and KPI deltas are factual
transforms of already-sourced numbers, not the skill's own estimate. Distribution is a human
action gated on the recorded approvals; this skill never publishes or distributes.

Usage: python calculate_or_transform.py request.json | --selftest
Normal mode prints the assembled packet JSON. --selftest additionally runs invariant checks
over the bundled fixture and prints a line ending "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Pre-event preview compilation only; no forecast, price target, rating, or trade view "
    "has been set, and no packet has been published or distributed. Consensus and guidance "
    "figures are third-party sourced, not the skill's estimates. External distribution "
    "requires the recorded supervisory-analyst, research-compliance, and legal approvals and "
    "is performed by a person, not this skill."
)
DRAFT_ONLY_NOTICE = (
    "DRAFT - pre-event research preview for internal analyst, supervisory-analyst, and "
    "compliance review only. Not for distribution until the required approvals are recorded. "
    "Contains no forecast, rating, price target, or trade recommendation."
)

# Forward-looking data-point kinds must be attributed to a third party (never the skill).
FORWARD_KINDS = {"consensus", "guidance", "sensitivity"}
SELF_ATTRIB = {"self", "own", "analyst", "analyst-own", "house", "our-model", "skill"}
# Kinds that would mean the skill originated a view — never permitted in a preview packet.
PROHIBITED_KINDS = {"own_forecast", "target", "price_target", "rating", "trade_view"}


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _item_status(it: dict) -> tuple[str, list[str]]:
    """Return (status, issues) for an item; the first blocking condition sets the status."""
    issues: list[str] = []
    dps = it.get("data_points") or []
    unsupported = []
    for c in dps:
        if not c.get("source_ref") or c.get("approved") is not True:
            unsupported.append(c)
            issues.append(f"unsupported/unapproved data point: {c.get('label','')!r}")
        if c.get("kind") in PROHIBITED_KINDS:
            issues.append(f"prohibited data-point kind (originated view): {c.get('kind')!r}")
        elif c.get("kind") in FORWARD_KINDS:
            attr = str(c.get("attribution", "")).strip().lower()
            if not attr or attr in SELF_ATTRIB:
                issues.append(f"forward-looking data point not third-party attributed: {c.get('label','')!r}")
    no_source = not it.get("sources")
    if no_source:
        issues.append("item has no source citation")
    no_takeaway = not it.get("takeaway")
    if no_takeaway:
        issues.append("item has no takeaway")
    appr = (it.get("approval") or {}).get("status")
    needs_approval = appr != "approved"
    if needs_approval:
        issues.append(f"content approval status is {appr!r}")

    if unsupported:
        return "unsupported-claim", issues
    if no_source or no_takeaway:
        return "needs-source", issues
    if needs_approval:
        return "needs-approval", issues
    return "ready", issues


def _consensus_vs_guidance(metrics: list) -> list:
    """Position each metric's consensus value within the company's prior guidance range.

    Purely descriptive: reports below/within/above and the numeric gap to the range midpoint
    of two already-sourced figures. It is NOT the skill's own estimate."""
    out = []
    for m in metrics or []:
        cons = _num(m.get("consensus_value"))
        lo = _num(m.get("guidance_low"))
        hi = _num(m.get("guidance_high"))
        mid = None
        position = "no-guidance"
        gap = None
        if lo is not None and hi is not None:
            mid = round((lo + hi) / 2, 6)
            if cons is not None:
                gap = round(cons - mid, 6)
                if cons < lo:
                    position = "below-range"
                elif cons > hi:
                    position = "above-range"
                else:
                    position = "within-range"
        out.append({
            "metric": m.get("metric"),
            "unit": m.get("unit"),
            "consensus_value": cons,
            "consensus_source": m.get("consensus_source"),
            "guidance_low": lo,
            "guidance_high": hi,
            "guidance_midpoint": mid,
            "guidance_source": m.get("guidance_source"),
            "position": position,
            "gap_to_midpoint": gap,
        })
    return out


def _kpi_trends(kpi_history: list) -> list:
    """Compute YoY/QoQ deltas over a reported KPI series (factual arithmetic on reported
    numbers). No projection is made for the upcoming period."""
    out = []
    for k in kpi_history or []:
        series = [p for p in (k.get("series") or []) if _num(p.get("value")) is not None]
        row = {"kpi": k.get("kpi"), "unit": k.get("unit"), "source": k.get("source"),
               "latest_period": None, "latest_value": None, "prior_value": None,
               "yoy_value": None, "qoq_delta": None, "yoy_delta": None}
        if series:
            latest = series[-1]
            row["latest_period"] = latest.get("period")
            row["latest_value"] = _num(latest.get("value"))
            if len(series) >= 2:
                row["prior_value"] = _num(series[-2].get("value"))
                row["qoq_delta"] = round(row["latest_value"] - row["prior_value"], 6)
            if len(series) >= 5:
                row["yoy_value"] = _num(series[-5].get("value"))
                row["yoy_delta"] = round(row["latest_value"] - row["yoy_value"], 6)
        out.append(row)
    return out


def assemble(doc: dict) -> dict:
    tmpl = doc.get("template") or {}
    required_sections = list(tmpl.get("required_sections") or [])
    items_in = doc.get("items") or []

    order = {s: i for i, s in enumerate(required_sections)}
    items_sorted = sorted(
        enumerate(items_in),
        key=lambda t: (order.get(t[1].get("section"), len(required_sections)), t[0]),
    )

    items_out = []
    unsupported_items = []
    for _, it in items_sorted:
        status, issues = _item_status(it)
        if status == "unsupported-claim":
            for c in (it.get("data_points") or []):
                if not c.get("source_ref") or c.get("approved") is not True:
                    unsupported_items.append({"item_id": it.get("item_id"), "data_point": c.get("label")})
        items_out.append({
            "item_id": it.get("item_id"),
            "section": it.get("section"),
            "title": it.get("title"),
            "source_component": it.get("source_component"),
            "takeaway": it.get("takeaway"),
            "data_points": it.get("data_points") or [],
            "sources": it.get("sources") or [],
            "approval": it.get("approval") or {},
            "status": status,
            "issues": issues,
        })

    present = {it["section"] for it in items_out}
    sections_present = [s for s in required_sections if s in present]
    sections_missing = [s for s in required_sections if s not in present]

    required_approvals = list(doc.get("required_approvals") or [])
    approvals = doc.get("approvals") or []
    appr_map = {a.get("role"): a.get("status") for a in approvals}
    approvals_status = {r: appr_map.get(r, "missing") for r in required_approvals}
    approvals_met = bool(required_approvals) and all(v == "approved" for v in approvals_status.values())

    all_ready = all(it["status"] == "ready" for it in items_out)
    complete = not sections_missing and all_ready and not unsupported_items
    packet_status = "ready-for-distribution" if (complete and approvals_met) else "hold-for-approval"

    cvg = _consensus_vs_guidance(doc.get("metrics") or [])
    kpi_trends = _kpi_trends(doc.get("kpi_history") or [])

    summary = {
        "items_total": len(items_out),
        "items_ready": sum(1 for it in items_out if it["status"] == "ready"),
        "items_blocked": sum(1 for it in items_out if it["status"] != "ready"),
        "sections_present": len(sections_present),
        "sections_missing": len(sections_missing),
        "unsupported_items": len(unsupported_items),
        "metrics_positioned": len(cvg),
        "kpis_trended": len(kpi_trends),
        "approvals_met": approvals_met,
    }

    return {
        "packet_id": doc.get("packet_id"),
        "job_id": doc.get("job_id"),
        "as_of_date": doc.get("as_of_date"),
        "issuer": doc.get("issuer") or {},
        "event": doc.get("event") or {},
        "template_id": tmpl.get("template_id"),
        "template_version": tmpl.get("version"),
        "template_required_sections": required_sections,
        "packet_status": packet_status,
        "sections_present": sections_present,
        "sections_missing": sections_missing,
        "items": items_out,
        "consensus_vs_guidance": cvg,
        "kpi_trends": kpi_trends,
        "unsupported_items": unsupported_items,
        "required_approvals": required_approvals,
        "approvals": approvals,
        "approvals_status": approvals_status,
        "summary": summary,
        "draft_only_notice": DRAFT_ONLY_NOTICE,
        "standing_note": STANDING_NOTE,
    }


def _selftest() -> int:
    """Assemble the bundled fixture and assert descriptive-only invariants."""
    base = Path(__file__).resolve().parents[1] / "evals" / "files"
    req = json.loads((base / "preview_request_example.json").read_text(encoding="utf-8"))
    out = assemble(req)
    errors: list[str] = []

    if out["packet_status"] != "ready-for-distribution":
        errors.append(f"expected packet_status ready-for-distribution, got {out['packet_status']!r}")
    if out["sections_missing"]:
        errors.append(f"unexpected missing sections: {out['sections_missing']}")
    if any(it["status"] != "ready" for it in out["items"]):
        errors.append("not all items are 'ready'")
    if out["unsupported_items"]:
        errors.append("unexpected unsupported items")

    # descriptive arithmetic tie-outs
    by_metric = {m["metric"]: m for m in out["consensus_vs_guidance"]}
    rev = by_metric.get("Revenue")
    if not rev or rev["position"] != "within-range" or rev["gap_to_midpoint"] != 10.0:
        errors.append(f"Revenue positioning wrong: {rev}")
    kpi = {k["kpi"]: k for k in out["kpi_trends"]}
    units = kpi.get("Units shipped")
    if not units or units["qoq_delta"] != -700.0 or units["yoy_delta"] != 4800.0:
        errors.append(f"Units shipped deltas wrong: {units}")

    # no forward-looking data point may be self-attributed or an originated view
    for it in out["items"]:
        for c in it["data_points"]:
            if c.get("kind") in PROHIBITED_KINDS:
                errors.append(f"prohibited data-point kind present: {c.get('kind')!r}")
            if c.get("kind") in FORWARD_KINDS and str(c.get("attribution", "")).lower() in SELF_ATTRIB:
                errors.append(f"self-attributed forward-looking data point: {c.get('label')!r}")

    print(json.dumps(out, indent=2))
    for e in errors:
        print("ERROR", e)
    print(f"transform selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
