#!/usr/bin/env python3
"""Deterministic data-quality exception detection for investment-data-quality-reviewer.

Reads a feed snapshot (see validate_input.py), runs the six deterministic checks, attaches
cited evidence (with as-of) to each exception, assigns a severity from versioned config
(escalated one band for NAV-impacting valuation-critical types), routes each exception, and
maps the exception set to a queue-priority band. Emits a machine-readable queue that the
SKILL wraps in a plain-language write-up.

IMPORTANT: This DETECTS, EVIDENCES, and PRIORITIZES only. It never corrects, overrides, fills,
suppresses, waives, or closes an exception, and never chooses a canonical value. Severities
and the priority mapping are deterministic and documented in references/data_quality-domain-rules.md.

Usage:
  python calculate_or_transform.py snapshot.json   # prints queue JSON
  python calculate_or_transform.py --selftest       # runs over the bundled fixture + invariants
Prints the queue JSON to stdout. --selftest also prints a line ending "N error(s)"; exit 0/1.
"""
from __future__ import annotations
import json, sys, hashlib, math
from collections import Counter
from datetime import date, datetime
from pathlib import Path

DISCLAIMER = ("Detection evidence only; exceptions are open findings. No data has been "
              "corrected, overridden, or suppressed, and no canonical value has been chosen.")

CHECKS = ["missing_price", "temporal_invalid", "stale_price", "implausible_move", "absent_factor", "duplicate_instrument",
          "conflicting_classification", "broken_mapping"]

DEFAULT_CONFIG = {
    "price_max_age_days": 5,
    "price_unchanged_max_days": 5,
    "move_band": {"equity": 0.25, "bond": 0.10, "default": 0.20},
    "required_factors": {"equity": ["beta", "sector"], "bond": ["duration", "rating"]},
    "severity": {
        "missing_price": "High", "temporal_invalid": "High", "broken_mapping": "High", "implausible_move": "High", "stale_price": "Medium",
        "conflicting_classification": "Medium", "duplicate_instrument": "Medium",
        "absent_factor": "Low",
    },
    "p1_high_count": 3,
}
ID_PRIORITY = ["isin", "cusip", "sedol", "ticker"]
SEV_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
NAV_ESCALATE_TYPES = {"stale_price", "implausible_move", "broken_mapping"}
ROUTE = {
    "missing_price": "fund-valuation-oversight-reviewer",
    "temporal_invalid": "investment-data-analyst-review",
    "conflicting_classification": "investment-data-quality-reviewer",
    "duplicate_instrument": "investment-reference-data-reviewer",
    "broken_mapping": "investment-reference-data-reviewer",
    "stale_price": "investment-data-analyst-review",
    "implausible_move": "investment-data-analyst-review",
    "absent_factor": "investment-data-analyst-review",
}


def _num(v):
    try:
        value = float(v)
        return value if not isinstance(v, bool) and math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _parse_date(s) -> date:
    s = str(s)[:10]
    return datetime.strptime(s, "%Y-%m-%d").date()


def _best_identifier(inst: dict) -> dict:
    ids = inst.get("identifiers") or {}
    for scheme in ID_PRIORITY:
        val = ids.get(scheme)
        if val:
            return {"scheme": scheme, "value": val}
    return {"scheme": None, "value": None}


def _severity(exc_type: str, nav: bool, cfg: dict) -> str:
    base = cfg["severity"].get(exc_type, "Medium")
    if nav and exc_type in NAV_ESCALATE_TYPES:
        return RANK_SEV[min(4, SEV_RANK[base] + 1)]
    return base


def _priority(sevs: list[str], cfg: dict) -> str:
    if not sevs:
        return "None"
    ranks = [SEV_RANK[s] for s in sevs]
    top = max(ranks)
    high_plus = sum(1 for r in ranks if r >= 3)
    if top == 4 or high_plus >= cfg["p1_high_count"]:
        return "P1"
    if top == 3:
        return "P2"
    if top == 2:
        return "P3"
    return "P4"


def _cite(system: str, key: str, extra: str, asof) -> str:
    tail = f";{extra}" if extra else ""
    return f"{system}:inst={key}{tail}@{asof}"


def _compute_native(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    # merge nested config maps so a partial config override does not drop defaults
    for nested in ("move_band", "required_factors", "severity"):
        merged = {**DEFAULT_CONFIG[nested], **((doc.get("config") or {}).get(nested) or {})}
        cfg[nested] = merged

    as_of = _parse_date(doc["as_of"])
    portfolio = str(doc.get("portfolio_id", "NA"))
    cfg_ver = str(doc.get("config_version", "NA"))
    queue_id = f"idqed-{portfolio}-{doc['as_of']}-{cfg_ver}-" + hashlib.sha256(json.dumps(doc, sort_keys=True, allow_nan=False).encode()).hexdigest()[:12]

    insts = doc.get("instruments") or []
    by_key = {i["instrument_key"]: i for i in insts}
    prices = doc.get("prices") or []
    factors = doc.get("factors") or []
    classifications = doc.get("classifications") or []
    mappings = doc.get("mappings") or []

    exceptions: list[dict] = []
    not_evaluable: list[dict] = []
    seq: Counter = Counter()

    def add(exc_type: str, inst_key: str, reason: str, evidence: list, breach: dict):
        seq[exc_type] += 1
        inst = by_key.get(inst_key, {})
        nav = bool(inst.get("nav_impacting"))
        exceptions.append({
            "exception_id": f"{queue_id}::{exc_type}::{seq[exc_type]:02d}",
            "type": exc_type,
            "instrument": {"instrument_key": inst_key, "identifier": _best_identifier(inst)},
            "severity": _severity(exc_type, nav, cfg),
            "nav_impacting": nav,
            "reason": reason,
            "evidence": evidence,
            "breach": breach,
            "route_to": ROUTE[exc_type],
            **({"route_mode": "vendor_feed", "handoff_status": "requires_reviewed_mapping"} if exc_type == "conflicting_classification" else {}),
            "status": "open",
        })

    valid_prices = []
    for inst in insts:
        if inst.get("held") is True and not any(p.get("instrument_key") == inst["instrument_key"] for p in prices):
            add("missing_price", inst["instrument_key"], "Held instrument has no supplied price observation",
                [{"citation": inst.get("source_ref"), "as_of": doc["as_of"]}], {"price_rows": 0})
    for p in prices:
        try:
            observed = _parse_date(p.get("price_asof"))
            valid = observed <= as_of
        except (ValueError, TypeError): valid = False
        if not valid:
            add("temporal_invalid", p.get("instrument_key"), "Price date absent, invalid or after cutoff; dependent price tests withheld",
                [{"citation": _cite("px", p.get("instrument_key"), "", p.get("price_asof")), "as_of": doc["as_of"]}], {"price_asof": p.get("price_asof")})
        else: valid_prices.append(p)
    prices = valid_prices
    # 1. stale_price
    for p in sorted(prices, key=lambda r: str(r.get("instrument_key"))):
        key = p.get("instrument_key")
        asof = p.get("price_asof")
        if not asof:
            not_evaluable.append({"check": "stale_price", "instrument_key": key,
                                  "why": "no price_asof"})
            continue
        age = (as_of - _parse_date(asof)).days
        stale_age = age > cfg["price_max_age_days"]
        unchanged = p.get("unchanged_days")
        prev = _num(p.get("prev_price"))
        cur = _num(p.get("price"))
        stale_flat = (unchanged is not None and prev is not None and cur is not None
                      and cur == prev and int(unchanged) >= cfg["price_unchanged_max_days"])
        if stale_age or stale_flat:
            if stale_age:
                reason = (f"price as-of {asof} is {age}d old vs snapshot {doc['as_of']} "
                          f"(> {cfg['price_max_age_days']}d)")
            else:
                reason = (f"price unchanged for {unchanged} observations "
                          f"(>= {cfg['price_unchanged_max_days']})")
            add("stale_price", key, reason,
                [{"instrument_key": key, "price": p.get("price"), "price_asof": asof,
                  "age_days": age, "unchanged_days": unchanged,
                  "citation": _cite("px", key, f"src={p.get('source','feed')}", asof),
                  "as_of": asof}],
                {"price_max_age_days": cfg["price_max_age_days"], "age_days": age,
                 "price_unchanged_max_days": cfg["price_unchanged_max_days"]})

    # 2. implausible_move
    for p in sorted(prices, key=lambda r: str(r.get("instrument_key"))):
        key = p.get("instrument_key")
        cur = _num(p.get("price"))
        prev = _num(p.get("prev_price"))
        if cur is None or prev is None or prev == 0:
            not_evaluable.append({"check": "implausible_move", "instrument_key": key,
                                  "why": "missing price or prev_price"})
            continue
        try:
            prior_date = _parse_date(p.get("prev_price_asof"))
            current_date = _parse_date(p.get("price_asof"))
            compatible = prior_date < current_date and p.get("comparison_basis_reviewed") is True
        except (ValueError, TypeError): compatible = False
        if not compatible:
            not_evaluable.append({"check": "implausible_move", "instrument_key": key, "why": "prior date and adjusted-price/currency/unit comparison basis require review"})
            continue
        ret = (cur - prev) / prev
        asset_class = str((by_key.get(key) or {}).get("asset_class", "default"))
        band = cfg["move_band"].get(asset_class, cfg["move_band"]["default"])
        if abs(ret) > band:
            asof = p.get("price_asof", doc["as_of"])
            add("implausible_move", key,
                f"day-over-day return {ret:+.2%} exceeds {asset_class} band +/-{band:.0%}",
                [{"instrument_key": key, "price": cur, "prev_price": prev,
                  "return": round(ret, 6),
                  "citation": _cite("px", key, f"src={p.get('source','feed')}", asof),
                  "as_of": asof}],
                {"asset_class": asset_class, "move_band": band, "return": round(ret, 6)})

    # 3. absent_factor (held instruments only)
    for inst in sorted(insts, key=lambda i: str(i.get("instrument_key"))):
        key = inst.get("instrument_key")
        if not inst.get("held"):
            continue
        asset_class = str(inst.get("asset_class", "default"))
        required = inst.get("required_factors")
        if required is None:
            required = cfg["required_factors"].get(asset_class, [])
        present = set()
        for f in factors:
            if f.get("instrument_key") != key or f.get("value") in (None, ""): continue
            try:
                age = (as_of - _parse_date(f.get("as_of"))).days
                if 0 <= age <= cfg.get("factor_max_age_days", 30): present.add(f.get("factor"))
                else: not_evaluable.append({"check": "absent_factor", "instrument_key": key, "why": "factor observation is stale or future dated"})
            except (ValueError, TypeError):
                not_evaluable.append({"check": "absent_factor", "instrument_key": key, "why": "factor date missing or invalid"})
        missing = [r for r in required if r not in present]
        if missing:
            add("absent_factor", key,
                f"held {asset_class} instrument missing required factor(s): {', '.join(missing)}",
                [{"instrument_key": key, "missing_factors": missing, "required": required,
                  "citation": _cite("sec-master", key, "", doc["as_of"]),
                  "as_of": doc["as_of"]}],
                {"required_factors": required, "missing_factors": missing})

    # 4. duplicate_instrument (distinct keys sharing a non-empty identifier value)
    collisions: dict = {}
    for scheme in ID_PRIORITY:
        buckets: dict = {}
        for inst in insts:
            val = (inst.get("identifiers") or {}).get(scheme)
            if scheme == "ticker":
                if not inst.get("exchange") or not inst.get("currency"): continue
                val = str(val) + "|" + inst["exchange"] + "|" + inst["currency"]
            if val:
                buckets.setdefault(str(val), set()).add(inst.get("instrument_key"))
        for val, keys in buckets.items():
            if len(keys) >= 2:
                fs = frozenset(keys)
                collisions.setdefault(fs, (scheme, val))
    for fs in sorted(collisions, key=lambda s: sorted(s)):
        scheme, val = collisions[fs]
        keys = sorted(fs)
        add("duplicate_instrument", keys[0],
            f"instrument keys {keys} share {scheme}={val}",
            [{"instrument_key": k, "identifier": {"scheme": scheme, "value": val},
              "citation": _cite("sec-master", k, f"{scheme}={val}", doc["as_of"]),
              "as_of": doc["as_of"]} for k in keys],
            {"scheme": scheme, "value": val, "keys": keys})

    # 5. conflicting_classification (same key + scheme, distinct non-empty values across feeds)
    grouped: dict = {}
    for c in classifications:
        key = c.get("instrument_key")
        scheme = c.get("scheme")
        val = c.get("value")
        if val in (None, ""):
            continue
        try:
            dt = _parse_date(c.get("as_of"))
            if dt > as_of: raise ValueError("future")
        except (TypeError, ValueError):
            not_evaluable.append({"check": "conflicting_classification", "instrument_key": key, "why": "classification effective date missing, invalid or future"})
            continue
        grouped.setdefault((key, scheme), []).append(c)
    for (key, scheme) in sorted(grouped, key=lambda t: (str(t[0]), str(t[1]))):
        rows = grouped[(key, scheme)]
        distinct = sorted({str(r.get("value")) for r in rows})
        if len(distinct) >= 2 and len({r.get("feed") for r in rows}) >= 2 and len({str(r.get("as_of"))[:10] for r in rows}) == 1:
            desc = " vs ".join(f"{r.get('feed','?')}={r.get('value')}" for r in rows)
            add("conflicting_classification", key,
                f"scheme {scheme}: conflicting values across feeds ({desc})",
                [{"instrument_key": key, "scheme": scheme, "feed": r.get("feed"),
                  "value": r.get("value"),
                  "citation": _cite("refdata", key, f"scheme={scheme};feed={r.get('feed')}",
                                    r.get("as_of", doc["as_of"])),
                  "as_of": r.get("as_of", doc["as_of"])} for r in rows],
                {"scheme": scheme, "distinct_values": distinct})

    # 6. broken_mapping — (a) unresolved mappings, (b) dangling references
    for m in sorted(mappings, key=lambda r: str(r.get("instrument_key"))):
        if m.get("resolved") is False:
            key = m.get("instrument_key")
            add("broken_mapping", key,
                f"mapping to {m.get('target','?')} is unresolved",
                [{"instrument_key": key, "target": m.get("target"), "resolved": False,
                  "citation": _cite("sec-master", key, f"target={m.get('target')}", doc["as_of"]),
                  "as_of": doc["as_of"]}],
                {"target": m.get("target"), "resolved": False})

    referenced: dict = {}
    for label, rows in (("prices", prices), ("factors", factors),
                        ("classifications", classifications), ("mappings", mappings)):
        for r in rows:
            k = r.get("instrument_key")
            if k is not None:
                referenced.setdefault(k, set()).add(label)
    for key in sorted(k for k in referenced if k not in by_key):
        add("broken_mapping", key,
            f"referenced instrument key {key!r} has no instrument record (dangling)",
            [{"referenced_key": key, "seen_in": sorted(referenced[key]),
              "citation": _cite("sec-master", key, "dangling", doc["as_of"]),
              "as_of": doc["as_of"]}],
            {"dangling": True, "seen_in": sorted(referenced[key])})

    severities = [e["severity"] for e in exceptions]
    return {
        "exception_queue_id": queue_id,
        "portfolio_id": portfolio,
        "as_of": doc["as_of"],
        "config_version": cfg_ver,
        "checks_run": CHECKS,
        "exceptions": exceptions,
        "not_evaluable": not_evaluable,
        "counts": {
            "total": len(exceptions),
            "by_type": dict(sorted(Counter(e["type"] for e in exceptions).items())),
            "by_severity": dict(sorted(Counter(severities).items())),
        },
        "queue_priority": _priority(severities, cfg),
        "priority_params": {"p1_high_count": cfg["p1_high_count"]},
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "feed_snapshot.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    queue = compute(doc)
    print(json.dumps(queue, indent=2))
    errors = []
    if not queue["exceptions"]:
        errors.append("selftest fixture produced no exceptions")
    for e in queue["exceptions"]:
        if not e.get("evidence"):
            errors.append(f"{e['exception_id']}: no evidence")
        for row in e.get("evidence", []):
            if not str(row.get("citation", "")).strip():
                errors.append(f"{e['exception_id']}: evidence row missing citation")
            if not str(row.get("as_of", "")).strip():
                errors.append(f"{e['exception_id']}: evidence row missing as_of")
        if e["severity"] not in SEV_RANK:
            errors.append(f"{e['exception_id']}: invalid severity {e['severity']!r}")
        if e["status"] != "open":
            errors.append(f"{e['exception_id']}: status must be 'open'")
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    recomputed = _priority([e["severity"] for e in queue["exceptions"]], cfg)
    if recomputed != queue["queue_priority"]:
        errors.append(f"queue_priority {queue['queue_priority']!r} != recomputed {recomputed!r}")
    for e in errors:
        print("ERROR", e)
    print(f"calculate_or_transform selftest: {len(errors)} error(s)")
    return 1 if errors else 0


from native_integrity import attach_source, canonical_hash

def compute(doc):
    canonical_hash(doc)
    return attach_source(_compute_native(doc), doc)


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
