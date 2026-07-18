#!/usr/bin/env python3
"""Deterministic, explainable validation checks for regulatory-reporting-data-validator.

Reads a regulatory-report package (see validate_input.py), runs the configured checks,
attaches evidence + citations to each fired finding, and maps the fired-findings set to a
filing-readiness band. Emits a machine-readable findings pack the SKILL wraps in a
plain-language deliverable.

IMPORTANT: This produces explainable *findings and a readiness band* only. It never makes a
filing determination, certifies/attests accuracy, signs off, files/submits a report, or
posts a GL correction. The band mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py package.json     # prints findings JSON
  python calculate_or_transform.py --selftest        # self-check bundled fixture, prints "N error(s)"
Exit 0 on pass, 1 on --selftest failure.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "variance_pct": 0.20,
    "required_sign_off_roles": ["preparer", "reviewer", "approver"],
    "enforce_segregation_of_duties": True,
    "recon_default_tolerance": 0.0,
    "due_soon_days": 5,
    "range_checks": [],
}
DISCLAIMER = ("Validation findings and cited evidence only; not a filing determination, "
              "certification, or submission. No regulatory report has been certified, "
              "signed off, filed, or submitted.")

# Which checks block filing readiness vs. which are advisory-only. Kept in sync with
# validate_output.py and references/domain-rules.md.
BLOCKING_CHECKS = {
    "completeness", "lineage_completeness", "edit_checks", "reconciliation_tie_out",
    "range_checks", "sign_off_completeness", "segregation_of_duties", "timeliness_overdue",
}
ADVISORY_CHECKS = {"variance_vs_prior", "timeliness_due_soon"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    cells = {c["cell_id"]: c for c in doc["cells"]}
    findings, not_evaluable = [], []

    def add(check, status, reason, evidence, basis):
        findings.append({"check": check, "status": status,
                         "fired": status in ("fail", "warn"),
                         "blocking": check in BLOCKING_CHECKS,
                         "reason": reason, "evidence": evidence, "basis": basis})

    # completeness ---------------------------------------------------------
    required = list(doc.get("required_cells") or [])
    missing = [rc for rc in required
               if rc not in cells or cells[rc].get("value") in (None, "")]
    add("completeness", "fail" if missing else "pass",
        f"{len(missing)} required cell(s) missing/blank" if missing else "all required cells present",
        [{"cell_id": m, "citation": f"required_cells:{m}@{doc['period_end']}"} for m in missing],
        {"required": len(required), "missing": len(missing)})

    # lineage_completeness -------------------------------------------------
    no_lineage = [c["cell_id"] for c in doc["cells"] if not (c.get("source_refs") or [])]
    add("lineage_completeness", "fail" if no_lineage else "pass",
        f"{len(no_lineage)} reported cell(s) lack source lineage" if no_lineage else "all cells have lineage",
        [{"cell_id": cid, "citation": f"cell:{cid}@{doc['period_end']}"} for cid in no_lineage],
        {"cells": len(doc["cells"]), "without_lineage": len(no_lineage)})

    # edit_checks (internal consistency) -----------------------------------
    ec_ev = []
    for ec in doc.get("edit_checks") or []:
        if ec.get("op") != "sum":
            not_evaluable.append({"check": "edit_checks", "id": ec.get("check_id"), "why": f"op {ec.get('op')!r} unsupported"})
            continue
        refs = [ec.get("target")] + list(ec.get("components") or [])
        if any(r not in cells or _num(cells[r].get("value")) is None for r in refs):
            not_evaluable.append({"check": "edit_checks", "id": ec.get("check_id"), "why": "references unknown/non-numeric cell"})
            continue
        target = _num(cells[ec["target"]]["value"])
        comp_sum = sum(_num(cells[c]["value"]) for c in ec["components"])
        tol = _num(ec.get("tolerance", 0.0)) or 0.0
        delta = round(target - comp_sum, 6)
        if abs(delta) > tol:
            ec_ev.append({"check_id": ec["check_id"], "description": ec.get("description"),
                          "target_cell": ec["target"], "reported": target,
                          "expected": comp_sum, "delta": delta, "tolerance": tol,
                          "citation": f"editcheck:{ec['check_id']}@{doc['period_end']}"})
    add("edit_checks", "fail" if ec_ev else "pass",
        f"{len(ec_ev)} edit check(s) do not foot within tolerance" if ec_ev else "all edit checks foot",
        ec_ev, {"evaluated": len(doc.get('edit_checks') or []), "failed": len(ec_ev)})

    # reconciliation_tie_out ----------------------------------------------
    rec_ev = []
    for r in doc.get("reconciliations") or []:
        sv, rv = _num(r.get("source_value")), _num(r.get("reported_value"))
        if sv is None or rv is None:
            not_evaluable.append({"check": "reconciliation_tie_out", "id": r.get("recon_id"), "why": "source unavailable/non-numeric"})
            continue
        tol = _num(r.get("tolerance", cfg["recon_default_tolerance"]))
        tol = cfg["recon_default_tolerance"] if tol is None else tol
        delta = round(rv - sv, 6)
        if abs(delta) > tol:
            rec_ev.append({"recon_id": r["recon_id"], "cell_id": r.get("cell_id"),
                           "source": r.get("source"), "source_value": sv, "reported_value": rv,
                           "delta": delta, "tolerance": tol,
                           "citation": f"recon:{r['recon_id']}@{doc['period_end']}"})
    add("reconciliation_tie_out", "fail" if rec_ev else "pass",
        f"{len(rec_ev)} reconciliation(s) do not tie to source within tolerance" if rec_ev else "all reconciliations tie",
        rec_ev, {"evaluated": len(doc.get('reconciliations') or []), "breaks": len(rec_ev)})

    # range_checks ---------------------------------------------------------
    rng_ev = []
    for rc in cfg.get("range_checks") or []:
        cid = rc.get("cell_id")
        if cid not in cells or _num(cells[cid].get("value")) is None:
            not_evaluable.append({"check": "range_checks", "id": cid, "why": "cell missing/non-numeric"})
            continue
        val = _num(cells[cid]["value"])
        lo, hi = _num(rc.get("min")), _num(rc.get("max"))
        if (lo is not None and val < lo) or (hi is not None and val > hi):
            rng_ev.append({"cell_id": cid, "value": val, "min": lo, "max": hi,
                           "citation": f"cell:{cid}@{doc['period_end']}"})
    add("range_checks", "fail" if rng_ev else "pass",
        f"{len(rng_ev)} cell(s) outside allowed range" if rng_ev else "all configured cells within range",
        rng_ev, {"evaluated": len(cfg.get('range_checks') or []), "out_of_range": len(rng_ev)})

    # sign_off_completeness + segregation_of_duties ------------------------
    sign_offs = doc.get("sign_offs") or []
    by_role = {}
    for s in sign_offs:
        by_role.setdefault(s.get("role"), s)
    required_roles = list(cfg.get("required_sign_off_roles") or [])
    missing_roles = [r for r in required_roles if r not in by_role]
    add("sign_off_completeness", "fail" if missing_roles else "pass",
        f"missing sign-off for role(s): {', '.join(missing_roles)}" if missing_roles else "all required roles signed",
        [{"role": r, "citation": f"signoff:{r}@missing"} for r in missing_roles],
        {"required_roles": required_roles, "missing": missing_roles})

    sod_ev = []
    as_of = _date(doc["as_of"])
    if cfg.get("enforce_segregation_of_duties"):
        prep = (by_role.get("preparer") or {}).get("name")
        appr = (by_role.get("approver") or {}).get("name")
        if prep is not None and appr is not None and prep == appr:
            sod_ev.append({"issue": "preparer is also approver", "name": prep,
                           "citation": f"signoff:preparer+approver@{doc['period_end']}"})
    for s in sign_offs:
        sa = s.get("signed_at")
        if sa and _date(sa) < as_of:
            sod_ev.append({"issue": "sign-off predates data as_of", "role": s.get("role"),
                           "signed_at": sa, "as_of": doc["as_of"],
                           "citation": f"signoff:{s.get('role')}@{sa}"})
    add("segregation_of_duties", "fail" if sod_ev else "pass",
        f"{len(sod_ev)} segregation/timing exception(s)" if sod_ev else "segregation of duties and sign-off timing satisfied",
        sod_ev, {"enforced": bool(cfg.get("enforce_segregation_of_duties"))})

    # timeliness -----------------------------------------------------------
    due = _date(doc["due_date"])
    days_to_due = (due - as_of).days
    if days_to_due < 0:
        add("timeliness_overdue", "fail",
            f"as_of {doc['as_of']} is {-days_to_due} day(s) past due_date {doc['due_date']}",
            [{"due_date": doc["due_date"], "as_of": doc["as_of"], "days_overdue": -days_to_due,
              "citation": f"calendar:{doc['report_code']}@{doc['due_date']}"}],
            {"due_date": doc["due_date"], "as_of": doc["as_of"]})
    elif days_to_due <= cfg["due_soon_days"]:
        add("timeliness_due_soon", "warn",
            f"{days_to_due} day(s) to due_date {doc['due_date']} (<= {cfg['due_soon_days']})",
            [{"due_date": doc["due_date"], "as_of": doc["as_of"], "days_to_due": days_to_due,
              "citation": f"calendar:{doc['report_code']}@{doc['due_date']}"}],
            {"due_soon_days": cfg["due_soon_days"]})

    # variance_vs_prior (advisory) ----------------------------------------
    prior = doc.get("prior_period")
    if prior and prior.get("cells"):
        var_ev = []
        pct = float(cfg["variance_pct"])
        for cid, cur in ((c["cell_id"], _num(c.get("value"))) for c in doc["cells"]):
            if cur is None or cid not in prior["cells"]:
                continue
            pv = _num(prior["cells"][cid])
            if pv is None:
                continue
            change = abs(cur - pv) / max(abs(pv), 1.0)
            if change > pct:
                var_ev.append({"cell_id": cid, "prior": pv, "current": cur,
                               "change_pct": round(change, 4), "threshold_pct": pct,
                               "restated": bool(prior.get("restated")),
                               "citation": f"cell:{cid}@{doc['period_end']}~prior:{prior.get('period_end')}"})
        add("variance_vs_prior", "warn" if var_ev else "pass",
            f"{len(var_ev)} cell(s) changed > {pct:.0%} vs prior period" if var_ev else "no material period-over-period change",
            var_ev, {"threshold_pct": pct, "prior_period": prior.get("period_end")})
    else:
        not_evaluable.append({"check": "variance_vs_prior", "why": "no prior_period provided"})

    # deterministic readiness band ----------------------------------------
    fired = [f for f in findings if f["fired"]]
    blocking_fired = sorted({f["check"] for f in fired if f["blocking"]})
    advisory_fired = sorted({f["check"] for f in fired if not f["blocking"]})
    if blocking_fired:
        band = "Blocked"
    elif advisory_fired:
        band = "Review"
    else:
        band = "Clear"

    remediation = []
    if fired:
        remediation = [
            "route reconciliation breaks to gl-reconciler for a proposed correction (human-approved)",
            "confirm mandatory cells and lineage against the reporting instructions",
            "obtain or re-date the missing/mis-timed sign-off from the correct role",
            "document the driver for any period-over-period variance (acquisition, reclassification, restatement, seasonality)",
            "re-run this validator after remediation and before any human sign-off",
        ]

    return {
        "validation_id": f"rrdv-{str(doc.get('entity_id','')).replace('*','')}-{doc['report_code'].replace(' ','')}-{doc['period_end']}-0001",
        "report_code": doc["report_code"],
        "entity_id": doc.get("entity_id"),
        "period_end": doc["period_end"],
        "as_of": doc["as_of"],
        "due_date": doc["due_date"],
        "config_version": doc.get("config_version"),
        "findings": findings,
        "blocking_findings": blocking_fired,
        "advisory_findings": advisory_fired,
        "not_evaluable": not_evaluable,
        "readiness_band": band,
        "remediation_prompts": remediation,
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors = []
    if out["readiness_band"] != "Blocked":
        errors.append(f"expected band Blocked, got {out['readiness_band']!r}")
    for expected in ("edit_checks", "reconciliation_tie_out"):
        if expected not in out["blocking_findings"]:
            errors.append(f"expected blocking finding {expected!r} not fired")
    if "variance_vs_prior" not in out["advisory_findings"]:
        errors.append("expected advisory finding variance_vs_prior not fired")
    for f in out["findings"]:
        if f["fired"] and not f["evidence"]:
            errors.append(f"fired finding {f['check']} has no evidence")
    if DISCLAIMER not in out["disclaimer"]:
        errors.append("disclaimer missing")
    for e in errors:
        print("ERROR", e)
    print(f"compute selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
