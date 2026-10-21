#!/usr/bin/env python3
"""Deterministic term normalization for credit-document-terms-reviewer.

Reads a document-intelligence extraction request (see validate_input.py), normalizes each
candidate term into a canonical schema, carries a page-level citation onto every field, and
flags ambiguous or conflicting candidates as `needs_review` instead of resolving them.

IMPORTANT — hard boundary. This maps and cites terms only. It NEVER interprets ambiguous
language, NEVER classifies a covenant as met/breached, NEVER computes a covenant test, and
NEVER makes an investment recommendation. Ambiguity is surfaced, not resolved. Ongoing
issuer monitoring is out of scope (route to issuer-credit-surveillance-reviewer).

Usage:
  python calculate_or_transform.py request.json | --selftest
Non-selftest prints the canonical extraction JSON to stdout.
--selftest checks its own output invariants over the bundled fixture and prints a line
ending "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, re, sys, hashlib
from datetime import date
from pathlib import Path

DISCLAIMER = ("Extracted terms and citations only; no compliance determination, covenant "
              "test, or investment advice has been made.")

# Source language that signals inherent ambiguity — these route to needs_review; the skill
# must not resolve them to a definitive canonical value.
AMBIGUITY_MARKERS = ("subject to", "as defined", "to be determined", "tbd", "to be agreed",
                     "[•]", "[●]", "intentionally omitted", "unless otherwise",
                     "as the context requires", "at the issuer's discretion")

SENIORITY_RANK = [
    ("junior subordinated", "junior_subordinated", 5),
    ("senior subordinated", "senior_subordinated", 3),
    ("subordinated", "subordinated", 4),
    ("senior secured", "senior_secured", 1),
    ("senior unsecured", "senior_unsecured", 2),
    ("senior", "senior_unsecured", 2),
]

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}

SINGLETON_FIELDS = {"maturity", "coupon", "seniority", "collateral"}


def _iso_date(s: str):
    s = str(s).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m and m.group(2).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def _find_first_date(s: str):
    m = re.search(r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})", s)
    if m:
        return _iso_date(m.group(1))
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    return _iso_date(m.group(1)) if m else None


def _usd_amount(s: str):
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million|bn|mm|m)?\b", s, re.I)
    if not m:
        return None
    val = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if unit in ("billion", "bn"):
        val *= 1_000_000_000
    elif unit in ("million", "mm", "m"):
        val *= 1_000_000
    return val


def _markers(raw: str):
    low = raw.lower()
    return [mk for mk in AMBIGUITY_MARKERS if mk in low]


def _normalize(field: str, raw: str):
    """Return (value, status, reason). status in extracted | needs_review."""
    if field=="coupon" and re.search(r"-\s*\d+(?:\.\d+)?\s*%",raw):
        return None,"needs_review","signed coupon expression requires reviewed interpretation"
    markers = _markers(raw)
    if markers:
        shown = ", ".join(repr(m) for m in markers)
        return None, "needs_review", f"ambiguity markers present ({shown}); requires human reading"
    low = raw.lower()
    if field=="seniority" and re.search(r"\b(no|not|without|except|excluding)\b",low):
        return None,"needs_review","negated or qualified seniority requires linked-document review"
    if field == "collateral" and re.search(r"\b(no|not|without|unsecured|except|excluding|release|released)\b", low):
        return None, "needs_review", "negative, qualified or release collateral language requires document review"
    if field == "basket" and re.search(r"\b(greater|lesser|ebitda|grower|ratio|net income)\b", low):
        return None, "needs_review", "formula or grower basket requires linked definitions and human normalization"

    if field == "maturity":
        iso = _iso_date(raw)
        if not iso:
            return None, "needs_review", "maturity date format not recognized"
        return {"maturity_date": iso}, "extracted", "date normalized to ISO-8601"

    if field == "coupon":
        rate = re.search(r"(\d+(?:\.\d+)?)\s*%", raw)
        floating = bool(re.search(r"\b(sofr|libor|euribor|base rate|floating|prime)\b", low)
                        or re.search(r"\+\s*\d+\s*(bps|basis points)", low))
        freq = None
        for key, norm in (("semi-annual", "semi_annual"), ("quarterly", "quarterly"),
                          ("annually", "annual"), ("monthly", "monthly")):
            if key in low:
                freq = norm
                break
        val = {"type": "floating" if floating else "fixed", "frequency": freq}
        if floating:
            idx = re.search(r"\b(sofr|libor|euribor|prime|base rate)\b", low)
            spread = re.search(r"\+\s*(\d+(?:\.\d+)?)\s*(bps|basis points)", low)
            percent_spread = re.search(r"\+\s*(\d+(?:\.\d+)?)\s*%", low)
            val["index"] = idx.group(1).upper() if idx else None
            val["spread_bps"] = float(spread.group(1)) if spread else round(float(percent_spread.group(1))*100,8) if percent_spread else None
            if val["index"] is None or val["spread_bps"] is None:
                return None,"needs_review","floating coupon index or spread unresolved; no complete coupon normalization"
        else:
            val["rate_pct"] = float(rate.group(1)) if rate else None
            if val["rate_pct"] is None:
                return None, "needs_review", "fixed coupon rate not parseable"
        return val, "extracted", "coupon parsed to rate/type/frequency"

    if field == "seniority":
        for key, norm, rank in SENIORITY_RANK:
            if key in low:
                return {"seniority": norm, "rank": rank}, "extracted", "seniority mapped to canonical rank"
        return None, "needs_review", "seniority language not in canonical ranking"

    if field == "collateral":
        secured = bool(re.search(r"\b(lien|secured|collateral|security interest|pledge|charge)\b", low))
        priority = None
        if "first-priority" in low or "first priority" in low:
            priority = "first"
        elif "second-priority" in low or "second priority" in low:
            priority = "second"
        return {"secured": secured, "lien_priority": priority, "description": raw}, "extracted", \
            "collateral flagged secured/unsecured with priority"

    if field == "call_provision":
        val = {
            "make_whole": "make-whole" in low or "make whole" in low,
            "non_call_until": _find_first_date(raw) if ("non-call" in low or "non-callable" in low) else None,
            "callable": "callable" in low and "non-callable" not in low.replace("non-callable until", ""),
            "raw": raw,
        }
        return val, "extracted", "call features captured factually (no valuation)"

    if field == "covenant":
        if "maintenance" in low or "at all times" in low or "as of the last day of each" in low:
            ctype = "maintenance"
        elif "incurrence" in low or "to incur" in low or "restricted payment" in low or "ratio debt" in low:
            ctype = "incurrence"
        else:
            ctype = "unclassified"
        thr = re.search(r"(\d+(?:\.\d+)?)\s*x", low)
        val = {"covenant_type": ctype, "threshold_value": float(thr.group(1)) if thr else None,
               "threshold_unit": "x" if thr else None, "raw": raw}
        return val, "extracted", "covenant classified by structure; threshold captured, not tested"

    if field == "basket":
        btype = "other"
        if "general debt" in low or "general basket" in low:
            btype = "general_debt"
        elif "builder" in low or "available amount" in low:
            btype = "builder"
        elif "restricted payment" in low:
            btype = "restricted_payments"
        return {"basket_type": btype, "cap_floor_usd": _usd_amount(raw), "raw": raw}, "extracted", \
            "basket type and stated cap captured"

    return None, "needs_review", "no normalizer for field"


def _cite(doc_id: str, page, locator: str) -> str:
    loc = f" {locator}" if locator else ""
    return f"{doc_id}:p.{page}{loc}"


def _compute_native(doc: dict) -> dict:
    doc_id = doc["doc_id"]
    fields, needs_review, seen = [], [], {}

    for c in doc.get("candidates", []):
        field = c.get("field")
        raw = str(c.get("raw_value", ""))
        value, status, reason = _normalize(field, raw)
        if doc.get("doc_version") != "execution" or doc.get("is_amendment") is True or doc.get("supersedes") or doc.get("amendments"):
            value, status, reason = None, "needs_review", "draft or amended document requires reviewed governing-term consolidation"
        if field == "maturity" and status == "extracted":
            try: date.fromisoformat(value["maturity_date"])
            except ValueError: value, status, reason = None, "needs_review", "invalid calendar date"
        evidence = {"page": c.get("page"), "locator": c.get("locator"),
                    "citation": _cite(doc_id, c.get("page"), c.get("locator", ""))}
        rec = {"field": field, "status": status, "value": value, "raw_value": raw,
               "evidence": evidence, "reason": reason}
        fields.append(rec)
        seen.setdefault(field, []).append(rec)

    # Conflict detection for singleton fields: differing extracted values -> needs_review.
    for field in SINGLETON_FIELDS:
        recs = [r for r in seen.get(field, []) if r["status"] == "extracted"]
        distinct = {json.dumps(r["value"], sort_keys=True) for r in recs}
        if len(recs) > 1 and len(distinct) > 1:
            for r in recs:
                r["status"] = "needs_review"
                r["value"] = None
                r["reason"] = "conflicting candidates for a single-value field; requires human resolution"

    for r in fields:
        if r["status"] == "needs_review":
            needs_review.append({"field": r["field"], "raw_value": r["raw_value"],
                                 "reason": r["reason"], "evidence": r["evidence"]})

    expected = doc.get("expected_fields") or []
    present = {r["field"] for r in fields}
    not_found = [{"field": f} for f in expected if f not in present]

    coverage = {
        "expected": len(expected),
        "extracted": sum(1 for r in fields if r["status"] == "extracted"),
        "needs_review": len(needs_review),
        "not_found": len(not_found),
    }

    return {
        "extraction_id": f"ctce-{doc_id}-{doc['effective_date']}-" + hashlib.sha256(json.dumps(doc, sort_keys=True, allow_nan=False).encode()).hexdigest()[:12],
        "doc_id": doc_id,
        "doc_type": doc.get("doc_type"),
        "issuer": doc.get("issuer"),
        "instrument": doc.get("instrument"),
        "effective_date": doc["effective_date"],
        "doc_version": doc.get("doc_version"),
        "governing_law": doc.get("governing_law"),
        "fields": fields,
        "needs_review": needs_review,
        "not_found": not_found,
        "coverage": coverage,
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "extraction_request.json"
    core = compute(_read_json(p.read_text(encoding="utf-8")))
    errors = []
    if not core["extraction_id"].startswith("ctce-"):
        errors.append("extraction_id does not start with 'ctce-'")
    if core["coverage"]["needs_review"] != 2:
        errors.append(f"expected exactly 2 needs_review, got {core['coverage']['needs_review']}")
    if core["not_found"]:
        errors.append(f"expected no not_found fields, got {core['not_found']}")
    by_field = {}
    for r in core["fields"]:
        by_field.setdefault(r["field"], []).append(r)
        if r["status"] in ("extracted", "needs_review"):
            pg = r["evidence"].get("page")
            if not isinstance(pg, int) or isinstance(pg, bool):
                errors.append(f"field {r['field']} missing integer page citation")
    mat = by_field.get("maturity", [{}])[0].get("value") or {}
    if mat.get("maturity_date") != "2031-04-15":
        errors.append(f"maturity not normalized to 2031-04-15 (got {mat.get('maturity_date')!r})")
    cpn = by_field.get("coupon", [{}])[0].get("value") or {}
    if cpn.get("rate_pct") != 6.5 or cpn.get("type") != "fixed":
        errors.append(f"coupon not normalized to fixed 6.5 (got {cpn})")
    sen = by_field.get("seniority", [{}])[0].get("value") or {}
    if sen.get("seniority") != "senior_secured":
        errors.append(f"seniority not normalized to senior_secured (got {sen.get('seniority')!r})")
    for e in errors:
        print("ERROR", e)
    print(f"normalize selftest: {len(errors)} error(s)")
    return 1 if errors else 0


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
    result.update({k:doc[k] for k in ("issuer_id","instrument_id")})
    result["source_scope"]="supplied candidates only; completeness, legal effect and source authenticity unverified"
    canonical_hash(result)
    return attach_source(result, doc)


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
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
