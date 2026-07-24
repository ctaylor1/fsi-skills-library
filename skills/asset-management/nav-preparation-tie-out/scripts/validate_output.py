#!/usr/bin/env python3
"""Deterministic output validation for nav-preparation-tie-out.

Validates a finished NAV tie-out packet (the calculate_or_transform core + an optional
narrative) before it is presented or delivered. Fails closed on any miss. This is the R3
control screen: it rejects any packet that would strike a NAV, choose a price, or post an
accounting entry, and confirms every resolution is PROPOSED-ONLY. Checks:

  1. TIE-OUTS       - every (component, currency) control total ties (difference ==
                      sum of that group's break impacts, recomputed from the break list);
                      overall residual == 0; non-timing break count == out_of_tolerance_count.
  2. BREAK TAXONOMY - every break type is in the fixed taxonomy and carries component, key,
                      impact, material flag, and lineage.
  3. LINEAGE        - every break cites source rows (book:/custodian:/administrator:/pricing:).
  4. IDEMPOTENCY    - tie_out_id is a pure function of stated inputs (fund/share_class/as_of +
                      input_fingerprint); no timestamp/random component.
  5. PROPOSED-ONLY  - every resolution has status "PROPOSED" and chooses_value/strikes_nav/
                      posts_entry are all false; every price_break routes to
                      valuation-exception-packet; timing differences carry no resolution;
                      the packet carries no struck-NAV / chosen-price field; and NO
                      NAV-struck / price-chosen / entry-posted language appears anywhere.
  6. DISCLAIMER     - the standing no-strike/no-price/no-post disclaimer is present.

Usage:
  python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

BREAK_TYPES = {"quantity_break", "price_break", "cash_break", "accrual_break",
               "income_break", "expense_break", "shares_break", "missing_record",
               "timing_difference"}
LINEAGE_PREFIXES = ("book:", "custodian:", "administrator:", "pricing:")
PRICE_ROUTE = "valuation-exception-packet"
FP_RE = re.compile(r"^[0-9a-f]{64}$")
# Fields whose mere presence would mean the skill struck a NAV or chose a price — forbidden.
FORBIDDEN_KEYS = ("nav_per_share", "struck_nav", "official_nav", "nav_value",
                  "chosen_price", "selected_price", "final_nav", "certified_nav")
DISCLAIMER = ("Tie-out and break packet only; NAV has not been struck, no price has been "
              "selected, and no accounting entry has been posted. All resolutions are "
              "PROPOSED and require fund-accountant review and authorized action in the "
              "systems of record.")

# Negations/routing that legitimately *deny* the prohibited action — stripped before scan.
NEG_STRIP = [
    re.escape(DISCLAIMER),
    r"(do|does|did|will|shall|must|can|could|would|has|have|had|is|are|was|were)?\s*(not|never)\s+(yet\s+)?(been\s+)?(post(ed|ing|s)?|struck|strike|chos(e|en)|choos(e|ing)|select(ed|ing|s)?|book(ed|ing)?|certif(y|ied|ies)|finali[sz](e|ed|es|ing))",
    r"no\s+(nav|price|accounting entry|entry|journal|adjustment)\s+(has|have|is|was|were)?\s*(been\s+)?(struck|chosen|selected|posted|booked|certified)",
    r"without\s+(post(ing)?|strik(ing|e)|choos(ing|e)|select(ing)?|book(ing)?|certif(ying|y))",
    r"route[sd]?\s+to\s+" + re.escape(PRICE_ROUTE),
]
# Positive assertions that a prohibited decision/action HAPPENED (fail closed on any).
POSTING_PATTERNS = [
    r"\bnav (has|have|was|were|is|been)\b[^.]*\bstr(uck|ike)\b",
    r"\bstr(uck|ike|iking) (the |a )?nav\b",
    r"\bnav (is|was|has been) (finali[sz]ed|certified|official|approved)\b",
    r"\b(chose|chosen|selected|set|overrode|override[ds]?) (the |a )?(vendor |market |fair )?(value|price)\b",
    r"\b(price|valuation) (has|have|was|were|is) (been )?(chosen|selected|set|overridden)\b",
    r"\b(posted|booked) (the |an |a )?(entry|journal|adjustment|accounting entry|correction|je)\b",
    r"\b(entry|journal|adjustment|correction) (has|have|was|were) (been )?(posted|booked)\b",
    r"\b(has|have|was|were) been posted\b",
    r"\bposted to the (ledger|gl|general ledger|accounting system|book of record)\b",
    r"\bwe (struck|posted|booked|certified|priced)\b",
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

    for k in ("tie_out_id", "input_fingerprint", "fund", "as_of", "tie_out", "breaks",
              "disclaimer"):
        if k not in pack:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors

    breaks = pack.get("breaks") or []
    tie = pack.get("tie_out") or {}

    # --- 5a: forbidden struck-NAV / chosen-price fields anywhere in the packet ---
    def scan_keys(obj, path="pack"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in FORBIDDEN_KEYS:
                    errors.append(f"forbidden field '{k}' at {path} (skill must not strike NAV or choose a price)")
                scan_keys(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan_keys(v, f"{path}[{i}]")
    scan_keys(pack)

    # --- 2/3 break taxonomy + lineage ---
    for b in breaks:
        bid = b.get("break_id", "?")
        if b.get("type") not in BREAK_TYPES:
            errors.append(f"{bid}: break type {b.get('type')!r} not in taxonomy {sorted(BREAK_TYPES)}")
        for f in ("component", "key", "impact", "material"):
            if f not in b:
                errors.append(f"{bid}: missing '{f}'")
        lineage = b.get("lineage") or []
        if not lineage:
            errors.append(f"{bid}: no lineage citation (break must trace to source rows)")
        for cit in lineage:
            if not str(cit).startswith(LINEAGE_PREFIXES):
                errors.append(f"{bid}: lineage citation {cit!r} lacks a book:/custodian:/administrator:/pricing: prefix")

    # --- 1 tie-outs: control totals recomputed from the break list ---
    non_timing = [b for b in breaks if b.get("type") != "timing_difference"]
    if "out_of_tolerance_count" in tie and tie["out_of_tolerance_count"] != len(non_timing):
        errors.append(f"tie-out: out_of_tolerance_count {tie['out_of_tolerance_count']} != non-timing breaks {len(non_timing)}")
    if "captured_break_count" in tie and tie["captured_break_count"] != len(non_timing):
        errors.append(f"tie-out: captured_break_count {tie['captured_break_count']} != non-timing breaks {len(non_timing)}")

    recomputed_residual = 0.0
    for c in tie.get("control_totals") or []:
        comp, ccy = c.get("component"), c.get("currency")
        impact = sum(_r2(b.get("impact", 0)) for b in breaks
                     if b.get("component") == comp and b.get("currency") == ccy)
        if not _eq(impact, c.get("breaks_impact_sum")):
            errors.append(f"control_total[{comp}/{ccy}]: breaks_impact_sum {c.get('breaks_impact_sum')} != recomputed {round(impact,2)}")
        if not _eq(c.get("difference"), c.get("breaks_impact_sum")):
            errors.append(f"control_total[{comp}/{ccy}]: difference {c.get('difference')} != breaks_impact_sum {c.get('breaks_impact_sum')} (does not tie)")
        if not _eq(c.get("book_total", 0) - c.get("verifier_total", 0), c.get("difference")):
            errors.append(f"control_total[{comp}/{ccy}]: difference != book_total - verifier_total")
        if c.get("ties_out") is not True:
            errors.append(f"control_total[{comp}/{ccy}]: ties_out is not true")
        recomputed_residual += _r2(c.get("difference", 0)) - _r2(c.get("breaks_impact_sum", 0))
    if not _eq(recomputed_residual, 0):
        errors.append(f"tie-out: recomputed residual {round(recomputed_residual,2)} != 0 (breaks do not explain the differences)")
    if "residual" in tie and not _eq(tie["residual"], 0):
        errors.append(f"tie-out: residual {tie['residual']} != 0 (reconciliation does not tie)")
    if tie.get("ties_out") is False and not breaks:
        errors.append("tie-out: ties_out false with no breaks")

    # --- 5b PROPOSED-ONLY resolutions ---
    all_res = []
    for b in breaks:
        r = b.get("proposed_resolution")
        if b.get("type") == "timing_difference":
            if r is not None or b.get("requires_resolution") is True:
                errors.append(f"{b.get('break_id','?')}: timing_difference must be a documented item with no resolution")
            continue
        if not r:
            errors.append(f"{b.get('break_id','?')}: non-timing break has no proposed_resolution")
            continue
        all_res.append((b, r))
    # cross-check the top-level list matches (no rogue extra resolution)
    top = pack.get("proposed_resolutions") or []
    for r in top:
        if r.get("status") != "PROPOSED":
            errors.append(f"{r.get('resolution_id','?')}: top-level resolution status {r.get('status')!r} != 'PROPOSED'")

    for b, r in all_res:
        rid = r.get("resolution_id", "?")
        if r.get("status") != "PROPOSED":
            errors.append(f"{rid}: resolution status {r.get('status')!r} != 'PROPOSED' (resolutions are proposed, never executed)")
        for flag in ("chooses_value", "strikes_nav", "posts_entry"):
            if r.get(flag) is not False:
                errors.append(f"{rid}: resolution '{flag}' must be false (R3 hard boundary — this skill never does this)")
        if b.get("type") == "price_break":
            if r.get("route_to") != PRICE_ROUTE:
                errors.append(f"{rid}: price_break must route to {PRICE_ROUTE} (skill never chooses a price), got {r.get('route_to')!r}")
            if r.get("disposition") != "route_to_valuation_exception_packet":
                errors.append(f"{rid}: price_break disposition must be route_to_valuation_exception_packet")

    # --- 5c prohibited-decision/action language screen ---
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(b.get("note", "")) for b in breaks]
    text_parts += [str(r.get("recommended_action", "")) + " " + str(r.get("note", "")) for _, r in all_res]
    text = " ".join(text_parts)
    for pat in NEG_STRIP:
        text = re.sub(pat, " ", text, flags=re.I)
    for pat in POSTING_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited-action language detected: {m.group(0)!r} (R3 tie-out never strikes NAV, chooses a price, or posts an entry)")

    # --- 4 idempotency: id is a pure function of stated inputs ---
    fp = str(pack.get("input_fingerprint", ""))
    if not FP_RE.match(fp):
        errors.append("input_fingerprint is not a 64-hex content hash (lineage/idempotency basis missing)")
    sclass = pack.get("share_class") or "NA"
    expected_prefix = f"npt-{pack.get('fund')}-{sclass}-{pack.get('as_of')}-"
    tid = str(pack.get("tie_out_id", ""))
    if not tid.startswith(expected_prefix):
        errors.append(f"tie_out_id {tid!r} not derived from fund/share_class/as_of (not idempotent)")
    elif fp and not tid.endswith(fp[:8]):
        errors.append("tie_out_id does not bind to input_fingerprint (id must be reproducible from inputs)")

    # --- 6 disclaimer ---
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing no-strike/no-price/no-post disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "tie_out_pack_example.json"
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
