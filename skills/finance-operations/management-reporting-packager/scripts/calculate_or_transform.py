#!/usr/bin/env python3
"""Deterministic management-report assembly engine for management-reporting-packager.

Assembles a controlled DRAFT management report package from approved finance inputs. For
each KPI it computes actual-to-budget and actual-to-prior variance, tags whether the figure
and its commentary are SUPPORTED by a cited source, evaluates every reconciliation tie-out
against tolerance, aggregates exception flags, and records the required approvals. It then
computes a package_status of `ready-for-review` or `blocked` from explicit blocking reasons.

It NEVER delivers, submits, distributes, or posts the pack (delivery_status is always
`draft`), NEVER approves a figure as final, and NEVER marks a package ready-for-review while
an unsupported claim, an unreconciled break, or a missing required approval remains.

Usage: python calculate_or_transform.py package.json | --selftest
Prints the assembled package JSON to stdout; --selftest also runs internal invariant checks
and prints a summary line ending "N error(s)".
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_APPROVAL_ROLES = ("preparer", "reviewer")
RECORDED = {"recorded", "complete", "signed"}
SECTIONS = [
    "Cover & reporting scope",
    "Executive takeaways",
    "KPI scorecard & commentary",
    "Reconciliation & tie-out summary",
    "Source lineage & citations",
    "Exceptions & data gaps",
    "Approvals & sign-off log",
    "Standing note & distribution control",
]
STANDING_NOTE = (
    "DRAFT management report package for human review only. No pack has been delivered, "
    "submitted, distributed, or posted to a system of record, and no figure has been "
    "approved as final."
)


def _pct(delta, base):
    try:
        if base in (None, 0):
            return None
        return round(delta / base * 100.0, 2)
    except (TypeError, ZeroDivisionError):
        return None


def _assemble_kpi(k):
    value = k.get("value")
    budget = k.get("budget")
    prior = k.get("prior")
    var_budget = (value - budget) if isinstance(budget, (int, float)) else None
    var_prior = (value - prior) if isinstance(prior, (int, float)) else None
    citations = []
    if k.get("source_ref"):
        citations.append(k["source_ref"])
    if k.get("commentary_source_ref"):
        citations.append(k["commentary_source_ref"])
    # A figure needs a source_ref; commentary (a claim) needs its own citation.
    figure_supported = bool(k.get("source_ref"))
    commentary_supported = (not k.get("commentary")) or bool(k.get("commentary_source_ref"))
    support_status = "supported" if (figure_supported and commentary_supported) else "unsupported"
    return {
        "id": k.get("id"),
        "name": k.get("name"),
        "value": value,
        "unit": k.get("unit"),
        "variance_vs_budget": var_budget,
        "variance_vs_budget_pct": _pct(var_budget, budget),
        "variance_vs_prior": var_prior,
        "variance_vs_prior_pct": _pct(var_prior, prior),
        "commentary": k.get("commentary"),
        "support_status": support_status,
        "citations": citations,
    }


def _assemble_recon(r, default_tol):
    tol = r.get("tolerance", default_tol)
    diff = float(r.get("ledger_balance", 0)) - float(r.get("subledger_balance", 0))
    status = "tie" if abs(diff) <= float(tol) else "break"
    return {
        "name": r.get("name"),
        "ledger_balance": r.get("ledger_balance"),
        "subledger_balance": r.get("subledger_balance"),
        "difference": round(diff, 2),
        "tolerance": tol,
        "tie_out_status": status,
        "citations": [r["source_ref"]] if r.get("source_ref") else [],
    }


def assemble(doc: dict) -> dict:
    default_tol = doc.get("reporting_tolerance", 0)
    kpis = [_assemble_kpi(k) for k in doc.get("kpis", [])]
    recons = [_assemble_recon(r, default_tol) for r in (doc.get("reconciliations") or [])]
    approvals = doc.get("approvals") or []
    exceptions = doc.get("exceptions") or []

    recorded_roles = {a.get("role") for a in approvals if a.get("status") in RECORDED}
    missing_appr = [r for r in REQUIRED_APPROVAL_ROLES if r not in recorded_roles]

    blocking = []
    unsupported = [k["id"] for k in kpis if k["support_status"] == "unsupported"]
    if unsupported:
        blocking.append(f"unsupported KPI claim(s): {', '.join(unsupported)}")
    breaks = [r["name"] for r in recons if r["tie_out_status"] == "break"]
    if breaks:
        blocking.append(f"unreconciled break(s): {', '.join(breaks)}")
    if not recons:
        blocking.append("no reconciliation tie-outs provided")
    if missing_appr:
        blocking.append(f"missing required approval(s): {', '.join(missing_appr)}")

    package_status = "ready-for-review" if not blocking else "blocked"

    package_id = f"MRP-{doc.get('entity', 'ENTITY')}-{doc.get('period', 'PERIOD')}".replace(" ", "_")

    return {
        "package_id": package_id,
        "config_version": doc.get("config_version"),
        "period": doc.get("period"),
        "entity": doc.get("entity"),
        "sections": list(SECTIONS),
        "kpis": kpis,
        "reconciliations": recons,
        "exceptions": exceptions,
        "approvals": approvals,
        "delivery_status": "draft",
        "package_status": package_status,
        "blocking_reasons": blocking,
        "summary": {
            "kpi_count": len(kpis),
            "unsupported_kpis": len(unsupported),
            "reconciliations": len(recons),
            "breaks": len(breaks),
            "exceptions": len(exceptions),
            "missing_approvals": len(missing_appr),
        },
        "standing_note": STANDING_NOTE,
    }


def _selfcheck(pkg: dict) -> list[str]:
    """Internal invariants the assembler must always satisfy (defence in depth)."""
    errs = []
    if pkg.get("delivery_status") != "draft":
        errs.append("delivery_status must be 'draft'")
    if set(pkg.get("sections", [])) != set(SECTIONS):
        errs.append("assembled sections do not match the approved template")
    blocked = bool(pkg.get("blocking_reasons"))
    if blocked and pkg.get("package_status") != "blocked":
        errs.append("blocking reasons present but package_status is not 'blocked'")
    if not blocked and pkg.get("package_status") != "ready-for-review":
        errs.append("no blocking reasons but package_status is not 'ready-for-review'")
    if STANDING_NOTE not in str(pkg.get("standing_note", "")):
        errs.append("standing note missing")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    pkg = assemble(doc)
    print(json.dumps(pkg, indent=2))
    if selftest:
        errs = _selfcheck(pkg)
        for e in errs:
            print("ERROR", e)
        print(f"assembly self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
