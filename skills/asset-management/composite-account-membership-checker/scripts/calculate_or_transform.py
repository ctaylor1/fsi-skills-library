#!/usr/bin/env python3
"""Deterministic composite-membership rule engine for composite-account-membership-checker.

Reads an account/composite dataset (see validate_input.py), applies the firm's approved,
versioned composite-inclusion rules to each portfolio, compares the rule-derived *expected*
membership to the *asserted* membership on file, and emits an **exception evidence queue**
with rule/version citations for a performance analyst to adjudicate.

IMPORTANT: This produces *findings and cited evidence only*. It NEVER changes a composite,
its membership, the methodology, or reported performance, and it never closes/files/writes a
system of record. Every exception is emitted with status "for_review". The queue-priority
mapping is deterministic and documented in references/domain-rules.md. Return/attribution
recalculation is out of scope — route that to performance-attribution-builder.

Usage:
  python calculate_or_transform.py membership_input.json | --selftest
Prints the exception-queue JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Composite-membership exceptions are evidence for analyst adjudication only; "
             "this skill does not modify composites, methodology, or reported performance.")

# Exceptions whose presence escalates the queue to Elevated (completeness/accuracy impact).
ESCALATORS = {"improper_inclusion", "stale_inclusion", "unassigned_discretionary"}
SEVERITY = {
    "improper_inclusion": "high", "stale_inclusion": "high", "unassigned_discretionary": "high",
    "missing_inclusion": "medium", "early_inclusion": "medium",
    "significant_cash_flow_review": "low",
}


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _period_key(d: datetime) -> int:
    """Ordinal month key so period comparisons ('last full period') are exact."""
    return d.year * 12 + d.month


def _months_between(d0: datetime, d1: datetime) -> int:
    """Whole months elapsed from d0 to d1 (day-of-month aware)."""
    m = (d1.year - d0.year) * 12 + (d1.month - d0.month)
    if d1.day < d0.day:
        m -= 1
    return m


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def expected_queue_priority(exception_types: list) -> str:
    """Deterministic queue priority from the set of exception types (see domain-rules.md)."""
    if not exception_types:
        return "None"
    if (ESCALATORS & set(exception_types)) or len(exception_types) >= 3:
        return "Elevated"
    return "Review"


def _pcite(p: dict, field: str, value) -> dict:
    ref = p.get("source_ref") or f"portfolio={p.get('portfolio_id', '?')}"
    return {"field": field, "value": value, "citation": f"pms:{ref};field={field}@as_of"}


def _rule_from_composite(c: dict) -> dict:
    return {"rule_id": c.get("rule_id"), "rule_version": c.get("rule_version"),
            "effective_date": c.get("effective_date")}


def _completeness_rule(doc: dict) -> dict:
    return {"rule_id": "R-COMPLETENESS", "rule_version": doc.get("ruleset_version"),
            "effective_date": doc.get("ruleset_effective_date")}


def compute(doc: dict) -> dict:
    as_of = _parse_date(doc["as_of"])
    composites = {c["composite_id"]: c for c in doc.get("composites", [])}
    review_id = f"camc-{doc.get('firm_id', 'FIRM')}-{doc['as_of']}-0001"

    exceptions, informational = [], []
    seq = 0

    def add_exc(ptf, composite_id, exc_type, reason, expected, actual, rule, evidence):
        nonlocal seq
        seq += 1
        exceptions.append({
            "case_ref": f"{review_id}-E{seq:03d}",
            "portfolio_id": ptf["portfolio_id"],
            "composite_id": composite_id,
            "exception_type": exc_type,
            "severity": SEVERITY.get(exc_type, "medium"),
            "reason": reason,
            "expected_membership": expected,
            "asserted_membership": actual,
            "status": "for_review",
            "rule": rule,
            "evidence": evidence,
        })

    for p in doc.get("portfolios", []):
        assigned = set(p.get("assigned_composite_ids") or [])
        strat = p.get("strategy")
        discretionary = bool(p.get("discretionary"))
        fee_paying = bool(p.get("fee_paying"))
        mv = _num(p.get("market_value")) or 0.0
        umd = _parse_date(p["under_mgmt_date"]) if p.get("under_mgmt_date") else None
        term = _parse_date(p["termination_date"]) if p.get("termination_date") else None
        scf = _num(p.get("significant_cash_flow_pct")) or 0.0
        terminated_past = bool(term and _period_key(as_of) > _period_key(term))

        # Rule-derived expected membership across defined composites.
        expected_ids, eligible_but_pending = set(), set()
        for cid, c in composites.items():
            if strat != c.get("strategy"):
                continue
            if c.get("requires_discretionary") and not discretionary:
                continue
            if mv < (_num(c.get("min_asset_value")) or 0.0):
                continue
            if terminated_past:
                continue
            lag = int(c.get("inclusion_lag_months") or 0)
            if umd is not None and _months_between(umd, as_of) < lag:
                eligible_but_pending.add(cid)
                continue
            expected_ids.add(cid)

        # Missing inclusions: rule says in, record says out.
        for cid in expected_ids - assigned:
            c = composites[cid]
            add_exc(p, cid, "missing_inclusion",
                    f"Meets all {cid} inclusion criteria (strategy, discretion, "
                    f"value >= {c.get('min_asset_value')}, past inclusion lag) but is not assigned to it; "
                    f"flagged as a potential missing inclusion for analyst adjudication.",
                    "included", "not assigned", _rule_from_composite(c),
                    [_pcite(p, "strategy", strat), _pcite(p, "market_value", mv),
                     _pcite(p, "under_mgmt_date", p.get("under_mgmt_date"))])

        # Improper / early / stale inclusions: record says in, rule says out.
        for cid in assigned - expected_ids:
            c = composites.get(cid)
            if c is None:
                add_exc(p, cid, "improper_inclusion",
                        f"Assigned to {cid}, which is not a defined composite in the ruleset; "
                        f"flagged as a potential improper inclusion for analyst adjudication.",
                        "excluded", "assigned", _completeness_rule(doc),
                        [_pcite(p, "assigned_composite_ids", sorted(assigned))])
                continue
            rule = _rule_from_composite(c)
            if cid in eligible_but_pending:
                add_exc(p, cid, "early_inclusion",
                        f"Assigned to {cid} before the documented inclusion lag "
                        f"({c.get('inclusion_lag_months')} month(s) after coming under management) has elapsed; "
                        f"flagged as a potential early inclusion for analyst adjudication.",
                        "not yet included", "assigned", rule,
                        [_pcite(p, "under_mgmt_date", p.get("under_mgmt_date"))])
            elif terminated_past:
                add_exc(p, cid, "stale_inclusion",
                        f"Terminated {p.get('termination_date')} yet still assigned to {cid} after its "
                        f"last full measurement period ({term.strftime('%Y-%m')}); "
                        f"flagged as a potential stale inclusion for analyst adjudication.",
                        "excluded", "assigned", rule,
                        [_pcite(p, "termination_date", p.get("termination_date"))])
            elif strat != c.get("strategy"):
                add_exc(p, cid, "improper_inclusion",
                        f"Assigned to {cid} but the portfolio strategy '{strat}' does not match the composite "
                        f"strategy '{c.get('strategy')}'; flagged as a potential improper inclusion for "
                        f"analyst adjudication.",
                        "excluded", "assigned", rule,
                        [_pcite(p, "strategy", strat)])
            elif c.get("requires_discretionary") and not discretionary:
                add_exc(p, cid, "improper_inclusion",
                        f"Assigned to {cid} but the portfolio is non-discretionary while the composite requires "
                        f"discretionary mandates; flagged as a potential improper inclusion for analyst adjudication.",
                        "excluded", "assigned", rule,
                        [_pcite(p, "discretionary", discretionary)])
            elif mv < (_num(c.get("min_asset_value")) or 0.0):
                add_exc(p, cid, "improper_inclusion",
                        f"Assigned to {cid} but market value {mv} is below the composite minimum "
                        f"{c.get('min_asset_value')}; flagged as a potential improper inclusion for "
                        f"analyst adjudication.",
                        "excluded", "assigned", rule,
                        [_pcite(p, "market_value", mv)])

        # Significant-cash-flow policy review on legitimately-held members.
        for cid in expected_ids & assigned:
            c = composites[cid]
            thr = _num(c.get("significant_cash_flow_pct"))
            if thr is not None and scf >= thr and scf > 0:
                add_exc(p, cid, "significant_cash_flow_review",
                        f"Significant external cash flow of {scf:.0%} meets the {cid} significant-cash-flow "
                        f"policy threshold ({thr:.0%}); flagged for analyst review of the temporary-removal "
                        f"policy.",
                        "temporary-removal review", "assigned", _rule_from_composite(c),
                        [_pcite(p, "significant_cash_flow_pct", scf)])

        # Completeness: a discretionary fee-paying portfolio that fits no composite and is held in none.
        if discretionary and fee_paying and not terminated_past and not expected_ids \
                and not eligible_but_pending and not assigned:
            add_exc(p, None, "unassigned_discretionary",
                    f"Discretionary fee-paying portfolio with strategy '{strat}' matches no defined composite "
                    f"and is assigned to none; every discretionary fee-paying portfolio must belong to a "
                    f"composite, so flagged as a composite-coverage gap for analyst adjudication.",
                    "member of >= 1 composite", "not assigned", _completeness_rule(doc),
                    [_pcite(p, "strategy", strat), _pcite(p, "discretionary", discretionary),
                     _pcite(p, "fee_paying", fee_paying)])

        # Informational states (not exceptions).
        if eligible_but_pending - assigned:
            informational.append({"portfolio_id": p["portfolio_id"], "state": "pending_inclusion",
                                  "detail": f"within inclusion lag for {sorted(eligible_but_pending - assigned)}"})
        if expected_ids and expected_ids <= assigned and not (assigned - expected_ids):
            informational.append({"portfolio_id": p["portfolio_id"], "state": "compliant",
                                  "detail": f"assigned exactly to expected {sorted(expected_ids)}"})

    exc_types = [e["exception_type"] for e in exceptions]
    priority = expected_queue_priority(exc_types)

    return {
        "review_id": review_id,
        "firm_id": doc.get("firm_id"),
        "as_of": doc["as_of"],
        "ruleset_version": doc.get("ruleset_version"),
        "ruleset_effective_date": doc.get("ruleset_effective_date"),
        "portfolios_evaluated": len(doc.get("portfolios", [])),
        "exceptions": exceptions,
        "exception_types": exc_types,
        "informational": informational,
        "queue_priority": priority,
        "human_adjudication_required": bool(exceptions),
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "membership_input.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
