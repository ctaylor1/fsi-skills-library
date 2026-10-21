#!/usr/bin/env python3
"""Deterministic coverage-dossier assembly for coverage-initiation-researcher.

Reads a coverage-research dossier (see validate_input.py), computes section-completeness
and evidence coverage, runs forecast internal-consistency checks, triangulates a DRAFT
valuation range from provided method outputs, and maps the result to a deterministic
draft-readiness band. Emits a machine-readable coverage pack that the SKILL wraps in a
plain-language, cited draft.

IMPORTANT: This assembles and checks a *draft* research artifact only. It never issues an
approved rating or price target, never provides personalized investment advice, and never
makes a buy/sell/hold decision. The readiness band is a workflow-state suggestion for the
analyst and reviewer, NOT an investment recommendation. The rating stays draft-unapproved
until a supervisory analyst and the research committee approve it (see references/controls.md).

Usage:
  python calculate_or_transform.py dossier.json | --selftest
Prints the coverage-pack JSON to stdout. Exit 0.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "business_model", "industry", "competitive_position", "forecast",
    "catalysts", "risks", "valuation", "thesis",
]
DEFAULT_CONFIG = {
    "min_claims_per_section": 1,
    "growth_tolerance": 0.005,
    "weights_tolerance": 0.01,
    "margin_min": None,
    "margin_max": None,
}
DRAFT_BANNER = "DRAFT — not approved for distribution."
DISCLAIMER = (
    "Research draft for internal review only; not investment advice, not an approved rating "
    "or price target, and subject to Reg AC certification and supervisory analyst and research "
    "committee approval before publication."
)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def expected_readiness(missing_sections, unevidenced_sections, forecast_errors,
                       valuation_complete, data_gaps, evidence_coverage) -> str:
    """Deterministic readiness mapping. Duplicated verbatim in validate_output.py so the
    output check can tie out the band without importing this module."""
    blocking = bool(missing_sections) or bool(unevidenced_sections) \
        or bool(forecast_errors) or not valuation_complete
    if blocking:
        return "Not ready"
    if data_gaps or (evidence_coverage is not None and evidence_coverage < 1.0):
        return "Analyst review"
    return "Ready for supervisory review"


def _native_compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    sections_in = {s.get("section"): s for s in (doc.get("sections") or [])}

    # --- section completeness + evidence coverage ---
    section_report, missing_sections, unevidenced_sections = [], [], []
    total_claims = total_cited = 0
    for name in REQUIRED_SECTIONS:
        s = sections_in.get(name)
        if s is None:
            missing_sections.append(name)
            section_report.append({"section": name, "present": False, "claim_count": 0,
                                    "cited_claims": 0, "evidenced": False})
            continue
        claims = s.get("claims") or []
        claim_count = len(claims)
        cited = sum(1 for c in claims if str(c.get("citation") or "").strip())
        total_claims += claim_count
        total_cited += cited
        evidenced = claim_count >= cfg["min_claims_per_section"] and cited == claim_count and claim_count > 0
        if not evidenced:
            unevidenced_sections.append(name)
        section_report.append({"section": name, "present": True, "claim_count": claim_count,
                               "cited_claims": cited, "evidenced": evidenced})
    evidence_coverage = round(total_cited / total_claims, 4) if total_claims else 0.0

    # --- forecast internal-consistency checks ---
    f = doc.get("forecast") or {}
    years = f.get("years") or []
    revenue = f.get("revenue") or []
    margins = f.get("ebit_margin") or []
    provided_growth = f.get("revenue_growth")
    fc_errors, fc_warnings, recomputed_growth = [], [], []
    if not years or not revenue:
        fc_errors.append("forecast missing years or revenue")
    else:
        if len(years) != len(revenue):
            fc_errors.append(f"years ({len(years)}) and revenue ({len(revenue)}) length mismatch")
        if any(_num(y) is None for y in years) or any(years[i] >= years[i + 1] for i in range(len(years) - 1)):
            fc_errors.append("forecast years must be numeric and strictly ascending")
        for i, r in enumerate(revenue):
            rn = _num(r)
            if rn is None or rn <= 0:
                fc_errors.append(f"revenue[{i}] must be positive numeric, got {r!r}")
        for i in range(len(revenue)):
            if i == 0:
                recomputed_growth.append(None)
            else:
                prev, cur = _num(revenue[i - 1]), _num(revenue[i])
                recomputed_growth.append(round(cur / prev - 1.0, 4) if (prev and cur is not None) else None)
        if isinstance(provided_growth, list):
            for i, g in enumerate(provided_growth):
                gn, rc = _num(g), recomputed_growth[i] if i < len(recomputed_growth) else None
                if gn is not None and rc is not None and abs(gn - rc) > cfg["growth_tolerance"]:
                    fc_errors.append(f"revenue_growth[{i}] {gn} != recomputed {rc}")
        for i, m in enumerate(margins):
            mn = _num(m)
            if mn is None or (cfg["margin_min"] is not None and mn < cfg["margin_min"]) or (cfg["margin_max"] is not None and mn > cfg["margin_max"]):
                fc_errors.append(f"ebit_margin[{i}] out of [{cfg['margin_min']},{cfg['margin_max']}]: {m!r}")
        if not margins:
            fc_warnings.append("no ebit_margin series provided — margin path unevidenced")

    # --- valuation triangulation (DRAFT range only, never an approved price target) ---
    v = doc.get("valuation") or {}
    methods = v.get("methods") or []
    weights = v.get("weights") or {}
    val_errors = []
    per_share, uncited_methods = {}, []
    for m in methods:
        name = m.get("method")
        val = _num(m.get("value_per_share"))
        if val is None:
            val_errors.append(f"valuation method {name!r} has non-numeric value_per_share")
        else:
            per_share[name] = val
        if not str(m.get("citation") or "").strip():
            uncited_methods.append(name)
    weights_sum = round(sum(_num(w) or 0.0 for w in weights.values()), 6) if weights else 0.0
    values = list(per_share.values())
    draft_value_range = {"low": round(min(values), 2), "high": round(max(values), 2)} if values else None
    blended_midpoint = None
    if per_share and weights and abs(weights_sum - 1.0) <= cfg["weights_tolerance"] \
            and set(weights) == set(per_share):
        blended_midpoint = round(sum((_num(weights[k]) or 0.0) * per_share[k] for k in per_share), 2)
    valuation_complete = bool(per_share) and not val_errors and not uncited_methods
    if uncited_methods:
        val_errors.append(f"valuation methods missing citation: {uncited_methods}")

    data_gaps = list(doc.get("data_gaps") or [])
    readiness = expected_readiness(missing_sections, unevidenced_sections, fc_errors,
                                   valuation_complete, data_gaps, evidence_coverage)

    if not doc.get("mnpi_attestation"):
        readiness = "Not ready"
    ticker = str(doc.get("ticker", "NA")).replace(" ", "")
    return {
        "coverage_id": f"cir-{ticker}-{doc.get('as_of', 'NA')}-0001",
        "ticker": doc.get("ticker"),
        "company_name": doc.get("company_name"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency", "USD"),
        "mnpi_attestation": bool(doc.get("mnpi_attestation", False)),
        "sections": [{**row, "claims": (sections_in.get(row["section"]) or {}).get("claims", [])} for row in section_report],
        "forecast_snapshot": f,
        "evidence_scope": "Supplied claims/citations and method values only; no retrieval, substantive validation or producer execution",
        "missing_sections": missing_sections,
        "unevidenced_sections": unevidenced_sections,
        "evidence_coverage": evidence_coverage,
        "forecast_checks": {"errors": fc_errors, "warnings": fc_warnings,
                            "recomputed_growth": recomputed_growth},
        "valuation": {"methods": methods, "weights": weights, "weights_sum": weights_sum,
                      "draft_value_range": draft_value_range, "blended_midpoint": blended_midpoint,
                      "errors": val_errors, "complete": valuation_complete},
        "data_gaps": data_gaps,
        "readiness": readiness,
        "proposed_rating": {"label": (doc.get("proposed_rating") or {}).get("label"),
                            "status": "draft-unapproved"},
        "approvals": doc.get("approvals") or {"supervisory_analyst": False, "research_committee": False},
        "draft_banner": DRAFT_BANNER,
        "disclaimer": DISCLAIMER,
    }


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
        path=Path(__file__).resolve().parents[1]/"evals/files/coverage_dossier_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        doc=_read_json(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False))
        if "--selftest" in argv and "coverage-initiation-researcher"=="market-landscape-researcher": print("calculate self-check: 0 error(s)")
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
