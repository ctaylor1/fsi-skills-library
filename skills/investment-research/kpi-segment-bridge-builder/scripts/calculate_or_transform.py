#!/usr/bin/env python3
"""Deterministic KPI / segment bridge engine for kpi-segment-bridge-builder.

Reads a KPI-bridge input file (see validate_input.py) and constructs the requested
revenue / margin / volume-price / segment bridges as a source-linked deliverable. Two
bridge families are supported, both DETERMINISTIC with explicit conventions:

  * `walk`  - an additive walk of DISCLOSED signed components from a beginning to an ending
    value (segment deltas, disclosed revenue/margin walks). The engine reconciles the
    components to the ending value and computes each component's contribution share.
  * `volume_price`  - a two-factor (units x price) decomposition of a revenue delta computed
    from disclosed prior/current units and price using a documented base-period-weighting
    convention with an explicit joint (mix) cross-term:
        volume = (units_t - units_0) * price_0
        price  = (price_t - price_0) * units_0
        mix    = (units_t - units_0) * (price_t - price_0)      # joint / cross term
        sum = units_t*price_t - units_0*price_0  == revenue delta  (exact by construction)

The engine NEVER forecasts and NEVER normalizes accounting judgment beyond approved
mappings: forward-looking source types are rejected upstream by validate_input, and any
re-mapped component must reference an approved `mapping_id`. Conventions, tolerances, and
approved mappings are versioned configuration (config_version, mapping_version), not the
skill's judgment. See references/domain-rules.md.

Usage:
  python calculate_or_transform.py kpi_bridge_input.json | --selftest
Prints the bridge pack JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROUND = 4          # value precision (units are typically millions or pct points)
CONTRIB_ROUND = 6  # contribution-share precision
TOL = 0.01         # tie-out tolerance
VP_CONVENTION = "base_period_weighted_with_joint_mix"
DISCLAIMER = ("Historical, source-linked KPI/segment bridge for analytical purposes only; a "
              "decomposition of disclosed, reported results. It is not a forecast, not "
              "normalized accounting, not investment advice, and not a recommendation. Every "
              "figure ties to a disclosed source, and a qualified human must review it before "
              "any use.")


def _v(node):
    return float(node.get("value")) if isinstance(node, dict) else float(node)


def _prov(node):
    return node.get("provenance", "") if isinstance(node, dict) else ""


def _cite(node):
    return node.get("citation", "") if isinstance(node, dict) else ""


def _src(node):
    return (node.get("source_type", "") if isinstance(node, dict) else "").strip().lower()


def _reconcile(b, reported, beginning, ending):
    """Reconcile beginning/ending to the stated authoritative (disclosed) totals."""
    rc = b.get("reconcile_to") or {}
    out = {"beginning_key": rc.get("beginning_key"), "ending_key": rc.get("ending_key"),
           "beginning_ok": None, "ending_ok": None}
    if rc.get("beginning_key") in reported:
        out["beginning_ok"] = abs(beginning - _v(reported[rc["beginning_key"]])) <= TOL
    if rc.get("ending_key") in reported:
        out["ending_ok"] = abs(ending - _v(reported[rc["ending_key"]])) <= TOL
    return out


def _reconcile_ok(rec):
    vals = [rec["beginning_ok"], rec["ending_ok"]]
    checked = [v for v in vals if v is not None]
    return len(checked) == 2 and all(checked)


def build_walk(b, reported):
    beginning = round(_v(b["beginning"]), ROUND)
    ending = round(_v(b["ending"]), ROUND)
    total_change = round(ending - beginning, ROUND)
    comps, csum = [], 0.0
    for c in b.get("components", []):
        amt = round(_v(c.get("amount")), ROUND)
        csum = round(csum + amt, ROUND)
        contribution = round(amt / total_change, CONTRIB_ROUND) if total_change else None
        comps.append({
            "id": c.get("id"), "label": c.get("label", c.get("id")),
            "amount": amt, "contribution": contribution,
            "derivation": (c.get("derivation") or "disclosed"),
            "source_type": _src(c), "mapping_id": c.get("mapping_id"),
            "provenance": _prov(c), "citation": _cite(c),
        })
    residual = round(total_change - csum, ROUND)
    contrib_sum = round(sum(x["contribution"] for x in comps if x["contribution"] is not None), CONTRIB_ROUND)
    rec = _reconcile(b, reported, beginning, ending)
    return {
        "beginning": beginning, "ending": ending, "total_change": total_change,
        "components": comps, "sum_components": csum, "residual": residual,
        "contribution_sum": contrib_sum, "reconcile_to": rec,
        "tieouts": {
            "walk_ok": abs(beginning + csum - ending) <= TOL,
            "contribution_sum_ok": (total_change == 0) or abs(contrib_sum - 1.0) <= 1e-4,
            "reconcile_ok": _reconcile_ok(rec),
        },
    }


def build_volume_price(b, reported):
    f = b["factors"]
    u0, p0 = _v(f["prior_units"]), _v(f["prior_price"])
    ut, pt = _v(f["current_units"]), _v(f["current_price"])
    beginning = round(u0 * p0, ROUND)
    ending = round(ut * pt, ROUND)
    total_change = round(ending - beginning, ROUND)
    volume = round((ut - u0) * p0, ROUND)
    price = round((pt - p0) * u0, ROUND)
    mix = round((ut - u0) * (pt - p0), ROUND)

    def cite_from(*keys):
        prov = next((_prov(f[k]) for k in keys if _prov(f[k])), "")
        cite = "; ".join(sorted({_cite(f[k]) for k in keys if _cite(f[k])}))
        return prov, cite

    comps = []
    for cid, label, amt, keys in (
        ("volume", "Volume effect", volume, ("current_units", "prior_units", "prior_price")),
        ("price", "Price/rate effect", price, ("current_price", "prior_price", "prior_units")),
        ("mix", "Mix (joint) effect", mix, ("current_units", "prior_units", "current_price", "prior_price")),
    ):
        prov, cite = cite_from(*keys)
        comps.append({
            "id": cid, "label": label, "amount": amt,
            "contribution": round(amt / total_change, CONTRIB_ROUND) if total_change else None,
            "derivation": "computed", "source_type": "derived", "mapping_id": None,
            "provenance": prov or "derived-from-disclosed-factors", "citation": cite,
        })
    csum = round(volume + price + mix, ROUND)
    contrib_sum = round(sum(x["contribution"] for x in comps if x["contribution"] is not None), CONTRIB_ROUND)
    rec = _reconcile(b, reported, beginning, ending)
    return {
        "beginning": beginning, "ending": ending, "total_change": total_change,
        "convention": VP_CONVENTION,
        "factors": {"prior_units": u0, "prior_price": p0, "current_units": ut, "current_price": pt},
        "components": comps, "sum_components": csum, "residual": round(total_change - csum, ROUND),
        "contribution_sum": contrib_sum, "reconcile_to": rec,
        "tieouts": {
            "walk_ok": abs(beginning + csum - ending) <= TOL,
            "contribution_sum_ok": (total_change == 0) or abs(contrib_sum - 1.0) <= 1e-4,
            "reconcile_ok": _reconcile_ok(rec),
            "factors_ok": abs(u0 * p0 - beginning) <= TOL and abs(ut * pt - ending) <= TOL,
        },
    }


def _register(doc):
    """Assumption register: every disclosed input with provenance + citation + source_type."""
    reg = []
    for key, node in (doc.get("reported_totals") or {}).items():
        reg.append({"id": f"reported:{key}", "scope": "reported-total", "value": _v(node),
                    "source_type": _src(node), "provenance": _prov(node), "citation": _cite(node)})
    for b in doc["bridges"]:
        bid = b.get("id")
        if b.get("type") == "walk":
            for side in ("beginning", "ending"):
                node = b.get(side)
                reg.append({"id": f"{bid}:{side}", "scope": "bridge-anchor", "value": _v(node),
                            "source_type": _src(node), "provenance": _prov(node), "citation": _cite(node)})
            for c in b.get("components", []):
                reg.append({"id": f"{bid}:comp:{c.get('id')}", "scope": "bridge-component",
                            "value": round(_v(c.get("amount")), ROUND), "source_type": _src(c),
                            "derivation": c.get("derivation") or "disclosed",
                            "mapping_id": c.get("mapping_id"),
                            "provenance": _prov(c), "citation": _cite(c)})
        elif b.get("type") == "volume_price":
            for fk, node in b["factors"].items():
                reg.append({"id": f"{bid}:factor:{fk}", "scope": "bridge-factor", "value": _v(node),
                            "source_type": _src(node), "provenance": _prov(node), "citation": _cite(node)})
    return reg


def _mapping_register(doc):
    used = set()
    for b in doc["bridges"]:
        for c in b.get("components", []):
            if c.get("mapping_id"):
                used.add(c["mapping_id"])
    approved = {m.get("mapping_id"): m for m in (doc.get("approved_mappings") or []) if isinstance(m, dict)}
    reg = []
    for mid in sorted(used):
        m = approved.get(mid, {})
        reg.append({"mapping_id": mid, "status": m.get("status", "UNAPPROVED"),
                    "effective_date": m.get("effective_date"), "description": m.get("description")})
    return reg


def _calculate_native(doc: dict) -> dict:
    reported = doc.get("reported_totals") or {}
    bridges_out = []
    for b in doc["bridges"]:
        core = build_walk(b, reported) if b.get("type") == "walk" else build_volume_price(b, reported)
        bridges_out.append({"id": b.get("id"), "type": b.get("type"), "metric": b.get("metric"),
                            "unit": b.get("unit", "currency"), **core})

    inputs_hash = _local_module("native_integrity.py").canonical_hash(doc)[:16]
    company = str(doc["company_id"]).replace("*", "")
    cur_label = (doc["current_period"] or {}).get("label", (doc["current_period"] or {}).get("end"))

    register = _register(doc)
    mapping_reg = _mapping_register(doc)
    all_tieouts_ok = all(all(v for v in bo["tieouts"].values() if isinstance(v, bool))
                         for bo in bridges_out)
    all_reconciled = all(bo["tieouts"].get("reconcile_ok", False) for bo in bridges_out)
    mappings_all_approved = all((m.get("status") or "").lower() == "approved" for m in mapping_reg)

    return {
        "pack_id": f"kpi-bridge-{company}-{cur_label}-{inputs_hash}",
        "job_id": doc.get("job_id", f"job-{company}-{inputs_hash}"),
        "company_id": doc["company_id"],
        "as_of": doc["as_of"],
        "prior_period": doc.get("prior_period"),
        "current_period": doc.get("current_period"),
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "config_version": doc.get("config_version"),
        "mapping_version": doc.get("mapping_version"),
        "inputs_hash": inputs_hash,
        "reported_totals": {k: _v(v) for k, v in reported.items()},
        "reconciliation_status": "reconciled" if all_reconciled else "partial-or-not-evaluable",
        "limitations": ["Historical closed periods only; not a forecast input adapter.", "Volume/price joint term is a two-factor interaction, not a general product-mix attribution."],
        "bridges": bridges_out,
        "assumptions_register": register,
        "mapping_register": mapping_reg,
        "model_checks": {
            "all_tieouts_ok": all_tieouts_ok,
            "all_reconciled": all_reconciled,
            "mappings_all_approved": mappings_all_approved,
        },
        "disclaimer": DISCLAIMER,
    }


def _strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return _read_json(text, object_pairs_hook=pairs, parse_constant=constant)

def _local_module(filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_local_" + filename.replace(".", "_"), Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def compute(doc):
    errors, warnings = _local_module("validate_input.py").validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    result = _calculate_native(doc)
    result["validation_warnings"] = warnings
    result["method_id"] = 'kpi-segment-bridge-builder'
    result["method_version"] = "0.3.0"
    result["result_origin"] = "local-analysis"
    result["review_status"] = "not-requested"
    result["execution_status"] = "not-performed"
    result["method_scope"] = 'kpi-segment-bridge-builder: bounded supplied-input local analysis; no source authentication, approval or execution'
    return _local_module("native_integrity.py").attach_source(result, doc)

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "kpi_bridge_input.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

_compute_phase1 = compute

def compute(doc):
    if isinstance(doc, dict) and doc.get('schema_version') == 'ir-phase2/1.0':
        return _local_module('phase2_domain.py').compute(doc)
    return _compute_phase1(doc)

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
