#!/usr/bin/env python3
"""Prepare separate notice receipt, field normalization, support completeness and timeliness states from supplied JSON. Gaps never block receipt. No claim action or adjudication.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

from insurance_contract import build_artifact, timestamp
from submission_checks import compute as check_submission

DISCLAIMER = (
    "Intake normalization only; not a coverage, liability, or reserve determination and "
    "not a claim-handling decision. No claim has been opened, routed, or adjudicated."
)

# canonical field -> raw field
PLAIN = {
    "policy_number": "policy_number",
    "loss_date": "loss_date",
    "reported_date": "reported_date",
    "claimant": "claimant_name",
    "loss_location": "loss_location_raw",
}
CODED = {"loss_type": ("loss_type_raw", "loss_type_map"), "cause": ("cause_raw", "cause_map")}


def _s(v):
    return str(v).strip() if v is not None else ""


def _calculate(doc: dict) -> dict:
    raw = doc["raw_fnol"]
    cfg = doc["config"]
    fid = raw.get("fnol_id")
    exceptions, log = [], []

    def cite(field):
        return f"intake:fnol={fid};field={field}"

    def exc(field, raw_field, reason, etype):
        exceptions.append(
            {
                "type": etype,
                "field": field,
                "raw_value": _s(raw.get(raw_field)),
                "reason": reason,
                "citation": cite(raw_field),
            }
        )

    normalized = {}
    # plain fields
    for canon, rawf in PLAIN.items():
        normalized[canon] = _s(raw.get(rawf)) or None
        log.append(
            {
                "field": canon,
                "raw_value": _s(raw.get(rawf)),
                "canonical_value": normalized[canon],
                "mapping_source": "carry-through",
                "citation": cite(rawf),
            }
        )
    # coded fields
    for canon, (rawf, mapname) in CODED.items():
        vmap = {k.lower().strip(): v for k, v in (cfg.get(mapname) or {}).items()}
        rawval = _s(raw.get(rawf))
        canonval = vmap.get(rawval.lower()) if rawval else None
        normalized[canon] = canonval
        log.append(
            {
                "field": canon,
                "raw_value": rawval,
                "canonical_value": canonval,
                "mapping_source": mapname,
                "citation": cite(rawf),
            }
        )
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
    dates_valid = True
    for field, value in (("loss_date", ld), ("reported_date", rd)):
        try:
            date.fromisoformat(str(value))
        except (ValueError, TypeError):
            dates_valid = False
            exc(field, field, "date missing or not an ISO calendar date", "invalid_date")
    if dates_valid and ld > rd:
        exceptions.append(
            {
                "type": "date_order",
                "field": "loss_date",
                "raw_value": ld,
                "reason": f"loss_date {ld} is after reported_date {rd}",
                "citation": cite("loss_date"),
            }
        )

    if not cfg.get("config_version"):
        exc("config_version", "config_version", "vocabulary version unavailable", "unknown_config")
    package = doc.get("claim_package")
    readiness = check_submission(package) if isinstance(package, dict) else None
    if readiness:
        linked = (
            package.get("fnol_id") == fid
            and package.get("policy_number") == raw.get("policy_number")
            and package.get("dates", {}).get("date_of_loss") == raw.get("loss_date")
            and package.get("dates", {}).get("date_reported") == raw.get("reported_date")
            and bool((package.get("identity_mapping") or {}).get("source_ref"))
        )
        if not linked:
            readiness["not_evaluable"].append(
                {
                    "check": "requirements",
                    "why": "notification-to-claim identity and date linkage requires reviewed source mapping",
                }
            )
            readiness["readiness_status"] = "Unknown"
    completeness = "unknown"
    timeliness = "unknown"
    if readiness:
        unknown = readiness["not_evaluable"]
        if not any(c["check"] in {"requirements", "config_version"} for c in unknown):
            completeness = (
                "gaps"
                if any(
                    g["category"] in {"required_document", "required_form", "required_field"} for g in readiness["gaps"]
                )
                else "complete"
            )
        if not any(c["check"].startswith(("chronology", "deadlines")) for c in unknown):
            timeliness = (
                "review" if any(g["category"] in {"chronology", "deadline"} for g in readiness["gaps"]) else "checked"
            )
    receipt = raw.get("receipt") or {}
    received = False
    if receipt.get("source_ref"):
        try:
            timestamp(receipt.get("received_at"))
            received = True
        except ValueError:
            pass
    states = {
        "receipt": "recorded" if received else "unverified",
        "normalization": "complete" if not exceptions else "exceptions",
        "completeness": completeness,
        "timeliness": timeliness,
    }
    disposition = (
        "prepared-for-review"
        if all(
            states[k] == v
            for k, v in (
                ("receipt", "recorded"),
                ("normalization", "complete"),
                ("completeness", "complete"),
                ("timeliness", "checked"),
            )
        )
        else "exceptions-for-review"
    )
    fingerprint = hashlib.sha256(
        json.dumps(doc, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return {
        "normalization_id": f"fnol-{fid or 'UNKNOWN'}-{fingerprint[:16]}",
        "input_fingerprint": fingerprint,
        "intake_states": states,
        "notice_receipt_blocked": False,
        "receipt_evidence": receipt,
        "submission_assessment": readiness,
        "fnol_id": fid,
        "config_version": cfg.get("config_version"),
        "normalized": normalized,
        "normalization_log": log,
        "exceptions": exceptions,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = [
        "intake: " + k + "=" + v
        for k, v in output["intake_states"].items()
        if v in {"unknown", "exceptions", "gaps", "review", "unverified"}
    ]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="claim-intake-preparer",
        artifact_type="fnol-normalizer-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


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
