#!/usr/bin/env python3
"""Deterministic financial-statement normalization + tie-out engine for financials-normalizer.

Reads a source financial-statement extract (see validate_input.py), maps each source line
item to a standard chart-of-accounts account, rolls the detail up per account and period,
applies documented normalization adjustments (with provenance), and runs source-linked
tie-outs (reported subtotals and the balance-sheet identity). Emits a machine-readable
normalized dataset the SKILL wraps in a plain-language pack.

IMPORTANT: This maps, rolls up, adjusts-with-rationale, and tie-out-checks only. It never
opines that the statements are GAAP/IFRS-compliant or materially correct, makes an
accounting/audit/investment judgment, restates or posts figures to any system of record, or
produces borrower credit spreading. The readiness mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py financials.json | --selftest
Prints the normalization JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "tie_out_tolerance": 1.0,          # abs currency units allowed between computed and reported
    "adjustment_materiality_pct": 5.0, # |adjustment| / revenue base, in %; material + no approver -> fire
    "escalate_finding_count": 4,       # >= this many fired findings -> Hold
}
DISCLAIMER = ("Normalization output only; not an accounting, audit, or investment judgment, "
              "and not a system-of-record posting. Source figures are mapped and tied out, "
              "not restated or re-booked; a human reviewer must accept the normalized mapping "
              "before use.")
HIGH = "high"
MED = "medium"
READY = "Model-ready"
NEEDS = "Needs mapping review"
HOLD = "Hold - tie-out break"
ROLES = {"total_assets", "total_liabilities", "total_equity"}


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _cite_line(line: dict, entity: str, as_of: str) -> str:
    ref = (line.get("source_ref") or "").strip()
    if ref:
        return f"fs:{ref}@{as_of}"
    return f"fs:entity={entity};line={line.get('line_id', '?')};period={line.get('period', '?')}@{as_of}"


def _cite_adj(adj: dict, entity: str, as_of: str) -> str:
    ref = (adj.get("source_ref") or "").strip()
    if ref:
        return f"fs:{ref}@{as_of}"
    return f"fs:entity={entity};adjustment={adj.get('adj_id', '?')}@{as_of}"


def _calculate_native(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    entity = doc["entity_id"]
    as_of = str(doc["as_of"])
    tol = _num(cfg["tie_out_tolerance"]) or 0.0

    lines = doc.get("line_items") or []
    detail = [ln for ln in lines if not ln.get("is_subtotal")]
    subtotals = [ln for ln in lines if ln.get("is_subtotal")]

    # mapping keyed by (raw_label, statement)
    mp = {}
    for m in doc.get("mapping") or []:
        mp[(str(m.get("source_label")), str(m.get("statement")))] = m

    # ---- roll detail up into standard accounts (account, statement, period) ----
    rollup: dict[tuple, dict] = {}
    unmapped = []
    for ln in detail:
        key = (str(ln.get("raw_label")), str(ln.get("statement")))
        m = mp.get(key)
        if not m:
            unmapped.append({"line_id": ln.get("line_id"), "raw_label": ln.get("raw_label"),
                             "statement": ln.get("statement"), "period": ln.get("period"),
                             "value": _num(ln.get("value")),
                             "citation": _cite_line(ln, entity, as_of)})
            continue
        acct_key = (str(m["std_account"]), str(ln.get("statement")), str(ln.get("period")))
        slot = rollup.setdefault(acct_key, {"std_account": m["std_account"],
                                            "statement": ln.get("statement"),
                                            "period": ln.get("period"), "mapped_value": 0.0,
                                            "provenance": [], "adjustments": []})
        slot["mapped_value"] += _num(ln.get("value")) or 0.0
        slot["provenance"].append(ln.get("line_id"))

    # ---- apply documented normalization adjustments onto standard accounts ----
    revenue_base = sum((_num(ln.get("value")) or 0.0) for ln in detail
                       if mp.get((str(ln.get("raw_label")), str(ln.get("statement"))), {}).get("std_account") == "revenue")
    bad_adjustments = []
    for a in doc.get("adjustments") or []:
        acct_key = (str(a["std_account"]), a["statement"], str(a["period"]))
        # adjustments may target an account not present in detail (e.g. a derived subtotal)
        slot = rollup.setdefault(acct_key, {"std_account": a.get("std_account"),
                                            "statement": a["statement"],
                                            "period": a.get("period"), "mapped_value": 0.0,
                                            "provenance": [], "adjustments": []})
        slot["adjustments"].append({"adj_id": a["adj_id"], "type": a["type"],
                                    "statement": a["statement"], "period": a["period"],
                                    "amount": _num(a["amount"]), "rationale": a.get("rationale"),
                                    "source_ref": a.get("source_ref"), "approver": a.get("approver"),
                                    "citation": _cite_adj(a, entity, as_of)})
        amt = abs(_num(a.get("amount")) or 0.0)
        period_revenue = sum((_num(ln["value"]) or 0) for ln in detail if ln["period"] == a["period"] and ln["statement"] == "income_statement" and mp.get((ln["raw_label"], ln["statement"]), {}).get("std_account") == "revenue")
        pct = (amt / abs(period_revenue) * 100.0) if period_revenue else None
        missing_expl = not (a.get("rationale") or "").strip() or not (a.get("source_ref") or "").strip()
        material_unapproved = (pct is None or pct >= _num(cfg["adjustment_materiality_pct"])) and not (a.get("approver") or "").strip()
        if missing_expl or material_unapproved:
            bad_adjustments.append({"adj_id": a.get("adj_id"), "type": a.get("type"),
                                    "amount": _num(a.get("amount")), "pct_of_revenue": round(pct, 2) if pct is not None else None,
                                    "citation": _cite_adj(a, entity, as_of)})

    normalized_accounts = []
    for _, slot in sorted(rollup.items()):
        adj_total = sum((r.get("amount") or 0.0) for r in slot["adjustments"])
        normalized_accounts.append({
            "std_account": slot["std_account"], "statement": slot["statement"],
            "period": slot["period"], "mapped_value": round(slot["mapped_value"], 2),
            "adjustments": slot["adjustments"], "adjustment_total": round(adj_total, 2),
            "normalized_value": round(slot["mapped_value"] + adj_total, 2),
            "provenance": sorted([p for p in slot["provenance"] if p]),
        })

    findings, not_evaluable, tie_out_detail = [], [], []

    def add(check, fired, severity, reason, evidence, context):
        findings.append({"check": check, "fired": bool(fired), "severity": severity,
                         "reason": reason, "evidence": evidence, "context": context})

    # 1. missing_provenance — a mapped detail line has no source_ref (untraceable to a cell)
    no_src = [ln for ln in detail if not (ln.get("source_ref") or "").strip()
              and mp.get((str(ln.get("raw_label")), str(ln.get("statement"))))]
    add("missing_provenance", bool(no_src), MED,
        (f"{len(no_src)} mapped line item(s) have no source reference (untraceable)"
         if no_src else "every mapped line item is traceable to a source cell"),
        [{"line_id": ln.get("line_id"), "raw_label": ln.get("raw_label"),
          "citation": _cite_line(ln, entity, as_of)} for ln in no_src],
        {"detail_lines": len(detail)})

    # 2. unmapped_line_item — source detail with no mapping (would be silently dropped)
    add("unmapped_line_item", bool(unmapped), MED,
        (f"{len(unmapped)} source line item(s) have no mapping to a standard account"
         if unmapped else "all source detail mapped to a standard account"),
        [{"line_id": u["line_id"], "raw_label": u["raw_label"], "citation": u["citation"]} for u in unmapped],
        {"unmapped_count": len(unmapped)})

    # 3. unexplained_adjustment — adjustment lacks rationale/source, or material w/o approver
    add("unexplained_adjustment", bool(bad_adjustments), MED,
        (f"{len(bad_adjustments)} normalization adjustment(s) lack rationale/source or are "
         f"material without an approver" if bad_adjustments else "adjustments explained, sourced, and approved"),
        bad_adjustments, {"materiality_pct": cfg["adjustment_materiality_pct"]})

    # 4. subtotal_tie_out_break — reported subtotal != sum of its declared components
    val_by_id = {str(ln.get("line_id")): _num(ln.get("value")) or 0.0 for ln in lines}
    breaks = []
    for st in subtotals:
        comps = st.get("components")
        if not comps:
            continue
        computed = sum(val_by_id.get(str(c), 0.0) for c in comps)
        reported = _num(st.get("value")) or 0.0
        diff = round(reported - computed, 2)
        within = abs(diff) <= tol
        tie_out_detail.append({"subtotal_line": st.get("line_id"), "raw_label": st.get("raw_label"),
                               "period": st.get("period"), "reported": round(reported, 2),
                               "computed": round(computed, 2), "diff": diff, "within_tolerance": within})
        if not within:
            breaks.append({"subtotal_line": st.get("line_id"), "raw_label": st.get("raw_label"),
                           "reported": round(reported, 2), "computed": round(computed, 2),
                           "diff": diff, "citation": _cite_line(st, entity, as_of)})
    add("subtotal_tie_out_break", bool(breaks), HIGH,
        (f"{len(breaks)} reported subtotal(s) do not reconcile to their captured components within "
         f"tolerance {tol}" if breaks else "reported subtotals reconcile to their components"),
        breaks, {"tie_out_tolerance": tol, "subtotals_checked": len(tie_out_detail)})

    # Reported anchors and reconstructed normalized balances are different checks.
    reported_bs, normalized_bs = [], []
    line_index = {row["line_id"]: row for row in lines}

    def leaves(line_id, trail=()):
        if line_id in trail:
            raise ValueError("cyclic subtotal component graph")
        row = line_index[line_id]
        if not row.get("is_subtotal"):
            return {line_id}
        if not row.get("components"):
            return None
        combined = set()
        for child in row["components"]:
            values = leaves(child, trail + (line_id,))
            if values is None or combined & values:
                return None
            combined |= values
        return combined

    for period in sorted({row["period"] for row in lines if row["statement"] == "balance_sheet"}):
        anchors = {row["role"]: row for row in subtotals if row["period"] == period and row.get("role") in ROLES}
        if set(anchors) != ROLES:
            not_evaluable.append({"check": "reported_balance_sheet_identity_break", "period": period, "why": "identity roles incomplete"})
            not_evaluable.append({"check": "balance_sheet_identity_break", "period": period, "why": "normalized reconstruction lacks complete role/component coverage"})
            continue
        a, l, e = (float(anchors[key]["value"]) for key in ("total_assets", "total_liabilities", "total_equity"))
        diff = round(a-l-e, 2)
        row = {"period": period, "total_assets": a, "total_liabilities": l, "total_equity": e, "diff": diff, "within_tolerance": abs(diff) <= tol, "citation": _cite_line(anchors["total_assets"], entity, as_of)}
        reported_bs.append(row)
        add("reported_balance_sheet_identity_break", abs(diff) > tol, HIGH, "Reported balance-sheet anchor identity for " + period, [row] if abs(diff) > tol else [], {"period": period, "tie_out_tolerance": tol})
        role_leaves = {key: leaves(anchor["line_id"]) for key, anchor in anchors.items()}
        complete = all(value is not None for value in role_leaves.values())
        account_roles = {}
        covered = set()
        if complete:
            for role, ids in role_leaves.items():
                if covered & ids:
                    complete = False
                covered |= ids
                for lid in ids:
                    ln = line_index[lid]
                    mapping = mp.get((ln["raw_label"], ln["statement"]))
                    if not mapping:
                        complete = False
                        continue
                    account = mapping["std_account"]
                    if account in account_roles and account_roles[account] != role:
                        complete = False
                    account_roles[account] = role
            expected = {ln["line_id"] for ln in detail if ln["statement"] == "balance_sheet" and ln["period"] == period}
            complete = complete and covered == expected and all(row["std_account"] in account_roles for row in normalized_accounts if row["statement"] == "balance_sheet" and row["period"] == period)
        if not complete:
            not_evaluable.append({"check": "balance_sheet_identity_break", "period": period, "why": "complete disjoint mapped detail/component coverage is required for normalized identity; raw anchors do not prove it"})
            continue
        values = {role: sum(row["normalized_value"] for row in normalized_accounts if row["statement"] == "balance_sheet" and row["period"] == period and account_roles[row["std_account"]] == role) for role in ROLES}
        diff = round(values["total_assets"] - values["total_liabilities"] - values["total_equity"], 2)
        row = {"period": period, **values, "diff": diff, "within_tolerance": abs(diff) <= tol, "citation": _cite_line(anchors["total_assets"], entity, as_of)}
        normalized_bs.append(row)
        add("balance_sheet_identity_break", abs(diff) > tol, HIGH, "Reconstructed normalized balance-sheet identity for " + period, [row] if abs(diff) > tol else [], {"period": period, "tie_out_tolerance": tol})

    fired = [f for f in findings if f["fired"]]
    fired_names = [f["check"] for f in fired]
    # deterministic readiness mapping (see references/domain-rules.md)
    if any(f["severity"] == HIGH for f in fired) or len(fired) >= _num(cfg["escalate_finding_count"]):
        readiness = HOLD
    elif fired or not_evaluable:
        readiness = NEEDS
    else:
        readiness = READY

    considerations = []
    if fired:
        considerations = [
            "a source subtotal that legitimately includes line items not in this extract (capture completeness)",
            "a rounding or presentation-scale difference within the source rather than a true break",
            "an adjustment pre-approved under a standing normalization-policy delegation",
            "an unmapped line that is genuinely immaterial or out of model scope",
            "a source cell whose reference is available in a later extract - confirm provenance",
        ]

    return {
        "normalization_id": f"fnorm-{entity}-{as_of}-0001",
        "entity_id": entity,
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "reporting_framework": doc.get("reporting_framework"),
        "currency": doc.get("currency"),
        "source_document": doc.get("source_document"),
        "normalized_accounts": normalized_accounts,
        "unmapped": unmapped,
        "tie_outs": tie_out_detail,
        "reported_balance_sheet_checks": reported_bs,
        "normalized_balance_sheet_checks": normalized_bs,
        "readiness_config": {"escalate_finding_count": cfg["escalate_finding_count"]},
        "limitations": ["Incomplete normalized identity coverage is not model-ready; reported anchor checks do not prove adjusted statements balance.", "Maps supplied extracts only; no accounting opinion or general framework conversion."],
        "findings": findings,
        "fired_findings": fired_names,
        "not_evaluable": not_evaluable,
        "suggested_readiness": readiness,
        "review_considerations": considerations,
        "disclaimer": DISCLAIMER,
    }


def _strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)

def _local_module(filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_local_" + filename.replace(".", "_"), Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def compute(doc):
    errors, warnings = _local_module("validate_input.py").validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    result = _calculate_native(doc)
    result["validation_warnings"] = warnings
    result["method_id"] = 'financials-normalizer'
    result["method_version"] = "0.2.0"
    result["result_origin"] = "local-analysis"
    result["review_status"] = "not-requested"
    result["execution_status"] = "not-performed"
    result["method_scope"] = 'financials-normalizer: bounded supplied-input local analysis; no source authentication, approval or execution'
    return _local_module("native_integrity.py").attach_source(result, doc)

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "financials_example.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
