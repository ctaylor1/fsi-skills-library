#!/usr/bin/env python3
"""Deterministic canonical normalization for investment-record-normalizer.

Reads a multi-source ingest bundle (see validate_input.py), maps each source record 1:1 into
the approved canonical schema using a versioned mapping ruleset, attaches full lineage (an
immutable source snapshot hash + provenance), and routes anything unmappable to a
rejected-record queue with a reason code. Emits a canonical pack (positions, cash, orders,
transactions) + the reject queue + a reconciliation count.

HARD BOUNDARY (fail closed; enforced here and re-checked by validate_output.py):
  * Never MERGE identities. Each canonical record derives from exactly one source record and
    carries exactly one source_record_id. Two source records that look like the "same"
    holding stay two canonical records (each with its own lineage); merging/deduping is the
    security master's job, not the normalizer's.
  * Never OVERWRITE a source record. Sources are read-only; every record keeps an immutable
    source_hash. The normalizer produces a derived canonical view, it does not mutate input.
  * Never CHOOSE a canonical value across conflicting sources, resolve a conflicting
    identity, or reconcile to custodian. Those are adjacent skills (see references/handoffs.md).

The mapping is a versioned contract (ruleset_version); it is not tuned per record. Output is
deterministic and reproducible: same bundle + same ruleset -> identical pack (records sorted
by canonical_id / source key).

Usage:
  python calculate_or_transform.py bundle.json    # prints the canonical pack JSON
  python calculate_or_transform.py --selftest      # self-check over bundled fixture
Selftest prints a line ending "N error(s)"; exit 0 pass / 1 fail.
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import date

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DISCLAIMER = ("Derived canonical view with lineage; no source record was merged or overwritten and no "
              "reference-data conflict, identity, or reconciliation was resolved. Not an investment recommendation.")

# --- Versioned mapping ruleset (a contract; overridable via doc['ruleset']) -----------------
# Per (source_system, record_type): raw payload key -> canonical field. Coded values are
# translated via ENUMS; an unmapped code fails closed to the reject queue (never guessed).
DEFAULT_RULESET = {
    "version": "canon-ruleset-2026.07",
    "field_maps": {
        "custodian": {
            "position": {"acct": "account_id", "sec": "security_id", "qty": "quantity",
                         "cost": "cost_basis", "mv": "market_value", "ccy": "currency"},
            "cash": {"acct": "account_id", "ccy": "currency", "bal": "amount", "state": "cash_type"},
        },
        "administrator": {
            "position": {"account": "account_id", "instrument": "security_id", "units": "quantity",
                         "book_cost": "cost_basis", "value": "market_value", "curr": "currency"},
        },
        "oms": {
            "order": {"acct": "account_id", "ord_id": "order_ref", "side": "side",
                      "sec": "security_id", "qty": "quantity", "status": "order_status", "ccy": "currency"},
        },
        "accounting": {
            "transaction": {"acct": "account_id", "ref": "txn_ref", "type": "txn_type",
                            "sec": "security_id", "amt": "amount", "qty": "quantity", "ccy": "currency",
                            "trade_dt": "trade_date", "settle_dt": "settle_date"},
        },
    },
    "enums": {
        "side": {"B": "buy", "S": "sell", "BUY": "buy", "SELL": "sell"},
        "cash_type": {"SETT": "settled", "PEND": "pending"},
        "order_status": {"NEW": "new", "PARTIAL": "partial", "FILLED": "filled", "CANC": "cancelled"},
        "txn_type": {"BUY": "buy", "SELL": "sell", "DIV": "dividend", "INT": "interest",
                     "FEE": "fee", "XFER": "transfer"},
    },
}
# Required canonical fields per record_type (missing -> MISSING_REQUIRED_FIELD).
REQUIRED = {
    "position": ["account_id", "security_id", "quantity", "currency"],
    "cash": ["account_id", "currency", "amount"],
    "order": ["account_id", "order_ref", "side", "security_id", "quantity", "currency"],
    "transaction": ["account_id", "txn_ref", "txn_type", "amount", "currency", "trade_date"],
}
CODED = {"side": "side", "cash_type": "cash_type", "order_status": "order_status", "txn_type": "txn_type"}
NUMERIC = {"quantity", "cost_basis", "market_value", "amount"}
DATES = {"trade_date", "settle_date"}


def _hash(rec: dict) -> str:
    """Immutable snapshot of the source record — proves the source was preserved, not overwritten."""
    return "sha256:" + hashlib.sha256(json.dumps(rec, sort_keys=True).encode("utf-8")).hexdigest()


def _canonical_id(source_system: str, source_record_id: str) -> str:
    """Deterministic per-source surrogate key. 1:1 with a single source record — NOT a merge."""
    return f"can-{source_system}-{source_record_id}"


def _num(v):
    try:
        if isinstance(v, bool): return None
        value = Decimal(str(v))
        return str(value) if value.is_finite() else None
    except (TypeError, ValueError, InvalidOperation):
        return None


def _valid_date(value):
    try: date.fromisoformat(str(value)); return True
    except (TypeError, ValueError): return False


def _reject(rec: dict, code: str, detail: str) -> dict:
    return {"source_system": rec.get("source_system"), "source_record_id": rec.get("source_record_id"),
            "record_type": rec.get("record_type"), "reason_code": code, "reason": detail,
            "source_as_of": rec.get("source_as_of"), "source_hash": _hash(rec)}


def _map_record(rec: dict, ruleset: dict) -> tuple[dict | None, dict | None]:
    """Map one source record to canonical, or return a reject. Never merges/overwrites."""
    ss, rt = rec.get("source_system"), rec.get("record_type")
    payload = rec.get("payload") or {}
    sysmap = ruleset["field_maps"].get(ss)
    if sysmap is None:
        return None, _reject(rec, "UNMAPPED_SOURCE_SYSTEM", f"no mapping for source_system {ss!r}")
    fmap = sysmap.get(rt)
    if fmap is None:
        return None, _reject(rec, "UNMAPPED_RECORD_TYPE", f"no mapping for {ss!r}/{rt!r}")

    # Identity guard: if the source carries two differing identifiers for the same security
    # (sec vs sec_alt) the normalizer must NOT pick or merge one — it fails closed and routes
    # the conflict to the security master (see handoffs.md).
    if payload.get("sec_alt") not in (None, "") and payload.get("sec") not in (None, "") \
            and str(payload["sec_alt"]) != str(payload["sec"]):
        return None, _reject(rec, "AMBIGUOUS_IDENTITY",
                             f"conflicting identifiers sec={payload['sec']!r} vs sec_alt={payload['sec_alt']!r}; "
                             "route to investment-reference-data-reviewer (do not merge)")

    identity_fields = [key for key, target in fmap.items() if target == "security_id"]
    identity_values = {str(payload[key]) for key in identity_fields if payload.get(key) not in (None, "")}
    identity_values.update(str(v) for v in rec.get("identity_candidates", []) if v not in (None, ""))
    if len(identity_values) > 1:
        return None, _reject(rec, "AMBIGUOUS_IDENTITY", "Conflicting supplied identity candidates require steward review")
    canon: dict = {}
    for raw_key, canon_key in fmap.items():
        if raw_key not in payload:
            continue
        val = payload[raw_key]
        if canon_key in CODED:
            table = ruleset["enums"].get(CODED[canon_key], {})
            if str(val) not in table:
                return None, _reject(rec, "UNMAPPED_CODE_VALUE",
                                     f"{canon_key} code {val!r} not in ruleset enum {CODED[canon_key]!r}")
            val = table[str(val)]
        elif canon_key in NUMERIC:
            n = _num(val)
            if n is None:
                return None, _reject(rec, "UNPARSEABLE_NUMBER", f"{canon_key}={val!r} is not numeric")
            val = n
        elif canon_key in DATES:
            if not DATE_RE.fullmatch(str(val)) or not _valid_date(val):
                return None, _reject(rec, "UNPARSEABLE_DATE", f"{canon_key}={val!r} is not YYYY-MM-DD")
            val = str(val)
        canon[canon_key] = val

    missing = [f for f in REQUIRED[rt] if canon.get(f) in (None, "")]
    if missing:
        return None, _reject(rec, "MISSING_REQUIRED_FIELD", f"canonical {rt} missing {missing}")

    canon["position_basis"] = rec.get("position_basis")
    canon["quantity_unit"] = rec.get("quantity_unit")
    canon["lot_id"] = rec.get("lot_id")
    canon["effective_at"] = rec.get("effective_at") or rec.get("source_as_of")
    record = {
        "canonical_id": _canonical_id(ss, rec["source_record_id"]),
        "record_type": rt,
        "lineage": {
            "source_system": ss,
            "source_record_id": rec["source_record_id"],
            "source_as_of": rec.get("source_as_of"),
            "ingest_batch_id": rec.get("_ingest_batch_id"),
            "ruleset_version": ruleset["version"],
            "source_hash": _hash(rec),
        },
        "canonical": canon,
    }
    return record, None


def _compute_native(doc: dict) -> dict:
    ruleset = doc.get("ruleset") or DEFAULT_RULESET
    if doc.get("ruleset_version") != ruleset.get("version"):
        raise ValueError("Requested ruleset_version does not identify the supplied or bundled mapping ruleset")
    bundle_id = doc.get("bundle_id", "unknown-bundle")
    as_of = doc.get("as_of", "unknown")
    job_id = f"htn-{bundle_id}-{as_of}-" + hashlib.sha256(json.dumps(doc, sort_keys=True, allow_nan=False).encode()).hexdigest()[:12]
    recs = doc.get("records") or []

    identities = [(r.get('source_system'),r.get('source_record_id')) for r in recs]
    if len(identities) != len(set(identities)): raise ValueError('Duplicate source identity requires upstream investigation')
    canonical, rejected = [], []
    for r in recs:
        try:
            temporal_valid = date.fromisoformat(str(r.get('source_as_of'))[:10]) <= date.fromisoformat(str(as_of)[:10])
        except (TypeError,ValueError): temporal_valid = False
        if not temporal_valid:
            rejected.append(_reject(r, 'INVALID_SOURCE_DATE', 'Source observation date invalid or future at snapshot cutoff'))
            continue
        record, rej = _map_record(r, ruleset)
        if rej is not None:
            rejected.append(rej)
        else:
            record["lineage"]["ingest_batch_id"] = bundle_id
            canonical.append(record)

    canonical.sort(key=lambda c: c["canonical_id"])
    rejected.sort(key=lambda c: (str(c["source_system"]), str(c["source_record_id"])))

    return {
        "job_id": job_id,
        "bundle_id": bundle_id,
        "as_of": as_of,
        "ruleset_version": ruleset["version"],
        "input_record_count": len(recs),
        "canonical_records": canonical,
        "rejected_records": rejected,
        "reconciliation": {"input": len(recs), "canonical": len(canonical), "rejected": len(rejected)},
        "disclaimer": DISCLAIMER,
    }


def _selfcheck(pack: dict) -> list[str]:
    """Invariants the transform must always hold (independent of validate_output.py)."""
    errs = []
    rec = pack["reconciliation"]
    if rec["input"] != rec["canonical"] + rec["rejected"]:
        errs.append("reconciliation does not tie out (records silently dropped)")
    if rec["canonical"] != len(pack["canonical_records"]) or rec["rejected"] != len(pack["rejected_records"]):
        errs.append("reconciliation counts disagree with actual record counts")
    seen = set()
    for c in pack["canonical_records"]:
        lin = c.get("lineage") or {}
        if isinstance(lin.get("source_record_id"), (list, tuple)):
            errs.append(f"{c.get('canonical_id')}: multiple source_record_ids (identity merge)")
        for k in ("source_system", "source_record_id", "source_as_of", "ruleset_version", "source_hash"):
            if not lin.get(k):
                errs.append(f"{c.get('canonical_id')}: lineage missing {k}")
        if c["canonical_id"] in seen:
            errs.append(f"duplicate canonical_id {c['canonical_id']}")
        seen.add(c["canonical_id"])
    return errs


from native_integrity import attach_source, canonical_hash

def compute(doc):
    canonical_hash(doc)
    return attach_source(_compute_native(doc), doc)


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "source_bundle.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        pack = compute(doc)
        errs = _selfcheck(pack)
        for e in errs:
            print("ERROR", e)
        exp = "expected canonical=5 rejected=3"
        if pack["reconciliation"]["canonical"] != 5 or pack["reconciliation"]["rejected"] != 3:
            errs.append(f"fixture mismatch: got {pack['reconciliation']} ({exp})")
            print("ERROR", errs[-1])
        print(f"normalization self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
