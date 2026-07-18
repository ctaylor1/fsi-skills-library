#!/usr/bin/env python3
"""Deterministic input validation for investment-thesis-monitor.

Validates a scheduled-run snapshot before breach computation. Fails closed on structural
problems; warns on data-quality/freshness gaps that limit which signals are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD), config_version, lookback_days, config{...thresholds...},
  prior_alerts[{alert_key,as_of,status}],
  theses[{
    thesis_id, security, direction ('long'|'short'), owner, thesis_asof,
    targets{price_target,stop_price},
    kpis[{name,expected,actual,direction ('higher_better'|'lower_better'),observed_at,source_ref}],
    catalysts[{name,due_by,status ('met'|'missed'|'pending'),observed_at,source_ref}],
    estimates{prior_consensus_eps,current_consensus_eps,observed_at,source_ref},
    market{price,price_asof,source_ref},
    news_flags[{risk_tag,observed_at,source_ref}]
  }]

Usage:
  python validate_input.py snapshot.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "theses")
REQUIRED_THESIS = ("thesis_id", "security", "direction", "owner")
DIRECTIONS = ("long", "short")


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

    theses = doc.get("theses") or []
    if not isinstance(theses, list) or not theses:
        errors.append("theses must be a non-empty list")
        return errors, warnings

    prior = doc.get("prior_alerts") or []
    if not isinstance(prior, list):
        errors.append("prior_alerts must be a list when present")
    else:
        for i, a in enumerate(prior):
            if not a.get("alert_key"):
                errors.append(f"prior_alerts[{i}]: missing 'alert_key'")

    seen = set()
    for i, t in enumerate(theses):
        tag = f"theses[{i}] ({t.get('thesis_id','?')})"
        for k in REQUIRED_THESIS:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if t.get("direction") not in DIRECTIONS:
            errors.append(f"{tag}: direction must be 'long' or 'short'")
        tid = t.get("thesis_id")
        if tid in seen:
            errors.append(f"{tag}: duplicate thesis_id")
        seen.add(tid)

        # A thesis needs at least one evaluable evidence surface.
        surfaces = sum(bool(t.get(k)) for k in ("kpis", "catalysts", "estimates", "market", "news_flags"))
        if surfaces == 0:
            warnings.append(f"{tag}: no evidence surfaces (kpis/catalysts/estimates/market/news) — nothing to monitor")

        for j, kp in enumerate(t.get("kpis") or []):
            if _num(kp.get("expected")) is None or _num(kp.get("actual")) is None:
                errors.append(f"{tag} kpis[{j}]: expected/actual must be numeric")
            if kp.get("direction") not in ("higher_better", "lower_better"):
                errors.append(f"{tag} kpis[{j}]: direction must be 'higher_better' or 'lower_better'")
            if not kp.get("observed_at"):
                warnings.append(f"{tag} kpis[{j}]: no observed_at — freshness not verifiable, kpi signal not evaluable")
            if not kp.get("source_ref"):
                warnings.append(f"{tag} kpis[{j}]: no source_ref — evidence will be uncitable")

        mkt = t.get("market") or {}
        if mkt and _num(mkt.get("price")) is None:
            errors.append(f"{tag} market: price must be numeric when market present")
        tgt = t.get("targets") or {}
        if mkt and not (tgt.get("price_target") or tgt.get("stop_price")):
            warnings.append(f"{tag}: market present but no price_target/stop_price — price signals not evaluable")

        est = t.get("estimates") or {}
        if est and (_num(est.get("prior_consensus_eps")) is None or _num(est.get("current_consensus_eps")) is None):
            errors.append(f"{tag} estimates: prior/current_consensus_eps must be numeric when estimates present")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "monitor_snapshot.json"
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
