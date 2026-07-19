#!/usr/bin/env python3
"""Deterministic output validation for operational-risk-event-analyzer.

Validates the final analysis pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. This is the R3 fail-closed screen. Checks:
  1. Impact arithmetic ties out (net loss, total impact recomputed from the pack).
  2. severity_band equals the deterministic mapping from banding amount + thresholds +
     escalation flags.
  3. Escalation flags do not under-flag relative to the thresholds (monotonic check).
  4. Every finding has >= 1 cited evidence row.
  5. requires_human_adjudication is present and true (R3 mandatory adjudication).
  6. No decision / closure / filing / posting language (narrative + findings + remediation).
  7. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_KEY = "not a risk decision or regulatory filing"
# Autonomous decision / closure / filing / system-of-record language an R3 skill must not use.
DECISION_PATTERNS = [
    r"\bcase (is )?closed\b", r"\bclose(d)? the case\b", r"\bevent (is )?closed\b",
    r"\bwe (have )?filed\b", r"\bfiled the (regulatory )?report\b",
    r"\bsubmitted to the regulator\b", r"\bposted to the (general ledger|gl)\b",
    r"\bjournal entry (has been |was )?posted\b", r"\bfinal determination\b",
    r"\brisk (is )?accepted\b", r"\bwrite-?off approved\b", r"\battestation (is )?approved\b",
    r"\bloss (is )?confirmed and closed\b", r"\bremediation (is )?complete(d)? and closed\b",
    r"\bsign-?off complete\b",
]


def _expected_severity(pack: dict) -> str:
    imp = pack.get("impact") or {}
    thr = pack.get("thresholds") or {}
    esc = pack.get("escalation") or {}
    ba = imp.get("banding_amount")
    board = bool(esc.get("board_notifiable"))
    reg = bool(esc.get("regulatory_reporting_candidate"))
    if ba is None:
        return "Critical" if board else ("High" if reg else "Low")
    if ba >= thr.get("critical_threshold", float("inf")) or board:
        return "Critical"
    if ba >= thr.get("high_threshold", float("inf")) or reg:
        return "High"
    if ba >= thr.get("moderate_threshold", float("inf")):
        return "Moderate"
    return "Low"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    imp = pack.get("impact") or {}
    thr = pack.get("thresholds") or {}
    esc = pack.get("escalation") or {}

    # 1. arithmetic tie-out
    gross = _num(imp.get("gross_loss"))
    rec = _num(imp.get("total_recoveries"))
    net = _num(imp.get("net_loss"))
    ind = _num(imp.get("indirect_costs"))
    tot = _num(imp.get("total_impact"))
    if None not in (gross, rec, net):
        exp_net = round(max(gross - rec, 0.0), 2)
        if round(net, 2) != exp_net:
            errors.append(f"net_loss tie-out failed: stated {net} != recomputed {exp_net}")
    if None not in (net, ind, tot):
        exp_tot = round(net + ind, 2)
        if round(tot, 2) != exp_tot:
            errors.append(f"total_impact tie-out failed: stated {tot} != recomputed {exp_tot}")

    # 2. severity band
    exp_sev = _expected_severity(pack)
    if pack.get("severity_band") != exp_sev:
        errors.append(f"severity_band {pack.get('severity_band')!r} != deterministic {exp_sev!r}")

    # 3. escalation must not under-flag versus thresholds
    ba = imp.get("banding_amount")
    if ba is not None:
        if _num(ba) >= thr.get("regulatory_reporting_threshold", float("inf")) and not esc.get("regulatory_reporting_candidate"):
            errors.append("regulatory_reporting_candidate under-flagged: banding amount meets the reporting threshold")
        if _num(ba) >= thr.get("board_notify_threshold", float("inf")) and not esc.get("board_notifiable"):
            errors.append("board_notifiable under-flagged: banding amount meets the board-notify threshold")

    # 4. every finding cited
    findings = pack.get("findings") or []
    if not findings:
        errors.append("no findings present")
    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('id')} has no evidence")
        for row in ev:
            if not str(row.get("citation", "")).strip():
                errors.append(f"finding {f.get('id')} evidence row missing citation")

    # 5. mandatory human adjudication
    if pack.get("requires_human_adjudication") is not True:
        errors.append("requires_human_adjudication must be present and true (R3 mandatory adjudication)")

    # 6. decision/closure/filing language screen (not the disclaimer field)
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(f.get("statement", "")) for f in findings]
    text_parts += [str(r.get("recommendation", "")) for r in (pack.get("remediation_recommendations") or [])]
    text = " ".join(text_parts)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} (R3 recommends, does not decide/close/file)")

    # 7. standing disclaimer
    disc = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER_KEY not in disc:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
