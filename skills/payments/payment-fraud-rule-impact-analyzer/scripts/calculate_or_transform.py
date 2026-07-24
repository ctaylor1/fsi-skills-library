#!/usr/bin/env python3
"""Deterministic fraud-rule impact estimate for payment-fraud-rule-impact-analyzer.

Evaluates a current and proposed rule over a labeled transaction sample and reports block counts,
decline-rate delta, and the confusion-matrix shift. Illustrative sample estimate only; never
deploys a rule or decisions a live transaction.

Usage: python calculate_or_transform.py sample.json | --selftest
"""
from __future__ import annotations
import json, operator, sys
from pathlib import Path

DISCLAIMER = ("Illustrative sample impact estimate only; not a rule deployment and not a "
              "block/allow decision on any live transaction or customer.")
OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}


def _blocks(rule, t):
    return OPS[rule["op"]](float(t[rule["field"]]), float(rule["threshold"]))


def _confusion(rule, txns):
    c = {"caught_fraud": 0, "missed_fraud": 0, "false_positives": 0, "true_allows": 0}
    for t in txns:
        label = t.get("label")
        if label not in ("fraud", "legit"):
            continue
        blocked = _blocks(rule, t)
        if label == "fraud":
            c["caught_fraud" if blocked else "missed_fraud"] += 1
        else:
            c["false_positives" if blocked else "true_allows"] += 1
    return c


def compute(doc: dict) -> dict:
    rc = doc["rule_change"]
    cur, prop = rc["current_rule"], rc["proposed_rule"]
    txns = doc["sample"]["transactions"]
    n = len(txns)
    labeled = [t for t in txns if t.get("label") in ("fraud", "legit")]

    blk_now = [t for t in txns if _blocks(cur, t)]
    blk_prop = [t for t in txns if _blocks(prop, t)]
    now_ids = {t["txn_id"] for t in blk_now}
    prop_ids = {t["txn_id"] for t in blk_prop}
    newly_blocked = sorted(prop_ids - now_ids)
    newly_allowed = sorted(now_ids - prop_ids)

    cm_now = _confusion(cur, txns)
    cm_prop = _confusion(prop, txns)
    delta = {k: cm_prop[k] - cm_now[k] for k in cm_now}

    dr_now = round(len(blk_now) / n, 4) if n else 0.0
    dr_prop = round(len(blk_prop) / n, 4) if n else 0.0
    return {
        "analysis_id": f"pfria-{rc.get('rule_id', 'UNKNOWN')}-0001",
        "rule_id": rc.get("rule_id"),
        "current_version": rc.get("current_version"), "proposed_version": rc.get("proposed_version"),
        "sample_size": n, "labeled_size": len(labeled), "unlabeled": n - len(labeled),
        "blocked_now": len(blk_now), "blocked_proposed": len(blk_prop),
        "newly_blocked": newly_blocked, "newly_allowed": newly_allowed,
        "decline_rate_now": dr_now, "decline_rate_proposed": dr_prop,
        "decline_rate_delta": round(dr_prop - dr_now, 4),
        "confusion_now": cm_now, "confusion_proposed": cm_prop, "confusion_delta": delta,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sample_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
