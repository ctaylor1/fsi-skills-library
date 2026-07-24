#!/usr/bin/env python3
"""Deterministic pre-publication checks for research-publication-preparation-assistant.

Checks disclosure completeness, rating-scale validity, rating/target directional consistency,
restricted-list status, and checklist completeness, and surfaces gaps/flags with citations.
Checks and flags only; never publishes, approves, or determines the rating/target.

Usage: python calculate_or_transform.py note.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Pre-publication preparation only; not a publication, a distribution, a publication "
              "approval, or a rating/target determination. Nothing has been published.")
DEFAULT_RANK = {"sell": 0, "hold": 1, "buy": 2}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    note = doc["note"]
    nid = note.get("note_id")
    gaps, flags = [], []

    def gcite(field):
        return f"note:note={nid};{field}"

    # disclosure completeness
    required = set(doc["disclosures"].get("required") or [])
    present = set(doc["disclosures"].get("present") or [])
    for d in sorted(required - present):
        gaps.append({"check": "disclosure_completeness", "detail": f"required disclosure '{d}' missing",
                     "citation": f"config:disclosures;item={d}"})

    # rating validity
    scale = doc["rating_scale"]
    rating = note.get("rating")
    if rating not in scale:
        flags.append({"check": "rating_validity", "detail": f"rating '{rating}' not in scale {scale}",
                      "citation": gcite("field=rating")})

    # rating/target directional consistency
    rank = {str(k).lower(): v for k, v in (doc.get("rating_rank") or DEFAULT_RANK).items()}
    pr, cr = note.get("prior_rating"), note.get("rating")
    pr_l, cr_l = str(pr).lower(), str(cr).lower()
    tp, ptp = _num(note.get("target_price")), _num(note.get("prior_target"))
    if pr_l in rank and cr_l in rank and tp is not None and ptp is not None:
        rchg = rank[cr_l] - rank[pr_l]
        tchg = (tp > ptp) - (tp < ptp)
        if (rchg > 0 and tchg < 0) or (rchg < 0 and tchg > 0):
            flags.append({"check": "rating_target_consistency",
                          "detail": f"rating {pr}->{cr} conflicts with target {ptp}->{tp}",
                          "citation": gcite("field=target_price")})

    # restricted list (hard stop)
    restricted = note.get("ticker") in set(doc["restricted_list"])
    if restricted:
        flags.append({"check": "restricted_list", "detail": f"ticker {note.get('ticker')} on restricted list — route to compliance",
                      "citation": "config:restricted_list", "hard_stop": True})

    # checklist completeness
    req_items = set(doc["checklist"].get("required_items") or [])
    pres_items = set(doc["checklist"].get("present_items") or [])
    for item in sorted(req_items - pres_items):
        gaps.append({"check": "checklist_completeness", "detail": f"checklist item '{item}' missing",
                     "citation": f"config:checklist;item={item}"})

    clean = not gaps and not flags
    disposition = "ready-for-compliance-review" if clean else "gaps-for-review"
    return {
        "prep_id": f"rppa-{nid or 'UNKNOWN'}-0001",
        "note_id": nid, "ticker": note.get("ticker"),
        "config_version": doc["checklist"].get("config_version"),
        "checks": {"rating": rating, "prior_rating": pr, "target_price": tp, "prior_target": ptp,
                   "restricted": restricted},
        "gaps": gaps, "flags": flags,
        "gap_count": len(gaps), "flag_count": len(flags),
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "note_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
