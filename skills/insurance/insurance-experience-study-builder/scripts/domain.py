"""Time-at-risk study with explicit delayed entry, censoring and constant intensities."""

from collections import defaultdict
from itertools import pairwise

from insurance_contract import iso_date
from native_support import PROFILE, SCOPE, D, blocked, dec, finding, result, start, unique, validate_schema

METHOD = "constant_intensity_act365_count"
SCHEMA = {
    "scope": SCOPE,
    "profile": PROFILE,
    "study_start": "date",
    "study_end": "date",
    "event_type": "text",
    "segments": [
        {
            "segment_id": "text",
            "expected_intensity": "nonnegative",
            "effective_from": "date",
            "effective_to": "date",
            "source_ref": "ref",
        }
    ],
    "exposures": [
        {
            "record_id": "text",
            "life_id": "text",
            "segment_id": "text",
            "entry_date": "date",
            "exit_date": "date",
            "exit_reason": "text",
            "source_ref": "ref",
        }
    ],
}


def validate(doc):
    return validate_schema(doc, SCHEMA)


def evaluate(doc):
    d, f = start(doc, SCHEMA, METHOD)
    empty = {"method": METHOD, "segments": None, "risk_sets": None, "rows": None, "credibility_assessed": False}
    if blocked(f):
        return result(f, empty)
    a, b = iso_date(d["study_start"]), iso_date(d["study_end"])
    if a >= b or b > iso_date(doc["as_of"]):
        f.append(finding("study_dates", "Study must have positive length and end no later than as_of"))
    if d["scope"]["currency"] != "NONE" or d["event_type"] not in {"death", "lapse"}:
        f.append(
            finding("unsupported_study", "Count-only death or first-lapse studies supported; no monetary weighting")
        )
    unique(d["segments"], "segment_id", f)
    unique(d["exposures"], "record_id", f)
    if not d["segments"] or not d["exposures"]:
        f.append(finding("empty_study", "Supplied segment rates and individual risk intervals required"))
    rates = {r["segment_id"]: r for r in d["segments"]}
    by_life = defaultdict(list)
    for r in d["segments"]:
        if iso_date(r["effective_from"]) > a or iso_date(r["effective_to"]) < b:
            f.append(finding("rate_dates", "Expected intensity must cover entire study interval", [r["source_ref"]]))
    for r in d["exposures"]:
        by_life[r["life_id"]].append(r)
        if r["segment_id"] not in rates or r["exit_reason"] not in {"event", "censored"}:
            f.append(
                finding(
                    "risk_definition",
                    "Every interval requires a known segment and event/censored exit",
                    [r["source_ref"]],
                )
            )
        if iso_date(r["entry_date"]) >= iso_date(r["exit_date"]) or iso_date(r["exit_date"]) > iso_date(doc["as_of"]):
            f.append(
                finding(
                    "risk_dates",
                    "Risk intervals require entry before exit and no future observation",
                    [r["source_ref"]],
                )
            )
    for life, rows in by_life.items():
        ordered = sorted(rows, key=lambda r: r["entry_date"])
        for prev, nxt in pairwise(ordered):
            if nxt["entry_date"] < prev["exit_date"] or prev["exit_reason"] == "event":
                f.append(
                    finding(
                        "risk_overlap",
                        f"{life}: overlapping intervals or exposure after terminal study event",
                        [prev["source_ref"], nxt["source_ref"]],
                    )
                )
    if blocked(f):
        return result(f, empty)
    cells = {
        k: {"days": D(0), "observed": D(0), "censored": 0, "source_refs": {v["source_ref"]}} for k, v in rates.items()
    }
    out_rows, event_dates = [], set()
    for r in d["exposures"]:
        entry, end = max(a, iso_date(r["entry_date"])), min(b, iso_date(r["exit_date"]))
        days = max((end - entry).days, 0)
        event = r["exit_reason"] == "event" and a < iso_date(r["exit_date"]) <= b and days > 0
        cell = cells[r["segment_id"]]
        cell["days"] += D(days)
        cell["observed"] += int(event)
        cell["censored"] += int(days > 0 and not event)
        cell["source_refs"].add(r["source_ref"])
        out_rows.append(
            {
                "record_id": r["record_id"],
                "life_id": r["life_id"],
                "segment_id": r["segment_id"],
                "risk_start": str(entry),
                "risk_end": str(end),
                "exposure_days": days,
                "observed_event": event,
                "source_ref": r["source_ref"],
            }
        )
        if event:
            event_dates.add(r["exit_date"])
    summaries = []
    for seg, c in cells.items():
        exposure = c["days"] / D(365)
        expected = exposure * D(str(rates[seg]["expected_intensity"]))
        if exposure == 0 or expected == 0:
            f.append(
                finding(
                    "zero_denominator",
                    f"{seg}: zero exposure or expected events; corresponding ratio undefined",
                    c["source_refs"],
                    "review",
                )
            )
        summaries.append(
            {
                "segment_id": seg,
                "exposure_days": dec(c["days"]),
                "exposure_years": dec(exposure),
                "observed_events": dec(c["observed"]),
                "expected_events": dec(expected),
                "central_observed_rate": dec(c["observed"] / exposure if exposure else None),
                "actual_to_expected": dec(c["observed"] / expected if expected else None),
                "right_censored_intervals": c["censored"],
                "source_refs": sorted(c["source_refs"]),
            }
        )
    risks = []
    for date in sorted(event_dates):
        rows = [r for r in out_rows if r["exposure_days"] > 0 and r["risk_start"] < date <= r["risk_end"]]
        risks.append(
            {
                "event_date": date,
                "at_risk_before_event": len(rows),
                "events": sum(r["observed_event"] and r["risk_end"] == date for r in rows),
                "life_ids": sorted(r["life_id"] for r in rows),
            }
        )
    return result(f, {**empty, "segments": summaries, "risk_sets": risks, "rows": out_rows})
