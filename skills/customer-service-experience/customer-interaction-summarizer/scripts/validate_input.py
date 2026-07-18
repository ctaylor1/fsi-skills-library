#!/usr/bin/env python3
"""Deterministic input validation for customer-interaction-summarizer.

Validates a single-interaction record against the documented schema BEFORE summarizing.
Fails closed on structural problems (missing fields, uncitable segments, multiple
interactions merged into one file); warns (does not fail) on data-quality gaps the summary
must surface (inaudible/redacted segments, unmasked identifiers, missing timestamps).

Input schema (JSON):
{
  "interaction_id": "str",
  "customer_ref": "****5678",          # masked; last 4 only
  "channel": "call|chat|email|thread|ivr",
  "interaction_date": "YYYY-MM-DD",
  "source": {"system": "ccaas|crm|complaints|email", "ref": "..."},
  "segments": [
    {"seq": 1, "speaker": "agent|customer|system|ivr",
     "timestamp": "MM:SS"(opt), "text": "...", "ref": "citation",
     "interaction_id": "..."(opt)}
  ]
}

Usage:
  python validate_input.py interaction.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DIGIT_RUN_RE = re.compile(r"\d{7,}")
INAUDIBLE_RE = re.compile(r"^\s*(\[?\s*(inaudible|redacted|unintelligible|no audio)\s*\]?)\s*$", re.I)
REQUIRED_TOP = ("interaction_id", "channel", "interaction_date", "source", "segments")
REQUIRED_SEG = ("speaker", "text", "ref")
KNOWN_CHANNELS = {"call", "chat", "email", "thread", "ivr"}
KNOWN_SPEAKERS = {"agent", "customer", "system", "ivr", "rep", "advisor"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["interaction_date"])):
        errors.append(f"interaction_date must be YYYY-MM-DD, got {doc['interaction_date']!r}")

    if str(doc.get("channel")) not in KNOWN_CHANNELS:
        warnings.append(f"channel {doc.get('channel')!r} not in {sorted(KNOWN_CHANNELS)} — confirm channel")

    src = doc.get("source") or {}
    if not (src.get("system") and src.get("ref")):
        errors.append("source must include 'system' and 'ref' (citation)")

    cust = str(doc.get("customer_ref", ""))
    if cust and DIGIT_RUN_RE.search(cust):
        warnings.append(f"customer_ref {cust!r} looks unmasked (7+ digit run) — mask to last 4 before summarizing")

    segments = doc.get("segments") or []
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty list")
        return errors, warnings

    top_iid = doc["interaction_id"]
    iids = {top_iid}
    speakers_seen = set()
    for i, s in enumerate(segments):
        tag = f"segments[{i}] (seq={s.get('seq', '?')})"
        for k in REQUIRED_SEG:
            if k not in s or (isinstance(s.get(k), str) and not str(s.get(k)).strip()) or s.get(k) is None:
                errors.append(f"{tag}: missing '{k}'")
        if s.get("interaction_id"):
            iids.add(s["interaction_id"])
        speakers_seen.add(s.get("speaker"))
        text = str(s.get("text", ""))
        if INAUDIBLE_RE.match(text):
            warnings.append(f"{tag}: inaudible/redacted placeholder - exclude and record as a data gap")
        elif not text.strip():
            warnings.append(f"{tag}: empty segment text — nothing to summarize")
        if "timestamp" not in s and str(doc.get("channel")) in {"call", "ivr"}:
            warnings.append(f"{tag}: no timestamp — reduces citation precision for a {doc.get('channel')}")
        if s.get("speaker") not in KNOWN_SPEAKERS:
            warnings.append(f"{tag}: speaker {s.get('speaker')!r} not in {sorted(KNOWN_SPEAKERS)}")

    if len(iids) > 1:
        errors.append(f"segments span multiple interaction_ids {sorted(iids)} — do not merge; confirm a single interaction")
    if speakers_seen and not ({"agent", "rep", "advisor"} & speakers_seen):
        warnings.append("no agent/rep segments present — confirm this is a complete interaction")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "interaction_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
