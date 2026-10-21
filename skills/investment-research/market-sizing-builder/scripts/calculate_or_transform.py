#!/usr/bin/env python3
"""Deterministic TAM/SAM/SOM market-sizing engine for market-sizing-builder.

Reads a market-sizing input file (see validate_input.py), builds a transparent market model
by supplied top-down and/or bottom-up methods per scenario; evidence independence is unverified:

  * top-down  : TAM = total_market; SAM = TAM * sam_ratio; SOM = SAM * som_ratio
  * bottom-up : per segment TAM = units * arpu; SAM = TAM * attach_rate;
                SOM = SAM * capture_rate; method totals are the segment sums

It then reconciles the two methods (triangulation gap per level per scenario), records every
driver assumption with its provenance and source tier, designates a documented primary method
for the reported headline figures, and emits per-scenario/per-method tie-outs. The output is a
machine-readable core the SKILL wraps in a plain-language pack.

IMPORTANT: This produces a transparent *market-size estimate* only. It NEVER produces
investment advice, a securities recommendation, a price target, or a guarantee of revenue or
market share. Scenario definitions, tolerances, and the primary method are configuration
(versioned), not per-engagement judgments. See references/domain-rules.md.

Usage:
  python calculate_or_transform.py market_sizing_input.json | --selftest
Prints the sizing JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "scenarios": ["low", "base", "high"],
    "primary_method": "top_down",
    "triangulation_tolerance_pct": 0.20,
    "tolerance": 0.01,
}
LEVELS = ("tam", "sam", "som")
DISCLAIMER = (
    "Market-size estimates for analytical purposes only; not investment advice, not a "
    "recommendation to buy, sell, or hold any security, and not a guarantee of revenue or "
    "market share. Estimates depend on the stated assumptions and sources and will vary."
)


def _r(x: float) -> float:
    return round(float(x), 2)


def _driver_value(driver: dict, scenario: str) -> float:
    return float(driver["values"][scenario])


def _register_driver(register: list, driver: dict, kind: str, scope: str) -> None:
    register.append({
        "id": driver["id"],
        "label": driver.get("label", driver["id"]),
        "kind": kind,
        "scope": scope,
        "provenance": driver.get("provenance", ""),
        "source_tier": driver.get("source_tier", ""),
        "source_date": driver.get("source_date"),
        "values": {k: float(v) for k, v in driver["values"].items()},
    })


def _top_down(td: dict, scenarios: list, register: list) -> dict:
    total = td["total_market"]
    sam_ratio = td["sam_ratio"]
    som_ratio = td["som_ratio"]
    _register_driver(register, total, "total_market", "top_down")
    _register_driver(register, sam_ratio, "sam_ratio", "top_down")
    _register_driver(register, som_ratio, "som_ratio", "top_down")
    rows = {}
    for sc in scenarios:
        tam = _r(_driver_value(total, sc))
        sr = _driver_value(sam_ratio, sc)
        cr = _driver_value(som_ratio, sc)
        sam = _r(tam * sr)
        som = _r(sam * cr)
        rows[sc] = {"scenario": sc, "tam": tam, "sam": sam, "som": som,
                    "sam_ratio": sr, "som_ratio": cr}
    return {"method": "top_down", "scenarios": rows}


def _bottom_up(bu: dict, scenarios: list, register: list) -> dict:
    segments = bu["segments"]
    for seg in segments:
        for kind in ("units", "arpu", "attach_rate", "capture_rate"):
            _register_driver(register, seg[kind], kind, f"bottom_up:{seg['id']}")
    rows = {}
    seg_detail = {sc: [] for sc in scenarios}
    for sc in scenarios:
        tam = sam = som = 0.0
        for seg in segments:
            units = _driver_value(seg["units"], sc)
            arpu = _driver_value(seg["arpu"], sc)
            attach = _driver_value(seg["attach_rate"], sc)
            capture = _driver_value(seg["capture_rate"], sc)
            s_tam = _r(units * arpu)
            s_sam = _r(s_tam * attach)
            s_som = _r(s_sam * capture)
            tam += s_tam
            sam += s_sam
            som += s_som
            seg_detail[sc].append({"id": seg["id"], "label": seg.get("label", seg["id"]),
                                   "tam": s_tam, "sam": s_sam, "som": s_som,
                                   "units": units, "arpu": arpu,
                                   "attach_rate": attach, "capture_rate": capture})
        rows[sc] = {"scenario": sc, "tam": _r(tam), "sam": _r(sam), "som": _r(som)}
    return {"method": "bottom_up", "scenarios": rows, "segments": seg_detail}


def _tieouts(top_down: dict, bottom_up: dict, scenarios: list, tol: float) -> list:
    """Formula tie-outs: each method must satisfy SOM <= SAM <= TAM per scenario, and the
    scenario series must be ordered (low <= base <= high) for every level."""
    checks = []
    for method_name, block in (("top_down", top_down), ("bottom_up", bottom_up)):
        if block is None: continue
        for sc in scenarios:
            r = block["scenarios"][sc]
            checks.append({
                "check": "containment", "method": method_name, "scenario": sc,
                "ok": bool(r["som"] <= r["sam"] + tol and r["sam"] <= r["tam"] + tol),
                "detail": {"som": r["som"], "sam": r["sam"], "tam": r["tam"]},
            })
        for level in LEVELS:
            series = [block["scenarios"][sc][level] for sc in scenarios]
            ordered = all(series[i] <= series[i + 1] + tol for i in range(len(series) - 1))
            checks.append({
                "check": "scenario_ordering", "method": method_name, "level": level,
                "ok": bool(ordered), "detail": dict(zip(scenarios, series)),
            })
    return checks


def _triangulate(top_down: dict, bottom_up: dict, scenarios: list, tol_pct: float) -> list:
    tri = []
    for sc in scenarios:
        for level in LEVELS:
            a = top_down["scenarios"][sc][level]
            b = bottom_up["scenarios"][sc][level]
            denom = max(abs(a), abs(b)) or 1.0
            gap = abs(a - b) / denom
            tri.append({"scenario": sc, "level": level, "top_down": a, "bottom_up": b,
                        "gap_pct": round(gap, 4), "within_tolerance": bool(gap <= tol_pct)})
    return tri


def _native_compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    scenarios = list(cfg["scenarios"])
    tol = float(cfg["tolerance"])
    tol_pct = float(cfg["triangulation_tolerance_pct"])
    primary = cfg["primary_method"]

    register=[]; blocks={}
    if doc.get("top_down") is not None: blocks["top_down"]=_top_down(doc["top_down"],scenarios,register)
    if doc.get("bottom_up") is not None: blocks["bottom_up"]=_bottom_up(doc["bottom_up"],scenarios,register)
    both=len(blocks)==2
    tieouts=_tieouts(blocks.get("top_down"),blocks.get("bottom_up"),scenarios,tol)
    triangulation=_triangulate(blocks["top_down"],blocks["bottom_up"],scenarios,tol_pct) if both else []
    dates_complete=all(dr.get("source_date") for dr in register)
    complete=both and doc.get("segment_coverage")=="complete" and dates_complete
    return {"sizing_id":f"mkt-{doc['market_id']}-{doc['as_of']}-0001","market_id":doc["market_id"],"market_name":doc.get("market_name",doc["market_id"]),"as_of":doc["as_of"],"currency":doc["currency"],"dimensions":doc["dimensions"],"config_version":doc["config_version"],"scenarios":scenarios,"primary_method":primary,"triangulation_tolerance_pct":tol_pct,
      "top_down":blocks.get("top_down"),"bottom_up":blocks.get("bottom_up"),"reported":{sc:{level:blocks[primary]["scenarios"][sc][level] for level in LEVELS} for sc in scenarios},
      "tieouts":tieouts,"triangulation":triangulation,"assumptions_register":register,"coverage_status":"complete-for-declared-scope" if complete else "partial",
      "segment_coverage":doc.get("segment_coverage","unknown"),"source_dates_complete":dates_complete,
      "limitations":["Market boundary, disjoint segments, source truth and independent-method evidence are caller declarations needing review", "Single-method or incomplete coverage is not a triangulated full-market estimate"],"disclaimer":DISCLAIMER}


def compute(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        from phase2_domain import compute as phase2_compute
        return phase2_compute(doc)
    import importlib.util
    from native_integrity import attach_source
    source=Path(__file__).with_name("validate_input.py")
    spec=importlib.util.spec_from_file_location("_native_input_"+Path(__file__).parents[1].name.replace("-","_"),source)
    validator=importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    errors,_=validator.validate(doc)
    if errors: raise ValueError("; ".join(errors))
    return attach_source(_native_compute(doc),doc)

def main(argv):
    try:
        path=Path(__file__).resolve().parents[1]/"evals/files/market_sizing_input_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        doc=_read_json(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False))
        if "--selftest" in argv and "market-sizing-builder"=="market-landscape-researcher": print("calculate self-check: 0 error(s)")
        return 0
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print("ERROR invalid input: "+str(exc)); return 1
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


if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
