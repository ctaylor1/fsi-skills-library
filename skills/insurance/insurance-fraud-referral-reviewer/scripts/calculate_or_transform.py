#!/usr/bin/env python3
"""Draft neutral insurance SIU review from versioned indicators, counterevidence and unknowns. Prior history never overrides thresholds. No fraud finding or adverse action.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from insurance_contract import build_artifact

# Documented indicator weights (versioned config; deployment overrides via indicator_config).
DEFAULT_CONFIG = {
    "late_report_days": 30,
    "early_loss_days": 60,
    "post_increase_days": 30,
    "claim_freq_min": 3,
    "inconsistency_min": 2,
    "weights": {
        "FR-LATE-REPORT": 2,
        "FR-EARLY-LOSS": 3,
        "FR-POST-INCREASE": 3,
        "FR-CLAIM-FREQ": 2,
        "FR-NO-REPORT": 2,
        "FR-DOC-GAP": 1,
        "FR-INCONSISTENT": 2,
        "FR-LAPSE-REINSTATE": 2,
        "FR-PRIOR-SIU": 3,
    },
    "refer_min": 6,
    "monitor_min": 3,
}
# The ONLY indicator IDs this skill may emit (approved red-flag catalogue).
APPROVED_INDICATORS = set(DEFAULT_CONFIG["weights"])
# Template sections the drafted referral document must contain (template fidelity).
REQUIRED_SECTIONS = [
    "Claim Summary",
    "Fraud Indicators Observed",
    "Chronology",
    "Supporting Evidence",
    "Recommendation",
    "Required Human Approvals",
    "Limitations",
]
STANDING_NOTE = (
    "Draft fraud referral only; no fraud finding has been made, no claim has "
    "been denied or closed, and no adverse customer decision has been taken. "
    "SIU adjudication and any decision require human review."
)


def _cite(c):
    return f"claimsys:{c.get('source_ref', '?')}"


def _mask(insured_id):
    s = str(insured_id or "")
    return ("*" * max(0, len(s) - 4)) + s[-4:] if s else "?"


def _pdate(v):
    try:
        return date.fromisoformat(str(v))
    except (ValueError, TypeError):
        return None


def _indicators(c, cfg):
    """Return list of triggered indicators; each with id, weight, evidence, citation."""
    out, w = [], cfg["weights"]
    cite = _cite(c)
    loss = _pdate(c.get("loss_date"))
    report = _pdate(c.get("report_date"))
    inception = _pdate(c.get("policy_inception_date"))
    increase = _pdate(c.get("coverage_increase_date"))

    def add(iid, evidence):
        out.append({"id": iid, "weight": w[iid], "evidence": evidence, "citation": cite})

    if loss and report and (report - loss).days > cfg["late_report_days"]:
        add("FR-LATE-REPORT", f"loss {loss} reported {report} ({(report - loss).days}d > {cfg['late_report_days']}d)")
    if loss and inception and 0 <= (loss - inception).days <= cfg["early_loss_days"]:
        add("FR-EARLY-LOSS", f"loss {(loss - inception).days}d after policy inception {inception}")
    if loss and increase and 0 <= (loss - increase).days <= cfg["post_increase_days"]:
        add("FR-POST-INCREASE", f"loss {(loss - increase).days}d after coverage increase {increase}")
    if int(c.get("prior_claims_24m") or 0) >= cfg["claim_freq_min"]:
        add("FR-CLAIM-FREQ", f"{c.get('prior_claims_24m')} prior claims in 24m (>= {cfg['claim_freq_min']})")
    if c.get("reportable_loss") is True and c.get("police_report") is False:
        add("FR-NO-REPORT", "reportable loss with no police/fire report on file")
    if c.get("documentation_complete") is False:
        add("FR-DOC-GAP", "supporting documentation incomplete per adjuster notes")
    if int(c.get("statement_inconsistencies") or 0) >= cfg["inconsistency_min"]:
        add("FR-INCONSISTENT", f"{c.get('statement_inconsistencies')} flagged statement inconsistencies")
    if c.get("coverage_lapse_reinstatement"):
        add("FR-LAPSE-REINSTATE", "loss adjacent to a coverage lapse/reinstatement")
    if c.get("prior_siu_flag") is True and c.get("prior_siu_status") == "open" and c.get("prior_siu_source_ref"):
        add("FR-PRIOR-SIU", "prior SIU referral remains open per supplied status; no finding implied")
    return out


def _chronology(c):
    events = []
    for label, key in (
        ("Policy inception", "policy_inception_date"),
        ("Coverage increase", "coverage_increase_date"),
        ("Date of loss", "loss_date"),
        ("Claim reported", "report_date"),
    ):
        if c.get(key):
            events.append({"date": c.get(key), "event": label})
    events.sort(key=lambda e: e["date"])
    return events


def _referral_document(c, indicators, score, band, rec):
    ind_lines = (
        "\n".join(
            f"- **{i['id']}** (weight {i['weight']}): {i['evidence']}  \n  Source: `{i['citation']}`"
            for i in indicators
        )
        or "- None triggered."
    )
    chrono_lines = "\n".join(f"- {e['date']} — {e['event']}" for e in _chronology(c)) or "- Not available."
    doc = f"""# SIU Fraud Referral (DRAFT) — {c.get("claim_id")}

Referral ID: FR-{c.get("claim_id")}  |  Referring adjuster: (to be recorded)  |  Status: DRAFT — pending human review

## Claim Summary
- Claim: {c.get("claim_id")}
- Insured (masked): {_mask(c.get("insured_id"))}
- Policy: {c.get("policy_ref")}
- Peril: {c.get("peril")}
- Date of loss: {c.get("loss_date")}  |  Reported: {c.get("report_date")}

## Fraud Indicators Observed
Observed indicators (red flags) only — not a determination of fraud.
{ind_lines}

## Chronology
{chrono_lines}

## Supporting Evidence
Every indicator above is sourced to the claim system record cited inline. Primary record: `{_cite(c)}`.

## Recommendation
Routing recommendation: **{rec}** (indicator score {score}, band "{band}"). This is a routing
recommendation for SIU intake, NOT a fraud finding or a coverage/claim decision.

## Required Human Approvals
- Referring adjuster attestation: pending
- SIU intake acknowledgment: pending

## Limitations
No fraud finding has been made. No claim has been denied, closed, or otherwise decided, and no
adverse customer action has been taken. SIU adjudication and any decision require human review.
"""
    return doc


def score_claim(c, doc, cfg):
    referral_id = f"FR-{c.get('claim_id')}"
    citations = [_cite(c)]
    rec = {
        "claim_id": c.get("claim_id"),
        "referral_id": referral_id,
        "citations": citations,
        "indicators_triggered": [],
        "indicator_score": 0,
        "score_band": None,
        "referral_package": None,
        "referral_document": None,
        "needs": [],
    }

    required = [
        "policy_inception_date",
        "reportable_loss",
        "police_report",
        "documentation_complete",
        "prior_claims_24m",
        "statement_inconsistencies",
        "coverage_lapse_reinstatement",
        "prior_siu_flag",
    ]
    rec["unknown_inputs"] = [k for k in required if c.get(k) is None]
    if _pdate(c.get("policy_inception_date")) is None and "policy_inception_date" not in rec["unknown_inputs"]:
        rec["unknown_inputs"].append("policy_inception_date")
    if c.get("prior_siu_flag") is True and (
        c.get("prior_siu_status") not in {"open", "closed_no_finding", "closed_finding"}
        or not c.get("prior_siu_source_ref")
    ):
        rec["unknown_inputs"].append("prior_siu_disposition_and_source")
    rec["needs"] = ["resolve " + k for k in rec["unknown_inputs"]]
    rec["counterevidence"] = c.get("counterevidence", [])
    rec["counterevidence_review_required"] = bool(rec["counterevidence"])
    rec["assessment_status"] = "partial" if rec["needs"] else "evaluable"
    indicators = _indicators(c, cfg)
    score = sum(i["weight"] for i in indicators)
    band = (
        "Refer"
        if score >= cfg["refer_min"]
        else "Monitor"
        if score >= cfg["monitor_min"]
        else "Needs data"
        if rec["needs"]
        else "Insufficient"
    )
    rec["indicators_triggered"] = indicators
    rec["indicator_score"] = score
    rec["score_band"] = band

    if band == "Refer":
        rec["recommendation"] = "refer-to-siu"
        rec["route"] = "Special Investigations Unit (human intake)"
        rec["referral_package"] = {
            "referral_id": referral_id,
            "claim_id": c.get("claim_id"),
            "insured_masked": _mask(c.get("insured_id")),
            "policy_ref": c.get("policy_ref"),
            "peril": c.get("peril"),
            "loss_date": c.get("loss_date"),
            "report_date": c.get("report_date"),
            "chronology": _chronology(c),
            "indicators": indicators,
            "counterevidence": rec["counterevidence"],
            "unknown_inputs": rec["unknown_inputs"],
            "citations": citations,
            "required_approvals": {"adjuster_attestation": "pending", "siu_intake_ack": "pending"},
        }
        rec["referral_document"] = (
            _referral_document(c, indicators, score, band, "refer-to-siu")
            + "\n## Counterevidence and Unknowns\n"
            + json.dumps({"counterevidence": rec["counterevidence"], "unknown_inputs": rec["unknown_inputs"]}, indent=2)
        )
    elif band == "Needs data":
        rec["recommendation"] = "needs-data"
    elif band == "Monitor":
        rec["recommendation"] = "monitor"
    else:
        rec["recommendation"] = "insufficient-indicators"
    return rec


def _calculate(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("indicator_config") or {})}
    cfg["weights"] = {**DEFAULT_CONFIG["weights"], **((doc.get("indicator_config") or {}).get("weights") or {})}
    numeric = [
        "late_report_days",
        "early_loss_days",
        "post_increase_days",
        "claim_freq_min",
        "inconsistency_min",
        "refer_min",
        "monitor_min",
    ]
    if any(
        isinstance(cfg[k], bool)
        or not isinstance(cfg[k], (int, float))
        or not __import__("math").isfinite(cfg[k])
        or cfg[k] < 0
        for k in numeric
    ):
        raise ValueError("indicator thresholds must be finite nonnegative numbers")
    if cfg["refer_min"] <= cfg["monitor_min"] or cfg["monitor_min"] <= 0:
        raise ValueError("refer_min must exceed positive monitor_min")
    if set(cfg["weights"]) != APPROVED_INDICATORS or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not __import__("math").isfinite(v) or v < 0
        for v in cfg["weights"].values()
    ):
        raise ValueError("weights must cover approved indicators with finite nonnegative numbers")
    records = [score_claim(c, doc, cfg) for c in doc["claims"]]
    summary = {
        "total": len(records),
        "refer_to_siu": sum(1 for r in records if r["recommendation"] == "refer-to-siu"),
        "monitor": sum(1 for r in records if r["recommendation"] == "monitor"),
        "insufficient": sum(1 for r in records if r["recommendation"] == "insufficient-indicators"),
        "needs_data": sum(1 for r in records if r["recommendation"] == "needs-data"),
    }
    # Record the effective (versioned) config on the output so the band tie-out in
    # validate_output uses exactly the thresholds/weights the engine used — a non-default
    # deployment config stays reproducible and must not be false-rejected downstream.
    return {
        "config_version": doc.get("config_version"),
        "indicator_config": cfg,
        "referrals": records,
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def transform(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = [r["claim_id"] + ": " + n for r in output["referrals"] for n in r.get("needs", [])]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="insurance-fraud-referral-reviewer",
        artifact_type="claims-fraud-referral-assistant-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claims_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(transform(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
