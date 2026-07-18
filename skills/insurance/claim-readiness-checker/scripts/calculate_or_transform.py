#!/usr/bin/env python3
"""Deterministic, explainable claim-readiness computation for claim-readiness-checker.

Reads a claim readiness file (see validate_input.py), runs the configured completeness,
form-validity, field-completeness, chronology, and deadline checks, attaches evidence +
citations for the items it inspected, records gaps, and maps the gap profile to a
readiness status band. Emits a machine-readable core the SKILL wraps in a plain-language
readiness assessment.

IMPORTANT: This produces an explainable *readiness / completeness assessment* only. It
never makes a coverage, eligibility, settlement, or fraud determination and never
adjudicates, approves, denies, or pays a claim. The status mapping is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py claim.json | --selftest
Prints the readiness JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

# Required-item catalog and thresholds. In production these come from a versioned,
# owned config (underwriting/claims standards), never tuned to an individual claim.
DEFAULT_CONFIG = {
    "at_risk_days": 7,
    "requirements": {
        "auto_collision": {
            "documents": [
                {"type": "proof_of_loss", "blocking": True},
                {"type": "repair_estimate", "blocking": True},
                {"type": "police_report", "blocking": False},
                {"type": "photos", "blocking": False},
            ],
            "forms": [
                {"type": "acord_claim_form", "blocking": True,
                 "accepted_versions": ["ACORD-1-2025", "ACORD-1-2024"]},
            ],
            "fields": ["claimant_name", "loss_description", "amount_claimed"],
        },
        "property_damage": {
            "documents": [
                {"type": "proof_of_loss", "blocking": True},
                {"type": "damage_inventory", "blocking": True},
                {"type": "photos", "blocking": False},
                {"type": "repair_estimate", "blocking": False},
            ],
            "forms": [
                {"type": "acord_claim_form", "blocking": True,
                 "accepted_versions": ["ACORD-1-2025", "ACORD-1-2024"]},
            ],
            "fields": ["claimant_name", "loss_description", "amount_claimed"],
        },
        "default": {
            "documents": [
                {"type": "proof_of_loss", "blocking": True},
            ],
            "forms": [
                {"type": "acord_claim_form", "blocking": True,
                 "accepted_versions": ["ACORD-1-2025"]},
            ],
            "fields": ["claimant_name", "loss_description", "amount_claimed"],
        },
    },
}
DISCLAIMER = ("Readiness and completeness check only; not a coverage, eligibility, or "
              "claim decision. No claim has been adjudicated, approved, denied, or paid.")


def _parse(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _cite(doc):
    return f"dms:{doc.get('source_ref', '?')}"


def _docs_by_type(documents):
    idx = {}
    for d in documents:
        idx.setdefault(str(d.get("type")), []).append(d)
    return idx


def _present(docs):
    return [d for d in docs if str(d.get("status")) == "present"]


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    req_map = cfg.get("requirements") or DEFAULT_CONFIG["requirements"]
    at_risk_days = cfg.get("at_risk_days", 7)
    claim_type = str(doc.get("claim_type", "default"))
    reqs = req_map.get(claim_type) or req_map.get("default")

    documents = doc.get("documents") or []
    idx = _docs_by_type(documents)
    dates = doc.get("dates") or {}
    fields = doc.get("fields") or {}
    as_of = _parse(doc.get("as_of"))

    checks, gaps, not_evaluable = [], [], []

    def add_gap(item, category, blocking, detail, citation=None):
        gaps.append({"item": item, "category": category, "blocking": bool(blocking),
                     "detail": detail, "citation": citation})

    # 1. Required documents present
    doc_evidence, doc_missing = [], []
    for r in reqs.get("documents", []):
        t = r["type"]
        present = _present(idx.get(t, []))
        if present:
            doc_evidence.append({"type": t, "doc_id": present[0].get("doc_id"),
                                 "citation": _cite(present[0])})
        else:
            statuses = [str(d.get("status")) for d in idx.get(t, [])] or ["absent"]
            add_gap(t, "required_document", r.get("blocking", False),
                    f"required document '{t}' not present (status: {', '.join(statuses)})")
            doc_missing.append(t)
    checks.append({"check": "required_documents_present",
                   "status": "gap" if doc_missing else "ok",
                   "detail": f"{len(doc_evidence)} of {len(reqs.get('documents', []))} required documents present",
                   "evidence": doc_evidence})

    # 2. Required forms valid (present + signed + accepted version)
    form_evidence, form_issue = [], False
    for r in reqs.get("forms", []):
        t = r["type"]
        present = _present(idx.get(t, []))
        if not present:
            add_gap(t, "required_form", r.get("blocking", False),
                    f"required form '{t}' not present")
            form_issue = True
            continue
        f = present[0]
        problems = []
        if not f.get("signed"):
            problems.append("unsigned")
        accepted = r.get("accepted_versions")
        if accepted and f.get("form_version") not in accepted:
            problems.append(f"version {f.get('form_version')!r} not in accepted {accepted}")
        if problems:
            add_gap(t, "required_form", r.get("blocking", False),
                    f"form '{t}' present but invalid: {'; '.join(problems)}", _cite(f))
            form_issue = True
        else:
            form_evidence.append({"type": t, "doc_id": f.get("doc_id"),
                                  "version": f.get("form_version"), "citation": _cite(f)})
    checks.append({"check": "required_forms_valid",
                   "status": "gap" if form_issue else "ok",
                   "detail": f"{len(form_evidence)} required form(s) present, signed, and accepted version",
                   "evidence": form_evidence})

    # 3. Required fields complete
    missing_fields = [k for k in reqs.get("fields", [])
                      if fields.get(k) in (None, "", [])]
    for k in missing_fields:
        add_gap(k, "required_field", True, f"required claim field '{k}' is missing or empty")
    checks.append({"check": "required_fields_complete",
                   "status": "gap" if missing_fields else "ok",
                   "detail": f"{len(reqs.get('fields', [])) - len(missing_fields)} of {len(reqs.get('fields', []))} required fields present",
                   "evidence": []})

    # 4. Chronology consistent
    dol = _parse(dates.get("date_of_loss"))
    dr = _parse(dates.get("date_reported"))
    dp = _parse(dates.get("date_prepared")) or as_of
    peff = _parse(dates.get("policy_effective"))
    pexp = _parse(dates.get("policy_expiration"))
    chrono_issues, chrono_checked = [], []
    if dol and peff and pexp:
        chrono_checked.append("loss within policy period")
        if not (peff <= dol <= pexp):
            chrono_issues.append(
                f"date_of_loss {dol} is outside policy period {peff}..{pexp}")
    else:
        not_evaluable.append({"check": "chronology_loss_in_period",
                              "why": "missing policy_effective/expiration or date_of_loss"})
    if dol and dr:
        chrono_checked.append("loss on/before reported")
        if dol > dr:
            chrono_issues.append(f"date_of_loss {dol} is after date_reported {dr}")
    if dr and dp:
        chrono_checked.append("reported on/before prepared")
        if dr > dp:
            chrono_issues.append(f"date_reported {dr} is after date_prepared {dp}")
    for issue in chrono_issues:
        add_gap("chronology", "chronology", True, issue)
    checks.append({"check": "chronology_consistent",
                   "status": "gap" if chrono_issues else ("ok" if chrono_checked else "not_evaluable"),
                   "detail": ("consistent: " + "; ".join(chrono_checked)) if not chrono_issues
                             else "; ".join(chrono_issues),
                   "evidence": []})

    # 5. Deadlines status (timeliness)
    deadlines = doc.get("deadlines") or []
    deadline_ev, missed, at_risk = [], [], []
    if not deadlines:
        not_evaluable.append({"check": "deadlines_status", "why": "no deadlines provided"})
    for d in deadlines:
        due = _parse(d.get("due_date"))
        if not due or not as_of:
            not_evaluable.append({"check": "deadlines_status",
                                  "why": f"deadline {d.get('name')!r} has no parseable due_date/as_of"})
            continue
        days = (due - as_of).days
        row = {"name": d.get("name"), "due_date": d.get("due_date"),
               "days_remaining": days, "hard": bool(d.get("hard")),
               "citation": d.get("source_ref") or f"policy:deadline={d.get('name')}@{d.get('due_date')}"}
        deadline_ev.append(row)
        if days < 0 and d.get("hard"):
            add_gap(d.get("name"), "deadline", True,
                    f"hard deadline '{d.get('name')}' passed {abs(days)} day(s) ago (due {d.get('due_date')})")
            missed.append(d.get("name"))
        elif days < 0:
            add_gap(d.get("name"), "deadline", False,
                    f"soft deadline '{d.get('name')}' passed {abs(days)} day(s) ago (due {d.get('due_date')})")
            at_risk.append(d.get("name"))
        elif 0 <= days <= at_risk_days:
            add_gap(d.get("name"), "deadline", False,
                    f"deadline '{d.get('name')}' due in {days} day(s) (<= {at_risk_days}-day at-risk window)")
            at_risk.append(d.get("name"))
    checks.append({"check": "deadlines_status",
                   "status": "gap" if (missed or at_risk) else ("ok" if deadline_ev else "not_evaluable"),
                   "detail": f"{len(missed)} missed hard, {len(at_risk)} at-risk of {len(deadline_ev)} deadline(s)",
                   "evidence": deadline_ev})

    # Deterministic readiness mapping (see references/domain-rules.md)
    blocking_gaps = [g["item"] for g in gaps if g["blocking"]]
    if blocking_gaps:
        status = "Not ready"
    elif gaps:
        status = "Ready with minor gaps"
    else:
        status = "Ready"

    considerations = []
    if gaps:
        considerations = [
            "Readiness reflects document/form presence, field completeness, chronology, and timeliness only, not whether the loss is covered or excluded.",
            "A coverage, eligibility, or settlement determination is the adjuster's and insurer's decision, made from the policy and facts.",
            "Confirm the policy is in force and check endorsements, limits, and deductibles against the system of record.",
            "Obtain or re-request any missing or illegible required items before submission.",
            "Verify each deadline against the controlling policy and jurisdiction; do not rely on this list alone.",
        ]

    return {
        "readiness_id": f"crc-{doc.get('claim_id')}-{doc.get('as_of')}-0001",
        "claim_id": doc.get("claim_id"),
        "policy_number": doc.get("policy_number"),
        "claim_type": claim_type,
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "checks": checks,
        "gaps": gaps,
        "blocking_gaps": blocking_gaps,
        "not_evaluable": not_evaluable,
        "readiness_status": status,
        "considerations": considerations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
