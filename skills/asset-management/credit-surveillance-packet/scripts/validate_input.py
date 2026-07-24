#!/usr/bin/env python3
"""Deterministic input validation for credit-surveillance-packet.

Validates a surveillance build request before the packet is assembled. Fails closed on
structural problems (so the skill never drafts on top of a malformed request); warns on
data-quality gaps that force a `needs-data` disposition or that must be disclosed in the
packet (e.g. an unapproved market/rating source whose claims will be blocked, or a missing
prior period that limits period-over-period change tracking).

Input schema (JSON): see references/source-map.md. Key fields:
  packet_version, config_version, issuer{issuer_id,name,sector,as_of,prior_as_of},
  sources[{source_id,type,ref,approved,as_of}],
  financials{source_id,ebitda,gross_debt,cash,interest_expense,capex,undrawn_revolver,
    stated_gross_leverage_x?,stated_net_leverage_x?,stated_interest_coverage_x?},
  prior_financials{source_id,ebitda,gross_debt,cash,interest_expense,...}?,
  maturities[{year,amount,source_id}], spreads{source_id,current_bps,prior_bps},
  ratings[{agency,rating,outlook,prior_rating,prior_outlook,source_id}],
  covenants[{covenant_id,name,changed,source_id}], approvals[{role,status}]

Usage: python validate_input.py surveillance_request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("packet_version", "config_version", "issuer", "sources", "financials",
                "maturities", "spreads", "ratings", "covenants", "approvals")
REQUIRED_ISSUER = ("issuer_id", "name", "sector", "as_of")
REQUIRED_FIN = ("ebitda", "gross_debt", "cash", "interest_expense", "capex", "undrawn_revolver")
UNAPPROVED_TYPES = {"market", "rating-agency"}  # external inputs that must be marked approved


def _num(obj, key):
    v = obj.get(key)
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    issuer = doc.get("issuer") or {}
    for k in REQUIRED_ISSUER:
        if not issuer.get(k):
            errors.append(f"issuer: missing '{k}'")

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return errors, warnings
    src_ids, src_types = set(), {}
    for i, s in enumerate(sources):
        sid = s.get("source_id")
        if not sid:
            errors.append(f"sources[{i}]: missing 'source_id'")
        if sid in src_ids:
            errors.append(f"sources[{i}]: duplicate source_id {sid!r}")
        src_ids.add(sid)
        src_types[sid] = s.get("type")
        if s.get("type") in UNAPPROVED_TYPES and not s.get("approved"):
            warnings.append(f"source {sid!r} ({s.get('type')}) is not marked approved -> "
                            f"claims relying on it will be blocked as unapproved (needs-data)")

    fin = doc.get("financials") or {}
    for k in REQUIRED_FIN:
        if not _num(fin, k):
            errors.append(f"financials: missing/non-numeric '{k}' (needed to compute credit metrics)")
    if not fin.get("source_id"):
        errors.append("financials: missing 'source_id'")
    elif fin.get("source_id") not in src_ids:
        errors.append(f"financials.source_id {fin.get('source_id')!r} not in sources[]")
    if _num(fin, "ebitda") and fin.get("ebitda") == 0:
        errors.append("financials.ebitda is 0 -> leverage/coverage ratios are undefined")
    if _num(fin, "interest_expense") and fin.get("interest_expense") == 0:
        errors.append("financials.interest_expense is 0 -> coverage ratios are undefined")

    prior = doc.get("prior_financials")
    if prior is None:
        warnings.append("no prior_financials supplied -> period-over-period change tracking is limited (needs-data)")
    elif prior.get("source_id") and prior.get("source_id") not in src_ids:
        warnings.append(f"prior_financials.source_id {prior.get('source_id')!r} not in sources[] -> change deltas unsupported")

    maturities = doc.get("maturities") or []
    if not isinstance(maturities, list):
        errors.append("maturities must be a list")
    else:
        for j, m in enumerate(maturities):
            if not _num(m, "year") or not _num(m, "amount"):
                errors.append(f"maturities[{j}]: 'year' and 'amount' must be numeric")
            if m.get("source_id") not in src_ids:
                warnings.append(f"maturities[{j}] cites source {m.get('source_id')!r} not in sources[] -> unsupported")

    spreads = doc.get("spreads") or {}
    if not _num(spreads, "current_bps"):
        warnings.append("spreads.current_bps missing -> spread section will be incomplete (needs-data)")
    if spreads.get("source_id") not in src_ids:
        warnings.append(f"spreads.source_id {spreads.get('source_id')!r} not in sources[] -> unsupported")
    elif src_types.get(spreads.get("source_id")) != "market":
        warnings.append("spreads should cite a 'market' source -> otherwise flagged for review")

    for j, r in enumerate(doc.get("ratings") or []):
        if not r.get("agency") or not r.get("rating"):
            warnings.append(f"ratings[{j}]: missing 'agency'/'rating' -> ratings section incomplete")
        if r.get("source_id") not in src_ids:
            warnings.append(f"ratings[{j}] cites source {r.get('source_id')!r} not in sources[] -> unsupported")
        elif src_types.get(r.get("source_id")) != "rating-agency":
            warnings.append(f"ratings[{j}] must cite a 'rating-agency' source (ratings are reported, never assigned)")

    for j, c in enumerate(doc.get("covenants") or []):
        if not c.get("covenant_id"):
            warnings.append(f"covenants[{j}]: missing 'covenant_id'")
        if c.get("source_id") not in src_ids:
            warnings.append(f"covenants[{j}] cites source {c.get('source_id')!r} not in sources[] -> unsupported")

    recorded = {a.get("role") for a in (doc.get("approvals") or []) if a.get("status") == "recorded"}
    for role in ("preparer", "reviewer"):
        if role not in recorded:
            warnings.append(f"approval '{role}' not yet recorded -> packet cannot be delivered until recorded")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "surveillance_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
