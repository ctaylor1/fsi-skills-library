#!/usr/bin/env python3
"""Review claim-file source and document quality. Financial totals require latest outstanding stocks and distinct cumulative payment transactions. No reserve adequacy or claim determination.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

from insurance_contract import build_artifact

DEFAULT_CONFIG = {
    "required_documents": {
        "auto_collision": ["fnol", "police_report", "repair_estimate", "photos"],
        "property_fire": ["fnol", "fire_report", "damage_estimate", "photos", "proof_of_loss"],
        "gl_bodily_injury": ["fnol", "medical_records", "demand_letter", "adjuster_report"],
        "default": ["fnol", "adjuster_report"],
    },
    "report_lag_days": 30,
    "stale_days": 30,
    "reserve_support_tolerance": 0.25,
    "large_loss_threshold": 100000.0,
}
DISCLAIMER = (
    "Review findings and evidence only; not a coverage or reserve determination. "
    "No claim decision, payment, reserve change, or case closure has been made."
)


def _dt(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _num(v):
    try:
        n = float(v)
        return n if not isinstance(v, bool) and math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def financial_snapshot(doc):
    """Select outstanding stocks, sum uniquely identified payment flows, never both."""
    currency = doc.get("currency")
    issues, balances, payments = [], {}, []
    if not currency:
        issues.append("financial currency missing")
    for row in doc.get("reserves") or []:
        key = row.get("balance_id")
        if row.get("entry_type") != "outstanding_balance" or not key:
            issues.append("reserve must identify an outstanding balance, not an unspecified movement")
            continue
        if row.get("currency") != currency or _num(row.get("amount")) is None or _num(row.get("amount")) < 0:
            issues.append(f"reserve {key}: invalid amount or mixed currency")
            continue
        try:
            when = _dt(row["as_of"])
        except (ValueError, KeyError, TypeError):
            issues.append(f"reserve {key}: invalid as_of")
            continue
        if when > _dt(doc["as_of"]):
            issues.append(f"reserve {key}: future balance excluded")
            continue
        if key in balances and balances[key]["as_of"] == row["as_of"]:
            issues.append(f"reserve {key}: duplicate balance snapshot")
        elif key not in balances or balances[key]["as_of"] < row["as_of"]:
            balances[key] = row
    seen = set()
    for row in doc.get("payments") or []:
        key = row.get("payment_id")
        if not key or key in seen:
            issues.append("payment transaction identity missing or duplicated")
        seen.add(key)
        if (
            row.get("entry_type") != "payment_transaction"
            or row.get("currency") != currency
            or _num(row.get("amount")) is None
            or _num(row.get("amount")) < 0
        ):
            issues.append(f"payment {key}: require nonnegative payment transaction in declared currency")
        elif row.get("date", "9999") > doc["as_of"]:
            issues.append(f"payment {key}: future transaction")
        else:
            payments.append(row)
    if doc.get("financial_collections_complete") is not True:
        issues.append("ledger completeness not confirmed")
    return list(balances.values()), payments, issues


def _calculate(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    req_docs = {**DEFAULT_CONFIG["required_documents"], **(cfg.get("required_documents") or {})}
    claim_id = doc["claim_id"]
    ctype = doc.get("claim_type")
    pol = doc.get("policy") or {}
    documents = doc.get("documents") or []
    events = doc.get("events") or []
    reserves, payments, financial_issues = financial_snapshot(doc)
    decisions = doc.get("decisions") or []
    as_of = _dt(doc["as_of"])

    findings: list[dict] = []
    n = {"c": 0}

    def add(category, severity, summary, evidence):
        n["c"] += 1
        findings.append(
            {
                "finding_id": f"F{n['c']:03d}",
                "category": category,
                "severity": severity,
                "summary": summary,
                "evidence": evidence,
            }
        )

    def cite(system, ref, date=None):
        return f"{system}:{ref}@{date}" if date else f"{system}:{ref}"

    for issue in financial_issues:
        add(
            "financial_data",
            "blocking",
            issue,
            [{"ref": claim_id, "citation": f"claims:{claim_id};financial-contract"}],
        )

    # ---- Coverage citation + policy-period fit -------------------------------
    for c in pol.get("coverages") or []:
        if not (c.get("citation") or "").strip():
            add(
                "coverage",
                "blocking",
                f"Coverage {c.get('code', '?')} has no policy/endorsement citation; coverage cannot be reviewed against a source form.",
                [
                    {
                        "ref": f"coverage:{c.get('code', '?')}",
                        "citation": cite("policy", f"{pol.get('policy_number', '?')};coverage={c.get('code', '?')}"),
                    }
                ],
            )

    loss = _dt(doc["loss_date"])
    eff = _dt(pol.get("effective_date")) if pol.get("effective_date") else None
    exp = _dt(pol.get("expiration_date")) if pol.get("expiration_date") else None
    if eff and exp and not (eff <= loss <= exp):
        add(
            "coverage",
            "blocking",
            f"Loss date {doc['loss_date']} falls outside the policy period {pol.get('effective_date')}..{pol.get('expiration_date')}; coverage in force is a threshold question for the adjuster.",
            [
                {
                    "ref": "policy_period",
                    "citation": cite(
                        "policy",
                        f"{pol.get('policy_number', '?')};period={pol.get('effective_date')}..{pol.get('expiration_date')}",
                    ),
                }
            ],
        )

    # ---- Chronology ----------------------------------------------------------
    report = _dt(doc["report_date"])
    chronology = sorted(events, key=lambda e: str(e.get("date")))
    chronology_out = [
        {
            "date": e.get("date"),
            "type": e.get("type"),
            "description": e.get("description", ""),
            "citation": cite("claims", e.get("source_ref", "?"), e.get("date")),
        }
        for e in chronology
    ]
    if report < loss:
        add(
            "chronology",
            "blocking",
            f"Report date {doc['report_date']} precedes loss date {doc['loss_date']} — a data-integrity issue to reconcile before review.",
            [
                {
                    "ref": "report_vs_loss",
                    "citation": cite("claims", f"claim={claim_id};loss={doc['loss_date']};report={doc['report_date']}"),
                }
            ],
        )
    elif (report - loss).days > cfg["report_lag_days"]:
        add(
            "chronology",
            "info",
            f"Reporting lag {(report - loss).days}d exceeds {cfg['report_lag_days']}d; note for late-notice review (not a coverage conclusion).",
            [
                {
                    "ref": "report_lag",
                    "citation": cite("claims", f"claim={claim_id};loss={doc['loss_date']};report={doc['report_date']}"),
                }
            ],
        )
    # largest gap between consecutive dated events
    dates = sorted({_dt(e["date"]) for e in chronology if e.get("date")})
    if len(dates) >= 2:
        gap = max((dates[i + 1] - dates[i]).days for i in range(len(dates) - 1))
        if gap > cfg["stale_days"]:
            add(
                "chronology",
                "info",
                f"Largest gap between recorded events is {gap}d (> {cfg['stale_days']}d); confirm no activity is unrecorded.",
                [{"ref": "chronology_gap", "citation": cite("claims", f"claim={claim_id};max_gap_days={gap}")}],
            )

    # ---- Missing documentation ----------------------------------------------
    required = req_docs.get(ctype) or req_docs.get("default") or []
    present_types = {str(d.get("type", "")).lower() for d in documents if d.get("status", "present") == "present"}
    for rt in required:
        if rt.lower() not in present_types:
            add(
                "documentation",
                "warning",
                f"Required document '{rt}' for claim type '{ctype}' is not present in the file.",
                [
                    {
                        "ref": f"required:{rt}",
                        "citation": cite("config", f"{doc.get('config_version', '?')};required_documents.{ctype}.{rt}"),
                    }
                ],
            )

    # ---- Reserve support / severity consistency ------------------------------
    doc_amounts = {d.get("doc_id"): _num(d.get("amount")) for d in documents}
    doc_ids = {d.get("doc_id") for d in documents}
    for r in reserves:
        if r.get("category") != "indemnity":
            continue  # expense (ALAE) reserves are not tied to a damage estimate
        sref = r.get("supporting_ref")
        amt = _num(r.get("amount"))
        if not sref or sref not in doc_ids:
            add(
                "reserve",
                "warning",
                f"Indemnity reserve {amt} has no supporting evidence document in the file; reserve support is unverifiable.",
                [
                    {
                        "ref": r.get("source_ref", "?"),
                        "citation": cite("claims", r.get("source_ref", "?"), r.get("as_of")),
                    }
                ],
            )
        else:
            est = doc_amounts.get(sref)
            if est and amt and est > 0 and abs(amt - est) / est > cfg["reserve_support_tolerance"]:
                add(
                    "reserve",
                    "warning",
                    f"Indemnity reserve {amt} deviates from supporting estimate {est} by more than {int(cfg['reserve_support_tolerance'] * 100)}%; confirm the basis with the adjuster/actuary.",
                    [
                        {
                            "ref": r.get("source_ref", "?"),
                            "citation": cite("claims", r.get("source_ref", "?"), r.get("as_of")),
                        },
                        {"ref": sref, "citation": cite("claims", f"claim={claim_id};doc={sref}")},
                    ],
                )

    # ---- Payment traceability ------------------------------------------------
    for p in payments:
        if not p.get("authority_ref"):
            add(
                "decision",
                "blocking",
                f"Payment {p.get('payment_id', '?')} ({_num(p.get('amount'))}) has no approval-authority reference; delegated authority is unverifiable.",
                [
                    {
                        "ref": p.get("payment_id", "?"),
                        "citation": cite("claims", p.get("source_ref", "?"), p.get("date")),
                    }
                ],
            )
        if not p.get("supporting_ref"):
            add(
                "decision",
                "warning",
                f"Payment {p.get('payment_id', '?')} has no supporting evidence reference; confirm the payment basis.",
                [
                    {
                        "ref": p.get("payment_id", "?"),
                        "citation": cite("claims", p.get("source_ref", "?"), p.get("date")),
                    }
                ],
            )

    # ---- Decision traceability ----------------------------------------------
    for d in decisions:
        missing = [k for k in ("rationale", "authority_ref", "source_ref") if not (d.get(k) or "").strip()]
        if missing:
            add(
                "decision",
                "warning",
                f"Recorded decision {d.get('decision_id', '?')} ({d.get('type', '?')}) is not fully traceable — missing: {', '.join(missing)}.",
                [
                    {
                        "ref": d.get("decision_id", "?"),
                        "citation": cite("claims", d.get("source_ref", "?"), d.get("date")),
                    }
                ],
            )

    # ---- Stale open issues ---------------------------------------------------
    open_issues = []
    for e in events:
        if (
            str(e.get("type", "")).lower() in ("open_task", "pending", "diary")
            and str(e.get("status", "open")).lower() == "open"
        ):
            age = (as_of - _dt(e["date"])).days
            open_issues.append(
                {
                    "date": e.get("date"),
                    "description": e.get("description", ""),
                    "age_days": age,
                    "citation": cite("claims", e.get("source_ref", "?"), e.get("date")),
                }
            )
            if age > cfg["stale_days"]:
                add(
                    "open_issue",
                    "warning",
                    f"Open task '{e.get('description', '?')}' has been open {age}d (> {cfg['stale_days']}d) with no recorded resolution.",
                    [
                        {
                            "ref": e.get("source_ref", "?"),
                            "citation": cite("claims", e.get("source_ref", "?"), e.get("date")),
                        }
                    ],
                )

    # ---- Descriptive incurred / severity band --------------------------------
    reserves_total = sum(_num(r.get("amount")) or 0.0 for r in reserves)
    paid_total = sum(_num(p.get("amount")) or 0.0 for p in payments)
    total_incurred = reserves_total + paid_total if not financial_issues else None
    if total_incurred is None:
        severity_band = "Unknown"
    elif total_incurred >= cfg["large_loss_threshold"]:
        severity_band = "Severe"
    elif total_incurred >= 0.1 * cfg["large_loss_threshold"]:
        severity_band = "Moderate"
    else:
        severity_band = "Minor"

    # ---- Deterministic readiness mapping ------------------------------------
    sev = {f["severity"] for f in findings}
    if "blocking" in sev:
        readiness = "escalate"
    elif "warning" in sev:
        readiness = "follow_up_required"
    else:
        readiness = "documentation_complete"

    considerations = []
    if findings:
        considerations = [
            "Coverage/exclusion interpretation is the adjuster's call; findings only flag missing citations or period questions.",
            "Reserve adequacy is an actuarial/adjuster judgement; findings only flag unsupported or divergent reserves.",
            "Jurisdiction-specific rules (e.g., late-notice, fair-claims deadlines) may change how a finding is weighted.",
            "A missing document may already exist outside the file; confirm before treating it as a gap.",
        ]

    handoffs = []
    if any(f["category"] == "reserve" for f in findings):
        handoffs.append("claim adjuster / delegated supervisor (case-reserve support review)")
    handoffs.append("subrogation-opportunity-screener (if recovery/subrogation potential is noted)")
    handoffs.append("insurance-fraud-referral-reviewer (if fraud indicators are present; referral is draft-only)")

    return {
        "review_id": f"cfr-{claim_id}-{doc['as_of']}-0001",
        "claim_id": claim_id,
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "claim_type": ctype,
        "jurisdiction": doc.get("jurisdiction"),
        "policy_period": {"effective": pol.get("effective_date"), "expiration": pol.get("expiration_date")},
        "financial_status": "not_evaluable" if financial_issues else "evaluable",
        "financial_issues": financial_issues,
        "financial_basis": {
            "currency": doc.get("currency"),
            "reserves": "latest outstanding stock per balance_id",
            "paid": "unique payment transactions",
        },
        "incurred": {
            "reserves_total": round(reserves_total, 2) if not financial_issues else None,
            "paid_total": round(paid_total, 2) if not financial_issues else None,
            "total_incurred": round(total_incurred, 2) if total_incurred is not None else None,
        },
        "severity_band": severity_band,
        "chronology": chronology_out,
        "open_issues": open_issues,
        "findings": findings,
        "fired_categories": sorted({f["category"] for f in findings}),
        "review_readiness": readiness,
        "reviewer_considerations": considerations,
        "recommended_handoffs": handoffs,
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = output.get("financial_issues", []) + [
        str(f.get("category")) + ": " + str(f.get("summary", "review finding")) for f in output.get("findings", [])
    ]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="claim-file-quality-reviewer",
        artifact_type="claims-file-reviewer-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


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
