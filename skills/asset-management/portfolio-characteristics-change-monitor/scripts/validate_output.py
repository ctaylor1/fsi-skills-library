#!/usr/bin/env python3
"""Deterministic output validation for portfolio-characteristics-change-monitor.

Validates the final change-and-exception packet (the calculate_or_transform core + a
narrative) before it is presented or delivered. This is the R2 prohibited-decision screen:
the skill evidences drift, it never directs an action or decides a limit. Checks:
  1. Every exception has >= 1 cited evidence row.
  2. suggested_priority equals the deterministic mapping from exceptions + routing.
  3. No rebalancing-direction, limit-modification, breach-determination, or advice language
     (narrative + reasons + notes + handoff reason).
  4. The standing disclaimer is present.
  5. If any characteristic is routed for limit proximity, a handoff to
     investment-mandate-reviewer is present and covers every routed item (breaches must be
     routed, never swallowed or self-adjudicated).

Usage:
  python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATE_EXCEPTION_COUNT = 4
ROUTING_SKILL = "investment-mandate-reviewer"
DISCLAIMER = ("Change and exception evidence only; not a rebalancing instruction or a "
              "compliance determination. No trade, rebalancing, or limit change has been "
              "made or directed.")

# Directive / decision assertions an R2 analyze-&-review skill must not make. These match
# instruction forms ("sell the ...", "raise the limit"), not neutral description of drift or
# the disclaimer's own "no rebalancing ... has been directed".
DIRECTION_PATTERNS = [
    r"\brebalance (the|this|to|into|toward|towards|down|up)\b",
    r"\bshould rebalance\b", r"\brecommend(?:ing)? (?:a )?rebalanc", r"\bdirect(?:ing)? (?:a )?rebalanc",
    r"\breweight(?:ing)? (?:the|to|toward)\b",
    r"\bsell (?:the|down|off|to|out|into)\b", r"\bbuy (?:more|the|into|back)\b",
    r"\btrim (?:the|to|down|back)\b", r"\badd to (?:the )?position\b",
    r"\b(?:reduce|increase|cut|raise) (?:the )?(?:position|weight|exposure|allocation) (?:in|to|toward)\b",
    r"\bexecute (?:the )?(?:trade|order|rebalanc)", r"\bplace (?:the )?(?:trade|order)\b",
    r"\b(?:raise|lower|loosen|widen|relax|modify|change|override|adjust|reset|update) the (?:limit|band|threshold|mandate)\b",
    r"\b(?:limit|band|threshold) (?:should|to) be (?:raised|lowered|widened|loosened|relaxed|changed)\b",
    r"\bis in breach\b", r"\bbreaches the (?:mandate|limit)\b", r"\bviolates the (?:mandate|limit)\b",
    r"\bmandate violation\b", r"\bin violation of\b", r"\bconfirmed breach\b",
    r"\byou should (?:buy|sell|rebalance|reweight)\b", r"\bwe recommend (?:buying|selling|rebalancing)\b",
]


def _expected_priority(exceptions: list, route_items: list) -> str:
    if route_items or len(exceptions) >= ESCALATE_EXCEPTION_COUNT:
        return "Elevated"
    return "Review" if exceptions else "Informational"


def _validate_legacy(pack: dict) -> list[str]:
    errors: list[str] = []
    exceptions = pack.get("exceptions") or []
    route_items = pack.get("route_to_compliance") or []

    for e in exceptions:
        ev = e.get("evidence") or []
        if not ev:
            errors.append(f"exception {e.get('characteristic')} has no evidence")
        for row in ev:
            if not str(row.get("citation") or "").strip():
                errors.append(f"exception {e.get('characteristic')} evidence row missing citation")

    exp = _expected_priority(exceptions, route_items)
    if pack.get("suggested_priority") != exp:
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic "
                      f"{exp!r} for {len(exceptions)} exception(s), {len(route_items)} routed")

    # free-text screen (narrative + notes + exception reasons + handoff reason), NOT disclaimer
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", "")),
                     str((pack.get("handoff") or {}).get("reason", ""))]
                    + [str(e.get("reason", "")) for e in exceptions])
    for pat in DIRECTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"direction/limit/determination language detected: {m.group(0)!r} "
                          "(R2 evidences drift; it does not direct trades, set limits, or adjudicate breaches)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if route_items:
        handoff = pack.get("handoff") or {}
        if handoff.get("skill") != ROUTING_SKILL:
            errors.append(f"route_to_compliance present but no handoff to {ROUTING_SKILL} "
                          "(limit-proximity items must be routed, not self-adjudicated)")
        else:
            handed = {(i.get("family"), i.get("key")) for i in (handoff.get("items") or [])}
            for i in route_items:
                if (i.get("family"), i.get("key")) not in handed:
                    errors.append(f"routed item {i.get('characteristic')} missing from handoff.items")

    return errors


def validate(pack: dict, source_doc: dict | None = None) -> list[str]:
    """Require detached original input; do not authenticate it or approve narrative."""
    import runpy
    try:
        errors = _validate_legacy(pack)
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        return [f"malformed output: {exc}"]
    engine = runpy.run_path(str(Path(__file__).with_name("calculate_or_transform.py")))
    integrity = runpy.run_path(str(Path(__file__).with_name("native_integrity.py")))
    integrity["validate_reconstruction"](pack, engine["compute"], errors, original_input=source_doc)
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "packet_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    source_doc = None
    if "--input" in argv:
        source_doc = json.loads(Path(argv[argv.index("--input") + 1]).read_text(encoding="utf-8"))
    errors = validate(pack, source_doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
