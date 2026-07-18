#!/usr/bin/env python3
"""Deterministic input validation for call-quality-compliance-reviewer.

Validates an interaction file before quality/compliance checks run. Fails closed on
structural problems; warns on data-quality gaps that limit which checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  interaction_id, as_of (YYYY-MM-DD), config_version, channel (voice|chat|email),
  context{requires_authentication, product_context, customer_stated_vulnerability},
  turns[{turn_id, speaker(agent|customer|system|ivr), text, ts?}],
  rubric{...required_disclosures[], prohibited_lexicon[], markers...}

Usage:
  python validate_input.py interaction.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("interaction_id", "as_of", "config_version", "channel", "turns")
REQUIRED_TURN = ("turn_id", "speaker", "text")
CHANNELS = {"voice", "chat", "email"}
SPEAKERS = {"agent", "customer", "system", "ivr"}
PRODUCTS = {"deposit", "lending", "collections", "investment", "general"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if doc["channel"] not in CHANNELS:
        errors.append(f"channel must be one of {sorted(CHANNELS)}, got {doc['channel']!r}")

    turns = doc.get("turns") or []
    if not isinstance(turns, list) or not turns:
        errors.append("turns must be a non-empty list")
        return errors, warnings

    ids = set()
    has_ts = 0
    n_agent = 0
    for i, t in enumerate(turns):
        tag = f"turns[{i}] ({t.get('turn_id', '?')})"
        for k in REQUIRED_TURN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if t.get("speaker") not in SPEAKERS:
            errors.append(f"{tag}: speaker must be one of {sorted(SPEAKERS)}")
        tid = t.get("turn_id")
        if tid in ids:
            errors.append(f"{tag}: duplicate turn_id")
        ids.add(tid)
        if t.get("ts"):
            has_ts += 1
        if t.get("speaker") == "agent":
            n_agent += 1

    ctx = doc.get("context") or {}
    prod = ctx.get("product_context")
    if prod is not None and prod not in PRODUCTS:
        warnings.append(f"context.product_context {prod!r} not in {sorted(PRODUCTS)} — product-specific disclosures may not be evaluable")
    if "requires_authentication" not in ctx:
        warnings.append("context.requires_authentication absent — assuming False; identity_authentication check may be skipped")
    if n_agent == 0:
        warnings.append("no agent turns — disclosure/prohibited-language checks are not evaluable")
    if has_ts == 0:
        warnings.append("no turn has a 'ts' — ordering falls back to array order; disclosure-before-auth ordering is best-effort")
    if not doc.get("rubric"):
        warnings.append("no 'rubric' block — default markers/lexicon will be used; record the config_version")
    if doc["channel"] != "voice":
        warnings.append("channel is not voice — recording_consent_disclosure is not evaluable for this channel")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "interaction_example.json"
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
