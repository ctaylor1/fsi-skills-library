#!/usr/bin/env python3
"""Deterministic input validation for mandate-compliance-monitor.

Validates a monitoring-run file before the rule engine evaluates it. Fails closed on
structural problems; warns on data-quality gaps that limit which rules are evaluable or
that disable freshness / deduplication for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD), config_version, max_staleness_days,
  open_alerts[{fingerprint}],                      # previously-open alerts, for dedup
  portfolios[{portfolio_id, mandate_id, nav, holdings_as_of, prices_as_of,
              holdings[{security_id,issuer,sector,asset_class,country,rating,
                        esg_score,market_value,is_restricted}],
              proposed_trades[{trade_id,security_id,issuer,side,market_value,sector,
                               asset_class}]}],
  rules[{rule_id, type, scope, limit_pct|max_pct|min_pct|min_score, warn_buffer_pct,
         restricted_securities[], excluded_sectors[]}]

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "portfolios", "rules")
REQUIRED_PORTFOLIO = ("portfolio_id", "nav", "holdings")
REQUIRED_HOLDING = ("security_id", "issuer", "market_value")
RULE_TYPES = {"concentration", "regulatory", "guideline", "restriction", "esg"}
THRESHOLD_TYPES = {"concentration", "regulatory", "guideline"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if "max_staleness_days" not in doc:
        warnings.append("no 'max_staleness_days' — freshness is not evaluable this run; alerts may be based on stale holdings")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every breach will be reported as new")

    portfolios = doc.get("portfolios") or []
    if not isinstance(portfolios, list) or not portfolios:
        errors.append("portfolios must be a non-empty list")
        return errors, warnings

    pids = set()
    for i, p in enumerate(portfolios):
        tag = f"portfolios[{i}] ({p.get('portfolio_id','?')})"
        for k in REQUIRED_PORTFOLIO:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        pid = p.get("portfolio_id")
        if pid in pids:
            errors.append(f"{tag}: duplicate portfolio_id")
        pids.add(pid)
        nav = _num(p.get("nav"))
        if nav is None or nav <= 0:
            errors.append(f"{tag}: nav must be a positive number")
        holdings = p.get("holdings") or []
        if not isinstance(holdings, list) or not holdings:
            errors.append(f"{tag}: holdings must be a non-empty list")
            continue
        if not p.get("holdings_as_of"):
            warnings.append(f"{tag}: no holdings_as_of — freshness not evaluable for this portfolio")
        seen_sec = set()
        for j, h in enumerate(holdings):
            htag = f"{tag}.holdings[{j}] ({h.get('security_id','?')})"
            for k in REQUIRED_HOLDING:
                if k not in h or h[k] in (None, ""):
                    errors.append(f"{htag}: missing '{k}'")
            if _num(h.get("market_value")) is None:
                errors.append(f"{htag}: market_value not numeric")
            sid = h.get("security_id")
            if sid in seen_sec:
                warnings.append(f"{htag}: repeated security_id — positions will be aggregated")
            seen_sec.add(sid)
            if not h.get("sector"):
                warnings.append(f"{htag}: no sector — sector concentration / ESG-exclusion not evaluable for this row")
            if not h.get("asset_class"):
                warnings.append(f"{htag}: no asset_class — asset-class guideline not evaluable for this row")
            if h.get("esg_score") is None:
                warnings.append(f"{htag}: no esg_score — ESG minimum-score rule not evaluable for this row")

    rules = doc.get("rules") or []
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty list")
        return errors, warnings
    rids = set()
    for i, r in enumerate(rules):
        tag = f"rules[{i}] ({r.get('rule_id','?')})"
        if not r.get("rule_id"):
            errors.append(f"{tag}: missing rule_id")
        if r.get("rule_id") in rids:
            errors.append(f"{tag}: duplicate rule_id")
        rids.add(r.get("rule_id"))
        rtype = r.get("type")
        if rtype not in RULE_TYPES:
            errors.append(f"{tag}: type must be one of {sorted(RULE_TYPES)}, got {rtype!r}")
            continue
        if rtype in THRESHOLD_TYPES:
            if _num(r.get("limit_pct")) is None and _num(r.get("max_pct")) is None and _num(r.get("min_pct")) is None:
                errors.append(f"{tag}: threshold rule needs limit_pct or max_pct or min_pct")
        if rtype == "restriction" and not r.get("restricted_securities"):
            warnings.append(f"{tag}: restriction rule has no restricted_securities — only per-holding is_restricted flags will fire")
        if rtype == "esg":
            scope = r.get("scope")
            if scope == "min_score" and _num(r.get("min_score")) is None:
                errors.append(f"{tag}: esg min_score rule needs numeric min_score")
            if scope == "exclusion" and not r.get("excluded_sectors"):
                warnings.append(f"{tag}: esg exclusion rule has no excluded_sectors")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
