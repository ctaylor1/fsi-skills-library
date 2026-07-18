#!/usr/bin/env python3
"""Deterministic output validation for reinsurance-treaty-interpreter.

Confirms the treaty interpretation is complete, fully cited, internally consistent with the
layer arithmetic, and free of binding coverage/recoverability determinations and
legal/actuarial/accounting advice BEFORE it is presented or delivered.

Checks:
  1. Interpretation lists at least one clause; each has a non-empty plain_summary.
  2. Each clause's clause_type is a recognized treaty-clause type.
  3. Each clause carries a non-empty citation.
  4. clauses_interpreted_count ties to the number of clauses listed.
  5. If a recovery_illustration is present: each occurrence carries a citation; the layer
     arithmetic ties out (layer_loss, ceded_recovery, cumulative, remaining aggregate); and
     total_ceded equals the sum of the occurrence recoveries and does not exceed the aggregate.
  6. Narrative / clause summaries / notes / data gaps contain no coverage-or-recoverability
     determination or legal/actuarial/accounting advice phrasing (R2 is interpretive only).
  7. The standing informational-only disclaimer is present.

Neutral third-person interpretation of the wording, and figures labeled illustrative, are
permitted; a determination about a real claim or advice on what to do is not.

Output schema (JSON):
{
  "interpretation_id","treaty_id","treaty_type","currency",
  "layer":{"attachment","limit","reinstatements","aggregate_limit","layer_premium"},
  "clauses":[{"clause_id","clause_type","plain_summary","citation"}],
  "clauses_interpreted_count": int,
  "recovery_illustration": {                       # optional
     "aggregate_limit": num,
     "occurrences":[{"occurrence_id","gross_loss","layer_loss","ceded_recovery",
                     "cumulative_ceded","remaining_aggregate","citation"}],
     "total_ceded": num, "total_reinstatement_premium": num },
  "data_gaps":[...], "narrative":"...", "disclaimer":"..."
}

Usage:
  python validate_output.py interpretation.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

MONEY_TOL = 1.0  # one currency unit
KNOWN_CLAUSE_TYPES = {
    "attachment", "limit", "exclusion", "reinstatement", "reporting",
    "definition", "condition", "recoverability", "other",
}

# Determination / advice phrasing an interpretive skill may never produce. Neutral
# description of the wording, and figures explicitly labeled illustrative, are NOT matched.
PROHIBITED_PATTERNS = [
    # Recoverability / coverage determination about a real loss or claim
    r"\bthis (?:loss|claim|occurrence|cession|event)\b[^.]{0,60}\b(?:is|is not|isn'?t|are|will be|would be)\b[^.]{0,40}\b(?:recoverable|not recoverable|covered|not covered|excluded|payable|paid)\b",
    r"\bis (?:fully |partially |definitely |certainly |not )?recoverable\b",
    r"\bthe reinsurer (?:will|would|must|shall|is obligated to|is required to|won'?t|will not|has to)\b[^.]{0,30}\b(?:pay|reimburse|indemnify|owe|cover|settle)\b",
    r"\byou (?:are|will be) (?:entitled|guaranteed) to (?:recover|recovery|reimbursement|payment)\b",
    r"\bguaranteed (?:recovery|to recover|recoverable|collectible|payment)\b",
    # Advice on what to do
    r"\byou (?:should|must|need to|ought to|had better) (?:bill|collect|commute|dispute|reserve|book|deny|accept|pursue|notify|report|recover|settle|hold)\b",
    r"\b(?:we|i) (?:recommend|suggest|advise)\b",
    r"\b(?:the )?(?:cedent|company) (?:should|must|ought to) (?:recover|collect|reserve|book|commute|dispute)\b",
    r"\bcommute the (?:treaty|contract|layer)\b",
    r"\b(?:bill|collect) (?:the|this) (?:reinsurer|recoverable)\b",
    r"\bbook (?:the|this) recoverable\b",
    r"\b(?:legal|actuarial|accounting|reserving|coverage) advice\b",
]
DISCLAIMER_RE = re.compile(
    r"informational.*only.*not .*(?:coverage or )?recoverability determination", re.I)
# The standing disclaimer legitimately contains "determination" and "legal advice"; strip that
# sentence before the language screen so the required disclaimer never false-trips the screen.
DISCLAIMER_STRIP = re.compile(
    r"informational[^.]*?(?:determination|legal advice)[^.]*\.", re.I)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _close(a, b, tol=MONEY_TOL) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def _check_illustration(ill: dict, layer: dict) -> list[str]:
    errors: list[str] = []
    att = _num(layer.get("attachment"))
    limit = _num(layer.get("limit"))
    agg = _num(ill.get("aggregate_limit")) or _num(layer.get("aggregate_limit"))
    if att is None or limit is None or agg is None:
        return ["recovery_illustration present but layer.attachment/limit/aggregate_limit not numeric"]

    cumulative = 0.0
    running_total = 0.0
    for occ in ill.get("occurrences") or []:
        oid = occ.get("occurrence_id", "?")
        if not (occ.get("citation") or "").strip():
            errors.append(f"occurrence {oid}: missing citation")
        gross = _num(occ.get("gross_loss"))
        ceded = _num(occ.get("ceded_recovery"))
        if ceded is None:  # explicitly excluded line — must be flagged, not silently zero
            if not (occ.get("note") or "").strip():
                errors.append(f"occurrence {oid}: no ceded_recovery and no explanatory note")
            continue
        if gross is None:
            errors.append(f"occurrence {oid}: numeric ceded_recovery but non-numeric gross_loss")
            continue
        exp_layer = min(max(gross - att, 0.0), limit)
        if not _close(_num(occ.get("layer_loss")), exp_layer):
            errors.append(f"occurrence {oid}: layer_loss {occ.get('layer_loss')} != min(max(gross-attachment,0),limit) {exp_layer}")
        exp_ceded = max(0.0, min(exp_layer, agg - cumulative))
        if not _close(ceded, exp_ceded):
            errors.append(f"occurrence {oid}: ceded_recovery {ceded} != layer loss capped by remaining aggregate {exp_ceded}")
        cumulative += ceded
        running_total += ceded
        if not _close(_num(occ.get("cumulative_ceded")), cumulative):
            errors.append(f"occurrence {oid}: cumulative_ceded {occ.get('cumulative_ceded')} != running total {cumulative}")
        if not _close(_num(occ.get("remaining_aggregate")), agg - cumulative):
            errors.append(f"occurrence {oid}: remaining_aggregate {occ.get('remaining_aggregate')} != aggregate - cumulative {agg - cumulative}")

    total = _num(ill.get("total_ceded"))
    if total is not None and not _close(total, running_total):
        errors.append(f"total_ceded {total} != sum of occurrence recoveries {running_total}")
    if total is not None and total - agg > MONEY_TOL:
        errors.append(f"total_ceded {total} exceeds aggregate_limit {agg}")
    return errors


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    clauses = s.get("clauses") or []
    if not clauses:
        return ["interpretation missing clauses"]

    for c in clauses:
        cid = c.get("clause_id", "?")
        if not (c.get("plain_summary") or "").strip():
            errors.append(f"clause {cid}: missing plain_summary")
        if not (c.get("citation") or "").strip():
            errors.append(f"clause {cid}: missing citation")
        ct = str(c.get("clause_type", "")).lower()
        if ct not in KNOWN_CLAUSE_TYPES:
            errors.append(f"clause {cid}: clause_type {c.get('clause_type')!r} not a recognized treaty-clause type")

    count = s.get("clauses_interpreted_count")
    if count is None:
        errors.append("missing clauses_interpreted_count")
    elif count != len(clauses):
        errors.append(f"clauses_interpreted_count {count} != number of clauses {len(clauses)}")

    ill = s.get("recovery_illustration")
    if isinstance(ill, dict):
        errors.extend(_check_illustration(ill, s.get("layer") or {}))

    # Language screen over all human-readable text, minus the standing disclaimer sentence.
    text = " ".join(str(s.get(k, "")) for k in ("narrative", "notes"))
    text += " " + " ".join(str(c.get("plain_summary", "")) for c in clauses)
    text += " " + json.dumps(s.get("data_gaps", ""))
    text = DISCLAIMER_STRIP.sub(" ", text)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"prohibited advice/determination language detected: {m.group(0)!r} "
                f"(R2 is interpretive only — no coverage/recoverability determination or advice)")

    if not DISCLAIMER_RE.search(str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))):
        errors.append("missing standing disclaimer: 'Informational interpretation only; not a "
                      "coverage or recoverability determination, reserving or accounting decision, "
                      "or legal advice.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "interpretation_example.json"
        s = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        s = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        s = json.loads(sys.stdin.read())
    errors = validate(s)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
