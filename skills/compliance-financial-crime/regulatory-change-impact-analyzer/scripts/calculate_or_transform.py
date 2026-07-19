#!/usr/bin/env python3
"""Deterministic regulatory-change impact analysis for regulatory-change-impact-analyzer.

Reads a regulatory-change assessment file (see validate_input.py), extracts the obligations,
tests each obligation's applicability to the firm, maps applicable obligations to the
policy / control / system / data / training / owner inventory, checks effective-date
integrity and lead time, flags authority conflicts, and maps the raised findings to a
recommended DISPOSITION band. Emits a machine-readable core the SKILL wraps in a
plain-language impact assessment.

IMPORTANT: This produces explainable *findings, cited evidence, and a triage
recommendation* only. It never makes a compliance determination, decides applicability,
closes a change item, files with a regulator, or attests. The disposition mapping is
deterministic and documented in references/domain-rules.md; every disposition requires
mandatory human adjudication (R3).

Usage:
  python calculate_or_transform.py change.json | --selftest
Prints the impact-assessment JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "near_term_days": 30,      # lead time strictly below this raises short_lead_time
    "require_policy": True,    # applicable obligation must map to >=1 policy
    "require_control": True,   # applicable obligation must map to >=1 control
    "require_owner": True,     # applicable obligation must have a named owner
}
DISCLAIMER = ("Impact assessment and evidence only; not a compliance determination. "
              "Applicability, disposition, and closure require human adjudication. No "
              "regulatory decision, filing, or system-of-record change has been made.")
ESCALATORS = {"overdue_or_retroactive", "authority_conflict"}


def _parse_date(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(instrument, ref=None):
    r = ref or instrument.get("source_ref", "?")
    return f"reg:{r}@{instrument.get('effective_date', '?')}"


def _applies(obl, instrument, firm):
    """An obligation applies when the instrument jurisdiction is one the firm operates in
    AND the obligation's business-line scope overlaps the firm (or is firm-wide)."""
    firm_juris = {str(j).upper() for j in firm.get("jurisdictions", [])}
    inst_juris = str(instrument.get("jurisdiction", "")).upper()
    juris_ok = inst_juris in firm_juris if firm_juris else False
    lines = [str(x).lower() for x in (obl.get("applies_to_lines") or [])]
    firm_lines = {str(x).lower() for x in firm.get("business_lines", [])}
    firm_wide = (not lines) or ("all" in lines)
    line_ok = firm_wide or bool(set(lines) & firm_lines)
    return juris_ok and line_ok, {"instrument_jurisdiction": inst_juris,
                                  "firm_jurisdictions": sorted(firm_juris),
                                  "obligation_lines": lines, "firm_wide": firm_wide}


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    instrument = doc["instrument"]
    obligations = doc["obligations"]
    firm = doc.get("firm_profile") or {}
    mappings = {m["obligation_id"]: m for m in (doc.get("inventory") or {}).get("mappings", [])}
    as_of = _parse_date(doc["as_of"])
    eff = _parse_date(instrument["effective_date"])
    pub = _parse_date(instrument["publication_date"]) if instrument.get("publication_date") else None
    lead_days = (eff - as_of).days

    findings, not_evaluable = [], []

    def add(name, raised, reason, evidence, basis, count):
        findings.append({"finding": name, "raised": raised, "reason": reason,
                         "evidence": evidence, "basis": basis, "count": count})

    # applicability of each obligation
    applicable, applicability_rows = [], []
    for o in obligations:
        ok, basis = _applies(o, instrument, firm)
        applicability_rows.append({"obligation_id": o["obligation_id"], "applicable": ok, "basis": basis})
        if ok:
            applicable.append(o)

    # applicable_in_scope
    add("applicable_in_scope", bool(applicable),
        f"{len(applicable)} of {len(obligations)} obligation(s) apply to the firm (jurisdiction + business-line scope)"
        if applicable else "no obligation applies to the firm on jurisdiction/business-line scope (confirm rationale with a human)",
        [{"obligation_id": o["obligation_id"], "obligation_type": o.get("obligation_type"),
          "citation": _cite(instrument, o.get("source_ref"))} for o in applicable],
        {"applicable": len(applicable), "total": len(obligations)}, len(applicable))

    # mapping_gap (policy/control coverage) over applicable obligations only
    gap_rows = []
    for o in applicable:
        m = mappings.get(o["obligation_id"], {})
        missing = []
        if cfg["require_policy"] and not (m.get("policies") or []):
            missing.append("policy")
        if cfg["require_control"] and not (m.get("controls") or []):
            missing.append("control")
        if missing:
            gap_rows.append({"obligation_id": o["obligation_id"], "missing": missing,
                             "citation": _cite(instrument, o.get("source_ref"))})
    add("mapping_gap", bool(gap_rows),
        f"{len(gap_rows)} applicable obligation(s) lack policy/control coverage in the inventory"
        if gap_rows else "all applicable obligations map to at least one policy and control",
        gap_rows, {"checked": len(applicable)}, len(gap_rows))

    # owner_gap (traceability) over applicable obligations
    owner_rows = []
    if cfg["require_owner"]:
        for o in applicable:
            m = mappings.get(o["obligation_id"], {})
            owner = (m.get("owner") or {}).get("role")
            if not owner:
                owner_rows.append({"obligation_id": o["obligation_id"],
                                   "citation": _cite(instrument, o.get("source_ref"))})
    add("owner_gap", bool(owner_rows),
        f"{len(owner_rows)} applicable obligation(s) have no named owner in the inventory"
        if owner_rows else "all applicable obligations have a named owner",
        owner_rows, {"checked": len(applicable)}, len(owner_rows))

    # effective-date integrity / overdue-or-retroactive
    retroactive = bool(pub and eff < pub)
    overdue = eff <= as_of
    od_reason = []
    if overdue:
        od_reason.append(f"effective_date {instrument['effective_date']} is on/before as_of {doc['as_of']} (already effective/overdue)")
    if retroactive:
        od_reason.append(f"effective_date {instrument['effective_date']} precedes publication_date {instrument.get('publication_date')} (retroactive)")
    add("overdue_or_retroactive", overdue or retroactive,
        "; ".join(od_reason) if (overdue or retroactive) else f"effective_date is future ({lead_days}d lead) and not retroactive",
        [{"effective_date": instrument["effective_date"], "publication_date": instrument.get("publication_date"),
          "as_of": doc["as_of"], "citation": _cite(instrument)}] if (overdue or retroactive) else [],
        {"lead_days": lead_days, "overdue": overdue, "retroactive": retroactive},
        1 if (overdue or retroactive) else 0)

    # short_lead_time (only when a future effective date)
    short = (not overdue) and lead_days < cfg["near_term_days"]
    add("short_lead_time", short,
        f"{lead_days}d until effective (below near-term window {cfg['near_term_days']}d)"
        if short else f"lead time {lead_days}d",
        [{"effective_date": instrument["effective_date"], "as_of": doc["as_of"],
          "lead_days": lead_days, "citation": _cite(instrument)}] if short else [],
        {"lead_days": lead_days, "near_term_days": cfg["near_term_days"]}, 1 if short else 0)

    # authority_conflict over applicable obligations that declare conflicts_with
    conflict_rows = []
    for o in applicable:
        cw = o.get("conflicts_with") or []
        if cw:
            conflict_rows.append({"obligation_id": o["obligation_id"], "conflicts_with": cw,
                                  "citation": _cite(instrument, o.get("source_ref"))})
    add("authority_conflict", bool(conflict_rows),
        f"{len(conflict_rows)} applicable obligation(s) declare a conflict with another instrument/jurisdiction (cite both; do not resolve silently)"
        if conflict_rows else "no declared authority conflict on applicable obligations",
        conflict_rows, {"count": len(conflict_rows)}, len(conflict_rows))

    raised = [f["finding"] for f in findings if f["raised"]]

    # deterministic disposition mapping (see references/domain-rules.md)
    if not applicable:
        disposition = "Informational"  # out of scope on the data; human confirms scoping rationale
    elif (ESCALATORS & set(raised)) or len(raised) >= 3:
        disposition = "Priority"
    else:
        disposition = "Assess"

    open_questions = []
    if applicable:
        open_questions = [
            "Confirm the authoritative text and effective date against the primary source before acting.",
            "Confirm business-line applicability and any exemptions with the accountable owner.",
            "For each mapping gap, decide whether a new/updated policy or control is required (route to gap analysis).",
            "For any authority conflict, obtain a legal/compliance reading on which requirement governs.",
            "Record the implementation decision, owner, and target date; a human adjudicates disposition and closure.",
        ]

    return {
        "assessment_id": f"rcia-{str(doc['change_id']).replace('/', '-')}-{doc['as_of']}-0001",
        "change_id": doc["change_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "instrument": {
            "authority": instrument.get("authority"),
            "citation": instrument.get("citation"),
            "authority_level": instrument.get("authority_level"),
            "jurisdiction": instrument.get("jurisdiction"),
            "publication_date": instrument.get("publication_date"),
            "effective_date": instrument.get("effective_date"),
            "lead_days": lead_days,
        },
        "applicability": applicability_rows,
        "findings": findings,
        "raised_findings": raised,
        "not_evaluable": not_evaluable,
        "recommended_disposition": disposition,
        "mandatory_adjudication": True,
        "open_questions": open_questions,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "change_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
