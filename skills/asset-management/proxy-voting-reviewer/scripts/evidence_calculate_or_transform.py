#!/usr/bin/env python3
"""Deterministic proxy-meeting evidence engine for proxy-voting-reviewer.

For each agenda item of a shareholder meeting: classify every collected item as an OBSERVED
FACT or a HYPOTHESIS via the source hierarchy, check that the required evidence categories
and a consistent record-date entitlement are present, compute a documented review-priority
band, and assemble a cited evidence bundle with a durable case_id. It NEVER casts a vote,
proposes or recommends a vote direction, submits a ballot, closes a case, or overrides
entitlement/record-date data. Cited board / research-provider / precedent directions are
recorded as observed facts, not as a proposed instruction. An entitlement/record-date
inconsistency is flagged (never corrected) and forces the top review-priority band. A
disagreement between the issuer and a research provider is surfaced as an observed fact
(`contested`) and also forces the top band; it is not a recommended resolution.

Usage:
  python calculate_or_transform.py meeting.json   # prints the packet JSON to stdout
  python calculate_or_transform.py --selftest      # runs over the bundled fixture, prints the
                                                    # packet, then a self-consistency summary line
Exit 0 on success (in --selftest, 0 only if the self-consistency check finds 0 error(s)).
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
from native_integrity import attach_source, canonical_hash

OBSERVATION_SOURCES = {
    "meeting_notice", "issuer_disclosure", "policy_clause", "research_provider", "precedent_vote",
}
HYPOTHESIS_SOURCES = {"analyst_inference", "market_commentary", "estimated_outcome", "draft_rationale"}
HIERARCHY = ["meeting_notice", "issuer_disclosure", "ownership_record", "policy_clause",
             "research_provider", "precedent_vote"]
REQUIRED_CATEGORIES = {"meeting_notice", "issuer_disclosure", "policy_clause"}
EXPECTED_CATEGORIES = {"research_provider", "precedent_vote"}
SENSITIVE_TYPES = {
    "say_on_pay", "shareholder_proposal", "merger", "contested_election", "compensation_plan",
    "bylaw_amendment", "board_declassification", "capital_authorization",
}
DIRECTIONS = {"for", "against", "abstain", "withhold"}
STANDING_NOTE = ("Proxy-meeting evidence packet only; no vote has been cast, proposed, or "
                 "recommended, and no entitlement or record-date data has been overridden. Cited "
                 "board, research-provider, and precedent directions are observed facts for the "
                 "proxy-voting analyst and proxy committee to adjudicate.")

_SYSTEM = {
    "meeting_notice": "meeting", "issuer_disclosure": "issuer", "policy_clause": "policy",
    "research_provider": "research", "precedent_vote": "precedent",
    "analyst_inference": "analyst", "market_commentary": "commentary",
    "estimated_outcome": "estimate", "draft_rationale": "draft",
}
_ROLE = {
    "meeting_notice": "issuer", "issuer_disclosure": "issuer", "policy_clause": "policy-owner",
    "research_provider": "research_provider", "precedent_vote": "precedent_source",
    "analyst_inference": "analyst", "market_commentary": "commentary",
    "estimated_outcome": "analyst", "draft_rationale": "analyst",
}


def _fact_type(source_type: str) -> str:
    return "observation" if source_type in OBSERVATION_SOURCES else "hypothesis"


def _is_isodate(s) -> bool:
    try:
        date.fromisoformat(str(s)[:10])
        return True
    except (ValueError, TypeError):
        return False


def _business_days(d_from: str, d_to: str):
    if not (_is_isodate(d_from) and _is_isodate(d_to)):
        return None
    a = date.fromisoformat(str(d_from)[:10])
    b = date.fromisoformat(str(d_to)[:10])
    if b <= a:
        return 0
    n, cur = 0, a
    while cur < b:
        cur = date.fromordinal(cur.toordinal() + 1)
        if cur.weekday() < 5:
            n += 1
    return n


def _cite_ev(ev):
    return f"{_SYSTEM.get(ev.get('source_type'), 'src')}:{ev.get('source_id', '?')}@{ev.get('as_of', '?')}"


def _tag_evidence(evidence):
    tagged = []
    for ev in evidence or []:
        st = ev.get("source_type")
        tagged.append({
            "source_id": ev.get("source_id"),
            "source_type": st,
            "fact_type": _fact_type(st),
            "as_of": ev.get("as_of"),
            "board_recommendation": (str(ev["board_recommendation"]).lower()
                                     if ev.get("board_recommendation") is not None else None),
            "provider_recommendation": (str(ev["provider_recommendation"]).lower()
                                        if ev.get("provider_recommendation") is not None else None),
            "precedent_direction": (str(ev["precedent_direction"]).lower()
                                    if ev.get("precedent_direction") is not None else None),
            "clause": ev.get("clause"),
            "detail": ev.get("detail"),
        })
    return tagged


def _contested(tagged):
    """Observed fact: issuer board rec disagrees with a provider, or providers disagree."""
    board = next((t["board_recommendation"] for t in tagged
                  if t["source_type"] == "issuer_disclosure" and t["board_recommendation"] in DIRECTIONS), None)
    providers = [t["provider_recommendation"] for t in tagged
                 if t["source_type"] == "research_provider" and t["provider_recommendation"] in DIRECTIONS]
    disagree = []
    if board and any(p != board for p in providers):
        disagree.append("issuer-vs-provider")
    if len(set(providers)) > 1:
        disagree.append("provider-vs-provider")
    return (len(disagree) > 0), disagree


def _review_priority(item, meeting, gaps, contested, as_of):
    score, why = 0, []
    if item.get("proposal_type") in SENSITIVE_TYPES:
        score += 2; why.append(f"sensitive proposal ({item.get('proposal_type')}) +2")
    for cat in sorted(gaps):
        score += 1; why.append(f"missing {cat} +1")
    pct = abs((item.get("ownership") or {}).get("pct_outstanding") or 0)
    if pct >= 5:
        score += 2; why.append("materiality>=5% +2")
    elif pct >= 1:
        score += 1; why.append("materiality>=1% +1")
    bdays = _business_days(as_of, meeting.get("vote_deadline"))
    if bdays is not None:
        if bdays <= 3:
            score += 2; why.append("deadline<=3bd +2")
        elif bdays <= 7:
            score += 1; why.append("deadline<=7bd +1")
    band = "P1 (Elevated)" if (score >= 7 or contested) \
        else "P2 (Standard)" if score >= 3 else "P3 (Low)"
    return score, band, "; ".join(why)


def _entitlement(item, meeting, as_of=None):
    own = item.get("ownership") or {}
    m_record = str(meeting.get("record_date") or "")[:10]
    o_record = str(own.get("record_date") or "")[:10]
    se = own.get("shares_entitled")
    reasons = []
    if as_of and m_record > as_of:
        reasons.append("record date not yet reached; entitlement remains provisional")
    if not o_record:
        reasons.append("ownership.record_date missing")
    elif m_record and o_record != m_record:
        reasons.append(f"ownership.record_date {o_record} != meeting.record_date {m_record}")
    if se is None or isinstance(se, bool) or not isinstance(se, (int, float)) or se <= 0:
        reasons.append("shares_entitled missing or non-positive")
    ledger = own.get("entitlement_ledger") or {}
    if not ledger.get("source_ref") or not own.get("account_ref"):
        reasons.append("independent entitlement ledger and account identity required")
    elif ledger.get("account_ref") != own.get("account_ref") or ledger.get("record_date") != m_record or ledger.get("shares_entitled") != se:
        reasons.append("entitlement ledger/account/share/date mismatch")
    return {
        "verification_status": "supplied-ledger-comparison-not-authenticated",
        "meeting_record_date": m_record or None,
        "ownership_record_date": o_record or None,
        "shares_entitled": se,
        "pct_outstanding": own.get("pct_outstanding"),
        "custodian_ref": own.get("custodian_ref"),
        "consistent": not reasons,
        "reasons": reasons,
    }


def _chronology(tagged):
    return sorted(
        ({"as_of": t["as_of"], "source_id": t["source_id"], "source_type": t["source_type"],
          "fact_type": t["fact_type"]} for t in tagged),
        key=lambda e: str(e["as_of"]))


def _parties(tagged, item):
    parties, seen = [], set()
    for t in tagged:
        key = (_ROLE.get(t["source_type"], "other"), t["source_id"])
        if key not in seen:
            seen.add(key)
            parties.append({"role": _ROLE.get(t["source_type"], "other"), "id": t["source_id"]})
    own = item.get("ownership") or {}
    if own.get("custodian_ref"):
        parties.append({"role": "custodian", "id": own["custodian_ref"]})
    if item.get("proponent"):
        parties.append({"role": "proponent", "id": item["proponent"]})
    return parties


def _observed_facts(tagged):
    board = next((t["board_recommendation"] for t in tagged
                  if t["source_type"] == "issuer_disclosure" and t["board_recommendation"]), None)
    research = [{"provider": t["source_id"], "recommendation": t["provider_recommendation"]}
                for t in tagged if t["source_type"] == "research_provider" and t["provider_recommendation"]]
    precedent = [{"source_id": t["source_id"], "direction": t["precedent_direction"]}
                 for t in tagged if t["source_type"] == "precedent_vote" and t["precedent_direction"]]
    return {"board_recommendation": board, "research_inputs": research, "precedent": precedent}


def _hypotheses(tagged):
    return [{"source_id": t["source_id"], "source_type": t["source_type"], "note": t.get("detail")}
            for t in tagged if t["fact_type"] == "hypothesis"]


def _recommend_flag():
    return ("Entitlement or record-date data is internally inconsistent (see entitlement block). "
            "Refer to the custodian and proxy operations to reconcile the record date and share "
            "entitlement before committee review; this packet flags the discrepancy and does not "
            "alter entitlement or record-date data.")


def _recommend_assembled(contested, gaps):
    if contested:
        return ("The supplied sources disagree on this item (see observed "
                "facts). Escalate to the proxy committee and route the analyst's draft instruction "
                "to proxy-voting-reviewer policy mode (separately prepared native request) for policy and precedent alignment. Evidence "
                "only; the outcome is the committee's to determine.")
    if gaps:
        return ("Obtain the missing evidence (" + ", ".join(sorted(gaps)) + ") before committee "
                "review, then route the analyst's draft instruction to proxy-voting-reviewer policy mode (separately prepared native request) "
                "for policy and precedent alignment. Evidence only; no direction is stated here.")
    return ("Route the analyst's draft instruction to proxy-voting-reviewer policy mode (separately prepared native request) for policy "
            "and precedent alignment, then refer to the proxy committee. This packet compiles cited "
            "evidence and does not decide the outcome.")


def investigate(item, doc, meeting, as_of):
    iid = item.get("item_id")
    case_id = f"PME-{meeting.get('meeting_id', 'MTG')}-{iid}"
    policy_version = doc.get("policy_version")
    base_cites = [f"meeting:{item.get('source_ref', '?')}", f"config:{doc.get('config_version')}"]
    if policy_version:
        base_cites.append(f"policy:{policy_version}")
    rec = {"item_id": iid, "case_id": case_id, "issuer_id": meeting.get("issuer_id"),
           "meeting_id": meeting.get("meeting_id"), "proposal_type": item.get("proposal_type"),
           "citations": list(base_cites), "needs": []}

    if not item.get("proposal_type"):
        rec["disposition"] = "needs-data"
        rec["needs"].append("proposal_type (required to classify the agenda item)")
        rec["evidence"] = _tag_evidence([e for e in item.get("evidence", []) if _is_isodate(e.get("as_of")) and e["as_of"] <= as_of])
        return rec

    eligible = []
    for evidence in item.get("evidence") or []:
        if not _is_isodate(evidence.get("as_of")) or evidence["as_of"] > as_of:
            rec["needs"].append("future or invalid evidence: " + str(evidence.get("source_id")))
        elif evidence.get("source_type") == "policy_clause" and evidence.get("mandate_id") not in (None, item.get("mandate_id") or doc.get("mandate_id")):
            rec["needs"].append("policy mandate mismatch: " + str(evidence.get("source_id")))
        else:
            eligible.append(evidence)
    tagged = _tag_evidence(eligible)
    rec["evidence"] = tagged
    for t in tagged:
        rec["citations"].append(_cite_ev(t))
    present = {t["source_type"] for t in tagged}

    missing_required = sorted(REQUIRED_CATEGORIES - present)
    if item.get("ownership") is None:
        missing_required.append("ownership")
    if not policy_version:
        missing_required.append("policy_version")
    if not tagged or missing_required:
        rec["disposition"] = "needs-data"
        for cat in missing_required:
            rec["needs"].append(f"required evidence category '{cat}'")
        if not tagged:
            rec["needs"].append("evidence (no items supplied)")
        return rec

    entitlement = _entitlement(item, meeting, as_of)
    own = item.get("ownership") or {}
    if own.get("custodian_ref"):
        rec["citations"].append(f"custodian:{own['custodian_ref']};record_date={own.get('record_date')}")
    gaps = sorted(EXPECTED_CATEGORIES - present)
    contested, contest_kinds = _contested(tagged)
    chronology = _chronology(tagged)
    parties = _parties(tagged, item)
    hierarchy_ref = [st for st in HIERARCHY if st in present]

    if not entitlement["consistent"]:
        rec["disposition"] = "entitlement-discrepancy-flagged"
        rec["review_priority"] = "P1 (Elevated)"
        rec["review_priority_reason"] = "entitlement/record-date integrity gap forces P1"
        rec["contested"] = contested
        rec["adjudication"] = "human-required"
        rec["evidence_bundle"] = {
            "case_id": case_id, "item_id": iid, "issuer_id": meeting.get("issuer_id"),
            "meeting_id": meeting.get("meeting_id"), "proposal_type": item.get("proposal_type"),
            "proponent": item.get("proponent"), "chronology": chronology, "parties": parties,
            "amounts": {"shares_entitled": own.get("shares_entitled"),
                        "pct_outstanding": own.get("pct_outstanding")},
            "observed_facts": _observed_facts(tagged), "hypotheses": _hypotheses(tagged),
            "policy_reference": {"policy_version": policy_version},
            "entitlement": entitlement, "contested": contested, "contest_kinds": contest_kinds,
            "gaps": gaps, "hierarchy_reference": hierarchy_ref,
            "review_priority": "P1 (Elevated)", "recommended_next_step": _recommend_flag(),
            "adjudication": "human-required", "citations": list(rec["citations"]),
        }
        return rec

    score, band, why = _review_priority(item, meeting, set(gaps), contested, as_of)
    rec["disposition"] = "packet-assembled"
    rec["review_score"] = score
    rec["review_priority"] = band
    rec["review_priority_reason"] = why
    rec["contested"] = contested
    rec["gaps"] = gaps
    rec["adjudication"] = "human-required"
    rec["evidence_bundle"] = {
        "case_id": case_id, "item_id": iid, "issuer_id": meeting.get("issuer_id"),
        "meeting_id": meeting.get("meeting_id"), "proposal_type": item.get("proposal_type"),
        "proponent": item.get("proponent"), "chronology": chronology, "parties": parties,
        "amounts": {"shares_entitled": own.get("shares_entitled"),
                    "pct_outstanding": own.get("pct_outstanding")},
        "observed_facts": _observed_facts(tagged), "hypotheses": _hypotheses(tagged),
        "policy_reference": {"policy_version": policy_version},
        "entitlement": entitlement, "contested": contested, "contest_kinds": contest_kinds,
        "gaps": gaps, "hierarchy_reference": hierarchy_ref, "review_priority": band,
        "recommended_next_step": _recommend_assembled(contested, set(gaps)),
        "adjudication": "human-required", "citations": list(rec["citations"]),
    }
    return rec


def _native_build_packet(doc: dict) -> dict:
    meeting = doc.get("meeting") or {}
    as_of = doc.get("as_of")
    job_id = f"PME-JOB-{meeting.get('meeting_id', 'MTG')}"
    records = [investigate(it, doc, meeting, as_of) for it in doc["agenda_items"]]
    summary = {
        "total": len(records),
        "packet_assembled": sum(1 for r in records if r["disposition"] == "packet-assembled"),
        "entitlement_discrepancy_flagged": sum(
            1 for r in records if r["disposition"] == "entitlement-discrepancy-flagged"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "contested": sum(1 for r in records if r.get("contested")),
    }
    return {"packet_id": job_id, "job_id": job_id, "as_of": as_of, "meeting_id": meeting.get("meeting_id"),
            "issuer_id": meeting.get("issuer_id"), "config_version": doc.get("config_version"),
            "policy_version": doc.get("policy_version"), "agenda": records, "summary": summary,
            "standing_note": STANDING_NOTE}


def _selfcheck(packet: dict) -> list[str]:
    """Internal self-consistency check for --selftest (independent of validate_output)."""
    errs = []
    if not packet.get("job_id"):
        errs.append("packet missing job_id")
    for r in packet.get("agenda", []):
        if not r.get("case_id"):
            errs.append(f"{r.get('item_id')}: missing case_id")
        for t in r.get("evidence", []) or []:
            exp = _fact_type(t.get("source_type"))
            if t.get("fact_type") != exp:
                errs.append(f"{r.get('item_id')}: {t.get('source_id')} mis-tagged "
                            f"{t.get('fact_type')} != {exp}")
        if r.get("disposition") in ("packet-assembled", "entitlement-discrepancy-flagged"):
            b = r.get("evidence_bundle") or {}
            if not b.get("citations"):
                errs.append(f"{r.get('item_id')}: evidence bundle missing citations")
            if r.get("adjudication") != "human-required":
                errs.append(f"{r.get('item_id')}: adjudication not human-required")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "meeting_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    packet = build_packet(doc)
    print(json.dumps(packet, indent=2))
    if selftest:
        errs = _selfcheck(packet)
        for e in errs:
            print("ERROR", e)
        print(f"transform selftest: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0




def build_packet(doc: dict) -> dict:
    # Reject non-JSON and non-finite input before any calculations.
    canonical_hash(doc)
    return attach_source(_native_build_packet(doc), doc)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
