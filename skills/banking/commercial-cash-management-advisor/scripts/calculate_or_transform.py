#!/usr/bin/env python3
"""Deterministic treasury-service fit analysis for commercial-cash-management-advisor.

Reads a de-identified commercial cash profile (see validate_input.py), computes which
treasury-management services fit the customer's operating cash flows and balances against
a versioned, documented rule set, attaches evidence + citations to each recommendation,
and maps the recommended set to an engagement-priority band.

IMPORTANT: This produces explainable *candidate service recommendations and implementation
questions* for a banker to discuss with the client. It NEVER makes a binding product,
pricing, credit, or investment decision, never approves credit or a line/overdraft, and
never opens/changes/prices an account or service. The priority mapping is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py profile.json | --selftest
Prints the advisory JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Versioned thresholds (see references/domain-rules.md). Config is a contract, not a guess;
# thresholds are never tuned to the individual customer.
DEFAULT_CONFIG = {
    "idle_balance_min": 250000.0,      # excess collected balance above the operating buffer
    "multi_account_min": 3,            # accounts before a concentration structure is indicated
    "check_positive_pay_min": 50,      # checks issued / month (fraud-control gap)
    "controlled_disbursement_min": 150,  # checks issued / month (payables automation)
    "lockbox_min": 200,                # mailed check receipts / month
    "rdc_min": 50,                     # checks deposited / month
    "ach_debit_block_min": 25,         # ACH debits received / month (fraud-control gap)
    "merchant_services_min": 50000.0,  # card acceptance amount / month
    "fx_services_min": 100000.0,       # cross-border amount / month
    "overdraft_referral_days": 3,      # overdraft days in the analysis period
}
DISCLAIMER = ("Advisory analysis only; not a binding product, pricing, credit, or investment "
              "decision. No account or service has been opened, changed, or priced.")
# Recommending any of these signals a fraud-control gap or a credit/liquidity referral that
# warrants a priority conversation regardless of how many other services fit.
ESCALATORS = {"check_positive_pay", "ach_debit_block", "overdraft_liquidity_referral"}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    accounts = doc.get("accounts") or []
    act = doc.get("activity") or {}
    crm = doc.get("crm") or {}
    existing = {str(s).lower() for s in crm.get("existing_services", [])}

    total_collected = sum(_num(a.get("avg_collected_balance")) for a in accounts)
    buffer = _num(doc.get("operating_buffer"))
    idle = max(0.0, total_collected - buffer)
    act_cite = act.get("source_ref", "?")

    recommendations, not_indicated, already_in_place = [], [], []

    def acct_evidence():
        return [{"account_id": a.get("account_id"), "type": a.get("type"),
                 "avg_collected_balance": a.get("avg_collected_balance"),
                 "citation": a.get("source_ref", "?")} for a in accounts]

    def act_evidence(metric):
        return [{"metric": metric, "value": act.get(metric), "citation": act_cite}]

    def consider(service, category, fires, rationale, evidence, basis, questions, why_not):
        """Add a service as recommended, already-in-place, or not-indicated (fail-open to
        not-indicated on missing data — never over-recommend)."""
        if service in existing:
            already_in_place.append(service)
            return
        if fires:
            recommendations.append({
                "service": service, "category": category, "recommended": True,
                "rationale": rationale, "evidence": evidence, "basis": basis,
                "implementation_questions": questions})
        else:
            not_indicated.append({"service": service, "why": why_not})

    # --- Liquidity / balances -------------------------------------------------
    consider(
        "excess_balance_investment", "liquidity",
        idle >= cfg["idle_balance_min"],
        f"estimated idle collected balance {idle:,.0f} >= {cfg['idle_balance_min']:,.0f}; "
        "an earnings-credit review or excess-balance solution may be worth discussing",
        acct_evidence(),
        {"total_avg_collected": round(total_collected, 2), "operating_buffer": buffer,
         "estimated_idle_balance": round(idle, 2), "threshold": cfg["idle_balance_min"]},
        ["What minimum operating buffer must stay liquid across the account group?",
         "Is the client open to an earnings-credit arrangement, a sweep, or a separate "
         "investment vehicle (route investment suitability to a licensed specialist)?",
         "What is the client's tolerance for tying up balances vs. same-day access?"],
        f"estimated idle balance {idle:,.0f} < {cfg['idle_balance_min']:,.0f}")

    consider(
        "liquidity_structure", "liquidity",
        len(accounts) >= cfg["multi_account_min"] and idle > 0,
        f"{len(accounts)} accounts with concentratable balances; a ZBA / target-balance "
        "sweep / pooling structure may simplify funding and visibility",
        acct_evidence(),
        {"account_count": len(accounts), "threshold": cfg["multi_account_min"]},
        ["Which account is the intended concentration (master) account?",
         "Are there legal-entity or tax constraints on moving funds between accounts?",
         "What target balances should each subsidiary account hold?"],
        f"{len(accounts)} accounts (< {cfg['multi_account_min']}) or no idle balance")

    # --- Receivables ----------------------------------------------------------
    consider(
        "lockbox_receivables", "receivables",
        _num(act.get("mailed_check_receipts")) >= cfg["lockbox_min"],
        f"{act.get('mailed_check_receipts')} mailed check receipts/month "
        f">= {cfg['lockbox_min']}; a wholesale lockbox may accelerate availability and AR posting",
        act_evidence("mailed_check_receipts"),
        {"mailed_check_receipts": act.get("mailed_check_receipts"), "threshold": cfg["lockbox_min"]},
        ["What is average and peak-day mailed receipt volume?",
         "Which remittance fields must be captured for automated AR posting?",
         "Is a wholesale, retail, or wholetail configuration expected?"],
        f"mailed check receipts {act.get('mailed_check_receipts')} < {cfg['lockbox_min']}")

    consider(
        "remote_deposit_capture", "receivables",
        _num(act.get("checks_deposited")) >= cfg["rdc_min"],
        f"{act.get('checks_deposited')} checks deposited/month >= {cfg['rdc_min']}; "
        "remote deposit capture may reduce branch trips and speed availability",
        act_evidence("checks_deposited"),
        {"checks_deposited": act.get("checks_deposited"), "threshold": cfg["rdc_min"]},
        ["How many deposit locations or users need scanning capability?",
         "What daily and per-item deposit limits are appropriate?"],
        f"checks deposited {act.get('checks_deposited')} < {cfg['rdc_min']}")

    consider(
        "merchant_services", "receivables",
        _num(act.get("card_acceptance_amount")) >= cfg["merchant_services_min"],
        f"card acceptance {_num(act.get('card_acceptance_amount')):,.0f}/month "
        f">= {cfg['merchant_services_min']:,.0f}; a merchant-services / acceptance review may fit",
        act_evidence("card_acceptance_amount"),
        {"card_acceptance_amount": act.get("card_acceptance_amount"),
         "threshold": cfg["merchant_services_min"]},
        ["What card mix and average ticket does the client process today?",
         "Is the client already on a processor, and what is the contract status?"],
        f"card acceptance {_num(act.get('card_acceptance_amount')):,.0f} < {cfg['merchant_services_min']:,.0f}")

    # --- Payables / disbursements --------------------------------------------
    consider(
        "controlled_disbursement_payables", "payables",
        _num(act.get("checks_issued")) >= cfg["controlled_disbursement_min"],
        f"{act.get('checks_issued')} checks issued/month >= {cfg['controlled_disbursement_min']}; "
        "integrated payables / controlled disbursement / virtual card may reduce cost and effort",
        act_evidence("checks_issued"),
        {"checks_issued": act.get("checks_issued"), "threshold": cfg["controlled_disbursement_min"]},
        ["What share of payables could move from check to ACH or virtual card?",
         "Does the client's ERP/AP system support a payment file integration?",
         "What approval and dual-control workflow is required?"],
        f"checks issued {act.get('checks_issued')} < {cfg['controlled_disbursement_min']}")

    # --- Fraud controls (gaps) -----------------------------------------------
    consider(
        "check_positive_pay", "fraud_control",
        _num(act.get("checks_issued")) >= cfg["check_positive_pay_min"],
        f"{act.get('checks_issued')} checks issued/month >= {cfg['check_positive_pay_min']}; "
        "check Positive Pay is a standard fraud control for this issuance volume",
        act_evidence("checks_issued"),
        {"checks_issued": act.get("checks_issued"), "threshold": cfg["check_positive_pay_min"]},
        ["Can the client transmit a daily issue file (with payee data for payee-match)?",
         "Who will adjudicate exceptions each morning, and by what cut-off?"],
        f"checks issued {act.get('checks_issued')} < {cfg['check_positive_pay_min']}")

    consider(
        "ach_debit_block", "fraud_control",
        _num(act.get("ach_debits_received")) >= cfg["ach_debit_block_min"],
        f"{act.get('ach_debits_received')} ACH debits received/month "
        f">= {cfg['ach_debit_block_min']}; ACH debit block/filter (ACH Positive Pay) limits "
        "unauthorized debit exposure",
        act_evidence("ach_debits_received"),
        {"ach_debits_received": act.get("ach_debits_received"), "threshold": cfg["ach_debit_block_min"]},
        ["Which originators should be on the authorized allow-list?",
         "Should unauthorized debits be blocked outright or routed to review?"],
        f"ACH debits received {act.get('ach_debits_received')} < {cfg['ach_debit_block_min']}")

    # --- International --------------------------------------------------------
    consider(
        "fx_international_services", "international",
        _num(act.get("cross_border_amount")) >= cfg["fx_services_min"],
        f"cross-border volume {_num(act.get('cross_border_amount')):,.0f}/month "
        f">= {cfg['fx_services_min']:,.0f}; FX / international payment services may fit",
        act_evidence("cross_border_amount"),
        {"cross_border_amount": act.get("cross_border_amount"),
         "currencies": act.get("fx_currencies", []), "threshold": cfg["fx_services_min"]},
        ["Which currencies and corridors are recurring vs. one-off?",
         "Does the client need forward/hedging conversations (route to a licensed FX desk)?"],
        f"cross-border volume {_num(act.get('cross_border_amount')):,.0f} < {cfg['fx_services_min']:,.0f}")

    # --- Credit / liquidity referral (NOT a credit decision) -----------------
    consider(
        "overdraft_liquidity_referral", "referral",
        _num(act.get("overdraft_days")) >= cfg["overdraft_referral_days"],
        f"{act.get('overdraft_days')} overdraft days in period "
        f">= {cfg['overdraft_referral_days']}; refer to commercial lending to assess a working-"
        "capital line or overdraft protection. This skill does not assess creditworthiness "
        "or offer credit terms",
        act_evidence("overdraft_days"),
        {"overdraft_days": act.get("overdraft_days"), "threshold": cfg["overdraft_referral_days"]},
        ["What is driving the timing mismatch (seasonality, receivables lag, one-off)?",
         "Should this be routed to commercial lending for a formal credit review?"],
        f"overdraft days {act.get('overdraft_days')} < {cfg['overdraft_referral_days']}")

    recommended_names = [r["service"] for r in recommendations if r["recommended"]]
    if len(recommended_names) >= 3 or (ESCALATORS & set(recommended_names)):
        priority = "Priority-review"
    elif recommended_names:
        priority = "Recommended-review"
    else:
        priority = "Informational"

    assumptions = []
    if recommended_names:
        assumptions = [
            "Volumes and balances are period averages from the profile; validate current "
            "figures with the client before any proposal.",
            "Thresholds are from the versioned config, not tuned to this customer.",
            "Service fit is a discussion starting point for the banker; pricing, credit, and "
            "investment suitability are handled by the responsible desk under human review.",
        ]
    if buffer == 0.0 and doc.get("operating_buffer") in (None, ""):
        assumptions.append("No operating buffer supplied; idle balance assumes a zero buffer "
                           "and is therefore an upper bound (low confidence).")

    return {
        "advisory_id": f"ccma-{str(doc['customer_id']).replace('*','').replace('-','')}-{doc['as_of']}-0001",
        "customer_id": doc["customer_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency"),
        "analysis_period_months": doc.get("analysis_period_months"),
        "balances": {"total_avg_collected": round(total_collected, 2),
                     "operating_buffer": buffer, "estimated_idle_balance": round(idle, 2)},
        "recommendations": recommendations,
        "recommended_services": recommended_names,
        "not_indicated": not_indicated,
        "already_in_place": already_in_place,
        "engagement_priority": priority,
        "assumptions": assumptions,
        "disclaimer": DISCLAIMER,
    }


def _selfcheck(res: dict) -> list[str]:
    """Internal consistency check of a computed advisory (used by --selftest)."""
    errors = []
    rec = [r for r in res.get("recommendations", []) if r.get("recommended")]
    names = {r["service"] for r in rec}
    if set(res.get("recommended_services", [])) != names:
        errors.append("recommended_services does not match recommended recommendation rows")
    for r in rec:
        if not r.get("evidence"):
            errors.append(f"recommended {r['service']} has no evidence")
        if not r.get("implementation_questions"):
            errors.append(f"recommended {r['service']} has no implementation questions")
    exp = ("Priority-review" if (len(names) >= 3 or (ESCALATORS & names))
           else "Recommended-review" if names else "Informational")
    if res.get("engagement_priority") != exp:
        errors.append(f"engagement_priority {res.get('engagement_priority')!r} != deterministic {exp!r}")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "profile_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        res = compute(doc)
        print(json.dumps(res, indent=2))
        errors = _selfcheck(res)
        for e in errors:
            print("ERROR", e)
        print(f"compute self-check: {len(errors)} error(s)")
        return 1 if errors else 0
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
