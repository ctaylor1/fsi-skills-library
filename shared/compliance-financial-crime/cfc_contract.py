"""Compliance adapter over workflow-evidence/1.0; offline review only (MIT).

Native inputs remain detached. Hashes, mappings and supplied reviewer identities
establish reproducibility, not source truth, professional approval or access rights.
"""
from __future__ import annotations

import copy
import importlib.util
import re
from datetime import date
from pathlib import Path

from native_integrity import canonical_hash
from workflow_contract import build_artifact, validate_artifact
_foundation_spec = importlib.util.spec_from_file_location(
    'compliance_foundation_contract', Path(__file__).with_name('foundation_contract.py'))
_foundation_module = importlib.util.module_from_spec(_foundation_spec)
_foundation_spec.loader.exec_module(_foundation_module)
validate_common = _foundation_module.validate_common
claim_value = _foundation_module.claim_value

VERSION = "compliance-evidence/1.0"
ROLES = {"control_operator", "oversight", "decision_support", "operational_qa",
         "independent_testing", "regulatory_affairs", "privacy_review"}
CLASSIFICATIONS = {"compliance_confidential", "customer_pii", "mnpi", "sar_restricted",
                   "legal_restricted"}
# A package with no unambiguous native subject/time mapping remains native-only.
ADAPTERS = {
    "customer-due-diligence-reviewer": ("/customer/customer_id", "/as_of", "customer"),
    "beneficial-ownership-analyzer": ("/legal_entity/entity_id", "/as_of", "legal_entity"),
    "customer-risk-rating-reviewer": ("/customer_id", "/as_of", "customer"),
    "enhanced-due-diligence-assessor": ("/customer/customer_id", "/as_of", "customer"),
    "adverse-media-investigator": ("/case_batch_id", "/as_of_date", "case_batch"),
    "transaction-monitoring-scenario-evaluator": ("/run_id", "/as_of", "monitoring_run"),
    "employee-trading-preclearance-reviewer": ("/request_id", "/request_date", "trade_request"),
    "conflicts-of-interest-reviewer": ("/matter_id", "/as_of", "conduct_matter"),
    "regulatory-change-impact-analyzer": ("/change_id", "/as_of", "regulatory_change"),
    "suspicious-activity-report-drafter": ("/case_id", "/as_of", "reporting_case"),
    "privacy-impact-assessment-assistant": ("/processing/processing_id", "/as_of", "processing"),
}
# Foundation adapters bind the actual domain object, not a router subject label.
FOUNDATION_ADAPTERS = {
    'compliance-program-designer': {'compliance_program'},
    'regulatory-applicability-reviewer': {'regulatory_perimeter'},
    'regulatory-source-monitor': {'regulatory_source_docket'},
    'regulatory-obligation-control-mapper': {'regulatory_obligation_inventory'},
    'compliance-financial-crime-risk-assessor': {'institution_compliance_risk'},
    'compliance-business-change-reviewer': {'business_change'},
    'compliance-program-effectiveness-reviewer': {'compliance_program_review'},
    'sanctions-exposure-reviewer': {'sanctions_exposure'},
    'financial-crime-case-investigator': {'financial_crime_case'},
    'financial-crime-information-sharing-reviewer': {'information_sharing_review'},
    'financial-crime-reporting-reviewer': {'financial_crime_reporting'},
    'compliance-regulatory-notification-reviewer': {'regulatory_notification'},
    'information-barrier-reviewer': {'information_barrier_review'},
    'anti-bribery-corruption-reviewer': {'abc_engagement_review'},
    'misconduct-investigation-assistant': {'misconduct_investigation'},
    'financial-promotion-reviewer': {'financial_promotion'},
    'customer-conduct-outcomes-reviewer': {'customer_conduct_review'},
    'compliance-control-testing-assistant': {'compliance_control_test'},
    'compliance-remediation-evidence-reviewer': {'compliance_remediation_review'},
    'sanctions-screening-control-evaluator': {'sanctions_screening_control_review'},
    'transaction-monitoring-scenario-designer': {'transaction_monitoring_scenario_design'},
    'transaction-monitoring-effectiveness-reviewer': {'transaction_monitoring_effectiveness_review'},
    'financial-crime-case-quality-reviewer': {'financial_crime_case_quality_review'},
}
EXPANDED_ADAPTERS = {
    'customer-due-diligence-reviewer': 'lifecycle',
    'enhanced-due-diligence-assessor': 'substantive',
}
NATIVE_ONLY = {
    "aml-alert-triager": "Alert batch has no authoritative single batch identity adapter.",
    "sanctions-match-investigator": "Mixed case batch has no authoritative single subject/as-of adapter.",
    "policy-procedure-gap-analyzer": "Framework label is not an institution or control-population identity.",
    "regulatory-exam-response-packager": "No common adapter is registered for the exam request population and response assessment.",
}


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value.lower() not in {"unknown", "n/a"}


def pointer(doc, path):
    if path == "":
        return doc
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("mapping requires an explicit JSON pointer")
    result = doc
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(result, list):
            result = result[int(part)]
        elif isinstance(result, dict):
            result = result[part]
        else:
            raise ValueError("pointer does not resolve")
    return result


def _native_issues(output):
    """Retain locations of native limitations without duplicating sensitive content."""
    found = []
    issue_fields = {'gaps', 'open_gaps', 'not_evaluable', 'unresolved_issues',
                    'evidence_gaps', 'limitations', 'warnings', 'missing_evidence',
                    'data_quality_issues'}
    def visit(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                child = path + '/' + key.replace('~', '~0').replace('/', '~1')
                if key in issue_fields and item:
                    found.append('Native evidence limitation at ' + child + '; see retained producer result.')
                visit(item, child)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                visit(item, path + '/' + str(i))
    visit(output, '')
    return found


def _errors(validator, *args):
    if not callable(validator):
        return ["actual installed native validator required"]
    try:
        result = validator(*[copy.deepcopy(arg) for arg in args])
        result = result[0] if isinstance(result, tuple) and len(result) == 2 else result
        if not isinstance(result, list) or not all(isinstance(e, str) for e in result):
            return ["validator must return errors or (errors, warnings)"]
        return result
    except Exception as exc:
        return [f"native validation failed: {type(exc).__name__}: {exc}"]


def _is_foundation(native, producer):
    return producer in FOUNDATION_ADAPTERS or (
        producer in EXPANDED_ADAPTERS and isinstance(native, dict) and
        native.get('mode') == EXPANDED_ADAPTERS[producer])


def _workflow(native, producer):
    foundation = _is_foundation(native, producer)
    if producer not in ADAPTERS and not foundation:
        raise ValueError(NATIVE_ONLY.get(producer, "unregistered native schema; no implicit conversion"))
    if foundation:
        errors = validate_common(native, object_types=FOUNDATION_ADAPTERS.get(producer, {'customer'}))
        if errors:
            raise ValueError('foundation context: ' + '; '.join(errors))
    if not isinstance(native, dict) or not isinstance(native.get("workflow"), dict):
        raise ValueError("native original requires explicit workflow context for a common handoff")
    w = copy.deepcopy(native["workflow"])
    context = w.get("context")
    if not isinstance(context, dict):
        raise ValueError("workflow.context required")
    for field in ("institution_id", "legal_entity_id", "capacity", "represented_party",
                  "object_id", "object_type", "jurisdiction", "line_of_business", "purpose"):
        if not _text(context.get(field)):
            raise ValueError("workflow.context." + field + " required")
    identity, clock, kind = ('/object_id', '/as_of', native['object_type']) if foundation else ADAPTERS[producer]
    if context["object_id"] != pointer(native, identity) or context["object_type"] != kind:
        raise ValueError("workflow subject differs from authoritative native identity")
    if w.get("as_of") != pointer(native, clock):
        raise ValueError("workflow as_of differs from native assessment date")
    if not isinstance(w["as_of"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", w["as_of"]):
        raise ValueError("workflow as_of must be a YYYY-MM-DD date")
    date.fromisoformat(w["as_of"])
    if w.get("role") not in ROLES:
        raise ValueError("explicit institutional responsibility required")
    if w.get("classification") not in CLASSIFICATIONS:
        raise ValueError("explicit evidence classification required")
    if not isinstance(w.get("allowed_audiences"), list) or not w["allowed_audiences"] or not all(_text(x) for x in w["allowed_audiences"]):
        raise ValueError("nonempty allowed_audiences required")
    if w.get("audience") not in w["allowed_audiences"]:
        raise ValueError("audience is not in the supplied access scope")
    if w.get("classification") == "sar_restricted" and w.get("audience") != "authorized_fiu":
        raise ValueError("SAR-restricted common artifacts are limited to authorized_fiu")
    if producer == "suspicious-activity-report-drafter" and w["classification"] != "sar_restricted":
        raise ValueError("reporting-case artifacts cannot downgrade SAR confidentiality")
    if not isinstance(w.get("sources"), list) or not w["sources"]:
        raise ValueError("versioned source records required")
    for item in w["sources"]:
        if not isinstance(item, dict) or any(not _text(item.get(k)) for k in ("source_ref", "version")):
            raise ValueError("each source needs source_ref and version")
    issues = w.get("unresolved_issues")
    if not isinstance(issues, list) or not all(_text(x) for x in issues):
        raise ValueError("explicit unresolved_issues list required")
    return w


def build_packet(native_input, native_output, *, producer, native_validator):
    errors = _errors(native_validator, native_output, native_input)
    if errors:
        raise ValueError("producer: " + "; ".join(errors))
    w = _workflow(native_input, producer)
    # The common layer never interprets a package's ready label as full assurance.
    issues = list(w["unresolved_issues"]) + _native_issues(native_output)
    issues += ["Supplied evidence is not authenticated; professional review remains required."]
    metadata = {k: copy.deepcopy(w[k]) for k in ("context", "as_of", "sources")}
    metadata["unresolved_issues"] = issues
    output = {"contract_version": VERSION, "producer": producer,
              "native_output": copy.deepcopy(native_output),
              "native_input_hash": canonical_hash(native_input),
              "workflow": w, "unresolved_issues": issues,
              "action_taken": False, "approval": "not_requested",
              "execution": "not_performed", "human_review_required": True}
    output["artifact"] = build_artifact(metadata, output, producer=producer,
        artifact_type="compliance-review", completeness="partial", evaluability="partial", issues=issues)
    return output


def validate_packet(packet, native_input, *, producer, native_validator):
    if not isinstance(packet, dict):
        return ["packet must be an object"]
    try:
        expected = build_packet(native_input, packet.get("native_output"),
                                producer=producer, native_validator=native_validator)
        errors = validate_artifact(packet.get("artifact"), output={k: v for k, v in packet.items() if k != "artifact"})
        if canonical_hash(packet) != canonical_hash(expected):
            errors.append("packet differs from detached native input and producer validation")
        return errors
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        return [str(exc)]


def validate_field_mappings(source_packet, source_input, target, mappings, supplemental_inputs=None):
    """Bind every target field to detached evidence; no semantic/source assurance."""
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("reviewed field mappings required")
    supplemental = supplemental_inputs or {}
    if not isinstance(supplemental, dict):
        raise ValueError("supplemental_inputs must be detached named objects")
    covered = set()
    pools = {"source_input": source_input, "source_output": source_packet["native_output"],
             "supplemental": supplemental}
    for m in mappings:
        if not isinstance(m, dict) or set(m) != {"target_field", "source", "source_pointer", "basis", "reviewed_by", "source_refs"}:
            raise ValueError("mapping requires exact field/source/pointer/basis/reviewer/source_refs schema")
        field = m["target_field"]
        if field in covered or field not in target:
            raise ValueError("duplicate or unknown target field")
        if not _text(m["basis"]) or not _text(m["reviewed_by"]) or not isinstance(m["source_refs"], list) or not m["source_refs"] or not all(_text(x) for x in m["source_refs"]):
            raise ValueError("mapping basis and review/source evidence required")
        if m["source"] not in pools:
            raise ValueError("unrecognized detached mapping source")
        if canonical_hash(target[field]) != canonical_hash(pointer(pools[m["source"]], m["source_pointer"])):
            raise ValueError("receiver field differs from mapped source: " + field)
        covered.add(field)
    if covered != set(target):
        raise ValueError("every receiver-native field, including workflow, needs a source mapping")
    return supplemental


def build_handoff(source_packet, source_input, target_input, *, producer,
                  target_skill, producer_validator, receiver_validator, mappings,
                  supplemental_inputs=None):
    """Validate every native target field against separately retained source values.

    This adapter permits same-context/same-audience handoffs only. Cross-subject,
    cross-institution or audience projections need a separately reviewed adapter.
    Supplemental inputs are detached; only their hashes are retained in this packet.
    """
    errors = validate_packet(source_packet, source_input, producer=producer,
                             native_validator=producer_validator)
    if errors:
        raise ValueError("source: " + "; ".join(errors))
    target = copy.deepcopy(target_input)
    tw = _workflow(target, target_skill)
    sw = source_packet["workflow"]
    if tw["context"] != sw["context"] or tw["as_of"] != sw["as_of"]:
        raise ValueError("cross-context/time handoff unsupported; provide a reviewed native adapter")
    for key in ("classification", "audience", "allowed_audiences"):
        if tw[key] != sw[key]:
            raise ValueError("audience/classification changes require a separate disclosure review")
    if not set(source_packet["unresolved_issues"]).issubset(tw["unresolved_issues"]):
        raise ValueError("receiver workflow dropped source unresolved issues")
    if not {canonical_hash(s) for s in sw["sources"]}.issubset({canonical_hash(s) for s in tw["sources"]}):
        raise ValueError("receiver workflow dropped source provenance records")
    foundation_target = _is_foundation(target, target_skill)
    if _is_foundation(source_input, producer):
        if not foundation_target:
            raise ValueError('foundation-to-legacy source projection requires a reviewed native adapter')
        if target['knowledge_cutoff'] != source_input['knowledge_cutoff']:
            raise ValueError('cross-knowledge-cutoff handoff unsupported')
        if not {canonical_hash(s) for s in source_input['sources']}.issubset({canonical_hash(s) for s in target['sources']}):
            raise ValueError('receiver dropped or altered detached source facts')
    supplemental = validate_field_mappings(source_packet, source_input, target, mappings, supplemental_inputs)
    for m in mappings:
        if foundation_target and not set(m['source_refs']).issubset({s['source_ref'] for s in target['sources']}):
            raise ValueError('mapping cites sources outside receiver detached registry')
    errors = _errors(receiver_validator, target)
    if errors:
        raise ValueError("receiver: " + "; ".join(errors))
    return {"contract_version": VERSION, "source_packet": copy.deepcopy(source_packet),
            "target_skill": target_skill, "target_input": target,
            "target_input_hash": canonical_hash(target), "mappings": copy.deepcopy(mappings),
            "supplemental_hashes": {k: canonical_hash(v) for k, v in supplemental.items()},
            "authority_granted": False, "action_mode": "review-only",
            "mapping_assurance": "supplied_not_authenticated"}


def validate_handoff(packet, source_input, *, producer, target_skill,
                     producer_validator, receiver_validator, supplemental_inputs=None):
    try:
        expected = build_handoff(packet["source_packet"], source_input, packet["target_input"],
            producer=producer, target_skill=target_skill, producer_validator=producer_validator,
            receiver_validator=receiver_validator, mappings=packet["mappings"],
            supplemental_inputs=supplemental_inputs)
        return [] if canonical_hash(packet) == canonical_hash(expected) else ["handoff differs from detached reconstruction"]
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return [str(exc)]
