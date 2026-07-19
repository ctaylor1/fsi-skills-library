#!/usr/bin/env python3
"""Deterministic input validation for market-surveillance-alert-investigator.

Validates an escalated surveillance case file before an evidence bundle is built. Fails
CLOSED on structural problems (including missing escalation provenance — investigation must
consume an escalation, never self-triage) and WARNS on data gaps that will force a
`needs-data` disposition or a limited chronology.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, cases[
    {alert_id, alert_type, surveillance_rule_id, source_ref,
     escalation{from_skill, triage_case_id, escalated_by, reason},
     instrument{symbol, asset_class, venue, currency}, period{from, to},
     subject_party_id?, parties[{party_id, role, account_ref}],
     orders[], trades[], messages[], market[], prior_cases[]}]

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "cases")
REQUIRED_CASE = ("alert_id", "alert_type", "surveillance_rule_id", "source_ref",
                 "escalation", "instrument", "period", "parties")
KNOWN_TYPES = {"spoofing_layering", "wash_trade", "marking_the_close", "ramping",
               "insider_dealing", "comms_collusion"}
REQUIRED_STREAMS = {
    "spoofing_layering": ["orders"],
    "wash_trade": ["trades"],
    "marking_the_close": ["market", "trades"],
    "ramping": ["trades"],
    "insider_dealing": ["messages"],
    "comms_collusion": ["messages"],
}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    cases = doc.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty list"], warnings

    seen = set()
    for i, c in enumerate(cases):
        tag = f"cases[{i}] ({c.get('alert_id','?')})"
        for k in REQUIRED_CASE:
            if k not in c or c[k] in (None, "", [], {}):
                errors.append(f"{tag}: missing '{k}'")
        aid = c.get("alert_id")
        if aid in seen:
            errors.append(f"{tag}: duplicate alert_id")
        seen.add(aid)

        # Escalation provenance is mandatory — fail closed if this case was not escalated.
        esc = c.get("escalation") or {}
        if not esc.get("triage_case_id") or not esc.get("escalated_by"):
            errors.append(f"{tag}: escalation must carry 'triage_case_id' and 'escalated_by' "
                          "(investigation consumes an escalation; it does not self-triage)")

        per = c.get("period") or {}
        if not (per.get("from") and per.get("to")):
            errors.append(f"{tag}: period requires 'from' and 'to'")

        parties = c.get("parties") or []
        if not parties:
            errors.append(f"{tag}: at least one party is required")
        party_ids = {p.get("party_id") for p in parties}
        for p in parties:
            if not p.get("party_id") or not p.get("role"):
                errors.append(f"{tag}: each party requires 'party_id' and 'role'")

        atype = c.get("alert_type")
        if atype and atype not in KNOWN_TYPES:
            warnings.append(f"{tag}: unknown alert_type {atype!r} -> generic indicators only")

        # Entity resolution: every order/trade/message actor should resolve to a party.
        for stream, idk in (("orders", "order_id"), ("trades", "trade_id"), ("messages", "msg_id")):
            for rec in c.get(stream) or []:
                if rec.get("party_id") and rec.get("party_id") not in party_ids:
                    warnings.append(f"{tag}: {stream} {rec.get(idk)} references unresolved party "
                                    f"{rec.get('party_id')!r} (entity resolution)")

        # Chronology: events outside the stated period are suspicious.
        pf, pt = str(per.get("from")), str(per.get("to"))
        for stream in ("orders", "trades", "messages", "market"):
            for rec in c.get(stream) or []:
                ts = str(rec.get("ts") or "")[:10]
                if ts and not (pf <= ts <= pt):
                    warnings.append(f"{tag}: {stream} event at {rec.get('ts')} is outside period "
                                    f"{pf}..{pt} (chronology)")

        # Required evidence streams for this alert type.
        for s in REQUIRED_STREAMS.get(atype, []):
            if not c.get(s):
                warnings.append(f"{tag}: required '{s}' stream absent for alert_type {atype!r} "
                                "-> disposition will be needs-data")
        # Market events must carry a source_ref for citation.
        for k in c.get("market") or []:
            if not k.get("source_ref"):
                warnings.append(f"{tag}: a market event lacks source_ref -> weak citation")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
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
