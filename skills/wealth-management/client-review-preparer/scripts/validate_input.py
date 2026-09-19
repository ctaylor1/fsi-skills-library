#!/usr/bin/env python3
"""Deterministic input validation for client-review-preparer.

Validates a client-review intake file before a review pack (brief, agenda, deck outline) is
drafted. Fails closed on structural problems (so a pack is never assembled from an ill-formed
record); warns on data gaps that force a `needs-data`, `unresolved-entity`,
`account-identity-gap`, `unsupported-content`, `stale-source`, `tieout-break`, or
`disclosure-gap` status downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version?, as_of_date, freshness_days?, critical_freshness_days?,
  disclosure_config?{review_type: [disclosure_id...]}, reviews[
    {client_id, household_name, advisor, review_type(annual|semiannual|ad-hoc),
     entity_resolved(bool), flags?{recommendation_contemplated,senior_investor,drift_flag},
     accounts[{account_id, type, registration, reported_value, source_id}],
     household_reported_value?,
     sources[{source_id, system, ref, date, classification?, stale_ack?}],
     holdings[{account_id, security, asset_class?, market_value, source_id}],
     performance?[{scope, period, return_pct, benchmark_pct?, source_id}],
     goals[{goal, target?, target_date?, source_id}],
     plan_items?[{item, status?, source_id}],
     prior_notes?[{note, date?, source_id}],
     service_history?[{case_ref, summary, status, source_id}],
     life_events?[{event, date?, source_id}],
     open_actions?[{action, owner?, due_date?, status, source_id}],
     discussion_questions?[{question, source_id}],
     disclosures?[{disclosure_id, source_id}]}]

Usage: python validate_input.py reviews.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("as_of_date", "reviews", "request_id", "config_version", "template_version", "template_contract", "author_id", "engagement", "disclosure_config")
REQUIRED_REVIEW = ("client_id", "household_name")  # structural; error if missing
REVIEW_TYPES = {"annual", "semiannual", "ad-hoc"}
# (list_key, label, text_field) -- content lists that must cite a source in the inventory
CONTENT_SPEC = [
    ("holdings", "holding", "security"),
    ("performance", "performance row", "period"),
    ("goals", "goal", "goal"),
    ("plan_items", "plan item", "item"),
    ("prior_notes", "prior note", "note"),
    ("service_history", "service case", "case_ref"),
    ("life_events", "life event", "event"),
    ("open_actions", "open action", "action"),
    ("discussion_questions", "discussion question", "question"),
    ("disclosures", "disclosure", "disclosure_id"),
]


def _is_iso_date(v) -> bool:
    try:
        return isinstance(v, str) and len(v) == 10 and date.fromisoformat(v).isoformat() == v
    except Exception:
        return False


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, "", {}, []):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")
    engagement = doc.get("engagement")
    if not isinstance(engagement, dict) or not isinstance(engagement.get("capacity"), str) or engagement.get("capacity") not in {"advisory", "brokerage", "private-bank", "trust"} or engagement.get("jurisdiction") != "US":
        errors.append("engagement requires an explicit supported capacity and US jurisdiction")
        engagement = {}
    config = doc.get("disclosure_config")
    if not isinstance(config, dict) or config.get("capacity") != (engagement or {}).get("capacity") or config.get("version") != doc.get("config_version"):
        errors.append("disclosure_config must match the engagement capacity and config_version")
    elif not isinstance(config.get("by_review_type"), dict):
        errors.append("disclosure_config.by_review_type must be an approved mapping")
    elif not all(config.get(k) for k in ("owner", "approved_by", "valid_until")) or not _is_iso_date(config.get("valid_until")) or config["valid_until"] < doc["as_of_date"]:
        errors.append("disclosure_config needs owner, approved_by, and an unexpired valid_until")
    elif not isinstance(config.get("required_roles"), list) or not config["required_roles"] or not all(isinstance(role, str) and role.strip() for role in config["required_roles"]):
        errors.append("disclosure_config.required_roles must record the approved human review roles")
    template = doc.get("template_contract")
    if not isinstance(template, dict) or template.get("version") != doc["template_version"] or not all(template.get(k) for k in ("owner", "approved_by")) or not _is_iso_date(template.get("valid_until")) or template["valid_until"] < doc["as_of_date"]:
        errors.append("template_contract needs matching version, owner, approved_by, and unexpired valid_until")
    for key in ("freshness_days", "critical_freshness_days"):
        value = doc.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{key} must be an explicit nonnegative integer")
    if errors:
        return errors, warnings

    reviews = doc.get("reviews") or []
    if not isinstance(reviews, list) or not reviews:
        errors.append("reviews must be a non-empty list")
        return errors, warnings

    ids, review_ids = set(), set()
    for i, r in enumerate(reviews):
        if not isinstance(r, dict):
            errors.append(f"reviews[{i}] must be an object")
            continue
        tag = f"reviews[{i}] ({r.get('client_id','?')})"
        for k in REQUIRED_REVIEW:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = r.get("client_id")
        if not isinstance(cid, str) or not cid.strip():
            errors.append(f"{tag}: client_id must be a nonempty string")
            continue
        if cid in ids:
            errors.append(f"{tag}: duplicate client_id")
        ids.add(cid)
        rid = r.get("review_id")
        if not isinstance(rid, str) or not rid.strip() or rid in review_ids:
            errors.append(f"{tag}: review_id must be present and unique")
        if isinstance(rid, str):
            review_ids.add(rid)

        rt = r.get("review_type")
        if not isinstance(rt, str) or rt not in REVIEW_TYPES:
            errors.append(f"{tag}: unsupported review_type {rt!r}")
        required = config.get("by_review_type", {}).get(rt) if isinstance(rt, str) else None
        if not isinstance(required, list) or not all(isinstance(x, str) and x for x in required):
            errors.append(f"{tag}: no approved disclosure requirements for this review type")
        if not isinstance(r.get("entity_resolved"), bool):
            errors.append(f"{tag}: entity_resolved must be boolean")
        for list_key in ("accounts", "sources") + tuple(k for k, _, _ in CONTENT_SPEC):
            value = r.get(list_key, [])
            if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
                errors.append(f"{tag}: {list_key} must be a list of objects")
        if errors:
            continue

        # source inventory (structural)
        sources = r.get("sources") or []
        if not isinstance(sources, list):
            errors.append(f"{tag}: sources must be a list")
            sources = []
        source_ids = set()
        for j, s in enumerate(sources):
            if not s.get("source_id") or not s.get("system") or not s.get("ref"):
                errors.append(f"{tag}: sources[{j}] needs source_id, system, and ref")
            if not isinstance(s.get("source_id"), str):
                errors.append(f"{tag}: source_id must be a string")
                continue
            if s.get("source_id") in source_ids:
                errors.append(f"{tag}: duplicate source_id")
            if not s.get("owner"):
                errors.append(f"{tag}: sources[{j}] needs an accountable owner")
            if not _is_iso_date(s.get("date")) or not _is_iso_date(s.get("valid_until")):
                errors.append(f"{tag}: sources[{j}] date and valid_until are required ISO dates")
            elif not s["date"] <= doc["as_of_date"] <= s["valid_until"]:
                errors.append(f"{tag}: sources[{j}] is future-dated or expired")
            if s.get("stale_ack") and not (s.get("stale_ack_by") and s.get("stale_ack_reason")):
                errors.append(f"{tag}: stale acknowledgement needs reviewer and reason")
            source_ids.add(s.get("source_id"))

        # account inventory: identity fields + numeric reported_value (structural numeric)
        account_ids = set()
        accounts = r.get("accounts") or []
        for k, a in enumerate(accounts):
            aid = a.get("account_id")
            if not isinstance(aid, str):
                errors.append(f"{tag}: account_id must be a string")
                continue
            if not aid or aid in account_ids:
                errors.append(f"{tag}: account_id must be present and unique")
            account_ids.add(aid)
            if not _is_number(a.get("reported_value")):
                errors.append(f"{tag}: accounts[{k}].reported_value must be a number")
            if not a.get("type") or not a.get("registration"):
                warnings.append(f"{tag}: accounts[{k}] ({aid}) missing type/registration -> account-identity-gap")

        # content-required gaps are WARNINGS -> drive statuses downstream, not input errors
        if not r.get("advisor"):
            warnings.append(f"{tag}: missing 'advisor' -> needs-data")
        if not accounts:
            warnings.append(f"{tag}: no accounts -> needs-data")
        if not r.get("goals"):
            warnings.append(f"{tag}: no goals -> needs-data")
        if "entity_resolved" not in r:
            warnings.append(f"{tag}: entity_resolved not set -> unresolved-entity")
        elif not r.get("entity_resolved"):
            warnings.append(f"{tag}: entity_resolved is false -> unresolved-entity (do not guess identity)")

        # holdings numerics are structural
        for k, h in enumerate(r.get("holdings") or []):
            if not _is_number(h.get("market_value")):
                errors.append(f"{tag}: holdings[{k}].market_value must be a number")
            if h.get("account_id") not in account_ids:
                warnings.append(f"{tag}: holdings[{k}] references unknown account {h.get('account_id')!r} -> account-identity-gap")

        # performance scope must be a known account or 'household'
        for k, p in enumerate(r.get("performance") or []):
            if not _is_number(p.get("return_pct")) or not p.get("period"):
                errors.append(f"{tag}: performance[{k}] needs a finite return_pct and period")
            if p.get("benchmark_pct") is not None and not _is_number(p["benchmark_pct"]):
                errors.append(f"{tag}: performance[{k}] benchmark_pct must be finite")
            scope = p.get("scope")
            if scope != "household" and scope not in account_ids:
                warnings.append(f"{tag}: performance[{k}] scope {scope!r} not a known account/household -> account-identity-gap")

        # every content item should cite a source in the inventory
        for list_key, label, text_field in CONTENT_SPEC:
            for k, item in enumerate(r.get(list_key) or []):
                if not isinstance(item.get(text_field), str) or not item[text_field].strip():
                    errors.append(f"{tag}: {label}[{k}] needs substantive {text_field}")
                sid = item.get("source_id")
                if not sid:
                    warnings.append(f"{tag}: {label}[{k}] has no source_id -> unsupported-content")
                elif sid not in source_ids:
                    warnings.append(f"{tag}: {label}[{k}] cites source {sid!r} not in inventory -> unsupported-content")

        for k, a in enumerate(r.get("open_actions") or []):
            if not a.get("owner") or not a.get("due_date") or a.get("status") not in {"open", "closed", "cancelled"}:
                errors.append(f"{tag}: open_actions[{k}] needs owner, due_date and supported status")
            if a.get("due_date") and not _is_iso_date(a.get("due_date")):
                errors.append(f"{tag}: open_actions[{k}] due_date is not an ISO date")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reviews_example.json"
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
