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


def _compute_native(doc: dict) -> dict:
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
    if note.get("rating_applicable") is True and rating not in scale:
        flags.append({"check": "rating_validity", "detail": f"rating '{rating}' not in scale {scale}",
                      "citation": gcite("field=rating")})

    # rating/target directional consistency
    rank = {str(k).lower(): v for k, v in (doc.get("rating_rank") or {}).items()}
    pr, cr = note.get("prior_rating"), note.get("rating")
    pr_l, cr_l = str(pr).lower(), str(cr).lower()
    tp, ptp = _num(note.get("target_price")), _num(note.get("prior_target"))
    if note.get("rating_applicable") is True and note.get("target_applicable") is True and pr_l in rank and cr_l in rank and tp is not None and ptp is not None:
        rchg = rank[cr_l] - rank[pr_l]
        tchg = (tp > ptp) - (tp < ptp)
        if (rchg > 0 and tchg < 0) or (rchg < 0 and tchg > 0):
            flags.append({"check": "rating_target_consistency",
                          "detail": f"rating {pr}->{cr} conflicts with target {ptp}->{tp}",
                          "citation": gcite("field=target_price")})

    # restricted list (hard stop)
    restricted = note.get("ticker") in set(doc["restricted_list"]) if doc.get("restricted_list_checked") is True and note.get("ticker") else None
    if restricted:
        flags.append({"check": "restricted_list", "detail": f"ticker {note.get('ticker')} on restricted list — route to compliance",
                      "citation": "config:restricted_list", "hard_stop": True})

    # checklist completeness
    req_items = set(doc["checklist"].get("required_items") or [])
    pres_items = set(doc["checklist"].get("present_items") or [])
    for item in sorted(req_items - pres_items):
        gaps.append({"check": "checklist_completeness", "detail": f"checklist item '{item}' missing",
                     "citation": f"config:checklist;item={item}"})

    context=doc.get("context") or {}
    for field in ("institution","jurisdiction","audience","research_type","profile_id","profile_version","source_ref"):
        if not context.get(field):
            gaps.append({"check":"applicability","detail":field+" unknown; supplied rules cannot establish applicability", "citation":"input:context."+field})
    if context.get("applicability_status")!="confirmed":
        gaps.append({"check":"applicability","detail":"applicability profile not confirmed in supplied input","citation":"input:context.applicability_status"})
    if context.get("rights_status")!="eligible":
        gaps.append({"check":"rights","detail":"source/distribution rights unknown or restricted; owner review required","citation":"input:context.rights_status"})
    if note.get("rating_applicable") is True and note.get("target_applicable") is True and not doc.get("rating_rank"):
        gaps.append({"check":"rating_target_configuration","detail":"rating direction map absent; directional consistency not evaluated","citation":"input:rating_rank"})
    if restricted is None:
        gaps.append({"check":"restricted_list_coverage","detail":"restricted list not checked; empty supplied list does not establish absence","citation":"input:restricted_list_checked"})
    for field in ("rating_applicable","target_applicable"):
        if note.get(field) is None:
            gaps.append({"check":"applicability","detail":field+" unknown","citation":"input:note."+field})
    if note.get("rating_applicable") is False and rating is not None:
        flags.append({"check":"rating_applicability","detail":"rating supplied despite declared non-applicability; review conflict","citation":"input:note.rating"})
    if not doc["checklist"].get("config_version"):
        gaps.append({"check":"configuration","detail":"configuration version missing","citation":"input:checklist.config_version"})
    clean = not gaps and not flags
    disposition = "ready-for-compliance-review" if clean else "gaps-for-review"
    return {
        "prep_id": f"rppa-{nid or 'UNKNOWN'}-0001",
        "note_id": nid, "ticker": note.get("ticker"),
        "config_version": doc["checklist"].get("config_version"),
        "checks": {"rating": rating, "prior_rating": pr, "target_price": tp, "prior_target": ptp,
                   "restricted": restricted, "rating_status":"not-applicable" if note.get("rating_applicable") is False else ("checked-against-supplied-scale" if note.get("rating_applicable") is True else "unknown")},
        "gaps": gaps, "flags": flags,
        "gap_count": len(gaps), "flag_count": len(flags),
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


from native_integrity import attach_source, canonical_hash

def _validated_input(doc):
    import importlib.util
    p=Path(__file__).with_name("validate_input.py")
    spec=importlib.util.spec_from_file_location("_native_input_"+p.parent.parent.name.replace("-","_"),p)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    errors,_=module.validate(doc)
    if errors: raise ValueError("; ".join(errors))

def compute(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        from phase2_domain import compute as phase2_compute
        return phase2_compute(doc)
    _validated_input(doc)
    result=_compute_native(doc)
    result.update({"issuer_id":doc["note"]["issuer_id"],"context":doc.get("context",{}),
                   "review_scope":"supplied checklist/configuration tokens only; note text, source fidelity, legal applicability and license authenticity are not verified",
                   "authority":"supplied eligibility and review assertions do not authorize publication or distribution",
                   "not_evaluated":["actual note-text disclosures","institutional/legal applicability authentication","source rights authentication","publication approval"]})
    canonical_hash(result)
    return attach_source(result,doc)


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "note_example.json"
        doc = _read_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _read_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _read_json(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
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
