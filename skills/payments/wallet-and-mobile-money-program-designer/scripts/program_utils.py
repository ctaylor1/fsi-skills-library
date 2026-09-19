from decimal import Decimal, InvalidOperation
from datetime import datetime


def amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("amount must be a decimal string or integer")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("amount must be finite and nonnegative")
    return result


def text(value):
    return isinstance(value, str) and bool(value.strip())


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return result


def rows(data, key, fields, errors, nullable=()):
    items = data.get(key)
    if not isinstance(items, list):
        errors.append(key + " must be an explicit list")
        return []
    seen = set()
    for row in items:
        if not isinstance(row, dict):
            errors.append(key + " row must be an object")
            continue
        for field in fields:
            if not text(row.get(field)):
                errors.append(key + "." + field + " required")
        rid = row.get(fields[0])
        if rid in seen:
            errors.append(key + " duplicate " + fields[0])
        seen.add(rid)
        if not isinstance(row.get("source_ids"), list) or not row["source_ids"]:
            errors.append(key + " row needs source_ids")
        if "currency" in fields and (len(row.get("currency", "")) != 3 or not row.get("currency", "").isupper()):
            errors.append(key + " currency requires uppercase three-letter code")
        for field in nullable:
            if row.get(field) is not None:
                try:
                    amount(row[field])
                except ValueError as exc:
                    errors.append(key + "." + field + ": " + str(exc))
    return items


def handoff(target, reason, required):
    return {"target_skill": target, "reason": reason, "required_inputs": required}

