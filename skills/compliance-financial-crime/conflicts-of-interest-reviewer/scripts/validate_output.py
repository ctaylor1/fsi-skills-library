#!/usr/bin/env python3
"""Deterministic output validation for conflicts-of-interest-reviewer.

Validates the final conflicts pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. This is the R3 fail-closed screen: a bad pack (one that decides,
clears, waives, closes, or files) must exit 1.

Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. Each finding's open_gap and residual_risk are RECOMPUTED from its own fired /
     inherent_severity / disclosure|control|approval status and must tie out (anti-tamper:
     a pack cannot under-state an unmitigated conflict by self-reporting a softer band).
  3. matter_residual_risk == deterministic max across the RECOMPUTED residuals.
  4. recommended_review_path == deterministic mapping from the recomputed residual + open gaps.
  5. No clearance / approval / waiver / closure / filing / determination language
     (narrative + notes + finding reasons).
  6. The standing disclaimer is present.
  7. mitigation_prompts present when any finding fired or any open gap exists.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

RANK = {"Low": 1, "Medium": 2, "High": 3}
BAND = {1: "Low", 2: "Medium", 3: "High"}
DISCLAIMER = ("Conflicts review and recommendations only; not a compliance determination, "
              "clearance, waiver, or approval. A qualified human adjudicator must decide. "
              "No matter has been closed and no filing has been made.")

# Decision / closure / filing / determination assertions that R3 must NOT make:
PROHIBITED_PATTERNS = [
    r"\bconflict (is )?(cleared|waived|approved)\b",
    r"\b(is|are) cleared\b", r"\bclear(ed)? to (proceed|trade|act|deal)\b",
    r"\bwaiver (is )?granted\b", r"\bgrant(ed)? (the |a )?waiver\b",
    r"\bwe (hereby )?approve\b", r"\bapproved to proceed\b", r"\bapprove the (conflict|matter|trade|request)\b",
    r"\bauthoriz(e|ed|ation) (to|is) (proceed|trade|act|granted)\b",
    r"\bcase (is )?closed\b", r"\bclose the (case|matter)\b", r"\bmatter (is )?closed\b",
    r"\bno further action (is )?(required|needed)\b", r"\bfinal (determination|disposition)\b",
    r"\bdisposition:? *(cleared|approved|closed|no conflict)\b",
    r"\bfile (a|an|the) (disclosure|report|form|u4|u5|attestation|sar)\b",
    r"\bsubmit(ted)? to (finra|the sec|the regulator)\b",
    r"\bthere is no conflict\b", r"\bno conflict exists\b",
    r"\binsider (trading|dealing)\b", r"\bmisused mnpi\b", r"\bengaged in insider\b",
]


def _review_path(matter_residual: str, has_gap: bool) -> str:
    if matter_residual == "High" or has_gap:
        return "Escalate to the conflicts/ethics committee (or designated compliance officer) for adjudication"
    if matter_residual == "Medium":
        return "Route to a compliance officer for review and disposition"
    return "Supervisor attestation and retention in the conflicts register"


def _fully_mitigated(f: dict) -> bool:
    """True only when disclosure AND control AND approval are all recorded complete."""
    return (f.get("disclosure_status") == "complete"
            and f.get("control_status") == "complete"
            and f.get("approval_status") == "complete")


def _expected_gap_residual(f: dict):
    """Recompute (open_gap, residual_risk) for a finding from its OWN fired / inherent_severity /
    disclosure|control|approval status, mirroring calculate_or_transform.compute(). Returns
    (None, None) when inherent_severity is not a valid band so the caller can fail closed.

    Anti-tamper: the fail-closed screen must not trust a finding's self-reported open_gap /
    residual_risk. Without this, a pack that under-states an unmitigated High conflict (open_gap
    forced to false, residual to Low) ties out against its own softened numbers and routes to the
    lightest review path instead of escalation.
    """
    if not f.get("fired"):
        return False, "Low"
    inherent = f.get("inherent_severity")
    if inherent not in RANK:
        return None, None
    gap = not _fully_mitigated(f)
    residual = inherent if gap else BAND[max(1, RANK[inherent] - 1)]
    return gap, residual


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    fired = [f for f in findings if f.get("fired")]

    for f in fired:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"fired finding {f.get('item_id')} ({f.get('conflict_type')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"fired finding {f.get('item_id')} evidence row missing citation")
        if f.get("residual_risk") not in RANK:
            errors.append(f"fired finding {f.get('item_id')} has invalid residual_risk {f.get('residual_risk')!r}")

    # Recompute each finding's open_gap + residual_risk from its own fired / inherent_severity /
    # disclosure|control|approval status and fail closed on any disagreement. The matter tie-outs
    # below consume these RECOMPUTED values (not the self-reported ones), so an inconsistent pack
    # cannot under-state an unmitigated conflict to route itself to a lighter review path.
    trusted = []  # (finding, expected_gap, expected_residual) for findings with a valid band
    for f in findings:
        exp_gap, exp_res = _expected_gap_residual(f)
        if exp_res is None:
            errors.append(f"finding {f.get('item_id')} has invalid/missing inherent_severity "
                          f"{f.get('inherent_severity')!r}; residual risk cannot be verified")
            continue
        if bool(f.get("open_gap")) != exp_gap:
            errors.append(f"finding {f.get('item_id')} open_gap {f.get('open_gap')!r} != deterministic "
                          f"{exp_gap!r} recomputed from disclosure/control/approval status")
        if f.get("residual_risk") != exp_res:
            band_note = "open gap; no mitigation credit" if exp_gap else "fully mitigated; one band credit"
            errors.append(f"finding {f.get('item_id')} residual_risk {f.get('residual_risk')!r} != "
                          f"deterministic {exp_res!r} (inherent {f.get('inherent_severity')!r}, {band_note})")
        trusted.append((f, exp_gap, exp_res))

    # deterministic matter residual tie-out (from RECOMPUTED residuals of fired findings)
    ranks = [RANK[res] for f, _gap, res in trusted if f.get("fired")]
    exp_matter = BAND[max(ranks)] if ranks else "Low"
    if pack.get("matter_residual_risk") != exp_matter:
        errors.append(f"matter_residual_risk {pack.get('matter_residual_risk')!r} != deterministic {exp_matter!r}")

    # deterministic review-path tie-out (from RECOMPUTED open gaps)
    has_gap = any(gap for _f, gap, _res in trusted)
    exp_path = _review_path(exp_matter, has_gap)
    if pack.get("recommended_review_path") != exp_path:
        errors.append(f"recommended_review_path != deterministic mapping (expected {exp_path!r})")

    # prohibited decision/closure/filing/determination language (not the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                          f"(R3 recommends + evidences; it does not decide/clear/close/file)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if (fired or has_gap) and not pack.get("mitigation_prompts"):
        errors.append("findings fired or gaps exist but no mitigation_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
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
