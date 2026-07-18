#!/usr/bin/env python3
"""Deterministic input validation for knowledge-base-curator.

Validates a knowledge-base export before curation. Fails closed on structural problems;
warns on data gaps that force a data-gap flag on a finding (missing last_reviewed, missing
owner, no source_ids to check currency against).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, as_of, review_period_days, policy{review_period_days, high_risk_tags[],
    high_risk_extra_severity}, sources[{source_id, system, ref, as_of, owner, asserts{}}],
  required_topics[{topic_id, title, required, owner_role}],
  articles[{article_id, title, status, owner, last_reviewed, review_period_days, expiry_date,
    tags[], content_hash, topic_id, source_ids[], supersedes[], asserts{}, location}]

Usage: python validate_input.py kb_export.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "as_of", "articles", "sources")
REQUIRED_ARTICLE = ("article_id", "title", "status")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    sources = doc.get("sources") or []
    if not isinstance(sources, list):
        errors.append("sources must be a list (approved-source register)")
        return errors, warnings
    src_ids = set()
    for i, s in enumerate(sources):
        sid = s.get("source_id")
        if not sid:
            errors.append(f"sources[{i}]: missing source_id")
        elif sid in src_ids:
            errors.append(f"sources[{i}]: duplicate source_id {sid!r}")
        src_ids.add(sid)
        if not s.get("as_of"):
            warnings.append(f"sources[{i}] ({sid}): no as_of date -> source-driven staleness cannot be checked")

    for i, t in enumerate(doc.get("required_topics") or []):
        if not t.get("topic_id"):
            errors.append(f"required_topics[{i}]: missing topic_id")
        if not t.get("title"):
            warnings.append(f"required_topics[{i}] ({t.get('topic_id','?')}): no title")

    articles = doc.get("articles") or []
    if not isinstance(articles, list) or not articles:
        errors.append("articles must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(articles):
        tag = f"articles[{i}] ({a.get('article_id','?')})"
        for k in REQUIRED_ARTICLE:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        aid = a.get("article_id")
        if aid in ids:
            errors.append(f"{tag}: duplicate article_id")
        ids.add(aid)
        for sid in a.get("source_ids") or []:
            if sid not in src_ids:
                errors.append(f"{tag}: source_id {sid!r} not in approved source register")
        if not a.get("last_reviewed"):
            warnings.append(f"{tag}: no last_reviewed -> will be flagged stale (data gap)")
        if not a.get("owner"):
            warnings.append(f"{tag}: no owner -> will be flagged ownerless (data gap)")
        if not (a.get("source_ids") or []):
            warnings.append(f"{tag}: no source_ids -> currency cannot be checked against a source-of-truth")

    # supersedes must reference known article ids
    for i, a in enumerate(articles):
        for sup in a.get("supersedes") or []:
            if sup not in ids:
                warnings.append(f"articles[{i}] ({a.get('article_id','?')}): supersedes unknown article_id {sup!r}")

    if not doc.get("required_topics"):
        warnings.append("no required_topics provided -> coverage-gap (missing) detection disabled")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "kb_export_example.json"
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
