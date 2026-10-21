"""Investment-specific adapter over workflow-evidence/1.0 (MIT).

Original inputs stay detached. Content binding is not source authentication,
license verification, approval or execution. Native adapters are deliberately bounded.
"""
from __future__ import annotations
import copy
import functools
import re
from datetime import date

from native_integrity import canonical_hash
from workflow_contract import build_artifact as workflow_artifact
from workflow_contract import validate_artifact, make_handoff as workflow_handoff
from workflow_contract import validate_handoff as workflow_validate_handoff

VERSION = "investment-evidence/1.0"
SUBJECTS = {"manager", "fund", "share_class", "portfolio", "account", "mandate",
            "investor", "issuer", "security", "manager_candidate", "platform", "institution", "product", "provider", "strategy"}


def _adapter(identity, as_of, subjects, **context):
    return {"identity_pointer": identity, "as_of_pointer": as_of,
            "subject_types": list(subjects), "context_pointers": context}


# These paths come from native input schemas, never from a caller's arbitrary
# pointer selection. Unsupported aggregate/time schemas remain native-only.
NATIVE_ADAPTERS = {
    "institutional-proposal-responder": _adapter("/client/client_id", "/as_of_date", ["investor"]),
    "investment-commentary-builder": _adapter("/fund/fund_id", "/as_of_date", ["fund"], currency="/fund/currency"),
    "fund-fact-sheet-builder": _adapter("/fund/fund_id", "/as_of_date", ["fund"], currency="/fund/currency"),
    "investment-thesis-monitor": {"blocked_reason": "Multi-thesis native input has no authoritative single subject or batch identity."},
    "investment-committee-memo-builder": {"blocked_reason": "Native deal schema has no authoritative review as-of date."},
    "investment-manager-due-diligence-reviewer": _adapter("/manager/manager_id", "/as_of", ["manager", "manager_candidate"], currency="/currency", represented_party="/household_id"),
    "investment-mandate-reviewer": {"blocked_reason": "Multi-portfolio native input identifies a run, not a single mandate/portfolio subject."},
    "portfolio-characteristics-change-monitor": _adapter("/portfolio_id", "/as_of", ["portfolio", "fund"]),
    "portfolio-hedge-reviewer": _adapter("/portfolio/id", "/as_of", ["portfolio", "fund"], currency="/base_currency", units="/units"),
    "portfolio-exposure-analyzer": _adapter("/portfolio_id", "/as_of", ["portfolio", "fund"], currency="/base_currency"),
    "portfolio-risk-contribution-analyzer": _adapter("/portfolio_id", "/as_of", ["portfolio", "fund"], currency="/currency", units="/units"),
    "portfolio-stress-test-runner": _adapter("/portfolio_id", "/as_of", ["portfolio", "fund"], currency="/base_currency", units="/units"),
    "fund-liquidity-assessor": _adapter("/portfolio_id", "/as_of", ["portfolio", "fund"], currency="/base_currency"),
    "portfolio-cashflow-forecaster": _adapter("/portfolio_id", "/as_of", ["portfolio", "fund"], currency="/currency", units="/units"),
    "counterparty-exposure-monitor": {"blocked_reason": "Native as-of permits a timezone-free timestamp; date/time conversion requires a declared adapter."},
    "portfolio-performance-attributor": _adapter("/portfolio_id", "/period/to", ["portfolio", "fund"], currency="/base_currency", units="/units"),
    "performance-composite-reviewer": _adapter("/firm_id", "/as_of", ["manager"]),
    "fund-valuation-oversight-reviewer": _adapter("/book", "/as_of", ["fund", "portfolio", "account"]),
    "fund-nav-control-reviewer": _adapter("/fund", "/as_of", ["fund"], currency="/base_currency", book_basis="/position_basis"),
    "investment-book-reconciler": _adapter("/entity", "/as_of", ["fund", "portfolio", "account"], currency="/base_currency", book_basis="/position_basis"),
    "proxy-voting-reviewer": {"modes": {
        "evidence": _adapter("/input/meeting/issuer_id", "/input/as_of", ["issuer"]),
        "policy": _adapter("/input/mandate_id", "/input/as_of", ["mandate"]),
    }},
    "issuer-engagement-reviewer": _adapter("/issuer/issuer_id", "/as_of_date", ["issuer"]),
    "investment-data-quality-reviewer": {"modes": {
        "data_quality": _adapter("/input/portfolio_id", "/input/as_of", ["portfolio", "fund"]),
        "vendor_feed": _adapter("/input/entity", "/input/as_of", ["manager", "platform"], currency="/input/currency"),
    }},
    "investment-reference-data-reviewer": _adapter("/entity", "/as_of", ["manager", "platform"]),
    "research-source-indexer": {"blocked_reason": "Native job_ref identifies metadata-indexing work, not an investment subject."},
    "investment-record-normalizer": {"blocked_reason": "Native bundle_id identifies a heterogeneous record batch, not an investment subject."},
    "credit-document-terms-reviewer": _adapter("/issuer", "/effective_date", ["issuer"]),
    "issuer-credit-surveillance-reviewer": _adapter("/issuer/issuer_id", "/issuer/as_of", ["issuer"]),
}

# Phase2 foundations use a single explicit native object/date/currency. Mixed
# result units are fixed by the native schema, never implicitly rescaled in a handoff.
FOUNDATION_SUBJECTS = {
    'portfolio-transition-planner':['portfolio', 'fund', 'account'],
    'securities-financing-reviewer':['portfolio', 'fund', 'account'],
    'private-fund-financing-reviewer':['fund'],
    'private-fund-restructuring-reviewer':['fund', 'investor'],
    'tokenized-fund-operations-reviewer':['fund', 'share_class'],
    'sustainability-mandate-reviewer':['mandate', 'portfolio', 'fund'],

    'investment-data-architecture-planner':['platform','manager'],
    'investment-platform-modernization-planner':['platform','manager'],
    'investment-operating-model-planner':['manager','platform'],
    'investment-ai-workflow-designer':['platform','manager','strategy'],
    'asset-manager-economics-analyzer':['manager'],
    'investment-product-lifecycle-planner':['product','fund','manager'],
    'investment-distribution-planner':['manager','product','fund'],
    'investment-client-service-preparer':['investor','institution','manager','mandate'],
    'investment-investor-report-builder':['investor','fund','portfolio','mandate'],
    'systematic-investment-research-reviewer':['strategy','portfolio'],
    'private-investment-due-diligence-reviewer':['issuer','security','fund','portfolio'],
    'private-investment-monitor':['issuer','security','fund','portfolio'],
    'private-credit-investment-reviewer':['issuer','security','fund','portfolio'],
    'institutional-investment-policy-builder':['institution','mandate','investor'],
    'asset-allocation-planner':['institution','portfolio','fund','mandate'],
    'portfolio-construction-analyzer':['portfolio','fund','account','mandate'],
    'portfolio-rebalancing-planner':['portfolio','fund','account'],
    'tax-aware-portfolio-implementation-reviewer':['portfolio','account'],
    'buy-side-trading-planner':['portfolio','fund','account'],
    'portfolio-performance-measurer':['portfolio','fund','account'],
    'private-fund-performance-analyzer':['fund','investor'],
    'fund-accounting-preparer':['fund','share_class'],
    'investment-asset-servicing-reviewer':['portfolio','fund','account'],
    'fund-investor-operations-reviewer':['fund','investor'],
    'fund-service-provider-oversight-reviewer':['fund','provider','manager'],
    'index-portfolio-reviewer':['portfolio','fund'],
    'etf-operations-reviewer':['fund','share_class'],
    'private-fund-capital-activity-reviewer':['fund','investor'],
    'private-capital-commitment-planner':['institution','investor','fund'],
    'private-fund-waterfall-reviewer':['fund','investor'],
    'institutional-investment-solutions-planner':['institution','investor','mandate','portfolio'],
    'investment-regulatory-obligation-reviewer':['institution','manager','fund','mandate'],
    'investment-disclosure-reviewer':['manager','fund','product'],
}

def _foundation_adapter(subjects):
    result=_adapter('/object_id','/as_of',subjects,currency='/currency')
    result['units_literal']='native-schema'
    return result

for _name,_subjects in FOUNDATION_SUBJECTS.items():
    NATIVE_ADAPTERS[_name]=_foundation_adapter(_subjects)

for _name,_modes,_subjects in [
    ('institutional-proposal-responder',['rfp'],['investor','institution','manager','fund','mandate']),
    ('investment-manager-due-diligence-reviewer',['institutional'],['manager','manager_candidate','mandate','investor']),
    ('investment-committee-memo-builder',['public-security','manager','allocation'],['security','manager','manager_candidate','portfolio','institution','mandate']),
]:
    NATIVE_ADAPTERS[_name]['foundation_modes']=_modes
    NATIVE_ADAPTERS[_name]['foundation_adapter']=_foundation_adapter(_subjects)

# Phase4 extensions retain explicit dispatch and earlier native schemas.
FOUNDATION_EXTENSIONS = {'portfolio-hedge-reviewer': 'advanced-derivatives', 'portfolio-performance-attributor': 'specialist-attribution', 'systematic-investment-research-reviewer': 'walk-forward', 'etf-operations-reviewer': 'specialized-basket', 'institutional-investment-solutions-planner': 'liability-real-assets', 'investment-regulatory-obligation-reviewer': 'jurisdiction-profile-comparison'}
for _name,_extension in FOUNDATION_EXTENSIONS.items():
    NATIVE_ADAPTERS[_name]['foundation_extensions']=[_extension]
    NATIVE_ADAPTERS[_name]['foundation_extension_adapter']=_foundation_adapter(
        FOUNDATION_SUBJECTS.get(_name,['portfolio','fund']))

# Temporary read compatibility for pre-migration packages; merged aliases retain
# their original unwrapped native schema. Canonical names require explicit mode.
_ALIASES = {
    "due-diligence-questionnaire-responder": "institutional-proposal-responder",
    "fund-commentary-drafter": "investment-commentary-builder",
    "mandate-compliance-monitor": "investment-mandate-reviewer",
    "portfolio-drift-monitor": "portfolio-characteristics-change-monitor",
    "hedge-analysis-support-packet": "portfolio-hedge-reviewer",
    "portfolio-risk-contribution-packet": "portfolio-risk-contribution-analyzer",
    "liquidity-stress-analyzer": "fund-liquidity-assessor",
    "portfolio-cashflow-liquidity-forecaster": "portfolio-cashflow-forecaster",
    "performance-attribution-builder": "portfolio-performance-attributor",
    "composite-account-membership-checker": "performance-composite-reviewer",
    "valuation-exception-packet": "fund-valuation-oversight-reviewer",
    "nav-preparation-tie-out": "fund-nav-control-reviewer",
    "position-cash-reconciliation-assistant": "investment-book-reconciler",
    "engagement-history-brief": "issuer-engagement-reviewer",
    "security-master-enricher": "investment-reference-data-reviewer",
    "investment-source-ingester": "research-source-indexer",
    "holdings-transaction-normalizer": "investment-record-normalizer",
    "credit-terms-covenant-extractor": "credit-document-terms-reviewer",
    "credit-surveillance-packet": "issuer-credit-surveillance-reviewer",
}
_LEGACY_MODES = {
    "proxy-meeting-evidence-packet": ("proxy-voting-reviewer", "evidence"),
    "voting-policy-consistency-checker": ("proxy-voting-reviewer", "policy"),
    "investment-data-quality-exception-detector": ("investment-data-quality-reviewer", "data_quality"),
    "investment-vendor-feed-reconciler": ("investment-data-quality-reviewer", "vendor_feed"),
}


def adapter_manifest():
    """Return reviewable schema support; does not imply professional acceptance."""
    return copy.deepcopy(NATIVE_ADAPTERS)


def _resolve_adapter(producer, native):
    if not isinstance(producer, str):
        raise ValueError("native_skill or explicit producer/receiver is required")
    if producer in _LEGACY_MODES:
        name, mode = _LEGACY_MODES[producer]
        adapter = copy.deepcopy(NATIVE_ADAPTERS[name]["modes"][mode])
        adapter["identity_pointer"] = adapter["identity_pointer"].removeprefix("/input")
        adapter["as_of_pointer"] = adapter["as_of_pointer"].removeprefix("/input")
        adapter["context_pointers"] = {k: v.removeprefix("/input") for k, v in adapter["context_pointers"].items()}
        return adapter
    name = _ALIASES.get(producer, producer)
    adapter = NATIVE_ADAPTERS.get(name)
    if adapter is None:
        raise ValueError("unsupported native producer/receiver; declare an authoritative adapter first")
    if 'foundation_extensions' in adapter and isinstance(native,dict):
        if 'extension' in native:
            if native['extension'] not in adapter['foundation_extensions']:
                raise ValueError('unsupported native specialist extension')
            return adapter['foundation_extension_adapter']
        if native.get('contract_version')=='investment-foundation/1.0':
            return adapter['foundation_extension_adapter']
    if 'foundation_modes' in adapter and isinstance(native,dict) and (
        native.get('mode') in adapter['foundation_modes'] or native.get('contract_version')=='investment-foundation/1.0'
    ):
        return adapter['foundation_adapter']
    if "blocked_reason" in adapter:
        raise ValueError("native-only adapter: " + adapter["blocked_reason"])
    if "modes" in adapter:
        mode = native.get("mode") if isinstance(native, dict) else None
        if not isinstance(mode, str) or mode not in adapter["modes"]:
            raise ValueError("merged native adapter requires a declared mode")
        adapter = adapter["modes"][mode]
    return adapter


def _safe_validation(function):
    """Public validators reject malformed JSON rather than crashing consumers."""
    @functools.wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
            return [f"invalid {function.__name__} content: {type(exc).__name__}: {exc}"]
    return checked


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and all(_text(v) for v in value)


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date must be YYYY-MM-DD")
    return date.fromisoformat(value)


@_safe_validation
def validate_request(doc, producer=None):
    if not isinstance(doc, dict):
        return ["request must be an object"]
    errors = []
    canonical_hash(doc)
    for key in ("request_id", "as_of", "knowledge_cutoff"):
        if not _text(doc.get(key)):
            errors.append(f"{key} required")
    cutoff = None
    try:
        _date(doc.get("as_of"))
        cutoff = _date(doc.get("knowledge_cutoff"))
    except ValueError as exc:
        errors.append(str(exc))
    context = doc.get("context", {})
    if not isinstance(context, dict):
        return errors + ["context must be an object"]
    for key in ("capacity", "represented_party", "object_id", "line_of_business", "currency", "units", "book_basis"):
        if not _text(context.get(key)):
            errors.append(f"context.{key} required (explicit not-applicable permitted)")
    if not isinstance(context.get("subject_type"), str) or context["subject_type"] not in SUBJECTS:
        errors.append("context.subject_type unsupported")
    if context.get("audience") != "internal-review":
        errors.append("cross-skill artifacts are internal-review only; create a separate publication projection")
    if not _strings(context.get("jurisdictions")) or not context["jurisdictions"]:
        errors.append("context.jurisdictions must be a nonempty list")
    native = doc.get("native_input")
    if not isinstance(native, dict):
        errors.append("native_input must be the receiver/producer native object")
    declared = doc.get("native_skill")
    if producer is not None and declared is not None and declared != producer:
        errors.append("native_skill differs from actual producer/receiver")
    try:
        adapter = _resolve_adapter(producer if producer is not None else declared, native)
        if context.get("subject_type") not in adapter["subject_types"]:
            errors.append("context.subject_type differs from authoritative native scope")
        for key, field, expected in (("native_identity_pointer", "identity_pointer", context.get("object_id")),
                                     ("native_as_of_pointer", "as_of_pointer", doc.get("as_of"))):
            authoritative = adapter[field]
            if doc.get(key) != authoritative:
                errors.append(f"{key} must be authoritative adapter path {authoritative}")
            if canonical_hash(pointer(native, authoritative)) != canonical_hash(expected):
                errors.append(f"{key} native value differs from context")
        for field, path in adapter["context_pointers"].items():
            if canonical_hash(context.get(field)) != canonical_hash(pointer(native, path)):
                errors.append(f"context.{field} differs from authoritative native field {path}")
        if 'units_literal' in adapter:
            if context.get('units')!=adapter['units_literal']:
                errors.append('foundation context.units must be native-schema; conversions require explicit mapped methods')
            if doc.get('knowledge_cutoff')!=native.get('knowledge_cutoff'):
                errors.append('foundation knowledge_cutoff differs from native request')
            if context.get('audience')!=native.get('audience'):
                errors.append('foundation audience differs from native request')
            # A wrapper may add provenance but cannot replace or omit the native
            # registry's version, observation time, knowledge time or restrictions.
            wrapped={x.get('source_ref'):x for x in doc.get('sources',[]) if isinstance(x,dict) and isinstance(x.get('source_ref'),str)}
            for source in native.get('sources',[]):
                if not isinstance(source,dict):raise ValueError('native source must be an object')
                candidate=wrapped.get(source.get('source_ref'),{})
                for key in ('source_ref','version','as_of','known_at','permitted_audiences','permitted_parties'):
                    if key in source and canonical_hash(source[key])!=canonical_hash(candidate.get(key)):
                        errors.append('foundation source registry metadata differs from wrapper')

    except (ValueError, KeyError, IndexError, TypeError) as exc:
        errors.append("native adapter: " + str(exc))
    if not _strings(doc.get("unresolved_issues", [])):
        errors.append("unresolved_issues must be strings")
    sources = doc.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must contain versioned source references")
    else:
        ids = set()
        for i, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"sources[{i}] must be an object"); continue
            for key in ("source_ref", "version", "as_of", "known_at", "permitted_use"):
                if not _text(source.get(key)):
                    errors.append(f"sources[{i}].{key} required")
            ref = source.get("source_ref")
            if isinstance(ref, str):
                if ref in ids: errors.append("duplicate source_ref")
                ids.add(ref)
            try:
                _date(source.get("as_of"))
                known = _date(source.get("known_at"))
                if cutoff and known > cutoff:
                    errors.append(f"sources[{i}] was not known at the knowledge cutoff")
            except ValueError as exc:
                errors.append(f"sources[{i}]: {exc}")
            # Optional supplied restrictions are enforced; absence still provides
            # no assertion that rights or client permissions were authenticated.
            for field, expected in (("permitted_audiences", context.get("audience")),
                                    ("permitted_parties", context.get("represented_party"))):
                if field in source and (not _strings(source[field]) or expected not in source[field]):
                    errors.append(f"sources[{i}].{field} excludes request scope")
    upstream = doc.get("upstream_artifacts", [])
    if not isinstance(upstream, list):
        errors.append("upstream_artifacts must be a list"); upstream = []
    for artifact in upstream:
        if not isinstance(artifact, dict) or artifact.get("contract_version") != "workflow-evidence/1.0":
            errors.append("upstream requires an explicit workflow-evidence/1.0 adapter")
        else:
            errors.extend(validate_artifact(artifact))
            if _date(artifact.get("as_of")) > _date(doc.get("as_of")):
                errors.append("upstream review as-of is later than receiver as-of")
            for source in artifact.get("sources", []):
                if not isinstance(source, dict):
                    errors.append("upstream source must be an object"); continue
                if cutoff and _date(source.get("known_at")) > cutoff:
                    errors.append("upstream evidence was not known at the receiver cutoff")
                for field, expected in (("permitted_audiences", context.get("audience")),
                                        ("permitted_parties", context.get("represented_party"))):
                    if field in source and (not _strings(source[field]) or expected not in source[field]):
                        errors.append(f"upstream source {field} excludes receiver scope")
    return errors


def native_issue_paths(result, path="result"):
    """Conservatively retain exception locations without copying sensitive text."""
    keys = {"warnings", "errors", "alerts", "exceptions", "findings", "gaps", "issues",
            "unresolved_issues", "missing_data", "missing_fields", "review_flags", "open_items",
            "unsupported_claims", "unapproved_messaging", "outstanding", "flags", "needs"}
    states = {"incomplete", "not-evaluable", "unavailable", "unsupported", "failed", "needs-data",
              "unknown", "unresolved", "blocked", "partial", "stale", "future", "pending",
              "unapproved", "data-gap", "reconcile-break", "numeric-break", "identity-mismatch"}
    found = []
    if isinstance(result, dict):
        for key, value in result.items():
            here = f"{path}/{key}"
            normalized = key.lower().replace("_", "-")
            exception_key = key in keys or normalized.endswith(("-gaps", "-issues", "-exceptions", "-errors", "-warnings", "-needs"))
            state = value.lower().replace("_", "-") if isinstance(value, str) else ""
            state_field = key in {"status", "state", "completeness", "evaluability", "data_status", "review_status"}
            bad_state = state in states or (state_field and any(state.startswith(s + "-") or state.endswith("-" + s) for s in states))
            if exception_key and value:
                found.append(f"native review finding retained at {here}")
            elif bad_state:
                found.append(f"native unresolved state retained at {here}")
            elif value is False and key in {"reconciled", "source_reference_resolved", "complete", "evaluable", "passed", "ok"}:
                found.append(f"native failed check retained at {here}")
            if key != "source_input":
                found.extend(native_issue_paths(value, here))
    elif isinstance(result, list):
        for i, item in enumerate(result):
            found.extend(native_issue_paths(item, f"{path}/{i}"))
    return list(dict.fromkeys(found))


def _validator_result(checked):
    if isinstance(checked, tuple):
        if len(checked) != 2:
            raise ValueError("native validator must return errors or (errors, warnings)")
        errors, warnings = checked
    else:
        errors, warnings = checked, []
    if not _strings(errors) or not _strings(warnings):
        raise ValueError("native validator must return lists of error/warning strings")
    return errors, warnings


def build_packet(request, native_result, *, producer, method, native_validator):
    errors = validate_request(request, producer=producer)
    if errors: raise ValueError("; ".join(errors))
    if not isinstance(native_result, dict): raise ValueError("native result must be an object")
    canonical_hash(native_result)
    if not callable(native_validator): raise ValueError("actual native output validator required")
    try:
        checked, warnings = _validator_result(native_validator(copy.deepcopy(native_result), copy.deepcopy(request["native_input"])))
    except Exception as exc:
        raise ValueError(f"native validation failed: {type(exc).__name__}: {exc}") from None
    if checked: raise ValueError("native output: " + "; ".join(checked))
    if not isinstance(method, dict) or any(not _text(method.get(k)) for k in ("id", "version", "implementation_version", "origin")):
        raise ValueError("method id/version/implementation_version/origin required")
    if method["origin"] != "local-analysis":
        raise ValueError("native packets require local-analysis origin; external or system-of-record origin requires a separate declared engine adapter")
    issues = list(dict.fromkeys(request.get("unresolved_issues", []) + native_issue_paths(native_result)
                               + (["native output validator retained review warnings"] if warnings else [])))
    result = {
        "investment_contract": VERSION, "request_id": request["request_id"],
        "knowledge_cutoff": request["knowledge_cutoff"], "method": copy.deepcopy(method),
        "method_metadata_assurance": "caller-declared-unverified",
        "native_input_hash": canonical_hash(request["native_input"]),
        "result": copy.deepcopy(native_result), "unresolved_issues": issues,
        "native_validation_warnings": copy.deepcopy(warnings),
        "action_taken": False, "human_review_required": True, "delivery_status": "not-delivered",
    }
    result["artifact"] = workflow_artifact(request, result, producer=producer,
        artifact_type="investment-native-review", completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable", issues=issues)
    return result


@_safe_validation
def validate_packet(packet, request=None, *, native_validator=None, integrity_only=False):
    """Validate native correspondence, or explicitly request envelope checks only.

    Source-bound validation requires the detached original request and the actual
    producer's native output validator. ``integrity_only=True`` checks supplied
    hashes/metadata, not whether a native validator ever accepted this content.
    Neither level authenticates the original inputs or supplies business approval.
    """
    if not isinstance(packet, dict): return ["packet must be an object"]
    canonical_hash(packet)
    errors = []
    if integrity_only is not True and integrity_only is not False:
        errors.append("integrity_only must be an explicit boolean")
    if integrity_only is True:
        if request is not None or native_validator is not None:
            errors.append("integrity-only checks cannot be combined with source-bound validation arguments")
    elif not isinstance(request, dict) or not callable(native_validator):
        errors.append("source-bound validation requires detached original request and actual native output validator; envelope checks require integrity_only=True")
    if packet.get("investment_contract") != VERSION: errors.append("unsupported investment contract")
    if packet.get("action_taken") is not False or packet.get("human_review_required") is not True or packet.get("delivery_status") != "not-delivered":
        errors.append("packet cannot grant action or delivery authority")
    artifact = packet.get("artifact")
    if not isinstance(artifact, dict) or artifact.get("contract_version") != "workflow-evidence/1.0":
        return errors + ["workflow-evidence/1.0 artifact required"]
    errors.extend(validate_artifact(artifact, input_doc=request, output=packet))
    context = artifact.get("context")
    if not isinstance(context, dict) or context.get("audience") != "internal-review":
        errors.append("packet audience must be internal-review")
    for field in ("unresolved_issues", "native_validation_warnings"):
        if not _strings(packet.get(field, [])):
            errors.append(f"packet.{field} must be strings")
    if not _strings(artifact.get("unresolved_issues")):
        return errors + ["artifact.unresolved_issues must be strings"]
    retained = set(artifact["unresolved_issues"])
    if not isinstance(packet.get("result"), dict): errors.append("native result must be an object")
    findings = native_issue_paths(packet.get("result"))
    if not set(findings).issubset(retained): errors.append("native findings were dropped")
    if packet.get("native_validation_warnings") and "native output validator retained review warnings" not in retained:
        errors.append("native validation warnings were dropped")
    if retained or findings or packet.get("unresolved_issues") or packet.get("native_validation_warnings"):
        if artifact.get("completeness") == "complete" or artifact.get("evaluability") == "evaluable":
            errors.append("unresolved/native findings cannot claim complete or fully evaluable")
    if not _text(packet.get("request_id")): errors.append("packet.request_id required")
    digest = packet.get("native_input_hash")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append("packet.native_input_hash must be a canonical digest")
    if isinstance(packet.get("result"), dict) and "input_hash" in packet["result"] and packet["result"]["input_hash"] != digest:
        errors.append("native result and packet original-input hashes differ")
    cutoff = _date(packet.get("knowledge_cutoff"))
    _date(artifact.get("as_of"))
    for i, source in enumerate(artifact.get("sources", [])):
        if not isinstance(source, dict):
            errors.append(f"artifact.sources[{i}] must be an object"); continue
        if any(not _text(source.get(k)) for k in ("source_ref", "version", "as_of", "known_at", "permitted_use")):
            errors.append(f"artifact.sources[{i}] requires investment source metadata")
        if _date(source.get("known_at")) > cutoff:
            errors.append(f"artifact.sources[{i}] was not known at the knowledge cutoff")
        for field, expected in (("permitted_audiences", "internal-review"),
                                ("permitted_parties", context.get("represented_party") if isinstance(context, dict) else None)):
            if field in source and (not _strings(source[field]) or expected not in source[field]):
                errors.append(f"artifact.sources[{i}].{field} excludes packet scope")
    method = packet.get("method")
    if not isinstance(method, dict) or any(not _text(method.get(k)) for k in ("id", "version", "implementation_version", "origin")):
        errors.append("packet method metadata required")
    elif method["origin"] != "local-analysis":
        errors.append("native packets require local-analysis origin; external or system-of-record origin requires a separate declared engine adapter")
    if packet.get("method_metadata_assurance") != "caller-declared-unverified":
        errors.append("method metadata must remain caller-declared-unverified")
    producer = artifact.get("producer")
    # Standalone validation checks registry identity; full schema/mode binding
    # additionally requires the detached original request.
    try:
        adapter = _resolve_adapter(producer, packet.get("result"))
        if not isinstance(context, dict) or context.get("subject_type") not in adapter["subject_types"]:
            errors.append("packet subject type differs from native adapter scope")
    except ValueError as exc:
        errors.append(str(exc))
    if request is not None:
        errors.extend(validate_request(request, producer=producer))
        if isinstance(request, dict):
            if packet.get("knowledge_cutoff") != request.get("knowledge_cutoff"): errors.append("knowledge cutoff changed")
            if packet.get("request_id") != request.get("request_id"): errors.append("request identity changed")
            if packet.get("native_input_hash") != canonical_hash(request.get("native_input")): errors.append("native original-input hash mismatch")
    if not errors and integrity_only is False:
        try:
            checked, warnings = _validator_result(native_validator(copy.deepcopy(packet["result"]), copy.deepcopy(request["native_input"])))
            errors.extend("native source reconstruction: " + error for error in checked)
            if packet.get("native_validation_warnings", []) != warnings:
                errors.append("native validation warnings differ from original-source validation")
        except Exception as exc:
            errors.append(f"native source validation failed: {type(exc).__name__}: {exc}")
    return errors


def pointer(doc, path):
    if path == "": return doc
    if not isinstance(path, str) or not path.startswith("/"): raise ValueError("mapping paths must be JSON pointers")
    node = doc
    for token in path[1:].split("/"):
        if re.search(r"~(?![01])", token): raise ValueError("invalid JSON pointer escape")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token): raise ValueError("noncanonical array index")
            node = node[int(token)]
        elif isinstance(node, dict): node = node[token]
        else: raise ValueError("JSON pointer traverses a scalar")
    return node


def _leaves(doc, path=""):
    if isinstance(doc, dict) and doc:
        return set().union(*(_leaves(v, path + "/" + k.replace("~", "~0").replace("/", "~1")) for k, v in doc.items()))
    if isinstance(doc, list) and doc:
        return set().union(*(_leaves(v, path + "/" + str(i)) for i, v in enumerate(doc)))
    return {path}


@_safe_validation
def validate_mapping(source_packet, target_request, mapping):
    """Check mapping structure only; never establish source native acceptance."""
    errors = validate_packet(source_packet, integrity_only=True)
    # target native_skill is required here because mapping is independently usable.
    errors.extend(validate_request(target_request))
    if errors: return errors
    if not isinstance(mapping, dict) or any(not _text(mapping.get(k)) for k in ("reviewed_by", "basis")):
        return ["explicit reviewed field mapping required; reviewer text is not authentication"]
    source_artifact = source_packet["artifact"]
    if mapping.get("source_artifact_hash") != source_artifact["artifact_hash"]:
        errors.append("mapping is not bound to the source artifact")
    if mapping.get("target_request_hash") != canonical_hash(target_request):
        errors.append("mapping is not bound to the complete target request")
    if _date(target_request["knowledge_cutoff"]) < _date(source_packet["knowledge_cutoff"]):
        errors.append("receiver knowledge cutoff precedes source review cutoff")
    if _date(target_request["as_of"]) < _date(source_artifact["as_of"]):
        errors.append("backward as-of handoff requires a separately declared temporal adapter")
    if source_artifact["context"] != target_request["context"]:
        context = mapping.get("context_mapping", {})
        if not isinstance(context, dict) or context.get("source") != source_artifact["context"] or context.get("target") != target_request["context"] or not _text(context.get("basis")):
            errors.append("cross-subject/currency/units/book/jurisdiction change requires explicit context mapping")
    # Source audience/party restrictions travel with inherited evidence.
    for i, source in enumerate(source_artifact["sources"]):
        for field, expected in (("permitted_audiences", target_request["context"]["audience"]),
                                ("permitted_parties", target_request["context"]["represented_party"])):
            if field in source and (not _strings(source[field]) or expected not in source[field]):
                errors.append(f"inherited sources[{i}].{field} excludes receiver scope")
    fields = mapping.get("fields")
    if not isinstance(fields, list) or not fields:
        return errors + ["mapping.fields must be a nonempty list"]
    covered = set()
    refs = {s["source_ref"] for s in target_request["sources"]}
    for item in fields:
        if not isinstance(item, dict):
            errors.append("field mapping must be an object"); continue
        try:
            target_path = item["target_path"]
            target_value = pointer(target_request["native_input"], target_path)
            if "source_path" in item:
                if "source_ref" in item or "value_hash" in item:
                    errors.append("mapping cannot combine source copy and additional-input branches")
                source_value = pointer(source_packet, item["source_path"])
                if canonical_hash(source_value) != canonical_hash(target_value): errors.append(f"mapped field differs: {target_path}")
            elif item.get("source_ref") not in refs or item.get("value_hash") != canonical_hash(target_value):
                errors.append(f"additional input requires its own source/hash: {target_path}")
            covered |= _leaves(target_value, target_path)
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            errors.append(f"invalid field mapping: {exc}")
    missing = _leaves(target_request["native_input"]) - covered
    if missing: errors.append("unmapped receiver fields: " + ", ".join(sorted(missing)))
    return errors


def make_handoff(source_packet, target_request, *, target_skill, requested_output, mapping, receiver_validator,
                 source_request, source_validator):
    # Structural preflight precedes the source reconstruction and receiver checks
    # in validate_handoff. No successful return can bypass those checks.
    errors = validate_packet(source_packet, integrity_only=True) + validate_request(target_request, producer=target_skill)
    if errors: raise ValueError("; ".join(errors))
    if target_request.get("native_skill") != target_skill:
        raise ValueError("handoff target_request.native_skill must identify the actual receiver")
    errors += validate_mapping(source_packet, target_request, mapping)
    if errors: raise ValueError("; ".join(errors))
    packet = workflow_handoff(source_packet["artifact"], target_skill=target_skill,
                              target_input=target_request, requested_output=requested_output)
    packet["source_packet"] = copy.deepcopy(source_packet)
    packet["mapping"] = copy.deepcopy(mapping)
    packet["mapped_target_request"] = copy.deepcopy(target_request)
    errors = validate_handoff(packet, target_skill=target_skill, receiver_validator=receiver_validator,
                              source_request=source_request, source_validator=source_validator)
    if errors: raise ValueError("; ".join(errors))
    return packet


@_safe_validation
def validate_handoff(packet, *, target_skill, receiver_validator, source_request, source_validator):
    """Require detached source reconstruction and the actual receiver validator."""
    if not isinstance(packet, dict): return ["handoff must be an object"]
    canonical_hash(packet)
    source = packet.get("source_packet")
    target = packet.get("target_input")
    errors = validate_packet(source, source_request, native_validator=source_validator)
    if not isinstance(target, dict): return errors + ["target_input required"]
    errors.extend(validate_request(target, producer=target_skill))
    if target.get("native_skill") != target_skill:
        errors.append("target native_skill must identify actual receiver")
    proposed = packet.get("mapped_target_request")
    if not isinstance(proposed, dict): return errors + ["mapped target request required"]
    errors.extend(validate_request(proposed, producer=target_skill))
    if errors: return errors
    errors.extend(validate_mapping(source, proposed, packet.get("mapping")))
    if packet.get("source_artifact") != source["artifact"]: errors.append("source artifact substitution")
    expected = workflow_handoff(source["artifact"], target_skill=target_skill,
                target_input=proposed, requested_output=packet.get("requested_output"))
    if canonical_hash(expected["target_input"]) != canonical_hash(target):
        errors.append("receiver input differs from reviewed mapping or inherited issues")
    if not callable(receiver_validator): return errors + ["actual receiver validator required"]
    errors.extend(workflow_validate_handoff(packet, target_skill=target_skill,
        receiver_validator=lambda request: receiver_validator(request["native_input"])))
    return errors
