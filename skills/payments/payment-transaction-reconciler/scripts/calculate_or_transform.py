#!/usr/bin/env python3
"""Read-only transaction comparisons. Decimal amounts serialize as strings."""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, localcontext
from itertools import combinations
from pathlib import Path
from payment_contract import money, require_currency, stable_hash, VERSION

PARTITION = ("legal_entity_id", "account_id", "currency", "settlement_cycle")
SOURCES = {"gateway", "processor", "acquirer", "bank", "ledger", "merchant", "settlement", "reserve", "fee_batch"}
DEFAULT_SOURCES = ["gateway", "processor", "bank", "ledger"]
DISCLAIMER = "Read-only evidence comparison; no journal, payment repair, or system-of-record change is proposed or executed."


def amount(value):
    return None if value is None else money(value)


def serial(value):
    return None if value is None else format(value, "f")


def validate_input(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], warnings
    for field in ("as_of", "config_version"):
        if not isinstance(doc.get(field), str) or not doc[field].strip():
            errors.append(f"{field} must be a nonempty string")
    try:
        date.fromisoformat(doc.get("as_of", ""))
    except (ValueError, TypeError):
        errors.append("as_of must be a valid ISO date")
    config = doc.get("config", {})
    if not isinstance(config, dict):
        return errors + ["config must be an object"], warnings
    try:
        if money(config.get("amount_tolerance", "0.01")) < 0:
            errors.append("amount_tolerance cannot be negative")
    except (ValueError, TypeError, ArithmeticError):
        errors.append("amount_tolerance must be finite money")
    expected = config.get("expected_sources", DEFAULT_SOURCES)
    if (not isinstance(expected, list) or len(expected) < 2 or
            any(not isinstance(s, str) or s not in SOURCES for s in expected)):
        errors.append("expected_sources must contain at least two distinct known sources")
    elif len(set(expected)) != len(expected):
        errors.append("expected_sources cannot contain duplicates")
    if "cash_rank" in config:
        errors.append("cash_rank is unsupported; only bank evidence establishes cash")
    records = doc.get("records")
    if not isinstance(records, list) or not records:
        return errors + ["records must be a nonempty list"], warnings
    for i, r in enumerate(records):
        label = f"records[{i}]"
        if not isinstance(r, dict):
            errors.append(f"{label}: record must be an object")
            continue
        for field in (*PARTITION, "record_id", "txn_ref", "source", "source_ref", "date"):
            if not isinstance(r.get(field), str) or not r[field].strip():
                errors.append(f"{label}: {field} must be a nonempty string")
        try:
            require_currency(r.get("currency"))
            date.fromisoformat(r.get("date", ""))
        except (ValueError, TypeError):
            errors.append(f"{label}: invalid currency or date")
        if not isinstance(r.get("source"), str) or r["source"] not in SOURCES:
            errors.append(f"{label}: unsupported source")
        if r.get("level", "transaction") not in ("transaction", "settlement"):
            errors.append(f"{label}: unsupported level")
        if r.get("normalized_state") is not None and (not isinstance(r["normalized_state"], str) or not r["normalized_state"].strip()):
            errors.append(f"{label}: normalized_state must be a nonempty string")
        try:
            if amount(r.get("amount")) is None:
                warnings.append(f"{label}: amount missing; comparisons cannot assume zero")
        except (ValueError, TypeError, ArithmeticError):
            errors.append(f"{label}: amount must be finite money or null")
    return errors, warnings


def handoff(identity, evidence, target, issues, requested):
    return {"contract_version": VERSION, "handoff_id": stable_hash({"identity": identity, "target": target, "issues": issues}),
            "source_skill": "payment-transaction-reconciler", "target_skill": target,
            "case_id": stable_hash(identity), "lead_owner": "payments-operations",
            "requested_output": requested, "action_mode": "read-only",
            "source_refs": [e["source_ref"] for e in evidence], "unresolved_issues": issues,
            "target_input": identity, "target_validation": "required", "authority_granted": False}


def compute(doc):
    errors, warnings = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    with localcontext() as ctx:
        ctx.prec = 60
        return _compute(doc, warnings)


def _compute(doc, warnings):
    tolerance = money(doc.get("config", {}).get("amount_tolerance", "0.01"))
    expected = doc.get("config", {}).get("expected_sources", DEFAULT_SOURCES)
    indexed = defaultdict(list)
    identity_uses = defaultdict(set)
    for record in doc["records"]:
        key = tuple(record[k] for k in PARTITION) + (record.get("level", "transaction"), record["txn_ref"])
        indexed[key].append(record)
        namespace = (record["legal_entity_id"], record["account_id"])
        identity_uses[("record_id", record["source"], namespace, record["record_id"])].add(key)
        identity_uses[("source_ref", record["source"], (), record["source_ref"])].add(key)
    identity_conflicts = defaultdict(list)
    for identity, uses in sorted(identity_uses.items()):
        if len(uses) > 1:
            conflict = {"source": identity[1], "identity_field": identity[0], "identity_value": identity[3],
                        "source_namespace": list(identity[2]),
                        "references": [{"partition": dict(zip(PARTITION, key[:4])), "level": key[4], "txn_ref": key[5]} for key in sorted(uses)]}
            for key in uses:
                identity_conflicts[key].append(conflict)
    groups, routed, partitions = [], [], defaultdict(list)
    for key, records in sorted(indexed.items()):
        partition = dict(zip(PARTITION, key[:4]))
        evidence = [{"evidence_id": r["record_id"], "source": r["source"], "status": "supplied",
                     "source_ref": f"{r['source']}:{r['source_ref']}@{r['date']}"}
                    for r in sorted(records, key=lambda r: (r["source"], r["record_id"], r["source_ref"]))]
        identity = {"partition": partition, "txn_ref": key[5], "level": key[4]}
        if key[4] == "settlement":
            route = {**identity, "evidence": evidence,
                           "handoff": handoff(identity, evidence, "payment-settlement-reconciler",
                                              ["settlement-level records require independent mapping and validation"] + identity_conflicts[key],
                                              "Compare settlement records; no transaction conclusion")}
            if identity_conflicts[key]:
                route["source_identity_conflicts"] = identity_conflicts[key]
                route["status"] = "quarantined"
            routed.append(route)
            continue
        by_source = defaultdict(list)
        for record in records:
            by_source[record["source"]].append(record)
        duplicates = sorted(s for s, rows in by_source.items() if len(rows) > 1)
        duplicate_ids = sorted({record_id for (_, record_id), n in Counter((r["source"], r["record_id"]) for r in records).items() if n > 1})
        quarantined = bool(duplicates or duplicate_ids or identity_conflicts[key])
        values = {s: None if quarantined or s not in by_source else amount(by_source[s][0].get("amount"))
                  for s in sorted(set(expected) | set(by_source))}
        issues, comparisons = [], []
        if quarantined:
            issues.append({"type": "AMBIGUOUS_DUPLICATE", "sources": duplicates, "record_ids": duplicate_ids, "difference": None})
            if identity_conflicts[key]:
                issues[-1]["reused_source_identities"] = identity_conflicts[key]
        else:
            for s in expected:
                if s not in by_source:
                    issues.append({"type": "MISSING_SOURCE", "source": s, "difference": None})
            for s in sorted(by_source):
                if values[s] is None:
                    issues.append({"type": "UNVALUED_RECORD", "source": s, "difference": None})
            for left, right in combinations(sorted(by_source), 2):
                delta = values[right] - values[left] if values[left] is not None and values[right] is not None else None
                state = "not_evaluable" if delta is None else "within_tolerance" if abs(delta) <= tolerance else "mismatch"
                comparisons.append({"left": left, "right": right, "right_minus_left": serial(delta), "status": state})
                if state == "mismatch":
                    issues.append({"type": "AMOUNT_MISMATCH", "sources": [left, right], "difference": serial(delta)})
            states = {s: by_source[s][0]["normalized_state"] for s in sorted(by_source) if by_source[s][0].get("normalized_state")}
            if len(set(states.values())) > 1:
                issues.append({"type": "STATE_MISMATCH", "states": states, "difference": None})
        bank, ledger = values.get("bank"), values.get("ledger")
        cash_delta = ledger - bank if bank is not None and ledger is not None else None
        cash_status = "not_evaluable" if cash_delta is None else "within_tolerance" if abs(cash_delta) <= tolerance else "mismatch"
        for issue in issues:
            issue["issue_id"] = stable_hash({**identity, **issue})
        group = {**identity, "group_id": stable_hash(identity), "status": "quarantined" if quarantined else "needs_review" if issues else "matched",
                 "source_amounts": {s: serial(v) for s, v in values.items()}, "comparisons": comparisons,
                 "cash_ledger_check": {"authority": "bank", "ledger_minus_bank": serial(cash_delta), "status": cash_status},
                 "issues": issues, "evidence": evidence}
        groups.append(group)
        partitions[key[:4]].append(group)
    totals = []
    for key, members in sorted(partitions.items()):
        source_totals = {}
        for source in sorted({s for group in members for s in group["source_amounts"]}):
            known = [amount(group["source_amounts"].get(source)) for group in members]
            known_count = sum(v is not None for v in known)
            subtotal = sum((v for v in known if v is not None), Decimal(0)) if known_count else None
            source_totals[source] = {"total": serial(subtotal) if known_count == len(members) else None,
                                     "known_subtotal": serial(subtotal), "known_groups": known_count,
                                     "missing_or_quarantined_groups": len(members) - known_count}
        totals.append({"partition": dict(zip(PARTITION, key)), "source_totals": source_totals})
    issues = [issue for group in groups for issue in group["issues"]]
    handoffs = [handoff({"partition": g["partition"], "txn_ref": g["txn_ref"]}, g["evidence"],
                        "bank-payment-exception-investigator", [i["issue_id"] for i in g["issues"]],
                        "Investigate source evidence; no accounting instruction") for g in groups if g["issues"]]
    complete = bool(groups) and not issues and not routed and all(g["cash_ledger_check"]["status"] != "not_evaluable" for g in groups)
    return {"schema_version": "1.0", "skill": "payment-transaction-reconciler", "mode": "reconcile-transactions",
            "input_hash": stable_hash(doc), "source_snapshot": doc, "as_of": doc["as_of"],
            "config_version": doc["config_version"], "amount_tolerance": serial(tolerance),
            "groups": groups, "partition_totals": totals, "routed_groups": routed, "investigation_handoffs": handoffs,
            "summary": {"group_count": len(groups), "issue_count": len(issues), "routed_count": len(routed),
                        "fully_evaluated_and_matched": complete}, "warnings": warnings, "disclaimer": DISCLAIMER}


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/ledger_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try:
        doc = json.loads(path.read_text() if path else sys.stdin.read(), parse_float=str)
        print(json.dumps(compute(doc), indent=2))
        return 0
    except (ValueError, TypeError, ArithmeticError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
