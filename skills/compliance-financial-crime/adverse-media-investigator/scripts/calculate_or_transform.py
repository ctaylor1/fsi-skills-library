#!/usr/bin/env python3
"""Deterministic adverse-media investigation engine for adverse-media-investigator.

For each subject in a screening batch this builds a durable case and an evidence bundle:
  1. Entity resolution   - score each candidate hit against the subject's identifiers and
     classify it strong / weak / namesake-discarded (a hard disambiguator such as a DOB or
     identifier mismatch discards the hit regardless of name).
  2. Source & assertion   - tier the source (1 official/court/regulator, 2 established media,
     3 low-reliability) and separate a `finding` from an `allegation` and a
     `resolved-dismissed` (mitigating) matter.
  3. Materiality (documented, deterministic) - category weight + assertion + source tier +
     recency, gated by entity match; namesake and resolved-dismissed hits contribute 0.
  4. Disposition RECOMMENDATION only - route sanctions/PEP proximity to a specialist, flag an
     unresolvable subject as needs-data, and otherwise recommend escalate-EDD / monitor /
     no-material-adverse-media. It NEVER closes a case, clears a customer, confirms a
     determination, or files anything - a human adjudicates every case.

Usage: python calculate_or_transform.py screening_batch.json | --selftest
Prints the investigation JSON (one case per subject) to stdout.
"""
from __future__ import annotations
import copy, json, sys
from datetime import date
from pathlib import Path

# ---- documented, versioned scoring configuration (overridable via input.scoring_config) ---
DEFAULT_CONFIG = {
    # entity-resolution weights
    "name": {"exact": 3, "partial": 1, "none": 0},
    "dob": {"match": 3, "mismatch": -99, "unknown": 0},
    "nationality": {"match": 1, "mismatch": -2, "unknown": 0},
    "location": {"match": 1, "mismatch": -1, "unknown": 0},
    "identifier": {"match": 4, "mismatch": -99, "unknown": 0},
    "strong_min": 6,
    "weak_min": 3,
    # materiality inputs
    "category_weight": {
        "money_laundering": 4, "terrorist_financing": 4, "sanctions_evasion": 4,
        "sanctions_designation": 4, "pep_exposure": 3,
        "fraud": 3, "corruption": 3, "bribery": 3, "tax_evasion": 3, "market_abuse": 3,
        "financial_crime_other": 2, "regulatory_breach": 2,
        "litigation_civil": 1, "adverse_other": 1,
    },
    "assertion_addend": {"finding": 3, "allegation": 1, "resolved-dismissed": 0},
    "source_tier_addend": {1: 3, 2: 1, 3: 0},
    "recency": {"within_2y_days": 730, "within_5y_days": 1826, "within_2y": 2, "within_5y": 1, "older": 0},
    "material_min": 9,   # case score >= -> Material
    "watch_min": 5,      # case score >= -> Watch
}
LIST_ROUTE = {"sanctions", "pep"}
STANDING_NOTE = ("Adverse-media investigation is decision support only; no case has been "
                 "closed, no customer cleared or determined, and no filing has been made.")


def _cfg(doc):
    c = copy.deepcopy(DEFAULT_CONFIG)
    for k, v in (doc.get("scoring_config") or {}).items():
        if isinstance(v, dict) and isinstance(c.get(k), dict):
            c[k].update(v)
        else:
            c[k] = v
    return c


def _days_between(published, as_of):
    try:
        p = date.fromisoformat(str(published)[:10])
        a = date.fromisoformat(str(as_of)[:10])
        return (a - p).days
    except Exception:
        return None


def _mask_identifiers(ids):
    out = []
    for i in ids or []:
        s = str(i)
        out.append(s[:4] + "****" + s[-3:] if len(s) > 10 else s.split(":")[0] + ":****")
    return out


def _cite(hit):
    return f"{hit.get('source','?')}:{hit.get('source_ref','?')}@{hit.get('published_date','?')}"


def resolve_entity(hit, cfg):
    """Return (match_tier, match_score, basis[], hard_discard_reason|None)."""
    em = hit.get("entity_match") or {}
    name = em.get("name", "none")
    basis, score, hard = [], 0, None
    n = cfg["name"].get(name, 0)
    score += n
    basis.append(f"name {name} {n:+d}")
    if name == "none":
        hard = "no name match"
    for field in ("dob", "nationality", "location", "identifier"):
        val = em.get(field, "unknown")
        pts = cfg[field].get(val, 0)
        if pts <= -90:            # hard disambiguator
            hard = hard or f"{field} mismatch"
            basis.append(f"{field} {val} (hard-discard)")
        else:
            score += pts
            basis.append(f"{field} {val} {pts:+d}")
    if hard:
        return "namesake-discarded", score, basis, hard
    if score >= cfg["strong_min"]:
        return "strong", score, basis, None
    if score >= cfg["weak_min"]:
        return "weak", score, basis, None
    return "namesake-discarded", score, basis, "insufficient corroborating identifiers"


def hit_materiality(hit, match_tier, cfg, as_of):
    if match_tier == "namesake-discarded":
        return 0, "excluded (namesake/discarded)"
    assertion = hit.get("assertion_type", "allegation")
    if assertion == "resolved-dismissed":
        return 0, "resolved/dismissed - not material (mitigating)"
    cat = hit.get("category", "adverse_other")
    cw = cfg["category_weight"].get(cat, 1)
    aw = cfg["assertion_addend"].get(assertion, 1)
    tier = hit.get("source_tier", 3)
    sw = cfg["source_tier_addend"].get(int(tier) if str(tier).isdigit() else 3, 0)
    d = _days_between(hit.get("published_date"), as_of)
    if d is None:
        rw, rlab = 0, "date unknown"
    elif d <= cfg["recency"]["within_2y_days"]:
        rw, rlab = cfg["recency"]["within_2y"], "<=2y"
    elif d <= cfg["recency"]["within_5y_days"]:
        rw, rlab = cfg["recency"]["within_5y"], "<=5y"
    else:
        rw, rlab = cfg["recency"]["older"], ">5y"
    total = cw + aw + sw + rw
    why = f"{cat} +{cw}; {assertion} +{aw}; tier{tier} +{sw}; recency {rlab} +{rw}"
    return total, why


def _band(score, cfg):
    if score >= cfg["material_min"]:
        return "Material"
    if score >= cfg["watch_min"]:
        return "Watch"
    return "Not material"


def investigate_subject(subj, doc, cfg):
    as_of = doc.get("as_of_date")
    case_id = subj.get("case_id") or f"AMI-{subj.get('subject_id')}"
    screening_ref = f"screening:{doc.get('config_version')}@{as_of}"

    matched, discarded, chronology, parties, amounts, citations = [], [], [], [], set(), [screening_ref]
    case_score, sanctions_pep_hit = 0, False

    name_matched_exists = False
    for hit in subj.get("hits") or []:
        tier, mscore, basis, hard = resolve_entity(hit, cfg)
        cite = _cite(hit)
        if (hit.get("entity_match") or {}).get("name") in ("exact", "partial"):
            name_matched_exists = True
        if tier == "namesake-discarded":
            discarded.append({
                "hit_id": hit.get("hit_id"), "reason": hard or "discarded",
                "match_score": mscore, "match_basis": "; ".join(basis),
                "headline": hit.get("headline"), "citation": cite,
            })
            citations.append(cite)
            continue
        rel, why = hit_materiality(hit, tier, cfg, as_of)
        citations.append(cite)
        item = {
            "hit_id": hit.get("hit_id"), "source": hit.get("source"),
            "source_tier": hit.get("source_tier"), "category": hit.get("category"),
            "assertion_type": hit.get("assertion_type"), "list_type": hit.get("list_type"),
            "match_tier": tier, "match_score": mscore, "match_basis": "; ".join(basis),
            "relevance": rel, "relevance_basis": why, "headline": hit.get("headline"),
            "published_date": hit.get("published_date"), "citation": cite,
        }
        matched.append(item)
        case_score = max(case_score, rel)
        if hit.get("list_type") in LIST_ROUTE:
            sanctions_pep_hit = True
        chronology.append({
            "date": hit.get("published_date"), "event": hit.get("headline"),
            "category": hit.get("category"), "assertion_type": hit.get("assertion_type"),
            "citation": cite,
        })
        for p in hit.get("named_parties") or []:
            if p not in parties:
                parties.append(p)
        for a in hit.get("amounts") or []:
            amounts.add(json.dumps({**a, "citation": cite}, sort_keys=True))

    chronology.sort(key=lambda c: str(c.get("date")))
    amounts_list = [json.loads(a) for a in sorted(amounts)]
    band = _band(case_score, cfg)

    has_disambig = bool(subj.get("dob") or subj.get("nationality") or subj.get("known_identifiers"))
    ambiguous = (not has_disambig) and name_matched_exists and not sanctions_pep_hit

    needs = []
    route_specialist = None
    if sanctions_pep_hit:
        disposition = "recommend-route-sanctions-pep"
        route_specialist = "sanctions-match-adjudicator"
        reason = "sanctions/PEP list proximity on a name-matched hit; specialist adjudicates identity and status."
    elif ambiguous:
        disposition = "needs-data"
        needs = ["subject date of birth or government/registry identifier to disambiguate a common-name hit"]
        reason = "subject cannot be resolved from available identifiers; do not attribute adverse media on a name alone."
    elif band == "Material":
        disposition = "recommend-escalate-edd"
        reason = "material adverse media matched to the subject; recommend enhanced due diligence and human adjudication."
    elif band == "Watch":
        disposition = "recommend-monitor"
        reason = "non-material adverse media matched to the subject; recommend ongoing monitoring, human review."
    else:
        disposition = "recommend-no-material-adverse-media"
        reason = "no material adverse media resolved to the subject after entity resolution; recommend human confirmation."

    evidence_bundle = {
        "case_id": case_id,
        "subject": {
            "subject_id": subj.get("subject_id"), "name": subj.get("name"),
            "type": subj.get("type"), "dob_year": (str(subj.get("dob"))[:4] if subj.get("dob") else None),
            "identifiers_masked": _mask_identifiers(subj.get("known_identifiers")),
        },
        "chronology": chronology,
        "parties": parties,
        "amounts": amounts_list,
        "matched_hits": matched,
        "discarded_namesakes": discarded,
        "reviewed_sources": sorted(set(citations)),
        "citations": sorted(set(citations)),
    }
    return {
        "subject_id": subj.get("subject_id"), "case_id": case_id,
        "materiality_score": case_score, "materiality_band": band,
        "disposition": disposition, "disposition_reason": reason,
        "needs": needs, "route_specialist": route_specialist,
        "matched_hits": matched, "discarded_namesakes": discarded,
        "evidence_bundle": evidence_bundle,
    }


def investigate(doc):
    cfg = _cfg(doc)
    cases = [investigate_subject(s, doc, cfg) for s in doc.get("subjects") or []]
    summary = {
        "total": len(cases),
        "escalate_edd": sum(1 for c in cases if c["disposition"] == "recommend-escalate-edd"),
        "monitor": sum(1 for c in cases if c["disposition"] == "recommend-monitor"),
        "route_sanctions_pep": sum(1 for c in cases if c["disposition"] == "recommend-route-sanctions-pep"),
        "no_material": sum(1 for c in cases if c["disposition"] == "recommend-no-material-adverse-media"),
        "needs_data": sum(1 for c in cases if c["disposition"] == "needs-data"),
    }
    return {"config_version": doc.get("config_version"), "as_of_date": doc.get("as_of_date"),
            "case_batch_id": doc.get("case_batch_id"), "cases": cases,
            "summary": summary, "standing_note": STANDING_NOTE}


def _load(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "screening_batch_example.json"
        return json.loads(p.read_text(encoding="utf-8"))
    if argv:
        return json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def main(argv):
    print(json.dumps(investigate(_load(argv)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
