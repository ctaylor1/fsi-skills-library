#!/usr/bin/env python3
"""Deterministic company-profile assembler for company-profile-builder.

Maps each fact to its profile section and assigns an assembly status:
  included -> asserted in the section; stale/unresolved/future -> withheld
  unsupported (no citation)       -> open item only, NEVER asserted
  restricted-mnpi (MNPI + external distribution) -> open item only, EXCLUDED from the profile

It also captures recorded approvals plus outstanding required approvals, flags required
sections with no asserted fact as `section-incomplete`, and builds a deduplicated source
index. It never issues investment advice, a rating, a recommendation, or a price-target
opinion, never fabricates a missing fact, and never distributes/sends/submits the profile.
The output is a DRAFT manifest (`assembly_status: draft-assembled`) for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the profile manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

CONTENT_SECTIONS = ["business_overview", "key_financials", "ownership", "management",
                    "trading_data", "transactions"]
ASSERTED = {"included"}

STANDING_NOTE = ("Draft company profile for human review only. This profile is not investment "
                 "advice or a recommendation, every stated fact is source-cited, and the profile "
                 "has not been distributed or delivered.")


def _mask_id(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}…{s[-2:]}"


def _cite(f):
    return f.get("source_ref") or None


def _is_stale(f, as_of):
    exp = f.get("expires")
    return bool(exp and as_of and str(exp) < str(as_of))


def _identity_mismatch(f, company):
    fid = f.get("company_id")
    if fid and company.get("company_id") and fid != company.get("company_id"):
        return f"fact company_id {fid!r} != profile company_id {company.get('company_id')!r}"
    return None


def _status(f, company, as_of, external):
    if f.get("value") is None or (isinstance(f.get("value"),str) and not f["value"].strip()): return "unresolved", "fact value missing"
    if not _cite(f): return "unsupported", "no source_ref"
    if f.get("mnpi") and external: return "restricted-mnpi", "restricted fact withheld"
    if not f.get("company_id") or _identity_mismatch(f, company): return "unresolved", "issuer identity missing or mismatched"
    if not f.get("effective_date"): return "unresolved", "effective date missing"
    if f["effective_date"] > as_of or (f.get("available_at") and f["available_at"] > as_of): return "future", "fact unavailable at cutoff"
    if _is_stale(f, as_of): return "stale", "fact expired before cutoff"
    return "included", None


def _entry(f, status, reason):
    entry = {"section": f.get("section"), "fact_id": f.get("fact_id"),
             "label": f.get("label"), "value": f.get("value"),
             "effective_date": f.get("effective_date"), "expires": f.get("expires"),
             "mnpi": bool(f.get("mnpi")), "status": status, "citation": _cite(f)}
    if reason:
        entry["reason"] = reason
    return entry


def _native_assemble(doc: dict) -> dict:
    company = doc.get("company") or {}
    as_of = doc.get("as_of_date")
    external = doc.get("intended_distribution") == "external"
    required = list(doc.get("required_sections") or [])
    facts = doc.get("facts") or []

    sections: dict = {
        "profile_summary": {},
        "business_overview": [], "key_financials": [], "ownership": [],
        "management": [], "trading_data": [], "transactions": [],
        "approvals": {"recorded": [], "outstanding": []},
        "open_items": [],
        "sources": [],
    }
    open_items: list = []
    citations: list = []

    for f in facts:
        sec = f.get("section")
        status, reason = _status(f, company, as_of, external)
        entry = _entry(f, status, reason)
        label = f.get("label") or f.get("fact_id")

        if status == "unsupported":
            open_items.append({"item": f"{sec}: {label}", "type": "unsupported-claim",
                               "action": "attach an approved source or remove the claim"})
            continue
        if status == "restricted-mnpi":
            open_items.append({"item": "Restricted fact omitted", "type": "mnpi-exclusion",
                               "action": "exclude from the external profile or obtain wall-crossing / compliance clearance"})
            continue
        if status != "included":
            open_items.append({"item": f"{sec}: {label}", "fact_id": f.get("fact_id"),
                               "type": {"stale": "stale-data", "future": "future-data"}.get(status, "identity-unresolved"),
                               "status": status, "reason": reason, "citation": entry["citation"],
                               "action": "resolve evidence before factual assertion"})
            continue

        # Eligible supplied facts only; unresolved/stale/future facts were withheld above
        if sec in CONTENT_SECTIONS:
            sections[sec].append(entry)
        citations.append(entry["citation"])
        if status == "stale":
            open_items.append({"item": f"{sec}: {label}", "type": "stale-data",
                               "citation": entry["citation"],
                               "action": "refresh with current data as of the profile date"})
        elif status == "unresolved":
            open_items.append({"item": f"{sec}: {label}", "type": "identity-unresolved",
                               "citation": entry["citation"],
                               "action": "reconcile company identity with a human"})

    # required content sections with no asserted fact -> section-incomplete (never padded)
    for sec in required:
        if sec in CONTENT_SECTIONS and not sections.get(sec):
            open_items.append({"item": sec, "type": "section-incomplete",
                               "action": "add at least one source-cited fact for this required section"})

    # approvals: capture recorded, then mark required-but-missing as outstanding
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask_id(a.get("approver")), "date": a.get("date"),
                   "citation": a.get("source_ref")}
            sections["approvals"]["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            if rec["citation"]:
                citations.append(rec["citation"])
        else:
            sections["approvals"]["outstanding"].append({"type": a.get("type"),
                                                          "status": a.get("status") or "outstanding"})
    for req_ap in doc.get("required_approvals") or []:
        if req_ap not in recorded_types:
            if not any(o.get("type") == req_ap for o in sections["approvals"]["outstanding"]):
                sections["approvals"]["outstanding"].append({"type": req_ap, "status": "outstanding"})
            open_items.append({"item": req_ap, "type": "outstanding-approval",
                               "action": "obtain the required approval before external distribution"})

    # dedup source index, preserving order
    seen = set()
    for cit in citations:
        if cit and cit not in seen:
            seen.add(cit)
            sections["sources"].append(cit)

    sections["open_items"] = open_items

    def _count(status):
        return sum(1 for sec in CONTENT_SECTIONS for e in sections[sec] if e.get("status") == status)

    def _open_count(t):
        return sum(1 for o in open_items if o.get("type") == t)

    sections["profile_summary"] = {
        "profile_id": doc.get("profile_id"),
        "company_legal_name": company.get("legal_name"),
        "ticker": company.get("ticker"),
        "entity_type": company.get("entity_type"),
        "company_id": _mask_id(company.get("company_id")),
        "as_of_date": as_of,
        "intended_distribution": doc.get("intended_distribution") or "internal",
        "required_sections": required,
        "counts": {
            "included": _count("included"),
            "stale": _open_count("stale-data"),
            "unresolved": _open_count("identity-unresolved"),
            "excluded_mnpi": _open_count("mnpi-exclusion"),
            "unsupported": _open_count("unsupported-claim"),
            "section_incomplete": _open_count("section-incomplete"),
            "open_items_total": len(open_items),
            "approvals_recorded": len(sections["approvals"]["recorded"]),
            "approvals_outstanding": len(sections["approvals"]["outstanding"]),
        },
    }

    return {
        "config_version": doc.get("config_version"),
        "profile_id": doc.get("profile_id"),
        "company_legal_name": company.get("legal_name"),
        "ticker": company.get("ticker"),
        "as_of_date": as_of,
        "intended_distribution": doc.get("intended_distribution") or "internal",
        "template_version": doc.get("template_version", "profile-template@0.1.0"),
        "assembly_status": "draft-assembled",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "coverage_status": "partial" if open_items else "complete-for-supplied-scope",
        "standing_note": STANDING_NOTE,
    }


def assemble(doc):
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
    return attach_source(_native_assemble(doc),doc)

def main(argv):
    try:
        path=Path(__file__).resolve().parents[1]/"evals/files/profile_intake_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        doc=_read_json(path.read_text() if path else sys.stdin.read())
        print(json.dumps(assemble(doc),indent=2,allow_nan=False))
        if "--selftest" in argv and "company-profile-builder"=="market-landscape-researcher": print("calculate self-check: 0 error(s)")
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
