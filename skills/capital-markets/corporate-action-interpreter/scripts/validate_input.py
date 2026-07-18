#!/usr/bin/env python3
"""Deterministic input validation for corporate-action-interpreter.

Validates a corporate-action NOTICE (plus optional eligible position) against the
documented schema BEFORE interpretation. Fails closed on structural problems; warns
(does not fail) on data-quality gaps the interpretation must surface for operations
review (missing dates, fractional-share exposure, election-deadline timing, unknown
event codes, position/record-date mismatches).

Notice schema (JSON) — see references/domain-rules.md for the field meanings:
{
  "event_id": "str",
  "event_type": "SPLF|SPLR|DVCA|DVSE|DVOP|SOFF|MRGR|TEND|EXOF|RHTS|...",
  "event_type_name": "str" (opt),
  "mandatory_voluntary": "mandatory"|"voluntary"|"mandatory-with-options",
  "security": {"instrument_id","id_type","description"},
  "dates": {"announcement_date","ex_date"(opt),"record_date"(opt),
            "election_deadline"(req for voluntary/options),"pay_date"(opt),
            "effective_date"(opt)},
  "terms": {"ratio_new"(opt),"ratio_old"(opt),"rate_per_share"(opt),
            "currency"(opt),"fractional_handling"(opt)},
  "options": [ {"option_id","option_code","description","default",
                "rate_per_share" | ("ratio_new","ratio_old")} ]  (req for voluntary/options),
  "eligible_position": {"quantity","as_of"} (opt),
  "source": {"system","ref"}
}

Usage:
  python validate_input.py notice.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

REQUIRED_TOP = ("event_id", "event_type", "mandatory_voluntary", "security", "dates", "source")
REQUIRED_SECURITY = ("instrument_id", "id_type", "description")
MV_VALUES = {"mandatory", "voluntary", "mandatory-with-options"}
OPTIONS_MV = {"voluntary", "mandatory-with-options"}

# Known corporate-action event codes (ISO 15022/20022 CAEV-style). Unknown codes warn.
KNOWN_EVENTS = {
    "SPLF": "Stock Split (forward)", "SPLR": "Reverse Stock Split",
    "DVCA": "Cash Dividend", "DVSE": "Stock Dividend",
    "DVOP": "Dividend Option (cash or stock)", "CAPG": "Capital Gains Distribution",
    "SOFF": "Spin-off", "MRGR": "Merger", "TEND": "Tender Offer",
    "EXOF": "Exchange Offer", "RHTS": "Rights Issue", "BONU": "Bonus Issue",
    "CONV": "Conversion", "REDM": "Redemption", "PCAL": "Partial Call",
    "LIQU": "Liquidation", "INTR": "Interest Payment", "CHAN": "Name/Identifier Change",
    "RHDI": "Rights Distribution", "CONS": "Consent Solicitation",
}
# Event types whose entitlement is computed from a ratio_new/ratio_old.
RATIO_EVENTS = {"SPLF", "SPLR", "DVSE", "BONU"}
# Event types whose entitlement is computed from a per-share rate.
RATE_EVENTS = {"DVCA", "CAPG", "INTR", "REDM"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _date(v):
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _check_fractional(tag, qty, rn, ro, has_handling, warnings):
    """Emit a fractional-share warning (containing 'fractional') when qty*rn/ro is not whole."""
    if qty is None or rn is None or not ro:
        return
    val = qty * rn / ro
    if abs(val - round(val)) > 1e-9:
        msg = f"{tag}: fractional shares result ({qty:g} x {rn:g}/{ro:g} = {val:g})"
        if not has_handling:
            msg += " and the notice does not state fractional-share treatment (cash-in-lieu vs round down)"
        msg += " — confirm with issuer/agent."
        warnings.append(msg)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, "", {}):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    sec = doc.get("security") or {}
    for k in REQUIRED_SECURITY:
        if not sec.get(k):
            errors.append(f"security: missing '{k}'")

    src = doc.get("source") or {}
    if not (src.get("system") and src.get("ref")):
        errors.append("source must include 'system' and 'ref' (citation)")

    mv = doc.get("mandatory_voluntary")
    if mv not in MV_VALUES:
        errors.append(f"mandatory_voluntary must be one of {sorted(MV_VALUES)}, got {mv!r}")

    ev = doc.get("event_type")
    if ev not in KNOWN_EVENTS:
        warnings.append(f"event_type {ev!r} is not a known code — confirm the CAEV mapping before interpreting")

    dates = doc.get("dates") or {}
    parsed = {}
    for k, v in dates.items():
        if v in (None, ""):
            continue
        d = _date(v)
        if d is None:
            errors.append(f"dates.{k} must be YYYY-MM-DD, got {v!r}")
        else:
            parsed[k] = d
    ann = parsed.get("announcement_date")
    rec = parsed.get("record_date")
    pay = parsed.get("pay_date")
    ele = parsed.get("election_deadline")
    if ann and rec and ann > rec:
        errors.append(f"announcement_date {ann} is after record_date {rec}")
    if rec and pay and rec > pay:
        errors.append(f"record_date {rec} is after pay_date {pay}")
    if ele and pay and ele > pay:
        warnings.append(f"election_deadline {ele} is after pay_date {pay} — confirm the response timeline")
    if not dates.get("ex_date"):
        warnings.append("no ex_date — confirm ex/record-date alignment for entitlement")

    terms = doc.get("terms") or {}
    qty = _num((doc.get("eligible_position") or {}).get("quantity"))
    has_handling = bool(terms.get("fractional_handling"))

    options = doc.get("options")
    if mv in OPTIONS_MV:
        if not ele:
            errors.append(f"{mv} event requires dates.election_deadline")
        if not options or not isinstance(options, list):
            errors.append(f"{mv} event requires a non-empty 'options' list")
            options = []
        defaults = 0
        for i, opt in enumerate(options):
            otag = f"options[{i}] ({opt.get('option_id', '?')})"
            if not opt.get("description"):
                errors.append(f"{otag}: missing 'description'")
            rate = _num(opt.get("rate_per_share"))
            rn, ro = _num(opt.get("ratio_new")), _num(opt.get("ratio_old"))
            if rate is None and (rn is None or ro is None):
                errors.append(f"{otag}: needs 'rate_per_share' or ('ratio_new','ratio_old')")
            if opt.get("default") is True:
                defaults += 1
            _check_fractional(otag, qty, rn, ro, has_handling or bool(opt.get("fractional_handling")), warnings)
        if defaults == 0:
            warnings.append("no option is marked default — for mandatory-with-options confirm the default outcome")
        elif defaults > 1:
            warnings.append(f"{defaults} options marked default — exactly one default is expected")
    else:
        # Mandatory reorg with a single outcome: require the parameter needed to compute it.
        if ev in RATIO_EVENTS and (_num(terms.get("ratio_new")) is None or _num(terms.get("ratio_old")) is None):
            warnings.append(f"{ev}: terms lack ratio_new/ratio_old — entitlement not computable until supplied")
        if ev in RATE_EVENTS and _num(terms.get("rate_per_share")) is None:
            warnings.append(f"{ev}: terms lack rate_per_share — entitlement not computable until supplied")
        _check_fractional("terms", qty, _num(terms.get("ratio_new")), _num(terms.get("ratio_old")), has_handling, warnings)

    pos = doc.get("eligible_position")
    if pos is not None:
        if _num(pos.get("quantity")) is None:
            errors.append("eligible_position.quantity must be numeric")
        pas = pos.get("as_of")
        if pas and _date(pas) is None:
            errors.append(f"eligible_position.as_of must be YYYY-MM-DD, got {pas!r}")
        elif pas and rec and _date(pas) != rec:
            warnings.append(f"eligible_position.as_of {pas} differs from record_date {rec} — confirm the entitled position")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "notice_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
