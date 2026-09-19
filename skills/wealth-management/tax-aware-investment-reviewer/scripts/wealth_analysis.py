"""Small strict decimal/evidence/CLI helpers for bounded P1 financial analyses."""
import json
import sys
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path

from wealth_contract import iso_date, nonempty, source_errors, validate_envelope, validate_output_envelope


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label="number", minimum=None, places=8):
    require(not isinstance(value, bool) and isinstance(value, (str, int, float)), f"{label}: decimal number required")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label}: invalid decimal") from exc
    require(result.is_finite(), f"{label}: finite value required")
    require(abs(result) <= Decimal("1e18") and result.as_tuple().exponent >= -places, f"{label}: unsupported magnitude/precision")
    require(minimum is None or result >= minimum, f"{label}: value below minimum")
    return result


def money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def precise(value):
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))


def dated(value, label):
    result = iso_date(value)
    require(result is not None, f"{label}: ISO date required")
    return result


def records(value, id_key, label, empty=False):
    require(isinstance(value, list) and (empty or bool(value)), f"{label}: {'possibly empty' if empty else 'nonempty'} list required")
    seen = set()
    for row in value:
        require(isinstance(row, dict), f"{label}: rows must be objects")
        key = row.get(id_key)
        require(nonempty(key) and key not in seen, f"{label}: unique {id_key} required")
        seen.add(key)
    return value


def finding(findings, code, message, **context):
    findings.append({"code": code, "message": message, **context})


def cited(row, doc, label, findings):
    errors = source_errors(row.get("source_ids"), doc)
    for error in errors:
        finding(findings, "source-gap", f"{label}: {error}")
    return not errors


def common(doc):
    errors = validate_envelope(doc)
    require(not errors, "; ".join(errors))
    issues = doc.get("unresolved_issues")
    require(isinstance(issues, list), "unresolved_issues must explicitly list known upstream concerns; [] only after review")
    for issue in issues:
        require(isinstance(issue, dict) and nonempty(issue.get("code")) and nonempty(issue.get("message")), "each unresolved issue requires code and message")
    return doc


def input_findings(doc):
    result = deepcopy(doc["unresolved_issues"])
    for row in doc["unresolved_issues"]:
        cited(row, doc, "upstream issue", result)
    return result


def input_errors(doc, check):
    try:
        check(doc)
        return []
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return [str(exc)]


def output_errors(out, skill, compute):
    errors = validate_output_envelope(out, skill)
    if errors:
        return errors
    try:
        expected = compute(out["result"].get("input_snapshot"))
        if expected != out:
            errors.append("output differs from recomputed financial evidence, findings or input binding")
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        errors.append(f"invalid bound input: {exc}")
    return errors


def cli(mode, check, compute, validate_output, script_path):
    args = sys.argv[1:]
    if not args or len(args) != 1:
        print(f"usage: python scripts/{Path(script_path).name} INPUT.json | --selftest")
        return 2
    try:
        fixture = Path(script_path).resolve().parents[1] / "evals/files/request_example.json"
        doc = json.loads((fixture if args == ["--selftest"] else Path(args[0])).read_text())
        if mode == "compute":
            print(json.dumps(compute(doc), indent=2, allow_nan=False))
            return 0
        if mode == "output" and args == ["--selftest"]:
            doc = compute(doc)
        errors = input_errors(doc, check) if mode == "input" else validate_output(doc)
        print(json.dumps({"errors": errors}))
        return int(bool(errors))
    except (ValueError, OSError, TypeError, KeyError, ArithmeticError) as exc:
        print(json.dumps({"errors": [str(exc)]}))
        return 1
