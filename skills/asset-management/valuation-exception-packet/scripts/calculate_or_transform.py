#!/usr/bin/env python3
"""Deterministic valuation-exception engine for valuation-exception-packet.

For each instrument on a fund book as of a valuation date: classify every candidate price as an
OBSERVATION or a HYPOTHESIS via the pricing hierarchy, detect stale / missing / disputed /
outlier exceptions against the versioned tolerance config, score a documented severity band,
and assemble a cited evidence bundle with a durable case_id. It NEVER selects/overrides a
price, certifies/strikes NAV, or closes an exception; disposition is recommendation-only and
every confirmed exception is marked `adjudication: human-required`.

Usage:
  python calculate_or_transform.py prices.json   # prints the packet JSON to stdout
  python calculate_or_transform.py --selftest     # runs over the bundled fixture, prints the
                                                   # packet, then a self-consistency summary line
Exit 0 on success (in --selftest, 0 only if the self-consistency check finds 0 error(s)).
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

OBSERVATION_SOURCES = {"exchange_close", "vendor_evaluated", "executable_quote", "trade_print"}
HYPOTHESIS_SOURCES = {"indicative_quote", "matrix_price", "model_price", "carry_forward"}
HIERARCHY = ["exchange_close", "vendor_evaluated", "executable_quote", "trade_print",
             "indicative_quote", "matrix_price", "model_price", "carry_forward"]
ILLIQUID = {"corporate_bond", "government_bond", "private_placement"}

DEFAULT_TOLERANCES = {
    "equity": {"staleness_max_days": 1, "outlier_move_pct": 10, "dispute_tolerance_pct": 1.0},
    "corporate_bond": {"staleness_max_days": 2, "outlier_move_pct": 5, "dispute_tolerance_pct": 1.0},
    "government_bond": {"staleness_max_days": 1, "outlier_move_pct": 3, "dispute_tolerance_pct": 0.5},
    "private_placement": {"staleness_max_days": 5, "outlier_move_pct": 15, "dispute_tolerance_pct": 3.0},
    "_default": {"staleness_max_days": 2, "outlier_move_pct": 10, "dispute_tolerance_pct": 2.0},
}
TYPE_WEIGHT = {"missing": 4, "disputed": 3, "outlier": 3, "stale": 2}
STANDING_NOTE = ("Valuation exception packet only; no price has been selected or overridden and "
                 "no NAV has been certified or struck. Observed prices and hypotheses are "
                 "evidence for the valuation committee's decision.")


def _price_type(source_type: str) -> str:
    return "observation" if source_type in OBSERVATION_SOURCES else "hypothesis"


def _business_days(d_from: str, d_to: str) -> int:
    a = date.fromisoformat(str(d_from)[:10])
    b = date.fromisoformat(str(d_to)[:10])
    if b <= a:
        return 0
    n, cur = 0, a
    while cur < b:
        cur = date.fromordinal(cur.toordinal() + 1)
        if cur.weekday() < 5:
            n += 1
    return n


def _tolerances(asset_class, overrides):
    base = dict(DEFAULT_TOLERANCES["_default"])
    base.update(DEFAULT_TOLERANCES.get(asset_class, {}))
    base.update((overrides or {}).get(asset_class, {}))
    return base


def _cite_instrument(ins):
    return f"pricing:{ins.get('source_ref','?')}"


def _cite_price(p):
    return f"{p.get('source_id','?')}:{p.get('source_type','?')}@{p.get('as_of','?')}"


def _role(source_type: str) -> str:
    if source_type == "exchange_close":
        return "exchange"
    if source_type == "vendor_evaluated":
        return "vendor"
    if source_type in ("executable_quote", "indicative_quote"):
        return "broker"
    if source_type == "trade_print":
        return "market"
    return "model"


def _tag_prices(candidates):
    tagged = []
    for p in candidates:
        st = p.get("source_type")
        tagged.append({
            "source_id": p.get("source_id"),
            "source_type": st,
            "price": p.get("price"),
            "price_type": _price_type(st),
            "as_of": p.get("as_of"),
            "firm": bool(p.get("firm")) if p.get("firm") is not None else None,
            "size": p.get("size"),
        })
    return tagged


def _severity(types, metrics, ins):
    score, why = 0, []
    base = max((TYPE_WEIGHT[t] for t in types), default=0)
    if base:
        top = max(types, key=lambda t: TYPE_WEIGHT[t])
        score += base
        why.append(f"type {top} +{base}")
    move = abs(metrics.get("day_over_day_move_pct") or 0)
    if move >= 25:
        score += 3; why.append("move>=25% +3")
    elif move >= 10:
        score += 2; why.append("move>=10% +2")
    disp = metrics.get("max_source_dispersion_pct") or 0
    if disp >= 5:
        score += 3; why.append("dispersion>=5% +3")
    elif disp >= 1:
        score += 1; why.append("dispersion>=1% +1")
    mv = abs(ins.get("market_value") or 0)
    if mv >= 1_000_000:
        score += 3; why.append("materiality>=1m +3")
    elif mv >= 100_000:
        score += 1; why.append("materiality>=100k +1")
    if ins.get("asset_class") in ILLIQUID:
        score += 2; why.append("illiquid class +2")
    if ins.get("open_challenge"):
        score += 2; why.append("open challenge +2")
    band = "P1 (Elevated)" if (score >= 7 or ins.get("open_challenge")) \
        else "P2 (Standard)" if score >= 3 else "P3 (Low)"
    return score, band, "; ".join(why)


def _metrics(observations, ins, as_of):
    m = {"staleness_business_days": None, "day_over_day_move_pct": None,
         "max_source_dispersion_pct": None}
    if observations:
        latest = max(o["as_of"] for o in observations)
        m["staleness_business_days"] = _business_days(latest, as_of)
        vals = [o["price"] for o in observations if isinstance(o["price"], (int, float))]
        if len(vals) >= 2 and min(vals) != 0:
            m["max_source_dispersion_pct"] = round((max(vals) - min(vals)) / abs(min(vals)) * 100, 4)
        today = [o["price"] for o in observations
                 if str(o["as_of"])[:10] == str(as_of)[:10] and isinstance(o["price"], (int, float))]
        prior = ins.get("prior_price")
        if today and isinstance(prior, (int, float)) and prior != 0:
            # rank today's observations by hierarchy; use the highest-ranked as reference
            ranked = sorted(
                [o for o in observations if str(o["as_of"])[:10] == str(as_of)[:10]
                 and isinstance(o["price"], (int, float))],
                key=lambda o: HIERARCHY.index(o["source_type"]) if o["source_type"] in HIERARCHY else 99)
            ref = ranked[0]["price"]
            m["day_over_day_move_pct"] = round((ref - prior) / abs(prior) * 100, 4)
    return m


def _detect(observations, hypotheses, metrics, ins, tol):
    types = []
    if not observations:
        types.append("missing")
    else:
        sb = metrics.get("staleness_business_days")
        if sb is not None and sb > tol["staleness_max_days"]:
            types.append("stale")
    disp = metrics.get("max_source_dispersion_pct")
    if ins.get("open_challenge") or (disp is not None and disp > tol["dispute_tolerance_pct"]):
        types.append("disputed")
    move = metrics.get("day_over_day_move_pct")
    if move is not None and abs(move) > tol["outlier_move_pct"]:
        types.append("outlier")
    # stable, de-duplicated order
    order = ["missing", "stale", "disputed", "outlier"]
    return [t for t in order if t in types]


def _recommendation(types):
    if "missing" in types:
        return ("Obtain an observed price from an approved source; if none is available, refer to "
                "the valuation committee for a fair-value determination. Do not adopt a hypothesis "
                "as the price.")
    if "disputed" in types:
        return ("Obtain a challenge quote from the secondary approved vendor and refer the "
                "dispersion to the valuation committee for adjudication.")
    if "outlier" in types:
        return ("Confirm the move against an independent observed source (trade print or second "
                "vendor) and cite any corporate-action context; refer unexplained moves to the "
                "valuation committee.")
    if "stale" in types:
        return ("Refresh the price from the primary vendor; a carry-forward requires valuation "
                "committee approval and must not be applied automatically.")
    return "Refer to the valuation committee."


def investigate(ins, doc, as_of):
    iid = ins.get("instrument_id")
    case_id = f"VEP-{str(as_of).replace('-', '')[:8]}-{iid}"
    rec = {"instrument_id": iid, "case_id": case_id, "asset_class": ins.get("asset_class"),
           "citations": [_cite_instrument(ins)], "needs": []}

    if not ins.get("asset_class"):
        rec["disposition"] = "needs-data"
        rec["needs"].append("asset_class (required to select tolerances)")
        return rec

    candidates = ins.get("candidate_prices")
    if candidates is None:
        rec["disposition"] = "needs-data"
        rec["needs"].append("candidate_prices (no pricing inputs supplied)")
        return rec

    tagged = _tag_prices(candidates)
    observations = [p for p in tagged if p["price_type"] == "observation"]
    hypotheses = [p for p in tagged if p["price_type"] == "hypothesis"]
    tol = _tolerances(ins.get("asset_class"), doc.get("asset_class_tolerances"))
    metrics = _metrics(observations, ins, as_of)
    types = _detect(observations, hypotheses, metrics, ins, tol)

    rec["candidate_prices"] = tagged
    rec["metrics"] = metrics
    for p in tagged:
        rec["citations"].append(_cite_price(p))

    if not types:
        rec["disposition"] = "no-exception-detected"
        rec["note"] = "No exception under the configured tolerances; not a price certification."
        return rec

    score, band, why = _severity(types, metrics, ins)
    chronology = sorted(
        ({"as_of": p["as_of"], "source_id": p["source_id"], "source_type": p["source_type"],
          "price": p["price"], "price_type": p["price_type"]} for p in tagged),
        key=lambda e: str(e["as_of"]))
    parties = []
    seen = set()
    for p in tagged:
        key = (p["source_id"], _role(p["source_type"]))
        if key not in seen:
            seen.add(key)
            parties.append({"role": _role(p["source_type"]), "id": p["source_id"]})
    if ins.get("open_challenge"):
        parties.append({"role": "challenger", "id": ins.get("challenger") or "portfolio-management"})
    hierarchy_ref = [st for st in HIERARCHY if st in {p["source_type"] for p in tagged}]

    rec["exception_type"] = types
    rec["severity_score"] = score
    rec["severity_band"] = band
    rec["severity_reason"] = why
    rec["disposition"] = "exception-confirmed"
    rec["adjudication"] = "human-required"
    rec["evidence_bundle"] = {
        "case_id": case_id,
        "instrument_id": iid,
        "asset_class": ins.get("asset_class"),
        "exception_type": types,
        "chronology": chronology,
        "parties": parties,
        "amounts": {
            "observed_prices": [o["price"] for o in observations],
            "hypotheses": [h["price"] for h in hypotheses],
            "market_value": ins.get("market_value"),
        },
        "metrics": metrics,
        "hierarchy_reference": hierarchy_ref,
        "recommended_next_step": _recommendation(types),
        "citations": list(rec["citations"]),
    }
    return rec


def build_packet(doc: dict) -> dict:
    as_of = doc.get("as_of")
    book = doc.get("book") or "BOOK"
    job_id = f"VEP-JOB-{str(as_of).replace('-', '')[:8]}-{book}"
    records = [investigate(ins, doc, as_of) for ins in doc["instruments"]]
    summary = {
        "total": len(records),
        "exception_confirmed": sum(1 for r in records if r["disposition"] == "exception-confirmed"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "no_exception_detected": sum(1 for r in records if r["disposition"] == "no-exception-detected"),
        "by_type": {t: sum(1 for r in records if t in (r.get("exception_type") or []))
                    for t in ("stale", "missing", "disputed", "outlier")},
    }
    return {"job_id": job_id, "as_of": as_of, "book": book,
            "config_version": doc.get("config_version"), "exceptions": records,
            "summary": summary, "standing_note": STANDING_NOTE}


def _selfcheck(packet: dict) -> list[str]:
    """Internal self-consistency check for --selftest (independent of validate_output)."""
    errs = []
    if not packet.get("job_id"):
        errs.append("packet missing job_id")
    for r in packet.get("exceptions", []):
        if not r.get("case_id"):
            errs.append(f"{r.get('instrument_id')}: missing case_id")
        for p in r.get("candidate_prices", []) or []:
            exp = _price_type(p.get("source_type"))
            if p.get("price_type") != exp:
                errs.append(f"{r.get('instrument_id')}: {p.get('source_id')} mis-tagged "
                            f"{p.get('price_type')} != {exp}")
        if r.get("disposition") == "exception-confirmed":
            b = r.get("evidence_bundle") or {}
            if not b.get("citations"):
                errs.append(f"{r.get('instrument_id')}: exception bundle missing citations")
            if r.get("adjudication") != "human-required":
                errs.append(f"{r.get('instrument_id')}: adjudication not human-required")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "prices_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    packet = build_packet(doc)
    print(json.dumps(packet, indent=2))
    if selftest:
        errs = _selfcheck(packet)
        for e in errs:
            print("ERROR", e)
        print(f"transform selftest: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
