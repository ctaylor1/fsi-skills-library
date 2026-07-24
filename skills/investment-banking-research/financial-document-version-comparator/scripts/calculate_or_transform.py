#!/usr/bin/env python3
"""Deterministic version diff for financial-document-version-comparator.

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


def compute(doc: dict) -> dict:
    a, b = doc["doc_a"], doc["doc_b"]
    va, vb = a.get("version"), b.get("version")
    sa = {s["id"]: s for s in a["sections"]}
    sb = {s["id"]: s for s in b["sections"]}
    changes = []

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
        if _norm(ra.get("text")) != _norm(rb.get("text")):
            changes.append({"type": "text_changed", "section_id": sid,
                            "heading": rb.get("heading"),
                            "before": str(ra.get("text", ""))[:160],
                            "after": str(rb.get("text", ""))[:160], "citation": cite(sid)})
        va_vals = ra.get("values") or {}
        vb_vals = rb.get("values") or {}
        for field in sorted(set(va_vals) | set(vb_vals)):
            if va_vals.get(field) != vb_vals.get(field):
                changes.append({"type": "value_changed", "section_id": sid, "field": field,
                                "before": va_vals.get(field), "after": vb_vals.get(field),
                                "citation": cite(sid)})

    from collections import Counter
    disposition = "clean" if not changes else "changes-for-review"
    return {
        "comparison_id": f"fdvc-{a.get('doc_id','NA')}-{va}-{vb}",
        "doc_id": a.get("doc_id"), "version_a": va, "version_b": vb,
        "change_counts": dict(Counter(c["type"] for c in changes)),
        "changes": changes,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "docs_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
