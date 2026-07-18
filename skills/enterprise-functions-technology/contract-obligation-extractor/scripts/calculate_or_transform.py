#!/usr/bin/env python3
"""Deterministic obligation-register assembler for contract-obligation-extractor.

Takes the structured contract intake (source clauses + candidate extractions + a required
taxonomy) and assembles a DRAFT, clause-cited obligation register. For each extraction it
resolves the source clause, assigns a status (extracted | ambiguous | conflict | unsourced),
and routes it to the right register section. Taxonomy categories with no extraction become
coverage gaps (flagged for confirmation, never asserted as silence). It never provides legal
advice or interpretation, never asserts an obligation without a clause citation, never claims
the register is complete/exhaustive, and never sends, submits, executes, or delivers.

Output is a DRAFT manifest (`assembly_status: draft-extracted`) for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the register manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Canonical category -> register section mapping (versioned contract; mirrors the template).
CATEGORY_SECTION = {
    "obligation": "obligations",
    "key-date": "key_dates",
    "service-level": "service_levels",
    "right": "rights_restrictions",
    "restriction": "rights_restrictions",
    "renewal": "renewal_termination",
    "termination": "renewal_termination",
    "data-term": "data_terms",
    "dependency": "dependencies",
}
# Categories where a single responsible party must be resolvable; otherwise -> ambiguous.
PARTY_REQUIRED = {"obligation", "service-level", "restriction", "right"}

STANDING_NOTE = ("Draft obligation register for human review only. This register is an "
                 "extraction aid, not legal advice or a completeness certification, and it "
                 "has not been delivered, executed, or acted on. Every obligation must be "
                 "verified against the source contract.")


def _mask_id(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}…{s[-2:]}"


def _resolve_citation(e, clause_index):
    """Return the citation for an extraction, or None if it cannot be sourced."""
    if e.get("citation"):
        return e["citation"]
    clause = clause_index.get(e.get("clause_ref"))
    if clause and clause.get("source_ref"):
        return clause["source_ref"]
    return None


def _conflict_categories(extractions):
    """Categories carrying two or more distinct terms.notice_days -> a reconciliation conflict."""
    by_cat: dict = {}
    for e in extractions:
        nd = (e.get("terms") or {}).get("notice_days")
        if nd is not None:
            by_cat.setdefault(e.get("category"), set()).add(nd)
    return {cat for cat, vals in by_cat.items() if len(vals) > 1}


def _status(e, cited, conflict_cats):
    """Deterministic precedence: unsourced > conflict > ambiguous > extracted."""
    if not cited:
        return "unsourced"
    cat = e.get("category")
    if cat in conflict_cats and (e.get("terms") or {}).get("notice_days") is not None:
        return "conflict"
    if cat in PARTY_REQUIRED and not e.get("responsible_party"):
        return "ambiguous"
    return "extracted"


def assemble(doc: dict) -> dict:
    contract = doc.get("contract") or {}
    taxonomy = list(doc.get("taxonomy") or [])
    clauses = doc.get("clauses") or []
    extractions = doc.get("extractions") or []
    clause_index = {c.get("clause_id"): c for c in clauses}
    conflict_cats = _conflict_categories(extractions)

    sections: dict = {
        "register_summary": {},
        "contract_profile": {
            "contract_id": contract.get("contract_id"),
            "title": contract.get("title"),
            "counterparty": contract.get("counterparty"),
            "contract_type": contract.get("contract_type"),
            "effective_date": contract.get("effective_date"),
            "term_end": contract.get("term_end"),
            "governing_law": contract.get("governing_law"),
            "citation": contract.get("source_ref"),
        },
        "obligations": [],
        "key_dates": [],
        "service_levels": [],
        "rights_restrictions": [],
        "renewal_termination": [],
        "data_terms": [],
        "dependencies": [],
        "reviews": {"recorded": [], "outstanding": []},
        "open_items": [],
        "source_index": [],
    }

    open_items: list = []
    citations: list = []
    covered = set()

    for e in extractions:
        cat = e.get("category")
        covered.add(cat)
        section = CATEGORY_SECTION.get(cat)
        cite = _resolve_citation(e, clause_index)
        status = _status(e, cite, conflict_cats)
        eid = e.get("extraction_id")

        if status == "unsourced":
            # Never asserted in a section; a citation-less claim becomes an open item.
            open_items.append({"item": f"{eid} ({cat})", "type": "needs-source",
                               "action": "locate and cite the governing clause, or remove the extraction",
                               "summary": e.get("summary")})
            continue

        entry = {"extraction_id": eid, "category": cat, "summary": e.get("summary"),
                 "responsible_party": e.get("responsible_party"), "due": e.get("due"),
                 "terms": e.get("terms") or {}, "clause_ref": e.get("clause_ref"),
                 "citation": cite, "status": status}
        if status == "ambiguous":
            entry["reason"] = "responsible party could not be resolved from the clause"
            open_items.append({"item": f"{eid} ({cat})", "type": "ambiguous-obligation",
                               "citation": cite, "action": "assign the responsible party with a human"})
        elif status == "conflict":
            entry["reason"] = "conflicting terms across clauses in this category"
            open_items.append({"item": f"{eid} ({cat})", "type": "term-conflict",
                               "citation": cite, "action": "reconcile the conflicting terms with a human"})

        if section:
            sections[section].append(entry)
        citations.append(cite)

    # coverage gaps: a required category with no extraction is flagged, never asserted silent.
    for cat in taxonomy:
        if cat not in covered:
            section = CATEGORY_SECTION.get(cat)
            gap = {"category": cat, "status": "coverage-gap",
                   "reason": "no extraction mapped to this required category"}
            if section:
                sections[section].append(gap)
            open_items.append({"item": cat, "type": "coverage-gap",
                               "action": f"confirm whether the contract addresses {cat} terms; do not assume silence"})

    # reviews: capture recorded, then mark required-but-missing as outstanding open items.
    recorded_types = set()
    for r in doc.get("reviews") or []:
        if r.get("status") == "recorded":
            rec = {"type": r.get("type"), "reviewer_role": r.get("reviewer_role"),
                   "reviewer": _mask_id(r.get("reviewer")), "date": r.get("date"),
                   "citation": r.get("source_ref") or "?"}
            sections["reviews"]["recorded"].append(rec)
            recorded_types.add(r.get("type"))
            if rec["citation"] != "?":
                citations.append(rec["citation"])
        else:
            sections["reviews"]["outstanding"].append({"type": r.get("type"),
                                                        "status": r.get("status") or "outstanding"})
    for req_rv in doc.get("required_reviews") or []:
        if req_rv not in recorded_types:
            if not any(o.get("type") == req_rv for o in sections["reviews"]["outstanding"]):
                sections["reviews"]["outstanding"].append({"type": req_rv, "status": "outstanding"})
            open_items.append({"item": req_rv, "type": "outstanding-review",
                               "action": "obtain the required human review before delivery"})

    # dedup source index, preserving order
    seen = set()
    for cit in citations:
        if cit and cit != "?" and cit not in seen:
            seen.add(cit)
            sections["source_index"].append(cit)

    sections["open_items"] = open_items

    def _count(status):
        n = 0
        for key, val in sections.items():
            if key in ("register_summary", "contract_profile", "reviews", "open_items", "source_index"):
                continue
            for e in val:
                if isinstance(e, dict) and e.get("status") == status:
                    n += 1
        return n

    sections["register_summary"] = {
        "register_id": doc.get("register_id"),
        "contract_id": contract.get("contract_id"),
        "counterparty": contract.get("counterparty"),
        "as_of_date": doc.get("as_of_date"),
        "taxonomy": taxonomy,
        "counts": {
            "extracted": _count("extracted"),
            "ambiguous": _count("ambiguous"),
            "conflict": _count("conflict"),
            "coverage_gap": _count("coverage-gap"),
            "unsourced": sum(1 for o in open_items if o.get("type") == "needs-source"),
            "open_items_total": len(open_items),
            "reviews_recorded": len(sections["reviews"]["recorded"]),
            "reviews_outstanding": len(sections["reviews"]["outstanding"]),
        },
    }

    return {
        "config_version": doc.get("config_version"),
        "register_id": doc.get("register_id"),
        "contract_id": contract.get("contract_id"),
        "as_of_date": doc.get("as_of_date"),
        "template_version": doc.get("template_version", "obligation-register-template@0.1.0"),
        "assembly_status": "draft-extracted",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "register_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
