#!/usr/bin/env python3
"""Deterministic clause-level comparison for policy-wording-comparator.

Reads a comparison request (see validate_input.py), aligns the subject and baseline forms by
clause_id, classifies each change (added / removed / modified) plus conflicts (dangling
references) and gaps (missing required clause types), flags materiality and escalation from the
versioned config, attaches both-side citations, generates a neutral reviewer question per
material finding, and maps the finding set to a suggested review track.

IMPORTANT: This produces cited *findings, questions, and a triage suggestion* only. It never
decides coverage or compliance, approves/files/binds a form, or closes the review. The track
mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py request.json | --selftest
Prints the comparison JSON to stdout.
"""
from __future__ import annotations
import difflib, json, sys
from pathlib import Path

MATERIAL_TYPES = {
    "insuring_agreement", "exclusion", "condition", "condition_precedent", "definition",
    "limit", "sublimit", "deductible", "coverage_trigger", "cancellation", "subrogation",
    "other_insurance",
}
ESCALATION_TYPES = {
    "insuring_agreement", "exclusion", "limit", "sublimit", "deductible", "coverage_trigger",
    "condition_precedent",
}
DEFAULT_CONFIG = {"material_text_change": 0.15}
OF_RECORD = {"filed", "approved"}
DISCLAIMER = ("Comparison evidence only; not a coverage, compliance, or filing determination. "
              "A licensed professional must adjudicate; no form has been filed, approved, or bound.")


def _cite(side: str, c: dict) -> str:
    return f"{side}:{c.get('clause_id','?')}@{c.get('source_ref','?')}"


def _by_id(form: dict) -> dict:
    return {c["clause_id"]: c for c in form.get("clauses", [])}


def _text_change_ratio(a: str, b: str) -> float:
    # 0.0 = identical, 1.0 = completely different (1 - difflib similarity ratio)
    return round(1.0 - difflib.SequenceMatcher(None, str(a), str(b)).ratio(), 4)


def _question(finding_type: str, clause_type: str, clause_id: str, extra: str = "") -> str:
    ct = clause_type.replace("_", " ")
    if finding_type == "added":
        base = f"Clause {clause_id} ({ct}) was added in the subject form"
        if clause_type == "exclusion":
            base += " — confirm the intended narrowing of coverage and the filing implications."
        else:
            base += " — confirm the intended effect and the filing implications."
    elif finding_type == "removed":
        base = f"Clause {clause_id} ({ct}) present in the baseline was removed from the subject form"
        if clause_type == "exclusion":
            base += " — confirm the intended broadening of coverage and the filing implications."
        else:
            base += " — confirm the intended effect and the filing implications."
    elif finding_type == "modified":
        base = (f"Clause {clause_id} ({ct}) wording changed ({extra}) — confirm the intended "
                "effect on coverage and the filing implications.")
    elif finding_type == "dangling_reference":
        base = (f"Clause {clause_id} references {extra}, which is not defined or present in the "
                "subject form — confirm this conflict and how it should read.")
    elif finding_type == "missing_required_clause":
        base = (f"The subject form has no clause of required type '{clause_type}' — confirm whether "
                "this gap is intended.")
    else:
        base = f"Review clause {clause_id} ({ct})."
    return base


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    material_types = set(doc.get("config", {}).get("material_types", MATERIAL_TYPES))
    escalation_types = set(doc.get("config", {}).get("escalation_types", ESCALATION_TYPES))
    thr = float(cfg.get("material_text_change", 0.15))

    subject = doc["subject_form"]
    baseline = doc["baseline_form"]
    base_of_record = baseline.get("filing_status") in OF_RECORD

    subj_by = _by_id(subject)
    base_by = _by_id(baseline)
    findings, not_evaluable = [], []
    seq = 0

    def new_id() -> str:
        nonlocal seq
        seq += 1
        return f"F-{seq:03d}"

    def add(finding_type, clause_type, clause_id, heading, material, escalate,
            filed_deviation, evidence, question, extra=None):
        findings.append({
            "finding_id": new_id(), "finding_type": finding_type, "clause_id": clause_id,
            "clause_type": clause_type, "heading": heading, "material": bool(material),
            "escalate": bool(escalate), "filed_deviation": bool(filed_deviation),
            "detail": extra, "evidence": evidence, "review_question": question,
        })

    # added: in subject, not in baseline
    for cid in sorted(set(subj_by) - set(base_by)):
        c = subj_by[cid]
        ct = c.get("clause_type", "")
        material = ct in material_types
        filed_dev = material and base_of_record
        escalate = material and (ct in escalation_types or filed_dev)
        add("added", ct, cid, c.get("heading"), material, escalate, filed_dev,
            [{"side": "subject", "source_ref": c.get("source_ref"), "citation": _cite("subject", c)}],
            _question("added", ct, cid))

    # removed: in baseline, not in subject
    for cid in sorted(set(base_by) - set(subj_by)):
        c = base_by[cid]
        ct = c.get("clause_type", "")
        material = ct in material_types
        filed_dev = material and base_of_record
        escalate = material and (ct in escalation_types or filed_dev)
        add("removed", ct, cid, c.get("heading"), material, escalate, filed_dev,
            [{"side": "baseline", "source_ref": c.get("source_ref"), "citation": _cite("baseline", c)}],
            _question("removed", ct, cid))

    # modified: same id, text differs
    for cid in sorted(set(subj_by) & set(base_by)):
        sc, bc = subj_by[cid], base_by[cid]
        if str(sc.get("text", "")) == str(bc.get("text", "")):
            continue
        ct = sc.get("clause_type", bc.get("clause_type", ""))
        ratio = _text_change_ratio(bc.get("text", ""), sc.get("text", ""))
        material = ct in material_types or ratio >= thr
        filed_dev = material and base_of_record
        escalate = material and (ct in escalation_types or filed_dev)
        add("modified", ct, cid, sc.get("heading"), material, escalate, filed_dev,
            [{"side": "baseline", "source_ref": bc.get("source_ref"), "citation": _cite("baseline", bc)},
             {"side": "subject", "source_ref": sc.get("source_ref"), "citation": _cite("subject", sc)}],
            _question("modified", ct, cid, f"{int(round(ratio*100))}% of wording changed"),
            extra={"text_change_ratio": ratio})

    # dangling_reference (conflict): a subject clause references a term/clause not defined/present
    subj_has_ref_meta = any(("references" in c or "defines" in c) for c in subject.get("clauses", []))
    if subj_has_ref_meta:
        defined = set(subj_by)
        for c in subject.get("clauses", []):
            for term in c.get("defines", []) or []:
                defined.add(str(term))
        for c in subject.get("clauses", []):
            for ref in c.get("references", []) or []:
                if str(ref) not in defined:
                    cid = c["clause_id"]
                    add("dangling_reference", c.get("clause_type", ""), cid, c.get("heading"),
                        True, True, False,
                        [{"side": "subject", "source_ref": c.get("source_ref"), "citation": _cite("subject", c)}],
                        _question("dangling_reference", c.get("clause_type", ""), cid, f"'{ref}'"),
                        extra={"missing_reference": str(ref)})
    else:
        not_evaluable.append({"check": "dangling_reference", "why": "no clause carries references/defines metadata"})

    # missing_required_clause (gap): required type absent from the subject form
    required = doc.get("required_clause_types") or []
    if required:
        present = {c.get("clause_type") for c in subject.get("clauses", [])}
        for rt in required:
            if rt not in present:
                add("missing_required_clause", rt, None, None, True, True, False,
                    [{"side": "requirement", "source_ref": f"required_clause_types:{rt}",
                      "citation": f"config:required_clause_types@{doc.get('config_version')}"}],
                    _question("missing_required_clause", rt, None))
    else:
        not_evaluable.append({"check": "missing_required_clause", "why": "no required_clause_types supplied"})

    material_findings = [f for f in findings if f["material"]]
    escalated = [f for f in findings if f["escalate"]]
    if escalated:
        track = "Legal/compliance review required"
    elif material_findings:
        track = "Standard review"
    else:
        track = "No material changes"

    legal_handoff = ""
    if track == "Legal/compliance review required":
        legal_handoff = ("Route to product counsel / compliance for adjudication of the escalated "
                         "findings before any coverage, compliance, or filing decision. This skill "
                         "does not approve, file, or bind the form.")

    review_questions = [f["review_question"] for f in material_findings]

    sid = str(subject.get("form_id", "subj")).replace("*", "")
    bid = str(baseline.get("form_id", "base")).replace("*", "")
    return {
        "comparison_id": f"pwc-{sid}-vs-{bid}-{doc['as_of']}-0001",
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "subject_form": {"form_id": subject.get("form_id"), "form_name": subject.get("form_name"),
                         "filing_status": subject.get("filing_status"), "edition_date": subject.get("edition_date")},
        "baseline_form": {"form_id": baseline.get("form_id"), "form_name": baseline.get("form_name"),
                          "filing_status": baseline.get("filing_status"), "edition_date": baseline.get("edition_date"),
                          "of_record": base_of_record},
        "findings": findings,
        "counts": {"total": len(findings), "material": len(material_findings), "escalated": len(escalated)},
        "suggested_review_track": track,
        "review_questions": review_questions,
        "legal_review_handoff": legal_handoff,
        "not_evaluable": not_evaluable,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "comparison_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
