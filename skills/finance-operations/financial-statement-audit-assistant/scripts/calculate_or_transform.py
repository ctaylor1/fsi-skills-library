#!/usr/bin/env python3
"""Deterministic audit working-paper drafter for financial-statement-audit-assistant.

Given a de-identified audit request (engagement, planning/materiality, financial-statement
captions, trial balance, a sampling population, and any known misstatements), this engine:

  1. Ties each financial-statement caption to its trial-balance support and flags any
     difference above the clearly-trivial threshold (footing / tie-out).
  2. Builds a documented monetary-unit sampling plan: 100%-examined key items at/above the
     sampling interval, plus a systematic selection over the residual population with a
     fixed random start. Reports examined value and coverage.
  3. Aggregates known + projected misstatements and compares them to overall materiality,
     stating ONLY that the auditor must evaluate the result -- it never concludes.
  4. Assembles the controlled working-paper sections, carries through the recorded human
     approvals, and stamps the standing limitation note.

It NEVER expresses or implies an audit opinion, concludes on fair presentation, materiality,
or going concern, signs off on behalf of a human, or delivers/files anything. Every tie-out
and finding carries a citation. Output is a draft for engagement-team review and partner
approval.

Usage: python calculate_or_transform.py audit_request.json | --selftest
Prints the working-paper draft JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft audit working papers only. No audit opinion is expressed or implied; no "
    "conclusion on fair presentation, materiality, or going concern has been reached. "
    "Requires engagement-team review and partner approval before any reliance or external "
    "delivery."
)
REQUIRED_SECTIONS = [
    "engagement_and_scope", "planning_and_materiality", "source_mapping_and_tieouts",
    "sampling_approach", "testing_results", "misstatement_summary",
    "open_items_and_requests", "approvals_and_signoff",
]


def _tie_outs(doc):
    tb = {r.get("account"): r for r in (doc.get("trial_balance") or [])}
    trivial = float(doc.get("planning", {}).get("clearly_trivial_threshold", 0) or 0)
    rows, open_items = [], []
    for fs in doc.get("financial_statements") or []:
        accts = fs.get("tb_accounts") or []
        citations = [fs.get("source_ref", "?")]
        tb_sum = 0.0
        missing = []
        for a in accts:
            if a in tb:
                tb_sum += float(tb[a].get("balance") or 0)
                citations.append(tb[a].get("source_ref", f"tb:{a}"))
            else:
                missing.append(a)
        diff = round(float(fs.get("fs_amount") or 0) - tb_sum, 2)
        if missing:
            status = "unmapped"
            open_items.append(
                f"{fs.get('caption')}: trial-balance account(s) {', '.join(missing)} not found; "
                "obtain mapping before relying on this tie-out."
            )
        elif abs(diff) > trivial:
            status = "difference"
        else:
            status = "tie"
        rows.append({
            "caption": fs.get("caption"), "assertion": fs.get("assertion"),
            "fs_amount": float(fs.get("fs_amount") or 0), "tb_sum": tb_sum,
            "difference": diff, "threshold": trivial, "status": status,
            "citations": citations,
        })
    return rows, open_items


def _sampling(doc):
    pop = doc.get("population") or {}
    items = pop.get("items") or []
    plan = doc.get("planning") or {}
    tm = float(plan.get("tolerable_misstatement") or 0)
    rf = float(plan.get("reliability_factor") or 0)
    if not items or tm <= 0 or rf <= 0:
        return {"status": "not-performed",
                "reason": "no population or invalid tolerable_misstatement/reliability_factor",
                "key_items": [], "sampled_items": []}
    interval = int(round(tm / rf))
    seed = int(plan.get("sample_seed", 0) or 0)
    start = seed % interval if interval else 0

    key_items, residual = [], []
    for it in items:
        amt = abs(float(it.get("amount") or 0))
        row = {"item_id": it.get("item_id"), "amount": amt, "source_ref": it.get("source_ref", "?")}
        if amt >= interval:
            key_items.append(row)
        else:
            residual.append(row)

    residual_total = sum(r["amount"] for r in residual)
    points, p = [], start
    while p < residual_total:
        points.append(p)
        p += interval
    sampled, cum = [], 0.0
    for r in residual:
        lo, hi = cum, cum + r["amount"]
        hit = next((pt for pt in points if lo <= pt < hi), None)
        if hit is not None:
            sampled.append({**r, "hit_at": hit})
        cum = hi

    pop_total = sum(abs(float(i.get("amount") or 0)) for i in items)
    examined = sum(k["amount"] for k in key_items) + sum(s["amount"] for s in sampled)
    coverage = round(examined / pop_total * 100, 1) if pop_total else 0.0
    return {
        "status": "planned",
        "population_label": pop.get("label"),
        "assertion": pop.get("assertion"),
        "population_total": pop_total,
        "population_count": len(items),
        "tolerable_misstatement": tm,
        "reliability_factor": rf,
        "sampling_interval": interval,
        "random_start": start,
        "key_item_threshold": interval,
        "key_items": key_items,
        "sampled_items": sampled,
        "sample_size": len(key_items) + len(sampled),
        "examined_value": examined,
        "coverage_pct": coverage,
        "population_source": pop.get("source_ref", "?"),
    }


def _misstatements(doc, tieouts):
    plan = doc.get("planning") or {}
    trivial = float(plan.get("clearly_trivial_threshold", 0) or 0)
    om = float(plan.get("overall_materiality") or 0)
    findings = []
    # tie-out differences become findings (each cites its tie-out sources)
    for t in tieouts:
        if t["status"] == "difference":
            findings.append({
                "finding_id": f"TIE-{t['caption'][:6].upper().replace(' ', '')}",
                "description": f"{t['caption']} caption differs from trial-balance support by {t['difference']}",
                "amount": abs(t["difference"]), "type": "factual",
                "disposition": "open-for-auditor-evaluation", "citations": t["citations"],
            })
    # carried-through known misstatements / exceptions
    for m in doc.get("known_misstatements") or []:
        findings.append({
            "finding_id": m.get("finding_id", "MS"),
            "description": m.get("description", ""),
            "amount": abs(float(m.get("amount") or 0)),
            "type": m.get("type", "factual"),
            "disposition": "open-for-auditor-evaluation",
            "citations": [m.get("source_ref", "?")],
        })
    # de-dup findings that describe the same underlying tie-out difference by amount+type
    seen, deduped = set(), []
    for f in findings:
        key = (round(f["amount"], 2), f["type"], f["description"][:24])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)

    above_trivial = [f for f in deduped if f["amount"] > trivial]
    aggregate_known = round(sum(f["amount"] for f in above_trivial if f["type"] == "factual"), 2)
    aggregate_projected = round(sum(f["amount"] for f in above_trivial if f["type"] == "projected"), 2)
    aggregate_total = round(aggregate_known + aggregate_projected, 2)
    status = "at-or-above-overall-materiality" if aggregate_total >= om > 0 else "below-overall-materiality"
    summary = {
        "clearly_trivial_threshold": trivial,
        "overall_materiality": om,
        "aggregate_known": aggregate_known,
        "aggregate_projected": aggregate_projected,
        "aggregate_total": aggregate_total,
        "status": status,
        "note": ("Comparison is presented for auditor evaluation only. This is not a "
                 "conclusion on the financial statements; the engagement team and partner "
                 "must evaluate identified and uncorrected misstatements."),
    }
    return deduped, summary


def _sections(doc, tieouts, sample, findings, ms):
    eng = doc.get("engagement") or {}
    plan = doc.get("planning") or {}
    n_diff = sum(1 for t in tieouts if t["status"] == "difference")
    n_tie = sum(1 for t in tieouts if t["status"] == "tie")
    return {
        "engagement_and_scope": (
            f"{eng.get('entity')} - {eng.get('period')} ({eng.get('framework')}, "
            f"{eng.get('reporting_currency')}). Support working paper covering tie-out, "
            "sampling, and misstatement accumulation. No opinion is expressed."
        ),
        "planning_and_materiality": (
            f"Overall materiality {plan.get('overall_materiality')}; performance materiality "
            f"{plan.get('performance_materiality')}; clearly-trivial threshold "
            f"{plan.get('clearly_trivial_threshold')}; tolerable misstatement "
            f"{plan.get('tolerable_misstatement')}. Values are inputs, not judgments."
        ),
        "source_mapping_and_tieouts": (
            f"{n_tie} caption(s) tie to the trial balance within threshold; {n_diff} "
            "difference(s) flagged for follow-up. Every tie-out cites its sources."
        ),
        "sampling_approach": (
            f"Monetary-unit sampling: interval {sample.get('sampling_interval')} "
            f"(tolerable/reliability), random start {sample.get('random_start')}. "
            f"{len(sample.get('key_items', []))} key item(s) examined 100%; "
            f"{len(sample.get('sampled_items', []))} residual selection(s). Examined coverage "
            f"{sample.get('coverage_pct')}%." if sample.get("status") == "planned"
            else "Sampling not performed (no eligible population or invalid parameters)."
        ),
        "testing_results": (
            f"{len(findings)} finding(s) recorded, each open for auditor evaluation and each "
            "carrying a citation. Results are evidence for the engagement team, not a conclusion."
        ),
        "misstatement_summary": (
            f"Aggregate accumulated misstatement {ms['aggregate_total']} vs. overall materiality "
            f"{ms['overall_materiality']} ({ms['status']}). Presented for auditor evaluation only."
        ),
        "open_items_and_requests": (
            "Outstanding client requests and unresolved tie-out/mapping items are listed in "
            "open_items; obtain support before reliance."
        ),
        "approvals_and_signoff": (
            "Preparer and engagement reviewer sign-off are recorded in approvals. Partner "
            "approval is required before any reliance or external delivery; this draft does "
            "not deliver, file, or submit anything."
        ),
    }


def build(doc: dict) -> dict:
    tieouts, open_items = _tie_outs(doc)
    sample = _sampling(doc)
    findings, ms = _misstatements(doc, tieouts)
    sections = _sections(doc, tieouts, sample, findings, ms)
    approvals = doc.get("approvals") or []
    narrative = (
        "Draft working paper assembled from documented sources. Tie-outs, sampling, and "
        "misstatement accumulation are presented as evidence for auditor evaluation. No "
        "opinion, and no conclusion on fair presentation, materiality, or going concern, is "
        "stated. Partner approval is required before any reliance or external delivery."
    )
    summary = {
        "tieout_count": len(tieouts),
        "tieout_differences": sum(1 for t in tieouts if t["status"] == "difference"),
        "sample_size": sample.get("sample_size", 0),
        "coverage_pct": sample.get("coverage_pct", 0.0),
        "finding_count": len(findings),
        "misstatement_status": ms["status"],
    }
    return {
        "config_version": doc.get("config_version"),
        "engagement": doc.get("engagement"),
        "sections": sections,
        "tieouts": tieouts,
        "sample": sample,
        "findings": findings,
        "misstatement_summary": ms,
        "open_items": open_items,
        "approvals": approvals,
        "narrative": narrative,
        "standing_note": STANDING_NOTE,
        "summary": summary,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "audit_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        out = build(doc)
        # A minimal invariant self-check so --selftest reports pass/fail like the validators.
        errors = []
        for s in REQUIRED_SECTIONS:
            if not out["sections"].get(s):
                errors.append(f"missing section {s}")
        for t in out["tieouts"]:
            if not t["citations"]:
                errors.append(f"tie-out {t['caption']} missing citation")
        for f in out["findings"]:
            if not f["citations"]:
                errors.append(f"finding {f['finding_id']} missing citation")
        print(json.dumps(out, indent=2))
        for e in errors:
            print("ERROR", e)
        print(f"working-paper build self-check: {len(errors)} error(s)")
        return 1 if errors else 0
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
