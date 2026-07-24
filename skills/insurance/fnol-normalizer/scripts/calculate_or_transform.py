#!/usr/bin/env python3
"""Deterministic FNOL normalization for fnol-normalizer.

Maps free-text loss_type/cause to the controlled vocabulary, carries plain fields through, and
flags missing required fields, unmappable codes, and loss/report date-order problems. Produces a
normalized record + exceptions; never adjudicates, opens, or routes a claim.

Usage: python calculate_or_transform.py fnol.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Intake normalization only; not a coverage, liability, or reserve determination and "
              "not a claim-handling decision. No claim has been opened, routed, or adjudicated.")

# canonical field -> raw field
PLAIN = {"policy_number": "policy_number", "loss_date": "loss_date",
         "reported_date": "reported_date", "claimant": "claimant_name",
         "loss_location": "loss_location_raw"}
CODED = {"loss_type": ("loss_type_raw", "loss_type_map"),
         "cause": ("cause_raw", "cause_map")}


def _s(v):
    return str(v).strip() if v is not None else ""


def compute(doc: dict) -> dict:
    raw = doc["raw_fnol"]
    cfg = doc["config"]
    fid = raw.get("fnol_id")
    exceptions, log = [], []

    def cite(field):
        return f"intake:fnol={fid};field={field}"

    def exc(field, raw_field, reason, etype):
        exceptions.append({"type": etype, "field": field, "raw_value": _s(raw.get(raw_field)),
                           "reason": reason, "citation": cite(raw_field)})

    normalized = {}
    # plain fields
    for canon, rawf in PLAIN.items():
        normalized[canon] = _s(raw.get(rawf)) or None
        log.append({"field": canon, "raw_value": _s(raw.get(rawf)),
                    "canonical_value": normalized[canon], "mapping_source": "carry-through",
                    "citation": cite(rawf)})
    # coded fields
    for canon, (rawf, mapname) in CODED.items():
        vmap = {k.lower().strip(): v for k, v in (cfg.get(mapname) or {}).items()}
        rawval = _s(raw.get(rawf))
        canonval = vmap.get(rawval.lower()) if rawval else None
        normalized[canon] = canonval
        log.append({"field": canon, "raw_value": rawval, "canonical_value": canonval,
                    "mapping_source": mapname, "citation": cite(rawf)})
        if rawval and canonval is None:
            exc(canon, rawf, f"value '{rawval}' not in {mapname}", "unmapped_code")

    # required-field presence (empty raw only; unmapped handled above)
    raw_of = {**{c: r for c, r in PLAIN.items()}, "loss_type": "loss_type_raw", "cause": "cause_raw"}
    for field in cfg.get("required_fields") or []:
        rawf = raw_of.get(field, field)
        if not _s(raw.get(rawf)):
            exc(field, rawf, "required field is empty/absent", "missing_required")

    # date order
    ld, rd = normalized.get("loss_date"), normalized.get("reported_date")
    if ld and rd and str(ld) > str(rd):
        exceptions.append({"type": "date_order", "field": "loss_date", "raw_value": ld,
                           "reason": f"loss_date {ld} is after reported_date {rd}",
                           "citation": cite("loss_date")})

    disposition = "normalized" if not exceptions else "exceptions-for-review"
    return {
        "normalization_id": f"fnol-{fid or 'UNKNOWN'}-0001",
        "fnol_id": fid,
        "config_version": cfg.get("config_version"),
        "normalized": normalized,
        "normalization_log": log,
        "exceptions": exceptions,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "fnol_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
