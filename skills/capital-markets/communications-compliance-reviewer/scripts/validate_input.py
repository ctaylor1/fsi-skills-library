#!/usr/bin/env python3
"""Deterministic input validation for communications-compliance-reviewer.

Validates a single communication record before the rule engine runs. Fails closed on
structural problems; warns on data-quality gaps that limit which checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  comm_id, as_of (YYYY-MM-DD), config_version, channel, audience, recipient_count,
  period_days, author, business_unit, subject, body, disclosures_present[],
  contains_testimonial, supervision{principal_pre_approved,approver_id,approval_date,
  reviewed,first_use_date}, retention{archived,archive_system,channel_approved}, source_ref

Usage:
  python validate_input.py communication.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("comm_id", "as_of", "config_version", "channel", "audience", "body", "source_ref")
KNOWN_CHANNELS = {
    "email", "social_media", "website", "letter", "advertisement", "research_report",
    "text_message", "chat", "internal_memo", "webinar", "print",
}
KNOWN_AUDIENCES = {"retail", "institutional", "internal"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if str(doc["audience"]) not in KNOWN_AUDIENCES:
        errors.append(f"audience must be one of {sorted(KNOWN_AUDIENCES)}, got {doc['audience']!r}")

    body = str(doc.get("body") or "")
    if len(body.strip()) < 3:
        errors.append("body is empty or too short to review")

    for block in ("supervision", "retention"):
        if not isinstance(doc.get(block), dict):
            errors.append(f"missing '{block}' object (required for supervision/retention checks)")

    if str(doc["channel"]) not in KNOWN_CHANNELS:
        warnings.append(f"channel {doc['channel']!r} not in known set — classification still attempted")

    if str(doc.get("audience")) == "retail" and doc.get("recipient_count") in (None, ""):
        warnings.append("retail audience without recipient_count — cannot split retail-communication vs "
                        "correspondence; the engine treats it conservatively as a retail communication")

    if "disclosures_present" not in doc:
        warnings.append("no 'disclosures_present' list — treated as empty; required-disclosure checks will "
                        "fire for every applicable disclosure")
    elif not isinstance(doc.get("disclosures_present"), list):
        errors.append("disclosures_present must be a list of disclosure tags")

    sup = doc.get("supervision") if isinstance(doc.get("supervision"), dict) else {}
    if "principal_pre_approved" not in sup and "reviewed" not in sup:
        warnings.append("supervision block has neither 'principal_pre_approved' nor 'reviewed' — "
                        "supervision gap will be reported conservatively")

    ret = doc.get("retention") if isinstance(doc.get("retention"), dict) else {}
    if "channel_approved" not in ret:
        warnings.append("retention.channel_approved missing — off-channel status not evaluable for this record")
    if not doc.get("config"):
        warnings.append("no 'config' block — default rule thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "communication_example.json"
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
