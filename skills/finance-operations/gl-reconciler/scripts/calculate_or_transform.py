#!/usr/bin/env python3
"""Deterministic GL-to-subledger reconciliation engine for gl-reconciler.

Matches GL records to subledger/source records by match_key, classifies unmatched or
disagreeing items into a fixed break taxonomy, preserves lineage (source citations on
every break), computes tie-outs, and emits PROPOSED-ONLY correction journal entries.

IMPORTANT: Corrections are PROPOSALS. This engine never posts, books, or writes a journal
entry to any system of record. Every proposed correction carries status "PROPOSED"; the
actual posting is a human/authorized-system action after review.

Break taxonomy (see references/domain-rules.md):
  timing_difference | amount_mismatch | unrecorded_in_gl | unsupported_in_gl | duplicate

Tie-out invariant: sum(break gl_impact) == (gl_total - subledger_total); residual == 0.
Each correctable break's adjustment_amount == -gl_impact (the correction offsets the break).

Usage:
  python calculate_or_transform.py reconciliation.json    # prints reconciliation JSON
  python calculate_or_transform.py --selftest             # runs bundled fixture + invariants
Prints the reconciliation JSON to stdout (file/stdin mode). In --selftest mode prints
self-check results ending in a line "reconciliation self-test: N error(s)" (exit 0/1).
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "amount_tolerance": 0.01,
    "date_tolerance_days": 5,
    "materiality_threshold": 100.0,
    "recon_suspense_account": "1990-reconciliation-suspense",
}
BREAK_TYPES = ("timing_difference", "amount_mismatch", "unrecorded_in_gl",
               "unsupported_in_gl", "duplicate")
DISCLAIMER = ("Reconciliation and proposed corrections only; no journal entry has been "
              "posted to the general ledger. Proposed corrections require human review and "
              "authorized posting.")


def _round(x: float) -> float:
    return round(float(x) + 0.0, 2)


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(system: str, r: dict) -> str:
    return f"{system}:{r.get('source_ref', '?')}@{r.get('date', '?')}"


def _fingerprint(doc: dict, cfg: dict) -> str:
    """Stable content hash of the normalized inputs — the basis of an idempotent id."""
    def norm(rows):
        return sorted(
            [{"entry_id": r.get("entry_id"), "match_key": r.get("match_key"),
              "account": r.get("account"), "date": str(r.get("date")),
              "amount": _round(r.get("amount", 0)), "currency": (r.get("currency") or "").upper(),
              "source_ref": r.get("source_ref")} for r in rows],
            key=lambda r: (str(r["entry_id"]),))
    payload = {
        "entity": doc.get("entity"), "account": doc.get("account"),
        "as_of": doc.get("as_of"), "config_version": doc.get("config_version"),
        "currency": (doc.get("currency") or "").upper(),
        "config": {k: cfg[k] for k in sorted(cfg)},
        "gl": norm(doc.get("gl_entries") or []),
        "subledger": norm(doc.get("subledger_entries") or []),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sort_key(r: dict):
    return (str(r.get("date")), str(r.get("entry_id")))


def _proposed_correction(pje_id: str, break_id: str, break_type: str, match_key: str,
                         gl_impact: float, recon_account: str, suspense: str) -> dict:
    """Build a PROPOSED (never posted) balanced correction JE that offsets gl_impact."""
    adjustment = _round(-gl_impact)  # change to the recon account to reach subledger
    if adjustment >= 0:  # increase the recon account
        lines = [{"account": recon_account, "dr": _round(adjustment), "cr": 0.0},
                 {"account": suspense, "dr": 0.0, "cr": _round(adjustment)}]
    else:  # decrease the recon account
        mag = _round(-adjustment)
        lines = [{"account": recon_account, "dr": 0.0, "cr": mag},
                 {"account": suspense, "dr": mag, "cr": 0.0}]
    return {
        "proposed_je_id": pje_id,
        "break_id": break_id,
        "status": "PROPOSED",
        "adjustment_amount": adjustment,
        "lines": lines,
        "memo": (f"Adjust {recon_account} by {adjustment:+.2f} to agree to subledger for "
                 f"{match_key} ({break_type}). PROPOSED - requires review and authorized "
                 f"posting; not posted by this skill."),
    }


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    amt_tol = float(cfg["amount_tolerance"])
    date_tol = int(cfg["date_tolerance_days"])
    mat_thr = float(cfg["materiality_threshold"])
    suspense = str(cfg["recon_suspense_account"])
    recon_account = doc["account"]

    gl_rows = list(doc.get("gl_entries") or [])
    sl_rows = list(doc.get("subledger_entries") or [])
    gl_total = _round(sum(float(r["amount"]) for r in gl_rows))
    sl_total = _round(sum(float(r["amount"]) for r in sl_rows))
    difference = _round(gl_total - sl_total)

    gl_by_key: dict = {}
    sl_by_key: dict = {}
    for r in gl_rows:
        gl_by_key.setdefault(str(r.get("match_key")), []).append(r)
    for r in sl_rows:
        sl_by_key.setdefault(str(r.get("match_key")), []).append(r)

    breaks: list = []
    matched_count = 0
    seq = 0

    def new_break(btype, match_key, gl_impact, gl_row=None, sl_row=None, note=None):
        nonlocal seq
        seq += 1
        gl_impact = _round(gl_impact)
        lineage = []
        b = {
            "break_id": f"BRK-{seq:04d}",
            "type": btype,
            "match_key": match_key,
            "gl_impact": gl_impact,
            "material": abs(gl_impact) >= mat_thr,
        }
        if gl_row is not None:
            b["gl"] = {"entry_id": gl_row.get("entry_id"), "amount": _round(gl_row["amount"]),
                       "date": gl_row.get("date"), "citation": _cite("gl", gl_row)}
            lineage.append(_cite("gl", gl_row))
        if sl_row is not None:
            b["subledger"] = {"entry_id": sl_row.get("entry_id"), "amount": _round(sl_row["amount"]),
                              "date": sl_row.get("date"), "citation": _cite("subledger", sl_row)}
            lineage.append(_cite("subledger", sl_row))
        b["lineage"] = lineage
        if note:
            b["note"] = note
        # timing_difference is a documented reconciling item — no correction proposed
        if btype == "timing_difference":
            b["requires_correction"] = False
            b["proposed_correction"] = None
        else:
            b["requires_correction"] = True
            b["proposed_correction"] = _proposed_correction(
                f"PJE-{seq:04d}", b["break_id"], btype, match_key, gl_impact,
                recon_account, suspense)
        breaks.append(b)

    for key in sorted(set(gl_by_key) | set(sl_by_key)):
        gl_list = sorted(gl_by_key.get(key, []), key=_sort_key)
        sl_list = sorted(sl_by_key.get(key, []), key=_sort_key)
        npair = min(len(gl_list), len(sl_list))
        for i in range(npair):
            g, s = gl_list[i], sl_list[i]
            ga, sa = float(g["amount"]), float(s["amount"])
            if abs(ga - sa) > amt_tol:
                new_break("amount_mismatch", key, ga - sa, gl_row=g, sl_row=s,
                          note=f"GL {ga:.2f} vs subledger {sa:.2f} (tolerance {amt_tol})")
            elif abs((_parse_dt(g["date"]) - _parse_dt(s["date"])).days) > date_tol:
                new_break("timing_difference", key, ga - sa, gl_row=g, sl_row=s,
                          note="matched amounts; posting dates differ beyond cutoff — clears next period")
            else:
                matched_count += 1
        # leftovers: duplicates (a pair existed) vs one-sided items
        for g in gl_list[npair:]:
            if npair >= 1:
                new_break("duplicate", key, float(g["amount"]), gl_row=g,
                          note="extra GL entry beyond the matched pair (duplicate posting)")
            else:
                new_break("unsupported_in_gl", key, float(g["amount"]), gl_row=g,
                          note="GL entry with no subledger support")
        for s in sl_list[npair:]:
            if npair >= 1:
                new_break("duplicate", key, -float(s["amount"]), sl_row=s,
                          note="extra subledger entry beyond the matched pair (duplicate)")
            else:
                new_break("unrecorded_in_gl", key, -float(s["amount"]), sl_row=s,
                          note="subledger item not yet recorded in the GL")

    breaks_total = _round(sum(b["gl_impact"] for b in breaks))
    residual = _round(difference - breaks_total)
    corrections = [b["proposed_correction"] for b in breaks if b.get("proposed_correction")]
    corrected_gl_total = _round(gl_total + sum(c["adjustment_amount"] for c in corrections))

    by_type = {t: sum(1 for b in breaks if b["type"] == t) for t in BREAK_TYPES}
    by_type = {t: n for t, n in by_type.items() if n}

    fp = _fingerprint(doc, cfg)
    recon_id = f"glr-{doc['entity']}-{doc['account']}-{doc['as_of']}-{fp[:8]}"

    return {
        "reconciliation_id": recon_id,
        "entity": doc["entity"],
        "account": doc["account"],
        "as_of": doc["as_of"],
        "currency": doc.get("currency"),
        "config_version": doc.get("config_version"),
        "input_fingerprint": fp,
        "tie_out": {
            "gl_total": gl_total,
            "subledger_total": sl_total,
            "difference": difference,
            "breaks_total_gl_impact": breaks_total,
            "residual": residual,
            "corrected_gl_total": corrected_gl_total,
            "ties_out": residual == 0.0,
            "status": "clean_tie_out" if not breaks else "reconciled_with_breaks",
        },
        "matched_count": matched_count,
        "breaks": breaks,
        "proposed_corrections": corrections,
        "summary": {
            "total_breaks": len(breaks),
            "by_type": by_type,
            "material_breaks": sum(1 for b in breaks if b["material"]),
            "corrections_proposed": len(corrections),
        },
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reconciliation_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors = []
    t = out["tie_out"]
    if t["residual"] != 0.0:
        errors.append(f"tie-out residual {t['residual']} != 0 (breaks do not explain the difference)")
    if t["breaks_total_gl_impact"] != t["difference"]:
        errors.append("sum of break gl_impact != GL-subledger difference")
    if t["corrected_gl_total"] != t["subledger_total"]:
        errors.append("corrected GL total does not equal subledger total after proposed corrections")
    for b in out["breaks"]:
        if b["type"] not in BREAK_TYPES:
            errors.append(f"{b['break_id']}: type {b['type']!r} not in taxonomy")
        if not b["lineage"]:
            errors.append(f"{b['break_id']}: no lineage citation")
        c = b.get("proposed_correction")
        if b["type"] == "timing_difference":
            if c is not None:
                errors.append(f"{b['break_id']}: timing_difference must not carry a correction")
        else:
            if not c or c.get("status") != "PROPOSED":
                errors.append(f"{b['break_id']}: correction missing or not PROPOSED")
            elif _round(c["adjustment_amount"]) != _round(-b["gl_impact"]):
                errors.append(f"{b['break_id']}: adjustment does not offset gl_impact")
    # idempotency: recompute must be identical
    if json.dumps(compute(doc), sort_keys=True) != json.dumps(out, sort_keys=True):
        errors.append("non-idempotent: recompute produced a different result")
    for e in errors:
        print("ERROR", e)
    print(f"reconciliation self-test: {len(errors)} error(s)")
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
