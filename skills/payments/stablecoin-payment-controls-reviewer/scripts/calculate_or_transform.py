#!/usr/bin/env python3
"""Deterministic stablecoin payment-controls evaluation for stablecoin-payment-controls-reviewer.

Reads a control-review file (see validate_input.py), applies the documented control rules
(references/domain-rules.md) to each attested control, derives a per-control finding
status (pass | fail | gap | not_evaluable) with an evidence citation, computes per-category
coverage, and maps the finding profile to a **suggested review disposition** band. Emits a
machine-readable core the SKILL wraps in a plain-language findings pack.

IMPORTANT: This produces control findings, cited evidence, and a triage *suggestion* only.
It never makes a compliance determination, launch approval, or attestation; it never closes
a finding or writes a system of record. The disposition mapping is deterministic and
documented in references/domain-rules.md. R3: mandatory human adjudication.

Usage:
  python calculate_or_transform.py review.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

CATEGORIES = ("reserve", "custody", "screening", "transaction",
              "operational", "reconciliation", "disclosure")

# Critical controls: a defect (fail/gap) OR an un-evaluable critical control escalates.
CRITICAL = {
    "reserve_backing_ratio", "reserve_asset_quality", "reserve_attestation_current",
    "custody_qualified_custodian", "sanctions_wallet_screening", "travel_rule",
    "onchain_ledger_recon",
}

DEFAULT_CONFIG = {
    "par_value": 1.0,
    "min_backing_ratio": 1.0,
    "min_eligible_pct": 100.0,
    "max_attestation_age_days": 31,
    "required_travel_rule_max": 1000.0,
    "required_min_confirmations": 12,
    "recon_break_tolerance_bps": 5.0,
    "required_report_cadence_days": 31,
    "escalate_fail_count": 3,
}

DISCLAIMER = ("Control-review evidence only; not a compliance determination, launch "
              "approval, or attestation. No finding has been closed and no filing or "
              "system-of-record change has been made.")


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _bool(v):
    return v if isinstance(v, bool) else None


# Each rule returns (status, observed_dict, reason). status in pass|fail|gap|not_evaluable.
def _r_backing(m, cfg, as_of):
    out, rmv = _num(m.get("outstanding_tokens")), _num(m.get("reserve_market_value"))
    if out is None or rmv is None or out <= 0:
        return "not_evaluable", {}, "missing outstanding_tokens or reserve_market_value"
    ratio = rmv / (out * cfg["par_value"])
    ok = ratio >= cfg["min_backing_ratio"]
    return ("pass" if ok else "fail"), {"backing_ratio": round(ratio, 6), "min": cfg["min_backing_ratio"]}, \
        f"backing ratio {ratio:.4f} {'>=' if ok else '<'} required {cfg['min_backing_ratio']}"


def _r_asset_quality(m, cfg, as_of):
    pct = _num(m.get("eligible_pct"))
    if pct is None:
        return "not_evaluable", {}, "missing eligible_pct"
    ok = pct >= cfg["min_eligible_pct"]
    return ("pass" if ok else "fail"), {"eligible_pct": pct, "min": cfg["min_eligible_pct"]}, \
        f"{pct:.2f}% eligible assets vs required {cfg['min_eligible_pct']:.2f}%"


def _r_attestation(m, cfg, as_of):
    d = _parse_date(m.get("last_attestation_date"))
    if d is None or as_of is None:
        return "not_evaluable", {}, "missing last_attestation_date"
    age = (as_of - d).days
    ok = age <= cfg["max_attestation_age_days"]
    return ("pass" if ok else "fail"), {"attestation_age_days": age, "max": cfg["max_attestation_age_days"]}, \
        f"attestation age {age}d vs max {cfg['max_attestation_age_days']}d"


def _r_bool(field, true_reason, false_reason):
    def fn(m, cfg, as_of):
        b = _bool(m.get(field))
        if b is None:
            return "not_evaluable", {}, f"missing '{field}'"
        return ("pass" if b else "fail"), {field: b}, (true_reason if b else false_reason)
    return fn


def _r_key_mgmt(m, cfg, as_of):
    scheme = str(m.get("scheme", "")).lower()
    quorum = m.get("quorum")
    if not scheme:
        return "not_evaluable", {}, "missing key scheme"
    strong = scheme in ("mpc", "hsm", "mpc_hsm", "threshold") and bool(quorum)
    return ("pass" if strong else "fail"), {"scheme": scheme, "quorum": quorum}, \
        ("signing keys under quorum-based MPC/HSM" if strong
         else "single-party or unquorumed signing key")


def _r_travel_rule(m, cfg, as_of):
    en = _bool(m.get("enabled"))
    if en is None:
        return "not_evaluable", {}, "missing travel-rule 'enabled'"
    if not en:
        return "fail", {"enabled": False}, "travel-rule data capture not enabled"
    thr = _num(m.get("threshold"))
    if thr is None:
        return "not_evaluable", {"enabled": True}, "missing travel-rule threshold"
    if thr > cfg["required_travel_rule_max"]:
        return "gap", {"threshold": thr, "required_max": cfg["required_travel_rule_max"]}, \
            f"threshold {thr:.0f} above required max {cfg['required_travel_rule_max']:.0f}"
    return "pass", {"threshold": thr, "required_max": cfg["required_travel_rule_max"]}, \
        f"threshold {thr:.0f} <= required max {cfg['required_travel_rule_max']:.0f}"


def _r_txn_limits(m, cfg, as_of):
    per, day = _num(m.get("per_txn_limit")), _num(m.get("daily_limit"))
    if per is None or day is None:
        return "gap", {"per_txn_limit": per, "daily_limit": day}, "per-txn and/or daily limit not evidenced"
    ok = per > 0 and day > 0
    return ("pass" if ok else "fail"), {"per_txn_limit": per, "daily_limit": day}, \
        ("per-txn and daily limits configured" if ok else "limit configured at 0 (ineffective)")


def _r_confirmations(m, cfg, as_of):
    c = _num(m.get("min_confirmations"))
    if c is None:
        return "not_evaluable", {}, "missing min_confirmations"
    ok = c >= cfg["required_min_confirmations"]
    return ("pass" if ok else "fail"), {"min_confirmations": c, "required": cfg["required_min_confirmations"]}, \
        f"min confirmations {c:.0f} vs required {cfg['required_min_confirmations']}"


def _r_recon(m, cfg, as_of):
    b = _num(m.get("break_bps"))
    tol = _num(m.get("tolerance_bps"))
    if tol is None:
        tol = cfg["recon_break_tolerance_bps"]
    if b is None:
        return "not_evaluable", {}, "missing break_bps"
    ok = b <= tol
    return ("pass" if ok else "fail"), {"break_bps": b, "tolerance_bps": tol}, \
        f"on-chain vs ledger break {b:.2f}bps vs tolerance {tol:.2f}bps"


def _r_report_cadence(m, cfg, as_of):
    c = _num(m.get("cadence_days"))
    if c is None:
        return "not_evaluable", {}, "missing reserve-report cadence_days"
    ok = c <= cfg["required_report_cadence_days"]
    return ("pass" if ok else "fail"), {"cadence_days": c, "required": cfg["required_report_cadence_days"]}, \
        f"reserve-report cadence {c:.0f}d vs required {cfg['required_report_cadence_days']}d"


# Registry: id -> (category, requirement_text, rule_fn)
CONTROL_CATALOG = {
    "reserve_backing_ratio": ("reserve", "Reserves fully back outstanding tokens (>= 1:1).", _r_backing),
    "reserve_asset_quality": ("reserve", "Reserves held in permitted high-quality liquid assets.", _r_asset_quality),
    "reserve_attestation_current": ("reserve", "Independent reserve attestation within required cadence.", _r_attestation),
    "reserve_segregation": ("reserve", "Reserve assets segregated from operating funds.",
                            _r_bool("segregated", "reserves segregated from operating funds", "reserves not segregated")),
    "custody_qualified_custodian": ("custody", "Reserve assets held at a qualified custodian.",
                                    _r_bool("qualified", "assets at qualified custodian", "custodian not qualified")),
    "key_management": ("custody", "Signing keys under quorum-based MPC/HSM controls.", _r_key_mgmt),
    "sanctions_wallet_screening": ("screening", "Counterparty wallet screening against sanctions lists.",
                                   _r_bool("enabled", "wallet sanctions screening enabled", "wallet sanctions screening not enabled")),
    "travel_rule": ("screening", "FATF travel-rule data captured for in-scope transfers.", _r_travel_rule),
    "kyc_program": ("screening", "KYC on originator/beneficiary for hosted-wallet transfers.",
                    _r_bool("enabled", "KYC program in place", "KYC program not evidenced")),
    "txn_limits": ("transaction", "Per-transaction and daily value limits enforced.", _r_txn_limits),
    "finality_confirmations": ("transaction", "Minimum confirmations before settlement credit.", _r_confirmations),
    "address_allowlist": ("transaction", "Address allowlist/blocklist enforced.",
                          _r_bool("enforced", "address allow/blocklist enforced", "address controls not enforced")),
    "incident_response": ("operational", "Incident runbook for key compromise/depeg/chain halt.",
                          _r_bool("runbook", "incident runbook in place", "incident runbook not evidenced")),
    "reorg_handling": ("operational", "Chain reorg/fork handling policy documented.",
                       _r_bool("policy", "reorg handling policy documented", "reorg handling policy not evidenced")),
    "onchain_ledger_recon": ("reconciliation", "On-chain balances reconciled to internal ledger.", _r_recon),
    "mint_burn_recon": ("reconciliation", "Mint/burn events reconciled to reserve movements.",
                        _r_bool("reconciled", "mint/burn reconciled to reserve", "mint/burn not reconciled")),
    "redemption_disclosure": ("disclosure", "Redemption rights and timing disclosed to holders.",
                              _r_bool("disclosed", "redemption terms disclosed", "redemption terms not disclosed")),
    "reserve_reporting": ("disclosure", "Reserve composition reported at required cadence.", _r_report_cadence),
}


def _cite(ctrl: dict) -> str:
    return f"controls:{ctrl.get('source_ref', '?')}"


def _disposition(evaluated: list[dict], cfg: dict) -> str:
    fails = [c for c in evaluated if c["status"] == "fail"]
    defects = [c for c in evaluated if c["status"] in ("fail", "gap")]
    critical_defect = any(
        c["id"] in CRITICAL and c["status"] in ("fail", "gap", "not_evaluable")
        for c in evaluated)
    if critical_defect or len(fails) >= cfg["escalate_fail_count"]:
        return "Material Gaps - Escalate"
    if defects:
        return "Findings - Remediation Recommended"
    return "Controls Evidenced"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_date(doc.get("as_of"))
    evaluated, findings, not_evaluable = [], [], []

    for ctrl in doc.get("controls", []):
        cid = ctrl.get("id")
        spec = CONTROL_CATALOG.get(cid)
        evidence = [{"citation": _cite(ctrl), "source_ref": ctrl.get("source_ref")}]
        if spec is None:
            row = {"id": cid, "category": ctrl.get("category", "unknown"), "status": "not_evaluable",
                   "requirement": "(unknown control id)", "observed": {},
                   "reason": "control id not in catalog", "evidence": evidence}
            evaluated.append(row)
            not_evaluable.append({"id": cid, "why": "unknown control id"})
            continue
        category, requirement, fn = spec
        if ctrl.get("attested") is False:
            status, observed, reason = "gap", {}, "attested as not implemented / not evidenced"
        else:
            status, observed, reason = fn(ctrl.get("metrics") or {}, cfg, as_of)
        row = {"id": cid, "category": category, "status": status, "requirement": requirement,
               "observed": observed, "reason": reason, "evidence": evidence}
        evaluated.append(row)
        if status in ("fail", "gap"):
            findings.append(row)
        elif status == "not_evaluable":
            not_evaluable.append({"id": cid, "why": reason})

    coverage = {}
    for cat in CATEGORIES:
        rows = [c for c in evaluated if c["category"] == cat and c["status"] in ("pass", "fail", "gap")]
        coverage[cat] = {"pass": sum(1 for c in rows if c["status"] == "pass"), "total": len(rows)}

    disposition = _disposition(evaluated, cfg)

    remediation = []
    if findings:
        remediation = [
            "Assign each finding to the accountable control owner (reserve, custody, "
            "screening, transaction, operational, reconciliation, or disclosure) for "
            "remediation planning.",
            "Treat critical-control defects (reserve backing, reserve quality, attestation "
            "currency, qualified custody, sanctions screening, travel rule, on-chain "
            "reconciliation) as escalations for human adjudication.",
            "Obtain independent verification of reserve and reconciliation figures from the "
            "source attestation before any decision is made.",
            "This review recommends; a licensed compliance owner decides, adjudicates, and "
            "records the outcome.",
        ]

    program = str(doc.get("program", "program")).replace(" ", "-")
    return {
        "review_id": f"spcr-{program}-{doc.get('as_of', 'na')}-0001",
        "program": doc.get("program"),
        "as_of": doc.get("as_of"),
        "jurisdiction": doc.get("jurisdiction", "US"),
        "config_version": doc.get("config_version"),
        "controls_evaluated": evaluated,
        "findings": findings,
        "category_coverage": coverage,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "remediation_prompts": remediation,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
