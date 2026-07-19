#!/usr/bin/env python3
"""Deterministic output validation for policy-procedure-gap-analyzer.

Validates the final gap-analysis pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. This is the R3 prohibited-decision screen: it fails closed on
any compliance determination, attestation, closure, or filing language, and confirms the
findings are evidenced and deterministically tied out.

Checks:
  1. Every finding has >= 1 cited evidence row (non-empty citation).
  2. Each finding.severity equals the deterministic mapping from finding_type + criticality.
  3. severity_counts tie out to the findings list.
  4. remediation_priority equals the deterministic mapping from severity_counts.
  5. No compliance determination / attestation / closure / filing language (narrative +
     notes + finding reasons + recommendations). The disclaimer field is not scanned.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Gap-analysis findings and recommendations only; not a compliance "
              "determination, attestation, or filing. Human adjudication required.")

BASE_SEVERITY = {
    "coverage_gap": "High", "parameter_conflict": "High",
    "evidence_gap": "Medium", "version_drift": "Medium", "stale_review": "Low",
}
_DROP = {"High": "Medium", "Medium": "Low", "Low": "Low"}

# Prohibited R3 assertions: a gap analysis evidences and recommends; it does not decide,
# attest, certify, close, or file.
DETERMINATION_PATTERNS = [
    r"\bfully compliant\b", r"\bis compliant\b", r"\bin full compliance\b",
    r"\bwe attest\b", r"\battest that\b", r"\bcertif(y|ies|ied) compliance\b",
    r"\bno gaps? (exist|remain|found|were found)\b", r"\bmeets all (regulatory )?requirements\b",
    r"\bsatisfies all\b", r"\bfinding(s)? closed\b", r"\bclose (this|the) finding\b",
    r"\bremediation complete\b", r"\bfiled? with the (regulator|examiner)\b",
    r"\bsubmit(ted)? to the (regulator|examiner)\b", r"\bsign(ed)? off\b",
    r"\bapproved for (the )?exam\b", r"\bno further action (is )?required\b",
    r"\bpasses the exam\b", r"\bself-certif",
]


def _severity(finding_type: str, criticality: str) -> str:
    base = BASE_SEVERITY.get(finding_type)
    if base is None:
        return "?"
    return _DROP[base] if criticality == "guidance" else base


def _expected_priority(counts: dict) -> str:
    if counts.get("High"):
        return "Priority-1"
    if counts.get("Medium"):
        return "Priority-2"
    if counts.get("Low"):
        return "Priority-3"
    return "None"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings")
    if not isinstance(findings, list):
        return ["missing or non-list 'findings'"]

    recomputed = {"High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        fid = f.get("finding_id", "?")
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {fid} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {fid} evidence row missing citation")
        exp = _severity(f.get("finding_type", ""), f.get("criticality", "control"))
        if f.get("severity") != exp:
            errors.append(f"finding {fid} severity {f.get('severity')!r} != deterministic {exp!r} "
                          f"for type={f.get('finding_type')!r} criticality={f.get('criticality')!r}")
        if f.get("severity") in recomputed:
            recomputed[f["severity"]] += 1

    counts = pack.get("severity_counts") or {}
    for band in ("High", "Medium", "Low"):
        if int(counts.get(band, 0)) != recomputed[band]:
            errors.append(f"severity_counts[{band}]={counts.get(band)} != actual {recomputed[band]}")

    exp_prio = _expected_priority(recomputed)
    if pack.get("remediation_priority") != exp_prio:
        errors.append(f"remediation_priority {pack.get('remediation_priority')!r} != deterministic "
                      f"{exp_prio!r} for counts={recomputed}")

    # Scan free text (narrative + notes + reasons + recommendations), NOT the disclaimer field.
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("reason", "")) for f in findings]
        + [str(f.get("recommendation", "")) for f in findings]
    )
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/attestation/closure/filing language detected: "
                          f"{m.group(0)!r} (R3 evidences and recommends; a human adjudicates)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_pack_example.json"
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
