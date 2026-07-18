#!/usr/bin/env python3
"""Deterministic input validation for payment-failure-diagnoser.

Validates a payment-trace file before diagnosis. Fails closed on structural problems; warns
on data-quality gaps that limit interpretation (no timestamps, unknown codes, non-contiguous
legs).

Input schema (JSON): see references/source-map.md. Key fields:
  payment_id, as_of (YYYY-MM-DD), rail (card|ach|iso20022|wire|rtp), codeset_version,
  config_version, amount, currency,
  legs[{seq,stage,status,reason_code?,timestamp?,source_ref}]

Usage:
  python validate_input.py trace.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("payment_id", "as_of", "rail", "legs")
REQUIRED_LEG = ("seq", "stage", "status", "source_ref")
RAILS = {"card", "ach", "iso20022", "wire", "rtp"}
STAGES = {"initiation", "authorization", "routing", "messaging",
          "screening", "clearing", "settlement"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if doc.get("rail") not in RAILS:
        errors.append(f"rail must be one of {sorted(RAILS)}, got {doc.get('rail')!r}")

    legs = doc.get("legs") or []
    if not isinstance(legs, list) or not legs:
        errors.append("legs must be a non-empty list")
        return errors, warnings

    seqs, has_time = set(), 0
    for i, lg in enumerate(legs):
        tag = f"legs[{i}] (seq={lg.get('seq','?')})"
        for k in REQUIRED_LEG:
            if k not in lg or lg[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        s = lg.get("seq")
        if not isinstance(s, int):
            errors.append(f"{tag}: seq must be an integer")
        elif s in seqs:
            errors.append(f"{tag}: duplicate seq")
        else:
            seqs.add(s)
        if lg.get("stage") not in STAGES:
            warnings.append(f"{tag}: stage {lg.get('stage')!r} not in known lifecycle stages")
        if lg.get("timestamp"):
            has_time += 1
        # reason_code is optional (progress legs carry none); it is checked in compute.

    if has_time == 0:
        warnings.append("no leg has a timestamp — ordering and stuck-in-flight detection are limited")
    elif has_time < len(legs):
        warnings.append(f"only {has_time}/{len(legs)} legs have timestamps — ordering may be incomplete")

    # contiguity: seqs should be a contiguous run for a complete trace
    if isinstance(min(seqs, default=None), int):
        expected = set(range(min(seqs), max(seqs) + 1))
        if seqs != expected:
            warnings.append(f"leg seq values are not contiguous ({sorted(seqs)}) — trace may be incomplete")

    if not doc.get("codeset_version"):
        warnings.append("no 'codeset_version' — default bundled code set will be used; record the version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "trace_example.json"
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
