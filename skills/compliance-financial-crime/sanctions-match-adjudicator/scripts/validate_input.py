#!/usr/bin/env python3
"""Deterministic input validation for sanctions-match-adjudicator.

Validates a screening-hit case file before an evidence bundle is built. Fails CLOSED on
structural problems (including missing screening provenance — adjudication must consume a
documented screening hit, never self-generate a match) and WARNS on data gaps that will
force a `needs-data` disposition or a weak chronology.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, cases[
    {alert_id, screening_context, list_program, source_ref,
     screening_provenance{screening_engine, screening_run_id, screened_at, screened_by},
     subject{subject_id, entity_type, name, aliases[], dob?, identifiers[]?, nationality?,
             place_of_birth?, addresses[]?, ownership[]?, as_of?},
     matched_entity{list_ref, entity_type, program, primary_name, aka[], dob?, identifiers[]?,
             nationality?, place_of_birth?, addresses[]?, list_effective_date, list_updated_date?},
     transaction_context?{payment_id, amount, currency, countries[], value_date, chain_parties[]},
     prior_cases[]}]

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "cases")
REQUIRED_CASE = ("alert_id", "screening_context", "list_program", "source_ref",
                 "screening_provenance", "subject", "matched_entity")
KNOWN_CONTEXTS = {"customer", "payment", "counterparty", "periodic-rescreening"}
KNOWN_PROGRAMS = {"OFAC-SDN", "OFAC-SSI", "EU-CFSP", "UN", "HMT-OFSI", "PEP"}
DISCRIMINATORS = ("dob", "identifiers", "nationality", "place_of_birth", "addresses", "ownership")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    cases = doc.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty list"], warnings

    seen = set()
    for i, c in enumerate(cases):
        tag = f"cases[{i}] ({c.get('alert_id','?')})"
        for k in REQUIRED_CASE:
            if k not in c or c[k] in (None, "", [], {}):
                errors.append(f"{tag}: missing '{k}'")
        aid = c.get("alert_id")
        if aid in seen:
            errors.append(f"{tag}: duplicate alert_id")
        seen.add(aid)

        # Screening provenance is mandatory — fail closed if the hit has no documented origin.
        prov = c.get("screening_provenance") or {}
        if not prov.get("screening_engine") or not prov.get("screening_run_id"):
            errors.append(f"{tag}: screening_provenance must carry 'screening_engine' and "
                          "'screening_run_id' (adjudication consumes a documented screening hit; "
                          "it does not self-generate a match)")
        if not prov.get("screened_at"):
            warnings.append(f"{tag}: screening_provenance has no 'screened_at' -> weak chronology")

        subj = c.get("subject") or {}
        if not subj.get("name"):
            errors.append(f"{tag}: subject requires a 'name'")
        if not subj.get("entity_type"):
            warnings.append(f"{tag}: subject has no 'entity_type' -> entity-type discriminator disabled")

        me = c.get("matched_entity") or {}
        for k in ("list_ref", "primary_name", "entity_type"):
            if not me.get(k):
                errors.append(f"{tag}: matched_entity requires '{k}'")
        if not me.get("list_effective_date"):
            warnings.append(f"{tag}: matched_entity has no 'list_effective_date' -> weak chronology/citation")
        prog = me.get("program")
        if prog and c.get("list_program") and prog != c.get("list_program"):
            warnings.append(f"{tag}: matched_entity.program {prog!r} != case list_program "
                            f"{c.get('list_program')!r} (entity resolution)")

        ctx = c.get("screening_context")
        if ctx and ctx not in KNOWN_CONTEXTS:
            warnings.append(f"{tag}: unknown screening_context {ctx!r}")
        if c.get("list_program") and c.get("list_program") not in KNOWN_PROGRAMS:
            warnings.append(f"{tag}: unknown list_program {c.get('list_program')!r} -> program severity may be under-weighted")

        # needs-data early warning: nothing to discriminate identity on (name-only hit).
        has_disc = any(subj.get(k) for k in DISCRIMINATORS) or bool(c.get("transaction_context"))
        if not has_disc:
            warnings.append(f"{tag}: subject carries a name only (no DOB/identifier/nationality/"
                            "address/ownership/transaction) -> disposition will be needs-data")

        # Ownership entries drive the 50% Rule override; each needs an owner list ref for citation.
        for o in subj.get("ownership") or []:
            if o.get("owner_listed") and not o.get("owner_list_ref"):
                warnings.append(f"{tag}: a listed ownership entry lacks 'owner_list_ref' -> weak citation")

        # Payment context should carry the fields the chronology/nexus rely on.
        tx = c.get("transaction_context")
        if ctx == "payment" and not tx:
            warnings.append(f"{tag}: payment screening with no transaction_context -> jurisdiction nexus disabled")
        if tx and not tx.get("value_date"):
            warnings.append(f"{tag}: transaction_context has no 'value_date' -> weak chronology")

        # Entity resolution: an ownership-derived hit is expected to differ in entity type.
        st, mt = str(subj.get("entity_type") or "").lower(), str(me.get("entity_type") or "").lower()
        if st and mt and st != mt and not subj.get("ownership"):
            warnings.append(f"{tag}: subject entity_type {st!r} != listed {mt!r} with no ownership nexus "
                            "(likely discriminator)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
