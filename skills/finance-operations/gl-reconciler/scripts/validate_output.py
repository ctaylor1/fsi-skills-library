#!/usr/bin/env python3
"""Deterministic output validation for gl-reconciler.

Validates a finished reconciliation pack (the calculate_or_transform core + an optional
narrative) before it is presented or delivered. Fails closed on any miss. Checks:

  1. TIE-OUTS      - breaks fully explain the GL-vs-subledger difference (residual == 0);
                     corrected GL ties to subledger after proposed corrections leaving only
                     documented reconciling items; correction lines balance (dr == cr) and
                     each adjustment offsets its break's gl_impact.
  2. BREAK TAXONOMY- every break's type is in the fixed taxonomy and carries an id, amount,
                     material flag, and lineage.
  3. LINEAGE       - every break cites source rows (gl:/subledger:) it was derived from.
  4. IDEMPOTENCY   - reconciliation_id is a pure function of stated inputs (entity/account/
                     as_of + input_fingerprint); no timestamp/random component.
  5. PROPOSED-ONLY - every correction has status "PROPOSED"; timing differences carry no
                     correction; NO posting/booking-completed language anywhere.
  6. DISCLAIMER    - the standing no-posting disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

BREAK_TYPES = {"timing_difference", "amount_mismatch", "unrecorded_in_gl",
               "unsupported_in_gl", "duplicate"}
DISCLAIMER = ("Reconciliation and proposed corrections only; no journal entry has been "
              "posted to the general ledger. Proposed corrections require human review and "
              "authorized posting.")
FP_RE = re.compile(r"^[0-9a-f]{64}$")
# Assertions that a journal entry was actually POSTED / BOOKED (an R2 draft-only skill must
# never claim this). Phrasing about *proposing* or *requiring* posting is allowed.
POSTING_PATTERNS = [
    r"\b(has|have|was|were) been posted\b",
    r"\bposted to the (general )?ledger\b",
    r"\bbooked to the (gl|general ledger)\b",
    r"\bposting (is )?complete\b",
    r"\b(i|we) posted\b",
    r"\bposted the (correction|entry|adjustment|journal|je)\b",
    r"\bautomatically post(ed|s|ing)\b",
    r"\bentr(y|ies) (has|have|was|were)? ?posted\b",
    r"\bsuccessfully posted\b",
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

    for k in ("reconciliation_id", "input_fingerprint", "entity", "account", "as_of",
              "tie_out", "breaks", "disclaimer"):
        if k not in pack:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors

    breaks = pack.get("breaks") or []
    tie = pack.get("tie_out") or {}

    # --- 2/3 break taxonomy + lineage ---
    for b in breaks:
        bid = b.get("break_id", "?")
        if b.get("type") not in BREAK_TYPES:
            errors.append(f"{bid}: break type {b.get('type')!r} not in taxonomy {sorted(BREAK_TYPES)}")
        if "gl_impact" not in b:
            errors.append(f"{bid}: missing gl_impact")
        if "material" not in b:
            errors.append(f"{bid}: missing material flag")
        lineage = b.get("lineage") or []
        if not lineage:
            errors.append(f"{bid}: no lineage citation (break must trace to source rows)")
        for cit in lineage:
            if not (str(cit).startswith("gl:") or str(cit).startswith("subledger:")):
                errors.append(f"{bid}: lineage citation {cit!r} lacks a gl:/subledger: source prefix")

    # --- 1 tie-outs ---
    breaks_total = sum(_r2(b.get("gl_impact", 0)) for b in breaks)
    if "difference" in tie and not _eq(breaks_total, tie["difference"]):
        errors.append(f"tie-out: sum of break gl_impact {round(breaks_total,2)} != difference {tie['difference']} (breaks do not explain the gap)")
    if "gl_total" in tie and "subledger_total" in tie and not _eq(tie["gl_total"] - tie["subledger_total"], tie.get("difference")):
        errors.append("tie-out: difference != gl_total - subledger_total")
    if "residual" in tie and not _eq(tie["residual"], 0):
        errors.append(f"tie-out: residual {tie['residual']} != 0 (reconciliation does not tie)")

    corrections = []
    documented_impact = 0.0
    for b in breaks:
        c = b.get("proposed_correction")
        if b.get("type") == "timing_difference":
            documented_impact += _r2(b.get("gl_impact", 0))
            if b.get("requires_correction") is True or c is not None:
                errors.append(f"{b.get('break_id','?')}: timing_difference must be a documented item with no correction")
            continue
        if not c:
            errors.append(f"{b.get('break_id','?')}: non-timing break has no proposed_correction")
            continue
        corrections.append(c)

    # correction integrity + PROPOSED-ONLY (also cross-check top-level list)
    all_corr = list(corrections)
    for c in pack.get("proposed_corrections") or []:
        if c not in all_corr:
            all_corr.append(c)
    recon_account = pack.get("account")
    adj_sum = 0.0
    for c in all_corr:
        cid = c.get("proposed_je_id", "?")
        if c.get("status") != "PROPOSED":
            errors.append(f"{cid}: correction status {c.get('status')!r} != 'PROPOSED' (corrections are proposed, never posted)")
        lines = c.get("lines") or []
        dr = sum(_r2(l.get("dr", 0)) for l in lines)
        cr = sum(_r2(l.get("cr", 0)) for l in lines)
        if not _eq(dr, cr):
            errors.append(f"{cid}: correction is unbalanced (dr {round(dr,2)} != cr {round(cr,2)})")
        net = sum(_r2(l.get("dr", 0)) - _r2(l.get("cr", 0)) for l in lines if l.get("account") == recon_account)
        if not _eq(net, c.get("adjustment_amount", 0)):
            errors.append(f"{cid}: recon-account net {round(net,2)} != adjustment_amount {c.get('adjustment_amount')}")
        adj_sum += _r2(c.get("adjustment_amount", 0))

    # each correctable break's adjustment offsets its gl_impact
    for b in breaks:
        c = b.get("proposed_correction")
        if c and not _eq(c.get("adjustment_amount", 0), -_r2(b.get("gl_impact", 0))):
            errors.append(f"{b.get('break_id','?')}: adjustment {c.get('adjustment_amount')} does not offset gl_impact {b.get('gl_impact')}")

    # corrected GL ties to subledger, leaving only documented reconciling items
    if "gl_total" in tie and "corrected_gl_total" in tie:
        if not _eq(tie["corrected_gl_total"], _r2(tie["gl_total"]) + adj_sum):
            errors.append("tie-out: corrected_gl_total != gl_total + sum(proposed adjustments)")
        if "subledger_total" in tie and not _eq(tie["corrected_gl_total"] - documented_impact, tie["subledger_total"]):
            errors.append("tie-out: corrected GL does not agree to subledger after corrections (excl. documented items)")

    # --- 4 idempotency: id is a pure function of stated inputs ---
    fp = str(pack.get("input_fingerprint", ""))
    if not FP_RE.match(fp):
        errors.append("input_fingerprint is not a 64-hex content hash (lineage/idempotency basis missing)")
    expected_prefix = f"glr-{pack.get('entity')}-{pack.get('account')}-{pack.get('as_of')}-"
    rid = str(pack.get("reconciliation_id", ""))
    if not rid.startswith(expected_prefix):
        errors.append(f"reconciliation_id {rid!r} not derived from entity/account/as_of (not idempotent)")
    elif fp and not rid.endswith(fp[:8]):
        errors.append("reconciliation_id does not bind to input_fingerprint (id must be reproducible from inputs)")

    # --- 5 proposed-only language screen ---
    # Scan free text, but not the standing disclaimer, which legitimately *negates* posting
    # ("no journal entry has been posted..."). Strip the disclaimer phrase before scanning.
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(b.get("note", "")) for b in breaks]
    text_parts += [str(c.get("memo", "")) for c in all_corr]
    text = " ".join(text_parts)
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    text = re.sub(r"not (yet )?posted", " ", text, flags=re.I)  # "not posted by this skill"
    for pat in POSTING_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"posting-completed language detected: {m.group(0)!r} (R2 proposes corrections; it never posts)")

    # --- 6 disclaimer ---
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing no-posting disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reconciliation_pack_example.json"
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
