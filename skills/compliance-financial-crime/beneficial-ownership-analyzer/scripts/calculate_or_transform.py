#!/usr/bin/env python3
"""Analyze supplied proportional-equity graphs and direct root control candidates.

No independent verification or legal beneficial-ownership determination is implemented.
Policy, structure type, source references and test applicability must be explicit.
"""
from __future__ import annotations
import json, sys
from policy_contract import require_valid, limitations
from validate_input import validate
from native_integrity import attach_source
from datetime import datetime
from decimal import Decimal
from pathlib import Path

DISCLAIMER = ("Supplied ownership-analysis evidence and recommendations only; not a beneficial-ownership "
              "determination or KYC/onboarding approval. No case has been approved, closed, "
              "or filed, and no system of record has been updated. Human adjudication is required.")

# Gap severity classes drive the deterministic readiness mapping (references/domain-rules.md).
BLOCKING = {"undeclared_owner", "undeclared_control", "control_prong_unsatisfied",
            "declared_not_supported", "circular_ownership"}
REMEDIABLE = {"missing_document", "expired_document", "pct_mismatch", "ownership_over_100", "incomplete_ownership"}


def readiness_from_gaps(gaps: list[dict]) -> str:
    types = {g["type"] for g in gaps}
    if types & BLOCKING:
        return "Escalate"
    if types & REMEDIABLE:
        return "Remediation-needed"
    return "Complete-for-review"


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    require_valid(doc, validate)
    cfg = doc["config"]
    threshold = float(cfg["ownership_threshold_pct"])
    tol = float(cfg["pct_tolerance"])
    as_of = _parse_date(doc["as_of"])

    kind = {n["node_id"]: n.get("kind") for n in doc["nodes"]}
    name = {n["node_id"]: n.get("name", n["node_id"]) for n in doc["nodes"]}
    persons = [nid for nid, k in kind.items() if k == "person"]
    root = doc["legal_entity"]["entity_id"]
    edges = doc.get("ownership_edges") or []

    # incoming ownership edges per owned entity
    incoming: dict[str, list[dict]] = {}
    for e in edges:
        incoming.setdefault(e["owned"], []).append(e)

    data_quality: list[dict] = []
    cycle_nodes: set[str] = set()

    # reachability to root (does an entity's ownership flow up into the root?)
    reach_memo: dict[str, bool] = {}

    def reaches_root(node: str, stack: frozenset = frozenset()) -> bool:
        if node == root:
            return True
        if node in reach_memo:
            return reach_memo[node]
        if node in stack:
            return False
        out = [e for e in edges if e["owner"] == node]
        res = any(reaches_root(e["owned"], stack | {node}) for e in out)
        reach_memo[node] = res
        return res

    # g(P, node) = fraction of `node` ultimately owned by person P
    def g(person: str, node: str, stack: frozenset) -> float:
        if node == person:
            return Decimal(1)
        if kind.get(node) == "person":
            return Decimal(0)
        if node in stack:
            cycle_nodes.add(node)
            return Decimal(0)
        total = Decimal(0)
        for e in incoming.get(node, []):
            p = Decimal(str(e["pct"])) / Decimal(100)
            total += p * g(person, e["owner"], stack | {node})
        return total

    computed_owners = []
    for pid in persons:
        frac = g(pid, root, frozenset())
        raw_pct = frac * Decimal(100)
        pct = round(float(raw_pct), 8)
        if pct <= 0:
            continue
        # contributing evidence: ownership edges whose owner is (transitively) owned by P
        # and whose owned side flows up to root.
        evidence = []
        for e in edges:
            if not reaches_root(e["owned"]):
                continue
            if e["owner"] == pid or (kind.get(e["owner"]) == "entity" and g(pid, e["owner"], frozenset()) > 0):
                cite = e.get("source_ref") or f"edge:{e['owner']}->{e['owned']}"
                evidence.append({"edge": f"{e['owner']}->{e['owned']}", "pct": e["pct"], "citation": cite})
        computed_owners.append({
            "person_id": pid, "name": name.get(pid, pid),
            "effective_pct": pct, "is_ubo": raw_pct >= Decimal(str(threshold)),
            "evidence": evidence,
        })
    computed_owners.sort(key=lambda o: (-o["effective_pct"], o["person_id"]))

    if cycle_nodes:
        for c in sorted(cycle_nodes):
            data_quality.append({"type": "circular_ownership", "subject": c,
                                 "detail": f"circular ownership detected at {name.get(c, c)}; affected chains were skipped"})

    # control prong
    control_edges = doc.get("control_edges") or []
    control_persons = []
    excluded_control_edges = []
    for c in control_edges:
        if c.get("entity") != root or c.get("type") not in cfg["qualifying_control_types"]:
            excluded_control_edges.append({"edge": c, "reason": "Not a qualifying direct root-entity control edge under the supplied policy; indirect/control-by-other-means analysis is unsupported."})
            continue
        cp = c.get("controller")
        if kind.get(cp) == "person" and cp not in [x["person_id"] for x in control_persons]:
            control_persons.append({
                "person_id": cp, "name": name.get(cp, cp),
                "role": c.get("role"), "type": c.get("type"),
                "evidence": [{"citation": c.get("source_ref") or f"control:{cp}->{c.get('entity')}"}],
            })

    # documents by subject
    docs = doc.get("documents") or []
    doc_by_id = {d.get("doc_id"): d for d in docs}
    docs_by_subject: dict[str, list[dict]] = {}
    for d in docs:
        docs_by_subject.setdefault(d.get("subject"), []).append(d)

    declared = {d["person_id"]: d for d in doc["declared_ubos"]}
    declared_bases = {(d["person_id"], d["basis"]) for d in doc["declared_ubos"]}
    ubo_owners = [o for o in computed_owners if o["is_ubo"]]

    # ----- assemble identified UBO list (ownership + control) -----
    ubos = []
    for o in ubo_owners:
        ubos.append({
            "person_id": o["person_id"], "name": o["name"], "basis": "ownership",
            "effective_pct": o["effective_pct"],
            "declared": (o["person_id"], "ownership") in declared_bases,
            "reason": f"effective ownership {o['effective_pct']:.2f}% at or above the {threshold:.0f}% ownership prong",
            "evidence": o["evidence"],
        })
    for cp in control_persons:
        ubos.append({
            "person_id": cp["person_id"], "name": cp["name"], "basis": "control",
            "role": cp["role"],
            "declared": (cp["person_id"], "control") in declared_bases,
            "reason": f"identified under the control prong ({cp.get('type') or 'control'})",
            "evidence": cp["evidence"],
        })

    # ----- gaps (each carries a subject reference and, where possible, evidence) -----
    gaps: list[dict] = []

    def _person_docs_fresh(pid: str, declared_doc_id):
        candidate_ids = []
        if declared_doc_id:
            candidate_ids.append(declared_doc_id)
        candidate_ids += [d.get("doc_id") for d in docs_by_subject.get(pid, [])]
        found_fresh = None
        found_any = False
        for did in candidate_ids:
            d = doc_by_id.get(did)
            if not d or d.get("subject") != pid or d.get("type") not in cfg["document_types"]:
                continue
            found_any = True
            exp = _parse_date(d.get("expires"))
            iss = _parse_date(d.get("issued"))
            expired = (exp is not None and as_of is not None and exp < as_of)
            too_old = (iss is not None and as_of is not None and (as_of - iss).days > int(cfg["doc_max_age_days"]))
            if iss is not None and iss <= as_of and exp is not None and exp >= iss and not expired and not too_old:
                found_fresh = did
                break
        return found_any, found_fresh

    # undeclared ownership UBOs (blocking)
    for o in ubo_owners:
        if (o["person_id"], "ownership") not in declared_bases:
            gaps.append({
                "type": "undeclared_owner", "subject": o["person_id"], "severity": "blocking",
                "detail": (f"computed beneficial owner {o['name']} ({o['effective_pct']:.2f}%) is not on the "
                           f"declared UBO list; declaration appears incomplete"),
                "evidence": o["evidence"],
            })

    # control prong
    if cfg.get("require_control_prong", True) and len(control_persons) < int(cfg.get("min_control_persons", 1)):
        gaps.append({
            "type": "control_prong_unsatisfied", "subject": root, "severity": "blocking",
            "detail": (f"supplied policy requires at least {cfg.get('min_control_persons', 1)} control-prong person "
                       f"(senior managing official); {len(control_persons)} identified"),
            "evidence": [],
        })
    for cp in control_persons:
        if (cp["person_id"], "control") not in declared_bases:
            gaps.append({
                "type": "undeclared_control", "subject": cp["person_id"], "severity": "blocking",
                "detail": f"control-prong person {cp['name']} identified from records but not on the declared UBO list",
                "evidence": cp["evidence"],
            })

    # declared parties not supported by the computed ownership / control evidence
    control_ids = {cp["person_id"] for cp in control_persons}
    owner_pct = {o["person_id"]: o["effective_pct"] for o in computed_owners}
    for d in doc["declared_ubos"]:
        pid = d["person_id"]
        basis = d.get("basis")
        if basis == "ownership":
            comp = owner_pct.get(pid, 0.0)
            if not any(o["person_id"] == pid and o["is_ubo"] for o in computed_owners):
                gaps.append({
                    "type": "declared_not_supported", "subject": pid, "severity": "blocking",
                    "detail": (f"declared owner {d.get('name', pid)} computes to {comp:.2f}% effective ownership, "
                               f"below the {threshold:.0f}% prong, and has no control basis on record"),
                    "evidence": [],
                })
            elif d.get("declared_pct") is not None and abs(float(d["declared_pct"]) - comp) > tol:
                gaps.append({
                    "type": "pct_mismatch", "subject": pid, "severity": "remediable",
                    "detail": (f"declared {float(d['declared_pct']):.2f}% vs computed {comp:.2f}% for "
                               f"{d.get('name', pid)} exceeds tolerance {tol:.2f} pp"),
                    "evidence": [],
                })
        elif basis == "control" and pid not in control_ids:
            gaps.append({
                "type": "declared_not_supported", "subject": pid, "severity": "blocking",
                "detail": f"declared control person {d.get('name', pid)} has no control edge on record",
                "evidence": [],
            })

    # document freshness for identified & declared UBOs
    if cfg.get("document_required_for_ubo", True):
        for u in ubos:
            pid = u["person_id"]
            found_any, fresh = _person_docs_fresh(pid, declared.get(pid, {}).get("doc_id"))
            if not found_any:
                gaps.append({"type": "missing_document", "subject": pid, "severity": "remediable",
                             "detail": f"no supporting document on record for {u['name']}", "evidence": []})
            elif not fresh:
                gaps.append({"type": "expired_document", "subject": pid, "severity": "remediable",
                             "detail": f"supporting document(s) for {u['name']} have absent/invalid dates, are expired, or are older than {cfg['doc_max_age_days']} days",
                             "evidence": []})

    # ownership-over-100 data quality (remediable)
    owned_sums: dict[str, float] = {}
    for e in edges:
        owned_sums[e["owned"]] = owned_sums.get(e["owned"], 0.0) + float(e["pct"])
    for w, s in owned_sums.items():
        if s > 100.0 + 1e-6:
            gaps.append({"type": "ownership_over_100", "subject": w, "severity": "remediable",
                         "detail": f"ownership of {name.get(w, w)} sums to {s:.2f}% (> 100%)", "evidence": []})

    # Complete arithmetic needs complete incoming equity for every root-relevant entity.
    for nid, node_kind in kind.items():
        if node_kind == "entity" and reaches_root(nid) and owned_sums.get(nid, 0) < 100.0 - 1e-8:
            gaps.append({"type": "incomplete_ownership", "subject": nid, "severity": "remediable",
                         "detail": "Supplied equity records do not account for 100% of this root-relevant entity; candidate ownership may be incomplete.",
                         "evidence": [{"citation": "input:ownership_edges", "status": "input-field-observation"}]})

    # circular ownership is a blocking data-quality gap
    for dq in data_quality:
        if dq["type"] == "circular_ownership":
            gaps.append({"type": "circular_ownership", "subject": dq["subject"], "severity": "blocking",
                         "detail": dq["detail"], "evidence": []})

    readiness = readiness_from_gaps(gaps)

    result = {
        "verification_id": f"bov-{doc['case_id']}-{doc['as_of']}-0001",
        "case_id": doc["case_id"],
        "as_of": doc["as_of"],
        "jurisdiction": doc["jurisdiction"],
        "config_version": doc.get("config_version"),
        "legal_entity": doc["legal_entity"],
        "threshold_pct": threshold,
        "jurisdiction_requirements": {
            "ownership_threshold_pct": threshold,
            "require_control_prong": bool(cfg.get("require_control_prong", True)),
            "doc_max_age_days": int(cfg["doc_max_age_days"]),
            "requirements_effective_date": doc["policy_profile"]["effective_date"],
            "authority": doc["policy_profile"]["authority"],
        },
        "computed_owners": computed_owners,
        "control_persons": control_persons,
        "excluded_control_edges": excluded_control_edges,
        "ubos": ubos,
        "declared_ubos": doc["declared_ubos"],
        "gaps": gaps,
        "data_quality": data_quality,
        "readiness": readiness,
        "disclaimer": DISCLAIMER,
        "adjudication_required": True,
        "limitations": limitations() + ["Scalar proportional-equity candidate analysis and direct root control only. Trusts, voting tests, indirect control, exemptions and legal beneficial-ownership/CTA reporting determinations are unsupported. Document support is not identity verification."],
    }
    return attach_source(result, doc)


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ownership_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
