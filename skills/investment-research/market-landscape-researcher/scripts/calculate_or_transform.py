#!/usr/bin/env python3
"""Deterministic landscape transform for market-landscape-researcher.

Reads a landscape brief (see validate_input.py), resolves every finding's citation from the
source list, and computes three reproducible scorecards:

  * concentration   — CR4/CR8 and the Herfindahl-Hirschman Index (HHI) over the NAMED firms,
                      plus a factual market-structure band (unconcentrated / moderately /
                      highly concentrated) using the standard 1500 / 2500 HHI thresholds.
  * evidence_coverage — findings cited vs. total, sources by tier, stale-source list.
  * dimension_completeness — which of the eight required dimensions carry a cited finding.

IMPORTANT: This is a research-synthesis transform. Concentration bands and coverage stats
are FACTUAL descriptors of market structure and evidence quality. They are NOT investment
advice, a rating, a price target, or a recommendation. The band thresholds are documented in
references/domain-rules.md and are not tuned to any deal or client.

Usage:
  python calculate_or_transform.py brief.json     # prints the landscape map JSON
  python calculate_or_transform.py --selftest      # runs on the bundled fixture + self-check
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

REQUIRED_DIMENSIONS = (
    "value_chain", "competitors", "customers", "regulation",
    "technology", "economics", "transactions", "strategic_implications",
)
DEFAULT_CONFIG = {"staleness_days": 365, "hhi_moderate": 1500.0, "hhi_high": 2500.0}
DISCLAIMER = ("Market research for informational purposes only; not investment advice, a "
              "recommendation, or an offer to buy or sell any security.")


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")[:40]


def _band(hhi: float, cfg: dict) -> str:
    if hhi >= cfg["hhi_high"]:
        return "highly concentrated"
    if hhi >= cfg["hhi_moderate"]:
        return "moderately concentrated"
    return "unconcentrated"


def _native_compute(doc):
    cfg={**DEFAULT_CONFIG, **doc.get("config",{})}; as_of=_parse_date(doc["as_of"])
    sources={s["source_id"]:s for s in doc["sources"]}
    eligible={sid for sid,s in sources.items() if 0 <= (as_of-_parse_date(s["date"])).days <= cfg["staleness_days"] and s["tier"]<4}
    requested=doc.get("required_dimensions",list(doc["dimensions"]))
    dims={}; withheld=[]; total=cited=0
    for key,findings in doc["dimensions"].items():
        dims[key]=[]
        for f in findings:
            total+=1; ids=[f.get("source_id")]+f.get("corroborating_source_ids",[])
            valid=[sid for sid in ids if sid in eligible]
            if not valid:
                withheld.append({"dimension":key,"source_ids":[x for x in ids if x],"reason":"no eligible nonfuture, current tier1-3 source"}); continue
            cited+=1
            dims[key].append({**f,"citation":"; ".join(sources[x].get("url_ref") or (sources[x].get("publisher","source")+":"+x+"@"+sources[x]["date"]) for x in valid)})
    comps=doc.get("competitors",[])
    usable=bool(comps) and all(c.get("revenue_share_pct") is not None and c.get("source_id") in eligible for c in comps)
    con=None
    if usable:
        ranked=sorted(comps,key=lambda x:float(x["revenue_share_pct"]),reverse=True); shares=[float(c["revenue_share_pct"]) for c in ranked]; hhi=round(sum(x*x for x in shares),2)
        con={"firm_count_named":len(shares),"named_share_sum_pct":round(sum(shares),2),"unattributed_tail_pct":round(max(0,100-sum(shares)),2),"cr4":round(sum(shares[:4]),2),"cr8":round(sum(shares[:8]),2),"hhi":hhi,"hhi_band":_band(hhi,cfg),"ranked_named_firms":ranked}
    share_gaps=any(c.get("revenue_share_pct") is not None and c.get("source_id") not in eligible for c in comps)
    safe_comps=[dict(c) if c.get("source_id") in eligible else {"name":c["name"],"source_id":c.get("source_id"),"revenue_share_pct":None,"share_status":"not-evaluable"} for c in comps]
    gaps=[k for k in requested if not dims.get(k)]
    stale=[sid for sid,s in sources.items() if (as_of-_parse_date(s["date"])).days>cfg["staleness_days"]]
    return {"landscape_id":f"mlr-{_slug(doc['theme'])}-{doc['as_of']}-0001","theme":doc["theme"],"geography":doc.get("geography"),"as_of":doc["as_of"],"config_version":doc["config_version"],
      "sources":list(sources.values()),"competitors":safe_comps,"concentration":con,
      "concentration_status":"computed-for-named-set" if usable else "not-evaluable",
      "evidence_coverage":{"total_findings":total,"cited_findings":cited,"cited_pct":round(100*cited/total,1) if total else 0,"sources_by_tier":{str(t):sum(s["tier"]==t for s in sources.values()) for t in range(1,5)},"stale_sources":stale},
      "dimension_completeness":{"required":requested,"addressed":[k for k in requested if dims.get(k)],"gaps":gaps},"dimensions":dims,"withheld_findings":withheld,
      "coverage_status":"partial" if gaps or withheld or share_gaps else "complete-for-requested-supplied-scope",
      "limitations":["Source and permission declarations are unverified; no retrieval or legal/competition opinion", "Concentration covers only cited named shares; missing shares are not invented"],"disclaimer":DISCLAIMER}


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
        path=Path(__file__).resolve().parents[1]/"evals/files/landscape_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        doc=_read_json(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False))
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
