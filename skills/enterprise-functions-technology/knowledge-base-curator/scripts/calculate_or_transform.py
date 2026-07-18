#!/usr/bin/env python3
"""Deterministic knowledge-base curation engine for knowledge-base-curator.

Takes a validated KB export and assembles a template-faithful DRAFT curation worklist:
  1. Classify each article by documented precedence
     (conflicting > retire > duplicate > stale > ownerless > current) with a severity and a
     draft-only proposal.
  2. Detect coverage gaps: required topics with no active (non-retired) article -> `missing`.
  3. Build the approvals register: every recommended change (action != none) is recorded
     `pending` with its approver role. No change is presented as applied or approved.
  4. Resolve each finding's supporting source_ids; record any that do not resolve as an
     unsupported claim.
  5. Emit the assembled pack, sources register, approvals, completeness, unsupported claims,
     and a standing DRAFT note.

This script NEVER publishes, edits, merges, retires, or deletes an article, NEVER writes a
system of record, and NEVER marks a change approved on its own.

Usage: python calculate_or_transform.py kb_export.json | --selftest
Prints the assembled curation pack JSON to stdout.
"""
from __future__ import annotations
import json, re, sys
from datetime import date
from pathlib import Path

DEFAULT_REVIEW_DAYS = 365
DEFAULT_HIGH_RISK_TAGS = ("compliance", "regulatory", "privacy")
REQUIRED_SECTIONS = ("cover", "summary", "findings", "retirements", "gaps")
ACTION_BY_FINDING = {
    "conflicting": "reconcile", "retire": "retire", "duplicate": "merge",
    "stale": "review-update", "ownerless": "assign-owner", "missing": "create",
    "current": "none",
}
BASE_SEVERITY = {
    "conflicting": "High", "missing": "High", "retire": "Medium", "duplicate": "Medium",
    "stale": "Medium", "ownerless": "Medium", "current": "Low",
}
APPROVER_ROLE = {
    "reconcile": "Content owner (SME)", "review-update": "Content owner",
    "merge": "Content owner", "assign-owner": "Knowledge governance",
    "retire": "Records / retention owner", "create": "Knowledge governance",
}
STANDING_NOTE = ("DRAFT knowledge-base curation worklist for human review; nothing has been "
                 "published, updated, merged, retired, or deleted, and no change has been "
                 "approved by this skill.")


def _d(s):
    try:
        return date.fromisoformat(str(s))
    except (ValueError, TypeError):
        return None


def _norm_title(t):
    return re.sub(r"\s+", " ", str(t or "").strip().lower())


def _citation(src):
    return f"{src.get('system','?')}:{src.get('ref','?')}@{src.get('as_of','?')}"


def _effective_review_days(a, doc):
    for v in (a.get("review_period_days"), (doc.get("policy") or {}).get("review_period_days"),
              doc.get("review_period_days")):
        if isinstance(v, int) and v > 0:
            return v
    return DEFAULT_REVIEW_DAYS


def _retire_reason(a, superseded_by):
    exp = _d(a.get("expiry_date"))
    if superseded_by:
        return f"superseded by {superseded_by}"
    if exp:
        return f"expired {a.get('expiry_date')}"
    return "flagged for retirement"


def classify(doc: dict):
    as_of = _d(doc.get("as_of"))
    index = {s.get("source_id"): s for s in doc.get("sources") or []}
    articles = doc.get("articles") or []
    high_risk = set((doc.get("policy") or {}).get("high_risk_tags") or DEFAULT_HIGH_RISK_TAGS)

    # supersede map: article -> the id that supersedes it
    superseded_by = {}
    for a in articles:
        for sup in a.get("supersedes") or []:
            superseded_by[sup] = a.get("article_id")

    def is_expired(a):
        exp = _d(a.get("expiry_date"))
        return bool(exp and as_of and exp <= as_of)

    to_retire = {a.get("article_id") for a in articles
                 if is_expired(a) or a.get("article_id") in superseded_by
                 or str(a.get("status", "")).lower() == "retired"}

    actives = [a for a in articles if a.get("article_id") not in to_retire]

    # duplicate groups among actives (by content_hash and by normalized title)
    hash_groups, title_groups = {}, {}
    for a in actives:
        if a.get("content_hash"):
            hash_groups.setdefault(a["content_hash"], []).append(a.get("article_id"))
        title_groups.setdefault(_norm_title(a.get("title")), []).append(a.get("article_id"))

    def dup_canonical(a):
        aid = a.get("article_id")
        group = None
        if a.get("content_hash") and len(hash_groups.get(a["content_hash"], [])) > 1:
            group = hash_groups[a["content_hash"]]
        else:
            tg = title_groups.get(_norm_title(a.get("title")), [])
            if len(tg) > 1:
                group = tg
        if not group:
            return None
        canonical = sorted(group)[0]
        return None if aid == canonical else canonical

    # topic -> active articles (for same-topic conflict detection)
    topic_actives = {}
    for a in actives:
        if a.get("topic_id"):
            topic_actives.setdefault(a["topic_id"], []).append(a)

    def source_conflict(a):
        my = a.get("asserts") or {}
        if not my:
            return None
        for sid in a.get("source_ids") or []:
            src = index.get(sid)
            if not src:
                continue
            sa = src.get("asserts") or {}
            for k, v in my.items():
                if k in sa and sa[k] != v:
                    return {"key": k, "article_value": v, "source_value": sa[k],
                            "source_id": sid, "citation": _citation(src)}
        return None

    def topic_conflict(a):
        my = a.get("asserts") or {}
        if not my or not a.get("topic_id"):
            return None
        for other in topic_actives.get(a["topic_id"], []):
            if other.get("article_id") == a.get("article_id"):
                continue
            oa = other.get("asserts") or {}
            for k, v in my.items():
                if k in oa and oa[k] != v:
                    return {"key": k, "article_value": v,
                            "other_article": other.get("article_id"), "other_value": oa[k]}
        return None

    def is_stale(a):
        lr = _d(a.get("last_reviewed"))
        if not a.get("last_reviewed"):
            return True, "no last_reviewed date (data gap)"
        if lr and as_of and (as_of - lr).days > _effective_review_days(a, doc):
            return True, f"last_reviewed {a.get('last_reviewed')} older than {_effective_review_days(a, doc)}d review period"
        for sid in a.get("source_ids") or []:
            src = index.get(sid)
            sa = _d((src or {}).get("as_of"))
            if lr and sa and sa > lr:
                return True, f"source {sid} updated {src.get('as_of')} after last_reviewed {a.get('last_reviewed')}"
        return False, ""

    findings, unsupported = [], []

    for a in articles:
        aid = a.get("article_id")
        cites = [f"kb:{aid}@{a.get('last_reviewed','?')}"]
        proposal, rationale, finding = {}, "", "current"

        # resolve supporting sources; record unresolved as unsupported
        for sid in a.get("source_ids") or []:
            src = index.get(sid)
            if src is None:
                unsupported.append({"kind": "article", "id": aid, "source_id": sid,
                                    "reason": "source_id not in approved source register"})
            else:
                cites.append(_citation(src))

        if aid in to_retire:
            finding = "retire"
            reason = _retire_reason(a, superseded_by.get(aid))
            rationale = f"retire: {reason}"
            proposal = {"reason": reason}
        else:
            sc = source_conflict(a)
            tc = topic_conflict(a)
            dup = dup_canonical(a)
            stale, stale_reason = is_stale(a)
            if sc:
                finding = "conflicting"
                rationale = (f"article asserts {sc['key']}={sc['article_value']!r} but source "
                             f"{sc['source_id']} asserts {sc['source_value']!r}")
                proposal = {"conflict": sc}
            elif tc:
                finding = "conflicting"
                rationale = (f"article asserts {tc['key']}={tc['article_value']!r} but "
                             f"{tc['other_article']} asserts {tc['other_value']!r}")
                proposal = {"conflict": tc}
            elif dup:
                finding = "duplicate"
                rationale = f"shares content with canonical {dup}"
                proposal = {"canonical_article_id": dup}
            elif stale:
                finding = "stale"
                rationale = stale_reason
                proposal = {"proposed_review_date": doc.get("as_of")}
            elif not a.get("owner"):
                finding = "ownerless"
                rationale = "no owner assigned"
                proposal = {"proposed_owner_role": "Knowledge governance"}
            else:
                finding = "current"
                rationale = "current: within review period, owned, no conflict or duplicate"

        severity = BASE_SEVERITY[finding]
        if finding == "stale" and (set(a.get("tags") or []) & high_risk):
            severity = "High"

        action = ACTION_BY_FINDING[finding]
        findings.append({
            "article_id": aid, "title": a.get("title"), "topic_id": a.get("topic_id"),
            "finding": finding, "severity": severity, "recommended_action": action,
            "rationale": rationale, "proposal": proposal, "citations": cites,
            "requires_approval": action != "none",
        })

    # coverage gaps: required topics with no active article
    covered = {a.get("topic_id") for a in actives if a.get("topic_id")}
    gaps = []
    for t in doc.get("required_topics") or []:
        if t.get("required") and t.get("topic_id") not in covered:
            gaps.append({
                "topic_id": t.get("topic_id"), "title": t.get("title"),
                "finding": "missing", "severity": "High", "recommended_action": "create",
                "rationale": "required topic has no active article",
                "proposal": {"proposed_owner_role": t.get("owner_role") or "Knowledge governance"},
                "citations": [f"topic-registry:{t.get('topic_id')}@{doc.get('config_version','?')}"],
                "requires_approval": True,
            })

    retirements = [f for f in findings if f["finding"] == "retire"]

    # approvals register: every recommended change (action != none)
    approvals = []
    for f in findings + gaps:
        if f["recommended_action"] == "none":
            continue
        role = APPROVER_ROLE.get(f["recommended_action"], "Knowledge governance")
        if f["recommended_action"] == "create":
            role = f.get("proposal", {}).get("proposed_owner_role") or "Knowledge governance"
        approvals.append({
            "ref_id": f.get("article_id") or f.get("topic_id"),
            "finding": f["finding"], "recommended_action": f["recommended_action"],
            "approver_role": role, "approver": "", "status": "pending", "date": None,
        })

    summary = {
        "total_articles": len(findings),
        "by_finding": {k: sum(1 for f in findings if f["finding"] == k)
                       for k in ("conflicting", "retire", "duplicate", "stale", "ownerless", "current")},
        "missing_topics": len(gaps),
        "by_severity": {sev: sum(1 for f in findings + gaps if f["severity"] == sev)
                        for sev in ("High", "Medium", "Low")},
        "changes_pending_approval": len(approvals),
    }

    sections = {
        "cover": {"scope": doc.get("scope") or "knowledge base", "as_of": doc.get("as_of"),
                  "config_version": doc.get("config_version"),
                  "classification": doc.get("classification") or "Confidential",
                  "curator": doc.get("curator") or ""},
        "summary": summary,
        "findings": findings,
        "retirements": retirements,
        "gaps": gaps,
    }
    present = [k for k in REQUIRED_SECTIONS if sections.get(k) not in (None,)]
    # non-empty requirement only for cover/summary/findings
    missing_sections = [k for k in ("cover", "summary", "findings") if not sections.get(k)]

    return {
        "pack_id": doc.get("pack_id") or f"KBC-{doc.get('as_of','')}",
        "config_version": doc.get("config_version"),
        "as_of": doc.get("as_of"),
        "status": "draft",
        "sections": sections,
        "sources": doc.get("sources") or [],
        "approvals": approvals,
        "completeness": {"required": list(REQUIRED_SECTIONS), "present": present,
                         "missing": missing_sections},
        "unsupported_claims": unsupported,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "kb_export_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(classify(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
