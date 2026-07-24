#!/usr/bin/env python3
"""Deterministic output validation for position-cash-reconciliation-assistant.

Validates a finished reconciliation pack (the calculate_or_transform core + narrative) before it
is presented or delivered. Fails closed on any miss. Checks:

  1. TIE-OUTS      - per reconciliation line (match_key) breaks fully explain the internal-vs-
                     external difference (residual == 0); corrected internal ties to external
                     after proposed items, leaving only documented pending / routed items; each
                     proposed item's adjustment offsets its break_amount.
  2. BREAK TAXONOMY- every break's type is in the fixed taxonomy and carries an id, break_amount,
                     unit, material flag, and lineage.
  3. LINEAGE       - every break cites source rows (internal:/external:) it was derived from.
  4. IDEMPOTENCY   - reconciliation_id is a pure function of stated inputs (entity/as_of +
                     input_fingerprint); no timestamp/random component.
  5. PROPOSED-ONLY / PROHIBITED SCREEN (R2) - every reconciling item has status "PROPOSED";
                     pending/routed breaks carry none; order/trade breaks route to
                     trade-break-resolver; NO record-repair, asset-movement, posting, or
                     investment-advice language anywhere (a break is evidenced, never actioned).
  6. DISCLAIMER    - the standing no-repair / no-move disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

BREAK_TYPES = {"quantity_break", "cash_break", "missing_internal", "missing_external",
               "pending_settlement", "duplicate"}
TRADE_ROUTE = "trade-break-resolver"
DISCLAIMER = ("Reconciliation and proposed reconciling items only; no record has been repaired or "
              "adjusted and no asset, position, or cash has been moved. Breaks and proposed items "
              "require human review and authorized action in the book of record.")
FP_RE = re.compile(r"^[0-9a-f]{64}$")

# R2 hard boundary: this skill classifies and evidences breaks and PROPOSES reconciling items. It
# must never claim a record was repaired/adjusted, an asset/position/cash was moved, a trade/entry
# was booked/posted, or give personalized investment advice. Language that *proposes* or *requires*
# an action, or *negates* it, is allowed and is stripped before scanning.
PROHIBITED_PATTERNS = [
    r"\b(records?|positions?|holdings?|balances?) (have|has|were|was) been "
    r"(repaired|adjusted|corrected|amended|overwritten|updated)\b",
    r"\b(assets?|positions?|holdings?|cash|funds?|securities) (have|has|were|was) been "
    r"(moved|transferred|settled|rebooked|liquidated)\b",
    r"\b(i|we) (repaired|adjusted|corrected|moved|transferred|rebooked|booked|posted|overwrote)\b",
    r"\b(trade|order) (has|have|was|were) been (placed|executed|booked|sent)\b",
    r"\bautomatically (repaired|adjusted|moved|posted|booked|corrected)\b",
    r"\bwe recommend (buying|selling|increasing|reducing|adding|trimming|overweight|underweight)\b",
    r"\byou should (buy|sell|increase|reduce|add|trim|hedge|rebalance)\b",
    r"\b(recommend|advise) (a|an|the)? ?(trade|buy|sell|allocation)\b",
]


def _r2(x) -> float:
    try:
        return round(float(x) + 0.0, 2)
    except (TypeError, ValueError):
        return float("nan")


def _eq(a, b) -> bool:
    return abs(_r2(a) - _r2(b)) < 0.005


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    for k in ("reconciliation_id", "input_fingerprint", "entity", "as_of", "tie_out", "breaks",
              "disclaimer"):
        if k not in pack:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors

    breaks = pack.get("breaks") or []
    tie = pack.get("tie_out") or {}
    groups = tie.get("groups") or []

    # --- 2/3 break taxonomy + lineage ---
    for b in breaks:
        bid = b.get("break_id", "?")
        if b.get("type") not in BREAK_TYPES:
            errors.append(f"{bid}: break type {b.get('type')!r} not in taxonomy {sorted(BREAK_TYPES)}")
        for f in ("break_amount", "material", "unit"):
            if f not in b:
                errors.append(f"{bid}: missing {f}")
        lineage = b.get("lineage") or []
        if not lineage:
            errors.append(f"{bid}: no lineage citation (break must trace to source rows)")
        for cit in lineage:
            if not (str(cit).startswith("internal:") or str(cit).startswith("external:")):
                errors.append(f"{bid}: lineage citation {cit!r} lacks an internal:/external: prefix")

    # --- 5a PROPOSED-ONLY + routing structure ---
    breaks_by_key: dict = {}
    for b in breaks:
        breaks_by_key.setdefault(b.get("match_key"), []).append(b)
        bid = b.get("break_id", "?")
        c = b.get("proposed_item")
        routed = bool(b.get("routing"))
        if b.get("type") == "pending_settlement":
            if c is not None or b.get("requires_correction"):
                errors.append(f"{bid}: pending_settlement must be documented with no proposed item")
            continue
        if routed:
            r = b.get("routing") or {}
            if r.get("route_to") != TRADE_ROUTE:
                errors.append(f"{bid}: routed break must route_to {TRADE_ROUTE!r}, got {r.get('route_to')!r}")
            if c is not None or b.get("requires_correction"):
                errors.append(f"{bid}: routed (trade) break must carry no proposed item — it is "
                              "routed, not adjusted here")
            continue
        if not c:
            errors.append(f"{bid}: adjusting break has no proposed_item")
            continue
        if c.get("status") != "PROPOSED":
            errors.append(f"{bid}: proposed item status {c.get('status')!r} != 'PROPOSED' "
                          "(reconciling items are proposed, never applied)")
        if not _eq(c.get("adjustment_amount", 0), -_r2(b.get("break_amount", 0))):
            errors.append(f"{bid}: adjustment {c.get('adjustment_amount')} does not offset "
                          f"break_amount {b.get('break_amount')}")

    # cross-check top-level proposed_items list statuses too
    for c in pack.get("proposed_items") or []:
        if c.get("status") != "PROPOSED":
            errors.append(f"{c.get('proposed_item_id', '?')}: status {c.get('status')!r} != 'PROPOSED'")

    # --- 1 tie-outs (per group / match_key) ---
    if not groups and breaks:
        errors.append("tie_out.groups missing but breaks present (cannot verify tie-out)")
    for g in groups:
        key = g.get("match_key", "?")
        it, et = _r2(g.get("internal_total", 0)), _r2(g.get("external_total", 0))
        if not _eq(g.get("difference"), it - et):
            errors.append(f"{key}: difference != internal_total - external_total")
        kbreaks = breaks_by_key.get(key, [])
        bt = sum(_r2(b.get("break_amount", 0)) for b in kbreaks)
        if not _eq(bt, g.get("breaks_total")):
            errors.append(f"{key}: breaks_total {g.get('breaks_total')} != sum of break_amount {round(bt, 2)}")
        if not _eq(g.get("difference"), g.get("breaks_total")):
            errors.append(f"{key}: breaks do not explain the difference "
                          f"(difference {g.get('difference')} != breaks_total {g.get('breaks_total')})")
        if not _eq(g.get("residual"), 0):
            errors.append(f"{key}: residual {g.get('residual')} != 0 (line does not tie)")
        adj = sum(_r2(b["proposed_item"]["adjustment_amount"]) for b in kbreaks
                  if b.get("proposed_item"))
        if not _eq(g.get("corrected_internal_total"), it + adj):
            errors.append(f"{key}: corrected_internal_total != internal_total + proposed adjustments")
        non_adjusting = sum(_r2(b.get("break_amount", 0)) for b in kbreaks
                            if not b.get("requires_correction"))
        if not _eq(g.get("documented_or_routed_total"), non_adjusting):
            errors.append(f"{key}: documented_or_routed_total != sum of documented/routed break_amount")
        if not _eq(_r2(g.get("corrected_internal_total", 0)) - et, non_adjusting):
            errors.append(f"{key}: corrected internal does not agree to external leaving only "
                          "documented pending / routed items")
        if bool(g.get("ties_out")) != _eq(g.get("residual"), 0):
            errors.append(f"{key}: ties_out flag inconsistent with residual")
    if "all_ties_out" in tie and bool(tie["all_ties_out"]) != all(g.get("ties_out") for g in groups):
        errors.append("tie_out.all_ties_out inconsistent with per-group ties_out")
    if groups and not all(g.get("ties_out") for g in groups) and tie.get("all_ties_out"):
        errors.append("tie-out: reconciliation reports all_ties_out but a line does not tie")

    # --- 4 idempotency: id is a pure function of stated inputs ---
    fp = str(pack.get("input_fingerprint", ""))
    if not FP_RE.match(fp):
        errors.append("input_fingerprint is not a 64-hex content hash (lineage/idempotency basis missing)")
    expected_prefix = f"pcr-{pack.get('entity')}-{pack.get('as_of')}-"
    rid = str(pack.get("reconciliation_id", ""))
    if not rid.startswith(expected_prefix):
        errors.append(f"reconciliation_id {rid!r} not derived from entity/as_of (not idempotent)")
    elif fp and not rid.endswith(fp[:8]):
        errors.append("reconciliation_id does not bind to input_fingerprint (id must be reproducible)")

    # --- 5b prohibited-decision / advice language screen (R2) ---
    # Scan free text, but not the standing disclaimer, which legitimately *negates* repair/move.
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(b.get("note", "")) for b in breaks]
    text_parts += [str((b.get("proposed_item") or {}).get("action", "")) for b in breaks]
    text_parts += [str(c.get("action", "")) for c in (pack.get("proposed_items") or [])]
    text = " ".join(text_parts)
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    text = re.sub(r"not applied", " ", text, flags=re.I)  # "not applied by this skill"
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited action/advice language detected: {m.group(0)!r} "
                          "(R2 classifies and proposes; it never repairs, moves, or advises)")

    # --- 6 disclaimer ---
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing no-repair / no-move disclaimer text")

    return errors


def _selftest() -> int:
    # Compute the compliant pack live from the bundled input fixture, then validate it. This keeps
    # the compliant self-test in lockstep with the engine (no hand-maintained golden pack to drift).
    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    import calculate_or_transform as engine
    doc = json.loads((scripts_dir.parent / "evals" / "files" /
                      "reconciliation_example.json").read_text(encoding="utf-8"))
    pack = engine.compute(doc)
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
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
