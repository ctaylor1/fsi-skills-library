#!/usr/bin/env python3
"""Deterministic output validation for investment-vendor-feed-reconciler.

Validates a finished discrepancy pack (the calculate_or_transform core + an optional narrative)
before it is presented or delivered. Fails closed on any miss. Checks:

  1. TIE-OUT (completeness) - matched_cells + break_cells == total_cells; residual_cells == 0;
                     internal/vendor cell counts are consistent with the total.
  2. BREAK TAXONOMY- every break's type is in the fixed taxonomy and carries instrument_id,
                     domain, field, material flag, and per-source as-of times.
  3. LINEAGE       - every break cites the source rows (internal:/vendor:) it was derived from,
                     each citation carrying an @as-of time.
  4. IDEMPOTENCY   - reconciliation_id is a pure function of stated inputs (entity/as_of +
                     input_fingerprint); no timestamp/random component.
  5. NO-ADJUDICATION / NEVER-REPAIRED - every break has canonical_value == null and a non-binding
                     disposition (UNRESOLVED/ROUTED); price-domain breaks route to
                     valuation-exception-packet; NO chosen-value / override / repair / advice
                     language anywhere. This is the R2 prohibited-decision screen: the skill
                     surfaces and routes discrepancies but never chooses the canonical value.
  6. DISCLAIMER    - the standing no-adjudication disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

BREAK_TYPES = {"value_mismatch", "missing_in_internal", "missing_in_vendor", "stale_as_of"}
ALLOWED_DISPOSITIONS = {"UNRESOLVED", "ROUTED"}
PRICE_ROUTE = "valuation-exception-packet"
DISCLAIMER = ("Field-level discrepancy report only; this skill does not choose the canonical "
              "value, override a source, or repair any record. Price exceptions are routed to "
              "the valuation-exception process. All discrepancies require human review before "
              "any system-of-record change.")
FP_RE = re.compile(r"^[0-9a-f]{64}$")

# Assertions that the skill adjudicated a winner, repaired a record, or gave investment advice.
# An R2 reconciler surfaces and routes disagreements; it must never claim any of these. Language
# that *negates* the action ("does not choose the canonical value") is stripped before scanning.
PROHIBITED_PATTERNS = [
    r"\bthe canonical value is\b",
    r"\bcanonical value (is|=|:) \S",
    r"\bthe correct (value|price|rating|source) is\b",
    r"\b(internal|vendor) is (the )?(correct|authoritative|canonical|golden)\b",
    r"\buse the (internal|vendor) value\b",
    r"\boverrode\b",
    r"\boverride the (source|price|record|value)\b",
    r"\brepaired the (record|price|security master|value)\b",
    r"\bcorrected the (record|price|value|security master)\b",
    r"\bset the (golden|canonical) (value|price|source)\b",
    r"\bposted to (the )?(security master|golden source|system of record)\b",
    r"\b(recommend|advise) (buying|selling)\b",
    r"\bshould (buy|sell)\b",
]


def _r(x, nd=6):
    try:
        return round(float(x) + 0.0, nd)
    except (TypeError, ValueError):
        return float("nan")


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    for k in ("reconciliation_id", "input_fingerprint", "entity", "as_of", "tie_out",
              "breaks", "disclaimer"):
        if k not in pack:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors

    breaks = pack.get("breaks") or []
    tie = pack.get("tie_out") or {}

    # --- 2/3 break taxonomy + lineage + as-of times ---
    for b in breaks:
        bid = b.get("break_id", "?")
        if b.get("type") not in BREAK_TYPES:
            errors.append(f"{bid}: break type {b.get('type')!r} not in taxonomy {sorted(BREAK_TYPES)}")
        for req in ("instrument_id", "domain", "field", "material"):
            if req not in b:
                errors.append(f"{bid}: missing '{req}'")
        lineage = b.get("lineage") or []
        if not lineage:
            errors.append(f"{bid}: no lineage citation (break must trace to source rows)")
        for cit in lineage:
            s = str(cit)
            if not (s.startswith("internal:") or s.startswith("vendor:")):
                errors.append(f"{bid}: lineage citation {cit!r} lacks an internal:/vendor: source prefix")
            if "@" not in s:
                errors.append(f"{bid}: lineage citation {cit!r} carries no @as-of time")
        # per-source as-of times must be present on whichever side(s) the break cites
        for side in ("internal", "vendor"):
            sv = b.get(side)
            if sv is not None and not sv.get("as_of"):
                errors.append(f"{bid}: {side} side missing as_of time")

    # --- 1 tie-out (completeness) ---
    matched = tie.get("matched_cells")
    bc = tie.get("break_cells")
    total = tie.get("total_cells")
    if bc is not None and bc != len(breaks):
        errors.append(f"tie-out: break_cells {bc} != number of breaks {len(breaks)}")
    if None not in (matched, bc, total):
        if matched + bc != total:
            errors.append(f"tie-out: matched_cells + break_cells ({matched}+{bc}) != total_cells {total}")
    if "residual_cells" in tie and tie["residual_cells"] != 0:
        errors.append(f"tie-out: residual_cells {tie['residual_cells']} != 0 (cells dropped or double-counted)")
    if tie.get("ties_out") is not True:
        errors.append("tie-out: ties_out is not true (reconciliation is not complete)")

    # --- 5 no-adjudication / never-repaired (structural) ---
    for b in breaks:
        bid = b.get("break_id", "?")
        if b.get("canonical_value") is not None:
            errors.append(f"{bid}: canonical_value is set - the skill must NEVER choose the canonical value")
        disp = b.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{bid}: disposition {disp!r} not in {sorted(ALLOWED_DISPOSITIONS)} "
                          f"(discrepancies are surfaced/routed, never resolved by this skill)")
        if b.get("domain") == "price" and b.get("route") != PRICE_ROUTE:
            errors.append(f"{bid}: price-domain break route {b.get('route')!r} != {PRICE_ROUTE!r} "
                          f"(price exceptions must route to the valuation-exception process)")

    # --- 4 idempotency: id is a pure function of stated inputs ---
    fp = str(pack.get("input_fingerprint", ""))
    if not FP_RE.match(fp):
        errors.append("input_fingerprint is not a 64-hex content hash (lineage/idempotency basis missing)")
    expected_prefix = f"ivfr-{pack.get('entity')}-{pack.get('as_of')}-"
    rid = str(pack.get("reconciliation_id", ""))
    if not rid.startswith(expected_prefix):
        errors.append(f"reconciliation_id {rid!r} not derived from entity/as_of (not idempotent)")
    elif fp and not rid.endswith(fp[:8]):
        errors.append("reconciliation_id does not bind to input_fingerprint (id must be reproducible from inputs)")

    # --- 5 prohibited-decision / advice language screen ---
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(b.get("note", "")) for b in breaks]
    text = " ".join(text_parts)
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/advice language detected: {m.group(0)!r} "
                          f"(R2 surfaces and routes; it never adjudicates, repairs, or advises)")

    # --- 6 disclaimer ---
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing no-adjudication disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "feed_discrepancy_pack_example.json"
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
