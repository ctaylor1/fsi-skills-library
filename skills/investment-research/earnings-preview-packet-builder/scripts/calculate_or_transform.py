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

    if unsupported or any("prohibited" in issue or "not third-party" in issue for issue in issues):
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
            "fiscal_period":m["fiscal_period"],"accounting_basis":m["accounting_basis"],
            "consensus_known_at":m.get("consensus_known_at"),"guidance_known_at":m.get("guidance_known_at"),
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


def _kpi_trends(kpi_history):
    out=[]
    for k in kpi_history or []:
        points={(p["fiscal_year"],p["fiscal_quarter"]):p for p in k["series"]}
        y,q=max(points); latest=points[(y,q)]
        prior_key=(y,q-1) if q>1 else (y-1,4)
        prior=points.get(prior_key); yoy=points.get((y-1,q))
        value=latest["value"]
        out.append({"kpi":k.get("kpi"),"unit":k["unit"],"source":k["source"],"known_at":k["known_at"],
                    "latest_period":latest["period"],"latest_value":value,
                    "fiscal_year":y,"fiscal_quarter":q,
                    "prior_period":prior["period"] if prior else None,
                    "yoy_period":yoy["period"] if yoy else None,
                    "prior_value":prior["value"] if prior else None,
                    "yoy_value":yoy["value"] if yoy else None,
                    "qoq_delta":round(value-prior["value"],6) if prior else None,
                    "yoy_delta":round(value-yoy["value"],6) if yoy else None,
                    "gaps":(["prior fiscal quarter missing"] if not prior else [])+(["same fiscal quarter last year missing"] if not yoy else [])})
    return out


def _assemble_native(doc: dict) -> dict:
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
            "source_component": it.get("source_component"),"known_at":it["known_at"],
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
    packet_status = "ready-for-control-review" if (complete and approvals_met) else "hold-for-approval"

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


from native_integrity import attach_source, canonical_hash

def _validated_input(doc):
    import importlib.util
    p=Path(__file__).with_name("validate_input.py")
    spec=importlib.util.spec_from_file_location("_native_input_"+p.parent.parent.name.replace("-","_"),p)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    errors,_=module.validate(doc)
    if errors: raise ValueError("; ".join(errors))

def assemble(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        from phase2_domain import compute as phase2_compute
        return phase2_compute(doc)
    _validated_input(doc)
    result=_assemble_native(doc)
    result.update({"knowledge_cutoff":doc["knowledge_cutoff"],
                   "review_profile_id":doc["review_profile_id"],"review_profile_version":doc["review_profile_version"],
                   "authority":"source eligibility and role records are supplied assertions; authentication, entitlement and distribution authority are not established",
                   "review_scope":"supplied sell-side preview profile only; alternate institutional profiles require review"})
    canonical_hash(result)
    return attach_source(result,doc)


def _selftest() -> int:
    """Assemble the bundled fixture and assert descriptive-only invariants."""
    base = Path(__file__).resolve().parents[1] / "evals" / "files"
    req = _read_json((base / "preview_request_example.json").read_text(encoding="utf-8"))
    out = assemble(req)
    errors: list[str] = []

    if out["packet_status"] != "ready-for-control-review":
        errors.append(f"expected packet_status ready-for-control-review, got {out['packet_status']!r}")
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
        doc = _read_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _read_json(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
