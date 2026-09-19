"""Supplied scenario comparison through explicitly ordered inuring layers."""

from decimal import Decimal
from domain_support import day, finding, money, num, profile_findings, result, structural


def validate(doc):
    errors = structural(doc, objects=("program_terms",), arrays=("programs", "scenarios"))
    d = doc.get("data", {})
    for collection, nested in (("programs", "layers"), ("scenarios", "events")):
        rows = d.get(collection)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            items = row.get(nested)
            if not isinstance(items, list) or not all(isinstance(x, dict) for x in items):
                errors.append(f"{collection}.{nested} must be an array of objects")
                continue
            for item in items:
                fields = (
                    ("attachment", "limit", "share", "aggregate_limit", "prior_erosion")
                    if nested == "layers"
                    else ("gross_loss",)
                )
                for key in fields:
                    try:
                        num(item.get(key))
                    except ValueError as exc:
                        errors.append(f"{key}: {exc}")
                if nested == "events" and (
                    not isinstance(item.get("eligible_layer_ids"), list)
                    or not all(isinstance(x, str) for x in item.get("eligible_layer_ids", []))
                ):
                    errors.append("event.eligible_layer_ids must explicitly enumerate reviewed eligible layers")
            if collection == "programs":
                try:
                    num(row.get("fixed_premium"))
                except ValueError as exc:
                    errors.append(str(exc))
                extras = row.get("scenario_additional_premiums")
                if not isinstance(extras, dict):
                    errors.append("scenario_additional_premiums must map each scenario to explicit amount")
                else:
                    for value in extras.values():
                        try:
                            num(value)
                        except ValueError as exc:
                            errors.append(str(exc))
    return errors


def evaluate(doc):
    d, f, comparisons = doc["data"], [], []
    f += profile_findings(doc, d["program_terms"], "program_terms")
    if not d["programs"] or not d["scenarios"]:
        f.append(finding("program_or_scenario_missing", "At least one supplied program and scenario required", []))
    profile_ok = not f
    program_ids = [p.get("program_id") for p in d["programs"]]
    scenario_ids = [s.get("scenario_id") for s in d["scenarios"]]
    duplicate_programs = {i for i in program_ids if not i or program_ids.count(i) > 1}
    duplicate_scenarios = {i for i in scenario_ids if not i or scenario_ids.count(i) > 1}
    for p in d["programs"]:
        for s in d["scenarios"]:
            refs = [p.get("source_ref"), s.get("source_ref")]
            issues = []
            if not profile_ok:
                issues.append("unusable program profile")
            if p.get("program_id") in duplicate_programs or s.get("scenario_id") in duplicate_scenarios:
                issues.append("duplicate or missing program/scenario identity")
            if not all(
                p.get(k) and p.get(k) == s.get(k) for k in ("currency", "loss_basis", "period_start", "period_end")
            ):
                issues.append("program/scenario currency, loss basis or period differs")
            if p.get("loss_basis") != "ground_up_occurrence_loss":
                issues.append("only ground_up_occurrence_loss scenarios supported")
            if not p.get("source_ref") or not s.get("source_ref"):
                issues.append("program or scenario source missing")
            layers = p["layers"]
            layer_ids = [x.get("layer_id") for x in layers]
            if not layers or any(not x for x in layer_ids) or len(layer_ids) != len(set(layer_ids)):
                issues.append("unique nonempty layer identities required")
            normalized = []
            for layer in layers:
                refs.append(layer.get("source_ref"))
                values = {
                    k: num(layer.get(k)) for k in ("attachment", "limit", "share", "aggregate_limit", "prior_erosion")
                }
                if (
                    not layer.get("source_ref")
                    or layer.get("inuring_basis") != "remaining_loss"
                    or layer.get("type") not in ("quota_share", "occurrence_xol")
                ):
                    issues.append(f"{layer.get('layer_id')}: source/type/ordered remaining_loss basis unsupported")
                if None in values.values() or any(v < 0 for v in values.values() if v is not None):
                    issues.append(
                        f"{layer.get('layer_id')}: all nonnegative financial fields required including prior erosion and share"
                    )
                elif (
                    values["share"] > 1
                    or values["prior_erosion"] > values["aggregate_limit"]
                    or values["limit"] == 0
                    or values["aggregate_limit"] == 0
                ):
                    issues.append(f"{layer.get('layer_id')}: invalid participation or capacity")
                elif layer["type"] == "quota_share" and values["attachment"] != 0:
                    issues.append(f"{layer.get('layer_id')}: quota share attachment must be explicit zero")
                normalized.append((layer, values))
            event_ids, previous_date = set(), None
            if not s["events"]:
                issues.append("scenario event schedule empty; explicit no-loss scenario needs a zero-loss event")
            for event in s["events"]:
                refs.append(event.get("source_ref"))
                eid = event.get("event_id")
                if not eid or eid in event_ids:
                    issues.append("duplicate or missing event identity")
                event_ids.add(eid)
                value = num(event.get("gross_loss"))
                if value is None or value < 0 or not event.get("source_ref"):
                    issues.append(f"{eid}: sourced nonnegative gross loss required")
                if any(x not in layer_ids for x in event["eligible_layer_ids"]):
                    issues.append(f"{eid}: eligible layer ID unknown to program")
                try:
                    when = day(event["event_date"])
                    if not day(p["period_start"]) <= when <= day(p["period_end"]) or (
                        previous_date and when < previous_date
                    ):
                        issues.append(f"{eid}: event is outside period or out of chronological order")
                    previous_date = when
                except (KeyError, ValueError, TypeError):
                    issues.append(f"{eid}: event/program dates missing or invalid")
            premium = num(p.get("fixed_premium"))
            additional = num(p.get("scenario_additional_premiums", {}).get(s.get("scenario_id")))
            if premium is None or additional is None or premium < 0 or additional < 0:
                issues.append("fixed and scenario-specific additional premiums must be explicit nonnegative amounts")
            entry = {
                "program_id": p.get("program_id"),
                "scenario_id": s.get("scenario_id"),
                "currency": p.get("currency"),
                "evaluation_status": "not_evaluable" if issues else "illustrative",
                "issues": issues,
                "source_refs": sorted(set(x for x in refs if x)),
                "events": None,
                "total_gross_loss": None,
                "illustrative_recoverable": None,
                "retained_loss": None,
                "supplied_total_premium": None,
                "retained_loss_plus_premium": None,
            }
            if issues:
                f.append(
                    finding(
                        "program_scenario_not_evaluable",
                        f"{p.get('program_id')}/{s.get('scenario_id')}: {'; '.join(issues)}",
                        refs,
                    )
                )
            else:
                remaining_caps = {
                    layer["layer_id"]: v["aggregate_limit"] - v["prior_erosion"] for layer, v in normalized
                }
                gross_total, recovery_total = Decimal(0), Decimal(0)
                events = []
                for event in s["events"]:
                    gross = num(event["gross_loss"])
                    remaining = gross
                    layer_results = []
                    for layer, v in normalized:
                        lid = layer["layer_id"]
                        eligible = lid in event["eligible_layer_ids"]
                        basis = remaining
                        pre_share = min(max(basis - v["attachment"], Decimal(0)), v["limit"])
                        calculated = pre_share * v["share"] if eligible else Decimal(0)
                        recovery = min(calculated, remaining_caps[lid], remaining)
                        remaining_caps[lid] -= recovery
                        remaining -= recovery
                        layer_results.append(
                            {
                                "layer_id": lid,
                                "reviewed_eligible": eligible,
                                "inuring_loss": money(basis),
                                "before_aggregate_recoverable": money(calculated),
                                "illustrative_recoverable": money(recovery),
                                "remaining_aggregate": money(remaining_caps[lid]),
                                "source_ref": layer["source_ref"],
                            }
                        )
                    gross_total += gross
                    recovery_total += gross - remaining
                    events.append(
                        {
                            "event_id": event["event_id"],
                            "gross_loss": money(gross),
                            "retained_loss": money(remaining),
                            "layers": layer_results,
                            "source_ref": event["source_ref"],
                        }
                    )
                retained = gross_total - recovery_total
                entry.update(
                    events=events,
                    total_gross_loss=money(gross_total),
                    illustrative_recoverable=money(recovery_total),
                    retained_loss=money(retained),
                    supplied_total_premium=money(premium + additional),
                    retained_loss_plus_premium=money(retained + premium + additional),
                )
            comparisons.append(entry)
    return result(
        f,
        {
            "comparisons": comparisons,
            "comparison_basis": "supplied deterministic event scenarios and ordered remaining-loss layers; no probabilities, PML, optimized purchase or legal recoverability implied",
            "recommended_program": None,
        },
    )
