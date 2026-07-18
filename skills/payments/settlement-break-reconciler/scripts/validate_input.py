#!/usr/bin/env python3
"""Deterministic input validation for settlement-break-reconciler.

Validates a reconciliation input file before matching. Fails closed on structural problems
(missing sources, malformed periods, non-numeric amounts); warns on data-quality gaps that
limit which tie-outs are evaluable (missing fee schedule, empty bank cash, etc.).

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD), period{start,end}, config_version, settlement_currency, config{...},
  fee_schedule[{scheme,rate_bps,reserve_bps}],
  sources{
    network[{match_key,scheme,settlement_date,currency,gross,source_ref}],
    processor[{match_key,scheme,settlement_date,currency,gross,fees,reserve,net,source_ref}],
    bank_cash[{match_key,value_date,currency,amount,source_ref}],
    ledger[{match_key,post_date,currency,net,source_ref}]
  }

Usage:
  python validate_input.py recon.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "period", "config_version", "sources")
SOURCE_KEYS = ("network", "processor", "bank_cash", "ledger")
REQUIRED_FIELDS = {
    "network": ("match_key", "settlement_date", "gross", "source_ref"),
    "processor": ("match_key", "settlement_date", "gross", "fees", "reserve", "net", "source_ref"),
    "bank_cash": ("match_key", "value_date", "amount", "source_ref"),
    "ledger": ("match_key", "post_date", "net", "source_ref"),
}
NUMERIC_FIELDS = {
    "network": ("gross",),
    "processor": ("gross", "fees", "reserve", "net"),
    "bank_cash": ("amount",),
    "ledger": ("net",),
}
DATE_FIELDS = {"network": "settlement_date", "processor": "settlement_date",
               "bank_cash": "value_date", "ledger": "post_date"}


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

    period = doc.get("period") or {}
    for k in ("start", "end"):
        if not period.get(k) or not DATE_RE.match(str(period.get(k))):
            errors.append(f"period.{k} must be YYYY-MM-DD, got {period.get(k)!r}")

    sources = doc.get("sources")
    if not isinstance(sources, dict):
        errors.append("sources must be an object with network/processor/bank_cash/ledger lists")
        return errors, warnings
    for sk in SOURCE_KEYS:
        if sk not in sources:
            errors.append(f"sources missing '{sk}' (use an empty list if the source is absent)")
        elif not isinstance(sources[sk], list):
            errors.append(f"sources.{sk} must be a list")
    if errors:
        return errors, warnings

    scheme_ref, scheme_have = set(), {str(s.get("scheme")) for s in (doc.get("fee_schedule") or [])}
    for sk in SOURCE_KEYS:
        rows = sources[sk]
        keys_seen: dict = {}
        for i, r in enumerate(rows):
            tag = f"sources.{sk}[{i}] ({r.get('match_key','?')})"
            if not isinstance(r, dict):
                errors.append(f"{tag}: record must be an object")
                continue
            for f in REQUIRED_FIELDS[sk]:
                if f not in r or r[f] in (None, ""):
                    errors.append(f"{tag}: missing '{f}'")
            for f in NUMERIC_FIELDS[sk]:
                if f in r and _num(r[f]) is None:
                    errors.append(f"{tag}: '{f}' not numeric ({r.get(f)!r})")
            df = DATE_FIELDS[sk]
            if r.get(df) and not DATE_RE.match(str(r[df])):
                errors.append(f"{tag}: {df} must be YYYY-MM-DD, got {r.get(df)!r}")
            mk = str(r.get("match_key"))
            keys_seen[mk] = keys_seen.get(mk, 0) + 1
            if sk in ("network", "processor") and r.get("scheme"):
                scheme_ref.add(str(r["scheme"]))
        dups = [k for k, c in keys_seen.items() if c > 1]
        if dups:
            warnings.append(f"sources.{sk}: duplicate match_key(s) {dups} — will classify as DUPLICATE breaks")
        if not rows:
            warnings.append(f"sources.{sk} is empty — tie-outs requiring {sk} are not evaluable")

    if not doc.get("fee_schedule"):
        warnings.append("no fee_schedule — FEE_VARIANCE and RESERVE_VARIANCE are not evaluable")
    else:
        missing_sched = scheme_ref - scheme_have
        if missing_sched:
            warnings.append(f"fee_schedule missing scheme(s) {sorted(missing_sched)} — fee/reserve not evaluable for those")

    if not doc.get("config"):
        warnings.append("no 'config' block — default tolerances will be used; record the config_version")
    if not doc.get("settlement_currency"):
        warnings.append("no settlement_currency — CURRENCY_MISMATCH relies on per-record currency only")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "recon_example.json"
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
