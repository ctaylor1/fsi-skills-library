#!/usr/bin/env python3
"""The professional output is sanctions investigation support. Phase 1 does not implement a universal sanctions engine. Scores are illustrative, uncalibrated identity heuristics. A restrictions decision, indirect ownership/control analysis, license/exemption review and any block/reject/release/report remain with an authorized sanctions officer.

Offline Phase 1 calculation; see references/domain-rules.md.
"""
from __future__ import annotations
import json, re, sys, unicodedata
from datetime import date
from decimal import Decimal
from pathlib import Path
from native_integrity import attach_source

# Documented, versioned defaults; a deployment overrides via case-file "config".
DEFAULT_CONFIG = {
    "weights": {
        "name_primary_match": 3,
        "alias_match": 2,
        "dob_match": 3,
        "strong_id_match": 5,
        "nationality_match": 1,
        "place_of_birth_match": 1,
        "address_country_match": 1,
        "ownership_nexus": 6,
        "transaction_jurisdiction_nexus": 2,
        "program_asset_freeze": 1,
    },
    "discriminators": {
        "dob_mismatch": -3,
        "strong_id_mismatch": -4,
        "nationality_mismatch": -2,
        "entity_type_mismatch": -4,
    },
    "bands": {"true_match_min": 6, "review_min": 2},
    "ownership_threshold_pct": 50,
    "asset_freeze_programs": ["OFAC-SDN"],
    "strong_id_types": ["passport", "national_id", "registration_number", "tax_id", "lei"],
}

CORROBORATORS = ("name_primary_match", "alias_match", "dob_match", "strong_id_match",
                 "nationality_match", "place_of_birth_match", "address_country_match",
                 "ownership_nexus", "transaction_jurisdiction_nexus", "program_asset_freeze")
DISCRIMINATORS = ("dob_mismatch", "strong_id_mismatch", "nationality_mismatch",
                  "entity_type_mismatch")

STANDING_NOTE = (
    "Sanctions adjudication decision-support only; no match has been confirmed or discounted, "
    "no payment has been blocked, rejected, or released, no account has been blocked or "
    "unblocked, and no blocking/OFAC report has been filed. An authorized sanctions officer "
    "must adjudicate every disposition."
)


def _cfg(doc):
    c = json.loads(json.dumps(DEFAULT_CONFIG))
    override = doc.get("config") or {}
    for section in ("weights", "discriminators", "bands"):
        c[section].update((override.get(section) or {}))
    for scalar in ("strong_id_types",):
        if scalar in override:
            c[scalar] = override[scalar]
    return c


def _norm_name(s):
    s = unicodedata.normalize("NFKC", str(s or "")).casefold().strip()
    s = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s)
    return re.sub(r"\s+", " ", s).strip()


def _name_variants(name, aliases):
    out = {_norm_name(name)}
    for a in aliases or []:
        out.add(_norm_name(a))
    return {x for x in out if x}


def _strong_ids(entity, strong_types):
    out = {}
    for idr in entity.get("identifiers") or []:
        t = str(idr.get("type", "")).lower()
        v = str(idr.get("value", "")).upper().replace(" ", "")
        country = _country(idr.get("country"))
        if t in strong_types and v and (country or t == "lei"):
            out.setdefault((t, country), set()).add(v)
    return out


def _country(v):
    return str(v or "").strip().upper()


def _addr_countries(entity):
    return {_country(a.get("country")) for a in (entity.get("addresses") or []) if a.get("country")}


def _factor(name, kind, weight, detail, citations):
    return {"name": name, "kind": kind, "weight": weight, "detail": detail,
            "citations": sorted(set(c for c in citations if c))}


def _cites(case):
    alert_id = case.get("alert_id")
    prov = case.get("screening_provenance") or {}
    me = case.get("matched_entity") or {}
    subj = case.get("subject") or {}
    tx = case.get("transaction_context") or {}
    hit = f"screening:hit={alert_id}@{prov.get('screening_run_id', '?')}"
    listc = (f"sanctions-list:{case.get('list_program')}/{me.get('list_ref')}"
             f"@{me.get('list_effective_date', '?')}")
    kyc = f"kyc:subject={subj.get('subject_id', '?')}@{subj.get('as_of', prov.get('screened_at', '?'))}"
    listc = me.get("source_ref") or listc
    kyc = subj.get("source_ref") or kyc
    txn = None
    if tx:
        txn = f"txns:payment={tx.get('payment_id', '?')}@{tx.get('value_date', '?')}"
    return {"hit": hit, "list": listc, "kyc": kyc, "txn": txn}


def _match_factors(case, cfg, c):
    subj = case.get("subject") or {}
    me = case.get("matched_entity") or {}
    w, d = cfg["weights"], cfg["discriminators"]
    factors = []

    subj_names = _name_variants(subj.get("name"), subj.get("aliases"))
    me_names = _name_variants(me.get("primary_name"), me.get("aka"))
    primary = _norm_name(subj.get("name")) == _norm_name(me.get("primary_name")) \
        and _norm_name(subj.get("name")) != ""
    if primary:
        factors.append(_factor("name_primary_match", "corroborator", w["name_primary_match"],
                               "subject name equals the listed primary name (normalized)",
                               [c["kyc"], c["list"]]))
    elif subj_names & me_names:
        shared = sorted(subj_names & me_names)
        factors.append(_factor("alias_match", "corroborator", w["alias_match"],
                               f"subject name/alias matches a listed name/AKA: {shared}",
                               [c["kyc"], c["list"]]))

    sd, md = str(subj.get("dob") or ""), str(me.get("dob") or "")
    if sd and md:
        if sd == md:
            factors.append(_factor("dob_match", "corroborator", w["dob_match"],
                                   f"date of birth matches ({sd})", [c["kyc"], c["list"]]))
        else:
            factors.append(_factor("dob_mismatch", "discriminator", d["dob_mismatch"],
                                   f"date of birth differs (subject {sd} vs listed {md})",
                                   [c["kyc"], c["list"]]))

    subj_ids = _strong_ids(subj, cfg["strong_id_types"])
    me_ids = _strong_ids(me, cfg["strong_id_types"])
    id_match = any(t in me_ids and (vs & me_ids[t]) for t, vs in subj_ids.items())
    if id_match:
        shared = sorted({v for t, vs in subj_ids.items() if t in me_ids for v in (vs & me_ids[t])})
        factors.append(_factor("strong_id_match", "corroborator", w["strong_id_match"],
                               f"strong identifier matches ({shared})", [c["kyc"], c["list"]]))
    elif set(subj_ids) & set(me_ids):
        common = sorted(set(subj_ids) & set(me_ids))
        factors.append(_factor("strong_id_mismatch", "discriminator", d["strong_id_mismatch"],
                               f"same-type strong identifier present on both but values differ ({common})",
                               [c["kyc"], c["list"]]))

    sn, mn = _country(subj.get("nationality")), _country(me.get("nationality"))
    if sn and mn:
        if sn == mn:
            factors.append(_factor("nationality_match", "corroborator", w["nationality_match"],
                                   f"nationality matches ({sn})", [c["kyc"], c["list"]]))
        else:
            factors.append(_factor("nationality_mismatch", "discriminator", d["nationality_mismatch"],
                                   f"nationality differs (subject {sn} vs listed {mn})",
                                   [c["kyc"], c["list"]]))

    sp, mp = _norm_name(subj.get("place_of_birth")), _norm_name(me.get("place_of_birth"))
    if sp and mp and sp == mp:
        factors.append(_factor("place_of_birth_match", "corroborator", w["place_of_birth_match"],
                               f"place of birth matches ({subj.get('place_of_birth')})",
                               [c["kyc"], c["list"]]))

    shared_addr = _addr_countries(subj) & _addr_countries(me)
    if shared_addr:
        factors.append(_factor("address_country_match", "corroborator", w["address_country_match"],
                               f"address country matches ({sorted(shared_addr)})", [c["kyc"], c["list"]]))

    ownership = _ownership(case)
    if ownership["status"] == "direct-aggregate-threshold-met":
        factors.append(_factor("ownership_nexus", "corroborator", 0,
                               f"supplied direct blocked ownership aggregates to {ownership['blocked_pct']}%; separate legal review required",
                               ownership["citations"]))

    st, mt = str(subj.get("entity_type") or "").lower(), str(me.get("entity_type") or "").lower()
    if st and mt and st != mt:
        factors.append(_factor("entity_type_mismatch", "discriminator", d["entity_type_mismatch"],
                               f"entity type differs (subject {st} vs listed {mt})",
                               [c["kyc"], c["list"]]))
    return factors


def _has(factors, name):
    return any(f["name"] == name for f in factors)


def _ownership(case):
    rows = (case.get("subject") or {}).get("ownership") or []
    result = {"status": "not-supplied", "blocked_pct": None, "citations": []}
    if not rows:
        return result
    if case.get("list_program") != "OFAC-SDN":
        result["status"] = "unsupported-regime"
        return result
    seen = set()
    total, all_ownership = Decimal("0"), Decimal("0")
    for row in rows:
        key = row.get("owner_id")
        pct = row.get("pct")
        if (not key or key in seen or not isinstance(pct, (int, float)) or isinstance(pct, bool)
                or not 0 <= pct <= 100 or row.get("direct") is not True
                or not isinstance(row.get("owner_blocked"), bool) or not row.get("source_ref")):
            result["status"] = "needs-ownership-evidence"
            return result
        seen.add(key)
        percentage = Decimal(str(pct))
        all_ownership += percentage
        if row["owner_blocked"]:
            if not row.get("owner_list_ref"):
                result["status"] = "needs-ownership-evidence"
                return result
            total += percentage
            result["citations"].append(row["source_ref"])
    if all_ownership > Decimal("100"):
        result["status"] = "needs-ownership-evidence"
        return result
    display_total = int(total) if total == total.to_integral_value() else float(total)
    result.update(blocked_pct=display_total, status="direct-aggregate-threshold-met" if total >= Decimal("50") else "below-direct-threshold-no-clearance")
    return result


def _data_gaps(case):
    gaps = []
    me, subj = case.get("matched_entity") or {}, case.get("subject") or {}
    try:
        assessed = date.fromisoformat(case["as_of"])
        retrieved = date.fromisoformat(me["retrieved_at"][:10])
        if not 0 <= (assessed - retrieved).days <= 1:
            gaps.append("current list snapshot")
    except (ValueError, TypeError, KeyError):
        gaps.append("dated list snapshot and assessment date")
    try:
        effective = date.fromisoformat(me["list_effective_date"])
        assessed = date.fromisoformat(case["as_of"])
        if effective.isoformat() != me["list_effective_date"]:
            raise ValueError("noncanonical effective date")
        if effective > assessed:
            gaps.append("list entry not yet effective as of assessment")
    except (ValueError, TypeError, KeyError):
        gaps.append("valid list effective date at assessment time")
    if not me.get("source_ref") or not subj.get("source_ref"):
        gaps.append("subject and list source references")
    if _ownership(case)["status"] in {"needs-ownership-evidence", "unsupported-regime"}:
        gaps.append("supported direct ownership evidence or specialist regime review")
    return gaps


def _chronology(case, c):
    me = case.get("matched_entity") or {}
    prov = case.get("screening_provenance") or {}
    tx = case.get("transaction_context") or {}
    events = []
    if me.get("list_effective_date"):
        events.append({"ts": me.get("list_effective_date"), "type": "list-entry",
                       "summary": f"{case.get('list_program')} listing {me.get('list_ref')} "
                                  f"({me.get('primary_name')}) effective", "citation": c["list"]})
    if me.get("list_updated_date"):
        events.append({"ts": me.get("list_updated_date"), "type": "list-update",
                       "summary": f"{me.get('list_ref')} listing last updated", "citation": c["list"]})
    if tx and tx.get("value_date"):
        events.append({"ts": tx.get("value_date"), "type": "transaction",
                       "summary": f"payment {tx.get('payment_id')} {tx.get('amount')} "
                                  f"{tx.get('currency')} ({'->'.join(tx.get('countries') or [])})",
                       "citation": c["txn"] or c["hit"]})
    for pc in case.get("prior_cases") or []:
        if pc.get("opened_at"):
            events.append({"ts": pc.get("opened_at"), "type": "prior-case",
                           "summary": f"prior adjudication {pc.get('case_id')} ({pc.get('status')})",
                           "citation": f"casemgmt:prior={pc.get('case_id')}"})
    if prov.get("screened_at"):
        events.append({"ts": prov.get("screened_at"), "type": "screening-hit",
                       "summary": f"screening hit {case.get('alert_id')} raised by "
                                  f"{prov.get('screening_engine')} (run {prov.get('screening_run_id')})",
                       "citation": c["hit"]})
    events.sort(key=lambda e: str(e.get("ts")))
    return events


def _parties(case, c):
    subj = case.get("subject") or {}
    me = case.get("matched_entity") or {}
    parties = [
        {"role": "subject", "id": subj.get("subject_id"), "name": subj.get("name"),
         "entity_type": subj.get("entity_type"), "citations": [c["kyc"]]},
        {"role": "matched-listed-entity", "id": me.get("list_ref"), "name": me.get("primary_name"),
         "entity_type": me.get("entity_type"), "citations": [c["list"]]},
    ]
    for o in subj.get("ownership") or []:
        if o.get("owner_listed"):
            parties.append({"role": "listed-owner", "id": o.get("owner_list_ref"),
                            "name": o.get("owner_name"), "pct": o.get("pct"),
                            "citations": [c["kyc"], c["list"]]})
    tx = case.get("transaction_context") or {}
    for p in tx.get("chain_parties") or []:
        parties.append({"role": "transaction-party", "id": p.get("party_ref"),
                        "name": p.get("name"), "citations": [c["txn"] or c["hit"]]})
    return parties


def _discriminating(subj, case):
    return bool(subj.get("dob") or subj.get("identifiers") or subj.get("nationality")
                or subj.get("place_of_birth") or subj.get("addresses")
                or subj.get("ownership"))


def _duplicate(case):
    subj = case.get("subject") or {}
    for pc in case.get("prior_cases") or []:
        if (pc.get("subject_id") == subj.get("subject_id")
                and pc.get("list_ref") == (case.get("matched_entity") or {}).get("list_ref")
                and pc.get("status") == "open"
                and case.get("evidence_snapshot_ref")
                and pc.get("evidence_snapshot_ref") == case.get("evidence_snapshot_ref")):
            return pc
    return None


def _routing(case, factors):
    r = []
    if _has(factors, "ownership_nexus"):
        r.append("beneficial-ownership-analyzer")
    if case.get("edd_required") is True:
        r.append("enhanced-due-diligence-assessor")
    if case.get("adverse_media_referral") is True:
        r.append("adverse-media-investigator")
    return r


def adjudicate_case(case, cfg):
    alert_id = case.get("alert_id")
    case_id = f"SANC-{alert_id}"
    c = _cites(case)
    subj = case.get("subject") or {}
    me = case.get("matched_entity") or {}
    tx = case.get("transaction_context") or {}

    factors = _match_factors(case, cfg, c)
    chronology = _chronology(case, c)
    parties = _parties(case, c)
    dup = _duplicate(case)

    all_cites = sorted(set([c["hit"], c["list"], c["kyc"]] + ([c["txn"]] if c["txn"] else [])
                           + [ct for f in factors for ct in f["citations"]]
                           + [ev["citation"] for ev in chronology if ev.get("citation")]))
    score = sum(f["weight"] for f in factors)
    corr = [f"{f['name']} +{f['weight']}" for f in factors if f["kind"] == "corroborator"]
    disc = [f"{f['name']} {f['weight']}" for f in factors if f["kind"] == "discriminator"]

    bundle = {
        "case_id": case_id,
        "subject_id": subj.get("subject_id"),
        "list_ref": me.get("list_ref"),
        "list_program": case.get("list_program"),
        "screening_context": case.get("screening_context"),
        "parties": parties,
        "chronology": chronology,
        "amounts": {"amount": tx.get("amount") if tx else None,
                    "currency": tx.get("currency") if tx else None},
        "match_factors": factors,
        "match_score": score,
        "corroborators": corr,
        "discriminators": disc,
        "linked_cases": [dup.get("case_id")] if dup else [],
        "citations": all_cites,
    }

    rec = {"alert_id": alert_id, "case_id": case_id, "as_of": case.get("as_of"), "list_retrieved_at": me.get("retrieved_at"), "list_program": case.get("list_program"),
           "screening_context": case.get("screening_context"),
           "screening_provenance": case.get("screening_provenance"),
           "evidence_bundle": bundle, "match_score": score,
           "score_reason": "; ".join(corr + disc), "recommended_routing": _routing(case, factors),
           "needs": [], "linked_case_id": None}

    rec["ownership_assessment"] = _ownership(case)
    rec["restrictions_assessment"] = "not-performed; sanctions officer must apply the specific regime, authorizations and effective date"
    rec["needs"] = _data_gaps(case)
    if case.get("list_program") == "PEP":
        rec["needs"].append("PEP review belongs to customer due diligence")
        rec["recommended_routing"] = ["customer-risk-rating-reviewer"]
    elif case.get("list_program") != "OFAC-SDN":
        rec["needs"].append("regime not implemented in Phase 1; identity factors are illustrative only")
    if rec["needs"]:
        rec.update(disposition_basis="needs-data", disposition_recommendation="needs-data",
                   rationale="Evidence or regime gaps require specialist review; no negative sanctions conclusion is available.")
        return rec

    # 1) needs-data: name-only hit with nothing to discriminate identity on.
    if not me:
        rec["needs"] = ["matched listed entity"]
        rec["disposition_basis"] = "needs-data"
        rec["disposition_recommendation"] = "needs-data"
        rec["rationale"] = "No matched listed entity supplied; needs-data."
        return rec
    if not _discriminating(subj, case):
        rec["needs"] = ["a secondary identifier, DOB, nationality, place of birth, address, "
                        "ownership, or transaction context to discriminate identity"]
        rec["disposition_basis"] = "needs-data"
        rec["disposition_recommendation"] = "needs-data"
        rec["rationale"] = ("The subject record carries a name only; a name-alone hit cannot be "
                            "confirmed or discounted. Needs-data: obtain a discriminating attribute "
                            "before adjudication.")
        return rec

    # 2) possible-duplicate: overlaps an open/prior adjudication for the same subject and listing.
    if dup:
        rec["linked_case_id"] = dup.get("case_id")
        rec["disposition_basis"] = "possible-duplicate"
        rec["disposition_recommendation"] = "possible-duplicate"
        rec["rationale"] = (f"Overlaps adjudication {dup.get('case_id')} for the same subject and "
                            "listing; recommend linking as a possible duplicate for human "
                            "confirmation rather than re-adjudicating in parallel.")
        return rec

    # 3) documented override: OFAC 50% Rule ownership nexus.
    if _has(factors, "ownership_nexus"):
        rec["disposition_basis"] = "ownership-override"
        rec["disposition_recommendation"] = "recommend-true-match-escalate"
        rec["rationale"] = ("Subject is owned at or above the ownership threshold by a listed party "
                            "(50% Rule); recommend escalating as a true match to an authorized "
                            "sanctions officer for the blocking/reporting decision. An entity-type "
                            "difference does not defeat an ownership nexus.")
        return rec

    # 4) documented override: matching strong identifier together with a matching name/alias.
    if _has(factors, "strong_id_match") and (_has(factors, "name_primary_match") or _has(factors, "alias_match")):
        rec["disposition_basis"] = "strong-id-override"
        rec["disposition_recommendation"] = "recommend-true-match-escalate"
        rec["rationale"] = ("A strong identifier matches together with the name/alias; identity is "
                            "corroborated. Recommend escalating as a true match to an authorized "
                            "sanctions officer for the blocking/reporting decision.")
        return rec

    # 5) conflict guard: strong corroborators and strong discriminators disagree -> never auto-discount.
    strong_corr = ((_has(factors, "name_primary_match") or _has(factors, "alias_match"))
                   and (_has(factors, "dob_match") or _has(factors, "nationality_match")))
    strong_disc = _has(factors, "strong_id_mismatch") or _has(factors, "dob_mismatch")
    if strong_corr and strong_disc and score < cfg["bands"]["review_min"]:
        rec["disposition_basis"] = "conflict-guard"
        rec["disposition_recommendation"] = "recommend-potential-match-l2-review"
        rec["rationale"] = ("Strong corroborating and strong discriminating signals disagree "
                            "(e.g., matching name/DOB but a differing identifier); the hit cannot be "
                            "auto-discounted. Recommend L2/senior sanctions review.")
        return rec

    # 6) documented score bands (a RECOMMENDATION only).
    rec["disposition_basis"] = "score-band"
    if score >= cfg["bands"]["true_match_min"]:
        rec["disposition_recommendation"] = "recommend-true-match-escalate"
        rec["rationale"] = ("Corroborating factors outweigh discriminators above the true-match band; "
                            "recommend escalating as a true match to an authorized sanctions officer. "
                            "Breached factors: " + "; ".join(corr + disc) + ".")
    elif score >= cfg["bands"]["review_min"]:
        rec["disposition_recommendation"] = "recommend-potential-match-l2-review"
        rec["rationale"] = ("Evidence is inconclusive (identity neither confirmed nor excluded); "
                            "recommend L2/senior sanctions review. Factors: " + "; ".join(corr + disc) + ".")
    else:
        if not disc:
            rec.update(disposition_basis="needs-data", disposition_recommendation="needs-data",
                       rationale="No compared discriminating evidence supports a negative identity conclusion.")
            rec["needs"].append("comparable identity attributes")
            return rec
        rec["disposition_recommendation"] = "recommend-false-positive-discount"
        rec["rationale"] = ("Discriminators outweigh corroborators and no strong-identity conflict "
                            "remains; recommend discounting as a false positive, subject to reviewer "
                            "confirmation. No determination is made here. Factors: "
                            + "; ".join(corr + disc) + ".")
    return rec


def _compute_unbound(doc):
    cfg = _cfg(doc)
    cases = [adjudicate_case(c, cfg) for c in doc.get("cases", [])]
    disp = lambda d: sum(1 for x in cases if x["disposition_recommendation"] == d)
    return {
        "config_version": doc.get("config_version"),
        "cases": cases,
        "summary": {
            "total": len(cases),
            "recommend_true_match_escalate": disp("recommend-true-match-escalate"),
            "recommend_potential_match_l2_review": disp("recommend-potential-match-l2-review"),
            "recommend_false_positive_discount": disp("recommend-false-positive-discount"),
            "needs_data": disp("needs-data"),
            "possible_duplicate": disp("possible-duplicate"),
        },
        "standing_note": STANDING_NOTE,
    }


def adjudicate(doc):
    """Reject invalid intake before producing a native result; warnings remain partial."""
    from validate_input import validate as validate_input
    errors, _warnings = validate_input(doc)
    if errors:
        raise ValueError("invalid sanctions-match-investigator input: " + "; ".join(errors))
    try:
        return attach_source(_compute_unbound(doc), doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        raise ValueError("invalid sanctions-match-investigator input: " + str(exc)) from exc


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = adjudicate(doc)
    except ValueError as exc:
        print("ERROR " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
