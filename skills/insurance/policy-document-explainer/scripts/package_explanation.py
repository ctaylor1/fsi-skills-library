#!/usr/bin/env python3
"""Bind a drafted explanation to source sections; does not generate/approve narrative."""
import copy, json, sys
from pathlib import Path
from insurance_contract import build_artifact, stable_hash

def package(source, draft):
    from validate_input import validate
    errors, _ = validate(source)
    if errors:
        raise ValueError("; ".join(errors))
    output = copy.deepcopy(draft)
    output["source_document"] = copy.deepcopy(source)
    sections = {s["section_id"]: s for s in source["sections"]}
    for element in output.get("elements", []):
        section = sections.get(element.get("section_id"))
        if section is None:
            raise ValueError("explanation references unknown source section")
        element["source_text"] = section["text"]
        element["source"] = copy.deepcopy(section["source"])
    output["explanation_id"] = "policy-explanation-" + stable_hash(source)[:24]
    issues = [str(g) for g in output.get("data_gaps", [])]
    output["artifact"] = build_artifact(source, output, producer="policy-document-explainer", artifact_type="policy_explanation", completeness="partial" if issues else "complete", evaluability="partial" if issues else "evaluable", issues=issues)
    return output

if __name__ == "__main__":
    source, draft = [json.loads(Path(p).read_text()) for p in sys.argv[1:]]
    print(json.dumps(package(source,draft),indent=2))
