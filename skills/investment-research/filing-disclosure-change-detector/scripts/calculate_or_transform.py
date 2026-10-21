#!/usr/bin/env python3
"""Deterministic filing/disclosure change detection for filing-disclosure-change-detector.

Reads a compare file (a prior filing and a current filing conforming to the schema in
validate_input.py / references/source-map.md), normalizes section and exhibit content,
and emits cited CHANGE FINDINGS: changed language, new/removed sections, new/removed risk
factors, restatement/non-reliance wording, and exhibit additions/changes/removals. Every
finding carries a section- or exhibit-level citation to the version(s) it came from.

IMPORTANT: This produces FACTUAL, cited change findings only. It never determines
materiality, legal significance, or investment implication -- those are human
determinations. The change summary and the human review-lane routing are deterministic
functions of the detected change TYPES (documented in references/domain-rules.md); they are
a fan-out to the right human reviewers, not a ranking of importance.

Usage:
  python calculate_or_transform.py compare.json | --selftest
Prints the change-pack JSON to stdout.
"""
from __future__ import annotations
import difflib, json, re, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "risk_section_prefixes": ["1a"],
    "restatement_markers": [
        "restate", "restated", "restatement", "revised previously issued",
        "should no longer be relied upon", "non-reliance", "item 4.02", "prior period adjustment",
    ],
    "material_contract_prefixes": ["10"],
    "max_evidence_spans": 4,
    "snippet_chars": 220,
}
DISCLAIMER = ("Change detection and citations only; not a determination of materiality, legal "
             "significance, or investment implication. A qualified human makes those determinations.")

# review lanes keyed by detected change type (deterministic fan-out, NOT a ranking)
LANE_STRUCTURAL = "Covering analyst"
LANE_RISK = "Research supervisory analyst"
LANE_RESTATEMENT = "Financial-reporting / disclosure-controls reviewer"
LANE_CONTRACT = "Legal / contracts reviewer"


def _norm(text: str) -> str:
    """Whitespace-normalized, case-folded text for change comparison (originals kept for quotes)."""
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;:])\s+", str(text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def _section_cite(filing: dict, section_id: str) -> str:
    acc = filing.get("accession")
    base = f"{filing.get('form_type', '?')}:{filing.get('period', '')}:§{section_id}@{filing.get('filing_date', '?')}"
    return f"{base} (acc {acc})" if acc else base


def _exhibit_cite(filing: dict, exhibit_no: str) -> str:
    acc = filing.get("accession")
    base = f"{filing.get('form_type', '?')}:{filing.get('period', '')}:EX-{exhibit_no}@{filing.get('filing_date', '?')}"
    return f"{base} (acc {acc})" if acc else base


def _is_risk(section: dict, cfg: dict) -> bool:
    if str(section.get("kind", "")).lower() == "risk_factor":
        return True
    sid = str(section.get("section_id", "")).lower()
    return any(sid.startswith(p) for p in cfg["risk_section_prefixes"])


def _is_material_contract(exhibit_no: str, cfg: dict) -> bool:
    en = str(exhibit_no)
    return any(en.split(".")[0] == p or en.startswith(p + ".") for p in cfg["material_contract_prefixes"])


def _section_map(filing: dict) -> dict:
    return {str(s["section_id"]): s for s in filing.get("sections", [])}


def _exhibit_map(filing: dict) -> dict:
    return {str(e["exhibit_no"]): e for e in (filing.get("exhibits") or [])}


def _changed_evidence(prior: dict, current: dict, prior_f: dict, current_f: dict,
                      section_id: str, cfg: dict) -> list[dict]:
    """Sentence-level added/removed evidence with citations (bounded)."""
    p_sents, c_sents = _sentences(prior.get("text", "")), _sentences(current.get("text", ""))
    sm = difflib.SequenceMatcher(None, [s.lower() for s in p_sents], [s.lower() for s in c_sents])
    ev: list[dict] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            for s in p_sents[i1:i2]:
                ev.append({"kind": "removed_text", "quote": s, "citation": _section_cite(prior_f, section_id)})
        if tag in ("replace", "insert"):
            for s in c_sents[j1:j2]:
                ev.append({"kind": "added_text", "quote": s, "citation": _section_cite(current_f, section_id)})
    if not ev:  # fallback: quote a bounded snippet of the current text
        snip = str(current.get("text", ""))[: cfg["snippet_chars"]]
        ev.append({"kind": "changed_text", "quote": snip, "citation": _section_cite(current_f, section_id)})
    return ev[: cfg["max_evidence_spans"]]


def _restatement_markers(text: str, cfg: dict) -> list[str]:
    low = _norm(text)
    return [m for m in cfg["restatement_markers"] if m.lower() in low]


def _native_compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    prior_f, current_f = doc["prior"], doc["current"]
    p_sec, c_sec = _section_map(prior_f), _section_map(current_f)
    job_id = doc.get("job_id") or _derive_job_id(doc)

    findings: list[dict] = []
    not_evaluable: list[dict] = []
    counter = {"n": 0}
    if not prior_f.get("accession") or not current_f.get("accession"):
        not_evaluable.append({"finding":"as_filed_anchor","why":"accession missing on at least one side"})

    def add(ftype: str, locator: dict, observation: str, citation: str,
            evidence: list[dict], metrics: dict | None = None) -> None:
        counter["n"] += 1
        findings.append({
            "finding_id": f"{job_id}-{counter['n']:03d}",
            "type": ftype,
            "locator": locator,
            "observation": observation,
            "citation": citation,
            "evidence": evidence,
            "metrics": metrics or {},
        })

    # ---- sections (stable order over the union of ids) ----
    for sid in sorted(set(p_sec) | set(c_sec)):
        in_p, in_c = sid in p_sec, sid in c_sec
        cur = c_sec.get(sid, {})
        pri = p_sec.get(sid, {})
        loc_title = (cur or pri).get("title", "")
        loc = {"section_id": sid, "section_title": loc_title, "form": current_f.get("form_type")}

        if in_c and not in_p and prior_f.get("sections_complete") is False:
            not_evaluable.append({"finding": "section_added", "section_id": sid, "why": "prior section inventory incomplete"})
        elif in_p and not in_c and current_f.get("sections_complete") is False:
            not_evaluable.append({"finding": "section_removed", "section_id": sid, "why": "current section inventory incomplete"})
        elif in_c and not in_p:
            if _is_risk(cur, cfg):
                add("new_risk_factor", loc,
                    "Risk-factor section present in the current filing but not in the prior filing.",
                    _section_cite(current_f, sid),
                    [{"kind": "section_text", "quote": str(cur.get("text", ""))[: cfg["snippet_chars"]],
                      "citation": _section_cite(current_f, sid)}])
            else:
                add("section_added", loc,
                    "Section present in the current filing but not in the prior filing.",
                    _section_cite(current_f, sid),
                    [{"kind": "section_text", "quote": str(cur.get("text", ""))[: cfg["snippet_chars"]],
                      "citation": _section_cite(current_f, sid)}])
        elif in_p and not in_c:
            ftype = "removed_risk_factor" if _is_risk(pri, cfg) else "section_removed"
            add(ftype, loc,
                "Section present in the prior filing but not in the current filing.",
                _section_cite(prior_f, sid),
                [{"kind": "section_text", "quote": str(pri.get("text", ""))[: cfg["snippet_chars"]],
                  "citation": _section_cite(prior_f, sid)}])
        else:
            if not pri.get("text") or not cur.get("text"):
                not_evaluable.append({"finding": "changed_language", "section_id": sid, "why": "section text missing/empty on at least one side"})
            elif _norm(pri.get("text", "")) != _norm(cur.get("text", "")):
                ratio = round(difflib.SequenceMatcher(None, _norm(pri.get("text", "")),
                                                      _norm(cur.get("text", ""))).ratio(), 3)
                p_words = len(_norm(pri.get("text", "")).split())
                c_words = len(_norm(cur.get("text", "")).split())
                add("changed_language", loc,
                    "Section text changed between the prior and current filing.",
                    _section_cite(current_f, sid),
                    _changed_evidence(pri, cur, prior_f, current_f, sid, cfg),
                    {"similarity_ratio": ratio, "prior_words": p_words, "current_words": c_words})

        # restatement / non-reliance wording in any section present in the CURRENT filing
        if in_c:
            markers = _restatement_markers(cur.get("text", ""), cfg)
            previous_markers = _restatement_markers(pri.get("text", ""), cfg) if in_p else []
            new_markers=[m for m in markers if m not in previous_markers]
            if new_markers:
                raw_text = str(cur.get("text", ""))
                marker_at = min(raw_text.lower().find(m.lower()) for m in new_markers)
                marker_quote = raw_text[max(0, marker_at - 40): marker_at + max(cfg["snippet_chars"], len(new_markers[0]))]
                add("restatement_language", loc,
                    "Restatement / non-reliance wording appears in the current section text "
                    "(verbatim excerpt attached; factual detection, not a reliance or materiality determination).",
                    _section_cite(current_f, sid),
                    [{"kind": "marker", "quote": marker_quote,
                      "citation": _section_cite(current_f, sid)}],
                    {"markers_detected": new_markers})

    # ---- exhibits ----
    p_ex, c_ex = _exhibit_map(prior_f), _exhibit_map(current_f)
    if "exhibits" not in prior_f or "exhibits" not in current_f:
        not_evaluable.append({"finding": "exhibit_*", "why": "exhibit inventory omitted on at least one side"})
    else:
        for en in sorted(set(p_ex) | set(c_ex)):
            in_p, in_c = en in p_ex, en in c_ex
            mc = _is_material_contract(en, cfg)
            item = "601(b)(10) material contract" if mc else "other exhibit"
            loc = {"exhibit_no": en, "exhibit_item": item, "form": current_f.get("form_type")}
            if in_c and not in_p:
                add("exhibit_added", loc,
                    "Exhibit present in the current filing but not in the prior filing.",
                    _exhibit_cite(current_f, en),
                    [{"kind": "exhibit", "quote": c_ex[en].get("description", ""),
                      "citation": _exhibit_cite(current_f, en)}], {"material_contract": mc})
            elif in_p and not in_c:
                add("exhibit_removed", loc,
                    "Exhibit present in the prior filing but not in the current filing.",
                    _exhibit_cite(prior_f, en),
                    [{"kind": "exhibit", "quote": p_ex[en].get("description", ""),
                      "citation": _exhibit_cite(prior_f, en)}], {"material_contract": mc})
            else:
                if not p_ex[en].get("hash") or not c_ex[en].get("hash"):
                    not_evaluable.append({"finding":"exhibit_content","exhibit_no":en,"why":"content hash missing; metadata comparison only"})
                same = (p_ex[en].get("hash"), p_ex[en].get("description")) == \
                       (c_ex[en].get("hash"), c_ex[en].get("description"))
                if not same:
                    add("exhibit_changed", loc,
                        "Exhibit content differs from the prior filing (content hash or description changed).",
                        _exhibit_cite(current_f, en),
                        [{"kind": "exhibit", "quote": c_ex[en].get("description", ""),
                          "citation": _exhibit_cite(current_f, en)},
                         {"kind": "exhibit_prior", "quote": p_ex[en].get("description", ""),
                          "citation": _exhibit_cite(prior_f, en)}], {"material_contract": mc})

    return _assemble(doc, job_id, findings, not_evaluable, cfg)


def _derive_job_id(doc: dict) -> str:
    p, c = doc.get("prior", {}), doc.get("current", {})
    slug = re.sub(r"[^a-z0-9]+", "-", str(doc.get("issuer", "issuer")).lower()).strip("-")[:24]
    return f"fdcd-{slug}-{c.get('form_type', 'form')}-{c.get('filing_date', 'cur')}-vs-{p.get('filing_date', 'pri')}"


def _routing(types: set) -> list[str]:
    lanes = set()
    if types & {"changed_language", "section_added", "section_removed"}:
        lanes.add(LANE_STRUCTURAL)
    if types & {"new_risk_factor", "removed_risk_factor"}:
        lanes.add(LANE_RISK)
    if "restatement_language" in types:
        lanes.add(LANE_RESTATEMENT)
    return sorted(lanes)


def _assemble(doc: dict, job_id: str, findings: list[dict], not_evaluable: list[dict], cfg: dict) -> dict:
    by_type: dict[str, int] = {}
    for f in findings:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1
    types = set(by_type)
    # material-contract exhibit change adds the legal/contracts lane
    if any(f["type"].startswith("exhibit_") and f.get("metrics", {}).get("material_contract") for f in findings):
        contract_lane = [LANE_CONTRACT]
    else:
        contract_lane = []
    routing = sorted(set(_routing(types)) | set(contract_lane))

    change_summary = {
        "total_findings": len(findings),
        "by_type": dict(sorted(by_type.items())),
        "sections_changed": sorted({f["locator"].get("section_id") for f in findings
                                    if f["locator"].get("section_id")}),
        "exhibits_changed": sorted({f["locator"].get("exhibit_no") for f in findings
                                    if f["locator"].get("exhibit_no")}),
    }
    return {
        "job_id": job_id,
        "issuer": doc.get("issuer"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "comparison": {
            "prior": {k: doc["prior"].get(k) for k in ("form_type", "period", "filing_date", "accession")},
            "current": {k: doc["current"].get(k) for k in ("form_type", "period", "filing_date", "accession")},
        },
        "findings": findings,
        "change_summary": change_summary,
        "review_routing": routing,
        "not_evaluable": not_evaluable,
        "coverage_status": "partial" if not_evaluable else "complete-for-supplied-aligned-inventories",
        "comparison_scope": "Supplied structured sections/exhibits only; extraction completeness and investment materiality are not established",
        "disclaimer": DISCLAIMER,
    }


def compute(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        from phase2_domain import compute as phase2_compute
        return phase2_compute(doc)
    import importlib.util
    from native_integrity import attach_source
    source=Path(__file__).with_name("validate_input.py")
    spec=importlib.util.spec_from_file_location("_native_input_"+Path(__file__).parents[1].name.replace("-","_"),source)
    validator=importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    errors,_=validator.validate(doc)
    if errors: raise ValueError("; ".join(errors))
    return attach_source(_native_compute(doc),doc)

def main(argv):
    try:
        path=Path(__file__).resolve().parents[1]/"evals/files/compare_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        doc=_read_json(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False))
        if "--selftest" in argv and "filing-disclosure-change-detector"=="market-landscape-researcher": print("calculate self-check: 0 error(s)")
        return 0
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print("ERROR invalid input: "+str(exc)); return 1
def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
