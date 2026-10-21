#!/usr/bin/env python3
"""Deterministic version diff for document-version-comparator.

Compares two structured document versions (same doc_id) and locates added/removed/text-changed
sections and changed data values, each with a location. Never judges significance, approves,
edits, or publishes.

Usage: python calculate_or_transform.py docs.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Change-location evidence only; not a judgment of legal significance, materiality, "
              "or disclosure sufficiency, and not an approval. No version has been edited or published.")


def _norm(t):
    return " ".join(str(t or "").split()).casefold()


def _native_compute(doc: dict) -> dict:
    a, b = doc["doc_a"], doc["doc_b"]
    va, vb = a.get("version"), b.get("version")
    sa = {s["id"]: s for s in a["sections"]}
    sb = {s["id"]: s for s in b["sections"]}
    changes = []
    not_evaluable = []

    def cite(sid):
        return f"{a.get('doc_id')}:{sid}@{va}->{vb}"

    for sid in sb:
        if sid not in sa:
            changes.append({"type": "section_added", "section_id": sid,
                            "heading": sb[sid].get("heading"), "citation": cite(sid)})
    for sid in sa:
        if sid not in sb:
            changes.append({"type": "section_removed", "section_id": sid,
                            "heading": sa[sid].get("heading"), "citation": cite(sid)})
    for sid in sa:
        if sid not in sb:
            continue
        ra, rb = sa[sid], sb[sid]
        if "heading" in ra and "heading" in rb and ra["heading"] != rb["heading"]:
            changes.append({"type": "heading_changed", "section_id": sid, "before": ra["heading"], "after": rb["heading"], "citation": cite(sid)})
        if "text" not in ra or "text" not in rb:
            not_evaluable.append({"section_id": sid, "surface": "text", "why": "text omitted on at least one side"})
        elif ra["text"] != rb["text"]:
            left,right=ra["text"],rb["text"]
            offset=next((i for i,(x,y) in enumerate(zip(left,right)) if x!=y),min(len(left),len(right)))
            start=max(0,offset-40)
            changes.append({"type": "text_changed", "section_id": sid, "character_offset": offset,
                            "heading": rb.get("heading"),
                            "before": str(ra.get("text", ""))[start:start+160],
                            "after": str(rb.get("text", ""))[start:start+160], "citation": cite(sid)})
        if ("values" in ra) != ("values" in rb):
            not_evaluable.append({"section_id": sid, "surface": "values", "why": "value inventory omitted on one side"})
            continue
        va_vals = ra.get("values") or {}
        vb_vals = rb.get("values") or {}
        for field in sorted(set(va_vals) | set(vb_vals)):
            if field not in va_vals or field not in vb_vals or va_vals[field] != vb_vals[field]:
                changes.append({"type": "value_changed", "section_id": sid, "field": field,
                                "before": va_vals.get(field), "after": vb_vals.get(field),
                                "before_present": field in va_vals, "after_present": field in vb_vals,
                                "citation": cite(sid)})

    common_a = [x for x in sa if x in sb]
    common_b = [x for x in sb if x in sa]
    if common_a != common_b:
        changes.append({"type": "section_order_changed", "before": common_a, "after": common_b, "citation": cite("section-order")})
    complete = a.get("extraction_complete") is True and b.get("extraction_complete") is True and not not_evaluable
    from collections import Counter
    disposition = "changes-for-review" if changes else ("clean-for-declared-extracted-scope" if complete else "partial-no-detected-change")
    return {
        "comparison_id": f"fdvc-{a.get('doc_id','NA')}-{va}-{vb}",
        "doc_id": a.get("doc_id"), "version_a": va, "version_b": vb,
        "change_counts": dict(Counter(c["type"] for c in changes)),
        "changes": changes,
        "not_evaluable": not_evaluable,
        "coverage_status": "complete-for-declared-extracted-scope" if complete else "partial",
        "limitations": ["Structured supplied text, headings, section order and explicit value maps only", "No OCR, page/cell extraction, formatting, formula semantics or materiality assessment; completeness declarations unverified"],
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def compute(doc):
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
        path=Path(__file__).resolve().parents[1]/"evals/files/docs_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        doc=json.loads(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False))
        if "--selftest" in argv and "document-version-comparator"=="market-landscape-researcher": print("calculate self-check: 0 error(s)")
        return 0
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print("ERROR invalid input: "+str(exc)); return 1
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
