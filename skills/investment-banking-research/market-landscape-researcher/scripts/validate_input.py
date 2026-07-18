#!/usr/bin/env python3
"""Deterministic input validation for market-landscape-researcher.

Validates a landscape research brief before synthesis. Fails closed on structural problems
(missing dimensions, malformed sources/shares); warns on evidence-quality gaps (uncited
findings, stale or low-tier sources, large unattributed competitive tail) that limit the
brief's confidence.

Input schema (JSON): see references/source-map.md. Key fields:
  theme, as_of (YYYY-MM-DD), config_version, geography,
  sources[{source_id, publisher, tier(1..4), date, url_ref?}],
  competitors[{name, revenue_share_pct, source_id?}],
  dimensions{ value_chain[], competitors[], customers[], regulation[], technology[],
              economics[], transactions[], strategic_implications[] },
    where each finding is {finding, source_id}
  config{ staleness_days, min_named_share_sum, ... } (optional; defaults applied)

Usage:
  python validate_input.py brief.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("theme", "as_of", "config_version", "sources", "competitors", "dimensions")
REQUIRED_DIMENSIONS = (
    "value_chain", "competitors", "customers", "regulation",
    "technology", "economics", "transactions", "strategic_implications",
)
DEFAULTS = {"staleness_days": 365, "min_named_share_sum": 70.0}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except ValueError:
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    cfg = {**DEFAULTS, **(doc.get("config") or {})}
    as_of = _parse_date(doc["as_of"])
    if not DATE_RE.match(str(doc["as_of"])) or as_of is None:
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    # ---- sources ----
    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return errors, warnings
    source_ids, tier4 = set(), 0
    for i, s in enumerate(sources):
        tag = f"sources[{i}] ({s.get('source_id','?')})"
        sid = s.get("source_id")
        if not sid:
            errors.append(f"{tag}: missing 'source_id'")
        elif sid in source_ids:
            errors.append(f"{tag}: duplicate source_id")
        source_ids.add(sid)
        tier = s.get("tier")
        if tier not in (1, 2, 3, 4):
            errors.append(f"{tag}: tier must be an integer 1..4, got {tier!r}")
        elif tier == 4:
            tier4 += 1
        sd = _parse_date(s.get("date"))
        if sd is None:
            errors.append(f"{tag}: date must be YYYY-MM-DD, got {s.get('date')!r}")
        elif as_of is not None and (as_of - sd).days > cfg["staleness_days"]:
            warnings.append(f"{tag}: source dated {s.get('date')} is older than "
                            f"{cfg['staleness_days']}d before as_of — treat as stale/refresh")
    if tier4:
        warnings.append(f"{tier4} tier-4 (unverified/marketing) source(s) present — "
                        f"do not let any finding rest solely on a tier-4 source")

    # ---- competitors ----
    comps = doc.get("competitors") or []
    if not isinstance(comps, list) or not comps:
        errors.append("competitors must be a non-empty list")
        return errors, warnings
    named_sum = 0.0
    for i, c in enumerate(comps):
        tag = f"competitors[{i}] ({c.get('name','?')})"
        if not c.get("name"):
            errors.append(f"{tag}: missing 'name'")
        share = _num(c.get("revenue_share_pct"))
        if share is None:
            errors.append(f"{tag}: revenue_share_pct not numeric")
        elif share < 0:
            errors.append(f"{tag}: revenue_share_pct negative")
        else:
            named_sum += share
        if c.get("source_id") and c["source_id"] not in source_ids:
            warnings.append(f"{tag}: references unknown source_id {c['source_id']!r}")
    if named_sum > 100.5:
        errors.append(f"named competitor shares sum to {named_sum:.1f}% (> 100%) — over-allocated")
    elif named_sum < cfg["min_named_share_sum"]:
        warnings.append(f"named shares sum to {named_sum:.1f}% — large unattributed tail; "
                        f"concentration metrics describe only the named set")

    # ---- dimensions ----
    dims = doc.get("dimensions")
    if not isinstance(dims, dict):
        errors.append("dimensions must be an object keyed by the eight landscape dimensions")
        return errors, warnings
    for d in REQUIRED_DIMENSIONS:
        rows = dims.get(d)
        if not isinstance(rows, list) or not rows:
            errors.append(f"dimension '{d}' missing or empty (all eight dimensions required)")
            continue
        for j, f in enumerate(rows):
            ftag = f"dimensions.{d}[{j}]"
            if not (f.get("finding") or "").strip():
                errors.append(f"{ftag}: missing 'finding' text")
            sid = f.get("source_id")
            if not sid:
                warnings.append(f"{ftag}: uncited finding — output validation will fail closed "
                                f"unless a citation is attached")
            elif sid not in source_ids:
                warnings.append(f"{ftag}: cites unknown source_id {sid!r}")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "landscape_example.json"
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
