#!/usr/bin/env python3
"""Deterministic actuarial data reconciliation for actuarial-data-lineage-checker.

Detects duplicates, missing periods, definition/version shifts, unexplained period-over-period
movement, and new series across current vs prior datasets; preserves lineage per break. Never
corrects data, selects assumptions, runs a model, or certifies reserves.

Usage: python calculate_or_transform.py data.json | --selftest
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

DEFAULT_CFG = {"movement_pct": 20.0, "definition_baseline_version": None}
DISCLAIMER = ("Data-lineage and break evidence only; no source data has been altered, no "
              "actuarial assumption selected, and no reserve data certified.")


def _num(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CFG, **(doc.get("config") or {})}
    cur = doc["current"]
    prior = {(_r["key"], _r["metric"], _r["period"]): _r for _r in (doc.get("prior") or [])}
    expected = doc.get("expected_periods") or []
    baseline = cfg.get("definition_baseline_version")
    mv = _num(cfg.get("movement_pct"), 20.0) / 100.0
    breaks = []

    def brk(t, r, detail):
        breaks.append({"type": t, "key": r.get("key"), "metric": r.get("metric"),
                       "period": r.get("period"), "detail": detail,
                       "citation": f"actl:{r.get('source_ref','?')}@{r.get('definition_version','')}"})

    # duplicates
    keys = Counter((r["key"], r["metric"], r["period"]) for r in cur)
    dup_seen = set()
    for r in cur:
        k = (r["key"], r["metric"], r["period"])
        if keys[k] > 1 and k not in dup_seen:
            dup_seen.add(k)
            brk("duplicate", r, f"{keys[k]} records for the same key/metric/period")

    # missing periods (per key/metric)
    if expected:
        present = {(r["key"], r["metric"], r["period"]) for r in cur}
        for (key, metric) in {(r["key"], r["metric"]) for r in cur}:
            for per in expected:
                if (key, metric, per) not in present:
                    brk("missing_period", {"key": key, "metric": metric, "period": per,
                                           "source_ref": "expected"}, f"expected period {per} absent")

    for r in cur:
        # definition shift
        dv = r.get("definition_version")
        if dv and baseline and dv != baseline:
            brk("definition_shift", r, f"definition_version {dv} != baseline {baseline}")
        # movement vs prior
        pr = prior.get((r["key"], r["metric"], r["period"]))
        cv = _num(r.get("value"))
        if pr is None:
            brk("new_series", r, "no prior value for this key/metric/period")
        else:
            pv = _num(pr.get("value"))
            if pv is not None and pv != 0 and cv is not None:
                pct = abs(cv - pv) / abs(pv)
                if pct > mv and not (r.get("documented_reason") or "").strip():
                    brk("unexplained_movement", r,
                        f"moved {pct*100:.1f}% ({pv} -> {cv}) > {mv*100:.0f}% with no documented reason")

    disposition = "clean" if not breaks else "breaks-for-review"
    return {
        "lineage_id": f"adl-{doc.get('as_of','NA')}-0001",
        "as_of": doc.get("as_of"), "config_version": doc.get("config_version"),
        "records_checked": len(cur),
        "break_counts": dict(Counter(b["type"] for b in breaks)),
        "breaks": breaks,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "data_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
